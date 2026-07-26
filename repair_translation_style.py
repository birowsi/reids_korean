import argparse
import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

from import_from_csv import canonical_source_text
from translation_codec import encode_text, load_korean_mapping


ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "translation_work.csv"
EXTRACTED_PATH = ROOT / "extracted_texts.jsonl"
MAPPING_PATH = ROOT / "nftr_korean_mapping.json"
LITERAL_CONTROL_PATTERN = re.compile(r"\\[A-Za-z0-9]+")


# These are intentionally explicit. Several source slots are too small for a
# mechanical "speaker + brackets + existing text" rewrite, so each constrained
# line has been phrased and measured individually.
SPEAKER_FIXES = {
    "514": "레이「재밌어?」",
    "719": "레이「사랑하면 세상이 달라 보인다는데, 정말…?」",
    "839": "레이「…!?」",
    "882": "레이:나무",
    "1093": r"레이「요즘,\1소위의시선이신경쓰여…」",
    "1183": "레이「하니?」",
    "1276": "레이「…다음일요일엔소위와코스프레의상만들자…」",
    "1352": "레이「이카리군」",
    "1394": "레이「다음일요일계획을생각해두자…」",
    "1484": "레이「그리고전세계사람들에게제연기보여주고싶어요」",
    "1498": "레이「아니…올거야」",
    "1718": "레이「초호기는 이카리군만 움직일수있어…」",
    "1729": "레이「그렇게봐?」",
    "1953": "레이「다음엔돼」",
    "2050": r"\1「글쎄….『일본 여성의 청초한 아름다움을 칭송하는 말』이라는 뜻일까?」",
    "2143": "레이「…뭐?」",
    "2393": "레이「다리…」",
    "2413": "레이「거짓」",
    "2435": "레이「한턱?」",
    "2472": "레이「카지씨는친절한사람.카츠라기소령을좋아하는것같아」",
    "2582": "레이「안경」",
    "2882": "레이「6위」",
    "2977": "레이「!」",
    "2995": "레이「괜찮아」",
    "3323": "레이「♪」",
    "3588": "레이「…!」",
    "3754": "레이「하지만」",
    "3861": "레이「이거」",
    "3899": "레이「!?…」",
    "5185": "레이「1위」",
    "5203": "레이「세워줘」",
    "5217": "레이「…단 거, 좋아해?」",
    "5223": "아스카「할수있어」",
    "5350": "레이「……별로」",
    "5394": "레이「거짓말」",
    "5763": "레이「나빠?」",
    "6059": "레이「마녀」",
    "6162": "레이「7위」",
    "6301": "신지「레이…」",
    "6701": "레이「응?」",
    "6702": "레이「괜찮아졌어?」",
    "6728": "레이「하지만」",
    "6833": r"레이「\1소위,내가 할수 있는 건 없어?」",
    "7405": "레이「이상해?」",
    "7897": r"레이「\1소위…」",
    "8593": "아스카「언제든지요」",
    "9163": "레이「2위」",
    "9467": "레이「모르겠어…」",
    "9725": "레이「돼?」",
    "9789": "레이「저건…」",
    "9843": r"레이「\1소위, 과찬이야…」",
    "9846": "레이「당신 누구…」",
    "10197": "아스카「일본…」",
    "10529": "레이「먼저」",
    "10666": "레이「없어」",
    "10823": "레이「…」",
    "10828": "레이「…아니」",
    "10848": "레이「음…」",
    "10850": "레이「함부로만지지마!」",
    "10858": "레이「비밀」",
    "10874": "레이「…상당히몸상태회복됐어」",
    "10925": "레이「…가만있어」",
    "10998": "레이「아스카」",
}


INNER_TITLE_IDS = {
    "2056",
    "2283",
    "2295",
    "3925",
    "4382",
    "5293",
    "5509",
    "5630",
    "5637",
    "5798",
    "5852",
    "6725",
    "7391",
    "8278",
    "8495",
    "8572",
    "9200",
    "9494",
    "10475",
}


STRUCTURAL_FIXES = {
    "48": "레이「어?」",
    "302": "레이「꺅!」",
    "395": "미사토「확인」",
    "736": "레이「지, 빤히 보지 마」",
    "918": "휴가「북동,고텐바방면에서도2개중대접근중!」",
    "1497": "레이「또 『코미케』예요?」",
    "1607": "아스카「『여심과 가을 하늘』이라잖아」",
    "1932": "레이「……!」",
    "2115": r"\1「대위님!」",
    "2163": "나는파도치는곳에서파도와장난치는레이의모습을멍하니보고있었다.좋겠다,이런것도…….",
    "2993": r"\1「(레이 씨의 코스프레는 『메이드 코만도☆미유키』인가. 귀엽네….)」",
    "3241": "레이「난 『시온』이 좋아요. 지금 제일 좋아하는 캐릭터예요」",
    "3568": "레이「………………」",
    "4156": "레이「무슨 일이야?」",
    "4244": "레이「그래…」",
    "4251": r"\1（음~…. 이거, 형편없는 성적이네.）",
    "4382": "레이「…「내뒤에서지마!」…」",
    "5142": "이부키「소위님?이부키예요」",
    "5290": "「품행단정한사람이좋다」",
    "5434": "레이「네♪」",
    "5912": r"\1「이목소리…」",
    "6210": "레이「네~!」",
    "6220": "이부키:1초",
    "6822": r"\1「살아서다행이야…정말」",
    "6818": "레이「네~ 알겠어요~」",
    "6841": r"\1(뭘까.레이가뭔가말하고싶은듯이이쪽을보고있어.)",
    "7108": r"\1（핫!? 그러고 보니, 여자에게 선 오일을 발라준 경험 같은 건 없잖아. 으음, 등은 당연하고….）",
    "7143": r"\1（아스카는 어떤 수영복을 가져왔을까….）",
    "7806": r"\1（이것이사도…네르프의…그리고레이가싸워야할적）",
    "7845": r"\1（어라?뭔가기분안좋아보이네）",
    "7889": r"\1（지금은레이를만날용기가없어）",
    "8211": "레이「핫!」",
    "8341": "레이「네!」",
    "8391": "레이「그래서?」",
    "8551": "겐도「위원회는 에바 시리즈 양산에 착수했다. 기회다, 후유츠키. 제레가 움직이기 전에, 모든 것을 끝내야 한다.」",
    "8716": "레이「왜?불렀어?」",
    "8677": "아오바「네」",
    "9162": r"레이「\1…\2」",
    "9507": "레이「피곤하네」",
    "9751": "레이「…알겠어요」",
    "9947": "레이「…………」",
    "10159": "레이「……?」",
    "10444": "레이「……………」",
    "10491": "레이「왜 그래?」",
    "10617": "레이「이게 『귀신 눈에도 눈물』이네…」",
    "10745": "레이「그렇지」",
    "11006": "레이「…그러네」",
    "11133": "레이「그럼, 제대로 해」",
    "11393": "레이「알겠어」",
}


SPEAKER_PREFIXES = {
    "綾波": "레이",
    "アスカ": "아스카",
    "ミサト": "미사토",
    "シンジ": "신지",
    "リツコ": "리츠코",
    "伊吹": "이부키",
    "加持": "카지",
    "青葉": "아오바",
    "マヤ": "마야",
    "ゲンドウ": "겐도",
    "冬月": "후유츠키",
    "日向": "휴가",
    "ケンスケ": "켄스케",
    "トウジ": "토우지",
    "ヒカリ": "히카리",
}


def normalize_speaker_spacing(source, translation):
    for japanese_name, korean_name in SPEAKER_PREFIXES.items():
        if source.startswith(japanese_name + "「"):
            spaced_prefix = korean_name + " 「"
            if translation.startswith(spaced_prefix):
                return korean_name + "「" + translation[len(spaced_prefix) :]
            break
    return translation


def normalize_title_quotes(source, translation):
    missing = source.count("『") - translation.count("『")
    while missing > 0 and "‘" in translation and "’" in translation:
        translation = translation.replace("‘", "『", 1).replace("’", "』", 1)
        missing -= 1

    while missing > 0:
        opening = translation.find("'")
        if opening < 0:
            break
        closing = translation.find("'", opening + 1)
        if closing < 0:
            break
        translation = (
            translation[:opening]
            + "『"
            + translation[opening + 1 : closing]
            + "』"
            + translation[closing + 1 :]
        )
        missing -= 1

    return translation


def replace_inner_dialog_with_title(source, translation):
    expected_dialogs = source.count("「")
    missing_titles = source.count("『") - translation.count("『")
    extra_dialogs = translation.count("「") - expected_dialogs
    replacements = min(missing_titles, extra_dialogs)
    if replacements <= 0:
        return translation

    opening_positions = [
        index for index, char in enumerate(translation) if char == "「"
    ]
    closing_positions = [
        index for index, char in enumerate(translation) if char == "」"
    ]

    # The outer dialogue opening is first and its closing is last. Convert the
    # nested pairs between them, preserving any source-level outer dialogue.
    replace_openings = set(
        opening_positions[expected_dialogs : expected_dialogs + replacements]
    )
    replace_closings = set(closing_positions[:replacements])

    return "".join(
        "『"
        if index in replace_openings
        else "』"
        if index in replace_closings
        else char
        for index, char in enumerate(translation)
    )


def load_capacities():
    capacities = defaultdict(list)
    with EXTRACTED_PATH.open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            item = json.loads(line)
            capacities[canonical_source_text(item["text"])].append(
                len(bytes.fromhex(item["raw_hex"]))
            )
    return {key: min(values) for key, values in capacities.items()}


def validate_replacement(row, replacement, capacities, mapping):
    source = row["Japanese"]
    source_controls = LITERAL_CONTROL_PATTERN.findall(source)
    target_controls = LITERAL_CONTROL_PATTERN.findall(replacement)
    if source_controls != target_controls:
        raise ValueError(
            f"ID {row['ID']}: literal controls differ "
            f"{source_controls!r} != {target_controls!r}"
        )

    capacity = capacities[canonical_source_text(source)]
    encoded_length = len(encode_text(replacement, mapping))
    if encoded_length > capacity:
        raise ValueError(
            f"ID {row['ID']}: replacement is {encoded_length} bytes, "
            f"capacity is {capacity}: {replacement!r}"
        )
    return encoded_length, capacity


def write_csv_atomic(path, rows):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["ID", "Japanese", "Korean"])
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp_path, path)


def main():
    parser = argparse.ArgumentParser(
        description="Apply reviewed speaker and dialogue-style repairs."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write repairs to translation_work.csv. The default is a dry run.",
    )
    args = parser.parse_args()

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    capacities = load_capacities()
    mapping = load_korean_mapping(MAPPING_PATH)
    changed = []

    for row in rows:
        replacement = SPEAKER_FIXES.get(row["ID"], row["Korean"])
        replacement = STRUCTURAL_FIXES.get(row["ID"], replacement)
        if row["ID"] in INNER_TITLE_IDS:
            replacement = replace_inner_dialog_with_title(
                row["Japanese"], replacement
            )
        replacement = normalize_speaker_spacing(row["Japanese"], replacement)
        replacement = normalize_title_quotes(row["Japanese"], replacement)
        if replacement is None or replacement == row["Korean"]:
            continue
        encoded_length, capacity = validate_replacement(
            row, replacement, capacities, mapping
        )
        changed.append(
            (row["ID"], row["Korean"], replacement, encoded_length, capacity)
        )
        row["Korean"] = replacement

    print(f"Rows requiring style repair: {len(changed)}")
    for row_id, old, new, encoded_length, capacity in changed:
        print(
            f"ID {row_id}: {old!r} -> {new!r} "
            f"({encoded_length}/{capacity} bytes)"
        )

    if args.write:
        write_csv_atomic(CSV_PATH, rows)
        print(f"Updated {CSV_PATH}")
    else:
        print("Dry run only. Pass --write to update the CSV.")


if __name__ == "__main__":
    main()
