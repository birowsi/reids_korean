"""Reviewed semantic corrections; never truncate text to meet a slot limit."""
import argparse
import csv
import re
from pathlib import Path

from repair_translation_style import load_capacities, validate_replacement, write_csv_atomic
from translation_codec import load_korean_mapping


REVIEW_FIXES = {
    "415": "나와 카츠라기 소령이 얘기하는 뒤편엔 아스카와 레이가 마주했다.",
    "510": "레이「그사람은소위와취미가같아…」",
    "570": r"\1「그렇네요…그러고보니,요즘카츠라기소령과만나고있나요?」",
    "810": r"\1「카츠라기소령왜!?」",
    "1435": r"\1「그래? 그럼 좀 깎아줘야겠네」",
    "2460": r"레이「\1소위가딴여자와있으면가슴이아파」",
    "3125": "레이「그쪽이 시끄럽잖아!!」",
    "3156": r"\1「설엔『새해복많이받으세요』라고해」",
    "3284": "그런 여유도 마음이 안정돼서겠지. 나로선 기쁘기 그지없다.",
    "3340": r"\1「레토르트랑 인스턴트뿐이잖아요. 직접 요리해 주세요」",
    "3511": r"\1「아,카츠라기 소령, 어디로?」",
    "4542": r"\1「소령님도 왠지 의욕 넘치시네요」",
    "5752": "카츠라기 소령이 들던 커피잔을 건네주었다.",
    "5971": r"\1「…아무것도…아냐…」",
    "6142": r"\1「대위?」",
    "6198": r"레이「\1소위가받아줬음해」",
    "6508": r"\1「소령님!」",
    "6532": r"\1「아,카지씨!…카츠라기소령도?」",
    "6634": r"\1「카츠라기소령,무슨일인가요?」",
    "7091": r"\1「그럼,카지씨,카츠라기소령…」",
    "8083": r"\1「신지군카츠라기소령과뭔가…?」",
    "8135": r"\1「소령님」",
    "8768": "이부키「카츠라기소령,보세요!」",
    "8951": "레이「알수없는사람이야」",
    "9393": r"\1「제 말입니까? 소령으로 승진해 월급 올랐을 텐데…」",
    "9442": "리츠코「해고 안 돼서 다행이네. 카츠라기 소령…」",
    "9893": "레이「소위…제얘기들어줄래요?」",
    "10011": "지정된장소에도착하자,그곳엔아카기박사,카츠라기소령,신지군이있었다.",
    "10062": r"\1「안녕하십니까카츠라기 소령」",
    "10327": "레이「소령이그랬어」",
    "11013": "레이「다음일요일엔어디로데려가달랠까…」",
    "11242": r"\1「조, 조금 덜 치댔나……」",
}


def visible_count(text):
    text = re.sub(r"\\+[A-Za-z0-9]+", "", text)
    return sum(ord(char) >= 0x20 for char in text)


def reviewed_translation(row, translation):
    translation = REVIEW_FIXES.get(row["ID"], translation)
    if "三佐" in row["Japanese"]:
        for old in ("삼좌", "삼사", "소좌"):
            translation = translation.replace(old, "소령")
        # 삼좌/소좌 end in a vowel, while 소령 ends in a consonant.
        for old, new in (("소령가", "소령이"), ("소령와", "소령과"),
                         ("소령는", "소령은"), ("소령를", "소령을"),
                         ("소령로", "소령으로")):
            translation = translation.replace(old, new)
    if "二尉" in row["Japanese"]:
        translation = translation.replace("이위", "중위")
    return translation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    with open("translation_work.csv", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))
    capacities = load_capacities()
    mapping = load_korean_mapping()
    changed = []
    for row in rows:
        replacement = reviewed_translation(row, row["Korean"])
        if row["ID"] in REVIEW_FIXES:
            if visible_count(replacement) > visible_count(row["Japanese"]):
                raise ValueError(f"ID {row['ID']}: reviewed text exceeds source character count")
        if replacement != row["Korean"]:
            used, capacity = validate_replacement(row, replacement, capacities, mapping)
            changed.append(row["ID"])
            print(f"ID {row['ID']}: {replacement!r} ({used}/{capacity} bytes)")
            row["Korean"] = replacement
    print(f"Reviewed changes: {len(changed)}")
    if args.write:
        write_csv_atomic(Path("translation_work.csv"), rows)


if __name__ == "__main__":
    main()
