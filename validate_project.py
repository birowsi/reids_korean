import csv
import json
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

from import_from_csv import canonical_source_text
from translation_codec import TextEncodingError, encode_fixed_length, encode_text
from translation_codec import load_korean_mapping


ROOT = Path(__file__).resolve().parent
LITERAL_CONTROL_PATTERN = re.compile(r"\\[A-Za-z0-9]+")
JAPANESE_PATTERN = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
ALLOWED_JAPANESE_PUNCTUATION = {"・", "ー"}
KNOWN_BRACKET_STYLE_EXCEPTIONS = {
    # Two exceptionally small dialogue slots use "speaker:text" because the
    # full-width dialogue pair cannot fit without losing the actual word.
    "882",
    "6220",
    # The Korean title already spells out the parenthetical reading "링링";
    # retaining the Japanese furigana-style parentheses would be redundant.
    "6741",
    "9278",
    "10624",
}


def load_jsonl(path):
    with path.open("r", encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


def real_controls(text):
    return [ord(char) for char in text if ord(char) < 0x20]


def classify_bracket_difference(row):
    source = row["Japanese"]
    translation = row["Korean"]
    differences = []
    style_only = False

    dialog_source = (source.count("「"), source.count("」"))
    dialog_target = (translation.count("「"), translation.count("」"))
    if dialog_source != dialog_target:
        curly_target = (translation.count("‘"), translation.count("’"))
        completed_source_fragment = (
            dialog_source in {(1, 0), (0, 1)} and dialog_target == (1, 1)
        )
        direct_quote_substitution = (
            dialog_target == (0, 0) and curly_target == dialog_source
        )
        if completed_source_fragment or direct_quote_substitution:
            style_only = True
        else:
            differences.append("「」")

    title_source = (source.count("『"), source.count("』"))
    title_target = (translation.count("『"), translation.count("』"))
    if title_source != title_target:
        differences.append("『』")

    aside_source = (source.count("（"), source.count("）"))
    aside_target = (translation.count("（"), translation.count("）"))
    aside_with_ascii = (
        aside_target[0] + translation.count("("),
        aside_target[1] + translation.count(")"),
    )
    if aside_source != aside_target:
        if aside_source == aside_with_ascii:
            style_only = True
        else:
            differences.append("（）")

    if row["ID"] in KNOWN_BRACKET_STYLE_EXCEPTIONS and differences:
        return [], True
    return differences, style_only


def validate():
    errors = []
    warnings = []
    bracket_style_substitutions = 0

    with (ROOT / "translation_work.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as source:
        rows = list(csv.DictReader(source))

    extracted = load_jsonl(ROOT / "extracted_texts.jsonl")
    translated = load_jsonl(ROOT / "translated_texts.jsonl")
    mapping = load_korean_mapping(ROOT / "nftr_korean_mapping.json")

    ids = [int(row["ID"]) for row in rows]
    if ids != list(range(len(rows))):
        errors.append("CSV IDs are not a unique contiguous sequence.")

    csv_by_source = {}
    for row in rows:
        key = canonical_source_text(row["Japanese"])
        if not row["Korean"].strip():
            errors.append(f"ID {row['ID']}: empty translation.")
        if key in csv_by_source and csv_by_source[key]["Korean"] != row["Korean"]:
            errors.append(f"ID {row['ID']}: conflicting normalized source key.")
        csv_by_source[key] = row

    extracted_sources = {canonical_source_text(item["text"]) for item in extracted}
    missing_csv = extracted_sources - set(csv_by_source)
    orphan_csv = set(csv_by_source) - extracted_sources
    if missing_csv:
        errors.append(f"{len(missing_csv)} extracted source strings have no CSV row.")
    if orphan_csv:
        errors.append(f"{len(orphan_csv)} CSV rows have no extracted source string.")

    if len(extracted) != len(translated):
        errors.append(
            f"JSONL line count mismatch: {len(extracted)} extracted, "
            f"{len(translated)} translated."
        )

    encoded_by_index = {}
    headroom = Counter()
    untranslated_count = 0

    for index, (original, localized) in enumerate(zip(extracted, translated)):
        localized_identity = {
            key: value
            for key, value in localized.items()
            if key != "translated_text"
        }
        if original != localized_identity:
            errors.append(f"JSONL line {index}: source metadata changed.")
            continue

        if "translated_text" not in localized:
            untranslated_count += 1
            continue

        source_text = original["text"]
        translated_text = localized["translated_text"]

        source_escapes = LITERAL_CONTROL_PATTERN.findall(source_text)
        translated_escapes = LITERAL_CONTROL_PATTERN.findall(translated_text)
        if source_escapes != translated_escapes:
            errors.append(
                f"JSONL line {index}: literal controls differ "
                f"{source_escapes!r} != {translated_escapes!r}."
            )

        if real_controls(source_text) != real_controls(translated_text):
            errors.append(
                f"JSONL line {index}: real control bytes differ "
                f"{real_controls(source_text)!r} != "
                f"{real_controls(translated_text)!r}."
            )

        capacity = len(bytes.fromhex(original["raw_hex"]))
        try:
            encoded = encode_text(translated_text, mapping)
        except TextEncodingError as exc:
            errors.append(f"JSONL line {index}: {exc}")
            continue

        if len(encoded) > capacity:
            errors.append(
                f"JSONL line {index}: {len(encoded)} bytes exceeds "
                f"{capacity} bytes."
            )
            continue

        encoded_by_index[index] = encode_fixed_length(
            translated_text,
            capacity,
            mapping,
        )
        headroom[capacity - len(encoded)] += 1

    if untranslated_count:
        errors.append(f"{untranslated_count} JSONL occurrences are untranslated.")

    for row in rows:
        source = row["Japanese"]
        translation = row["Korean"]
        residue = JAPANESE_PATTERN.findall(translation)
        substantive = [
            char for char in residue if char not in ALLOWED_JAPANESE_PUNCTUATION
        ]
        if substantive and source != translation:
            errors.append(
                f"ID {row['ID']}: Japanese text remains: {''.join(substantive)!r}."
            )

        if "三尉" in source and "소위" not in translation:
            errors.append(f"ID {row['ID']}: 三尉 is not translated as 소위.")
        if "一尉" in source and "대위" not in translation:
            errors.append(f"ID {row['ID']}: 一尉 is not translated as 대위.")

        bracket_differences, style_only = classify_bracket_difference(row)
        if bracket_differences:
            warnings.append(
                f"ID {row['ID']}: bracket structure differs for "
                f"{', '.join(bracket_differences)}."
            )
        elif style_only:
            bracket_style_substitutions += 1

    items_by_file = defaultdict(list)
    for index, item in enumerate(translated):
        items_by_file[item["file"]].append((index, item))

    for file_name, items in sorted(items_by_file.items()):
        backup_path = ROOT / "data" / f"{file_name}.bak"
        packed_path = ROOT / "data" / file_name
        backup = backup_path.read_bytes()
        packed = packed_path.read_bytes()

        if len(backup) != len(packed):
            errors.append(f"{file_name}: packed size differs from source backup.")
            continue

        entry_count = struct.unpack_from("<I", backup, 4)[0]
        header_size = struct.unpack_from("<I", backup, 8)[0]
        if header_size != 16 + 16 * entry_count:
            errors.append(f"{file_name}: inconsistent SCD header size.")

        allowed = bytearray(len(backup))
        for index, item in items:
            raw = bytes.fromhex(item["raw_hex"])
            offset = item["original_offset"]

            if backup[offset : offset + len(raw)] != raw:
                errors.append(
                    f"{file_name} line {index}: source bytes do not match raw_hex."
                )

            expected = encoded_by_index.get(index, raw)
            if packed[offset : offset + len(raw)] != expected:
                errors.append(
                    f"{file_name} line {index}: packed bytes do not match translation."
                )

            allowed[offset : offset + len(raw)] = b"\x01" * len(raw)

        outside_changes = sum(
            left != right and not allowed[index]
            for index, (left, right) in enumerate(zip(backup, packed))
        )
        if outside_changes:
            errors.append(
                f"{file_name}: {outside_changes} changed bytes are outside "
                "known text spans."
            )

    return errors, warnings, {
        "csv_rows": len(rows),
        "jsonl_occurrences": len(translated),
        "exact_fit": headroom[0],
        "warnings": len(warnings),
        "bracket_style_substitutions": bracket_style_substitutions,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    errors, warnings, summary = validate()

    print(
        "Validated "
        f"{summary['csv_rows']} unique translations / "
        f"{summary['jsonl_occurrences']} occurrences."
    )
    print(f"Exact byte fits: {summary['exact_fit']}")
    print(f"Bracket structure warnings: {summary['warnings']}")
    print(
        "Accepted bracket style substitutions: "
        f"{summary['bracket_style_substitutions']}"
    )

    if warnings:
        print("\nFirst 20 warnings:")
        for warning in warnings[:20]:
            print(f"- {warning}")

    if errors:
        print(f"\nFAILED with {len(errors)} error(s):")
        for error in errors[:100]:
            print(f"- {error}")
        if len(errors) > 100:
            print(f"- ... {len(errors) - 100} more")
        raise SystemExit(1)

    print("\nPASS: translation and packed-script integrity checks succeeded.")


if __name__ == "__main__":
    main()
