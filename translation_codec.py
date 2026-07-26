import json
from pathlib import Path


# Characters used by the Korean script that are not directly encodable by
# Python's Shift-JIS codec, but have visually equivalent glyphs in the
# original game font.
ENCODING_ALIASES = {
    "·": "・",
    "—": "―",
}


class TextEncodingError(ValueError):
    pass


def load_korean_mapping(path="nftr_korean_mapping.json"):
    mapping_path = Path(path)
    with mapping_path.open("r", encoding="utf-8") as mapping_file:
        return json.load(mapping_file)


def encode_text(text, korean_mapping):
    encoded = bytearray()

    for index, original_char in enumerate(text):
        char = ENCODING_ALIASES.get(original_char, original_char)

        if char in korean_mapping:
            sjis = korean_mapping[char]["sjis"]
            encoded.extend(((sjis >> 8) & 0xFF, sjis & 0xFF))
            continue

        try:
            encoded.extend(char.encode("shift_jis"))
        except UnicodeEncodeError as exc:
            raise TextEncodingError(
                f"Unsupported character U+{ord(original_char):04X} "
                f"{original_char!r} at character index {index}"
            ) from exc

    return bytes(encoded)


def encode_fixed_length(text, capacity, korean_mapping):
    encoded = encode_text(text, korean_mapping)
    if len(encoded) > capacity:
        raise TextEncodingError(
            f"Encoded text is {len(encoded)} bytes but capacity is {capacity}: {text!r}"
        )
    return encoded.ljust(capacity, b"\x00")
