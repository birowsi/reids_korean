import argparse
import csv
import os
import re
from pathlib import Path


CSV_PATH = Path("translation_work.csv")
BINARY_FALSE_POSITIVE_PATTERN = re.compile(r"^[\u3400-\u9fff][\x01-\x07]$")


MANUAL_FIXES = {
    "200": r"\1「엣… 자,잠깐 소령님… 큰일 났네… 어쩔 수 없지, 혼나러 가야겠다…」",
    "374": "미안…아스카…….",
    "513": r"\1「카츠라기대위아닙니까?」",
    "1587": r"\1「죄송해요카츠라기대위」",
    "1954": r"\1「『하모닉스』라는 말을 알고 있니?」",
    "2241": r"\1「하지만정신적으로상당히지쳐있습니다만…」",
    "2414": "아스카「역시 바다는 기분 좋아~!!」",
    "2641": r"\1「…내가기분상하게할만한짓이라도했나」",
    "3158": "아스카「당연하잖아! 내가 그린 거니까!」",
    "3197": "아스카「하면 되는 거네, 뭐든지」",
    "3274": r"\1「레이!무슨일이야?」",
    "3279": r"\1「아뇨아무것도요」",
    "4022": "아스카「오늘은 카지 씨랑 데이트야.」",
    "4043": "아스카「근데 말이야, 사실 나도 조금은 부끄러워…. 있잖아, 이상하지 않을까?」",
    "4048": "미사토「에바의 지상 요격은 늦을 거야. 0호기와 2호기를 지오프론트 내에 배치해!」",
    "4195": r"미사토「\1소위…. 오늘… 카지 군 만났어?」",
    "4757": r"\1「아니그러니까그게아니라……」",
    "4780": r"\1「오늘상영할영화는공포영화『악마의치키치키몬스터』다」",
    "4976": r"아스카「있잖아, 기념품 사 왔어. \1소위가 같이 못 갔으니까. 열심히 골랐다고」",
    "5808": r"\1「R1점」",
    "6457": r"\1「그러고 보니,이번엔 어디로 가는 거야?」",
    "6538": r"\1「상영시간도 다가오니, 음료수라도 사서 바로 들어가자」",
    "6576": r"아스카「\1소위,보고 있어. 나도 할 수 있는 일을! 우오오오오옷!!」",
    "6704": r"\1「아이다군」",
    "6715": r"\1「보통은『귀신은밖으로복은안으로』라고외치며콩을뿌려.사악한기운을쫓고,한해의무병장수를빌기위해서야」",
    "6738": r"레이「아\1소위님」",
    "6768": r"\1「음,저기… 자고 있을 때 보는 환상의 영화 같은 걸까? 즐거운 기분일 때는 즐거운 꿈을, 힘들 때는 무서운 꿈을…」",
    "6832": "켄스케「오랜만에 왔었지이.」",
    "7419": "아스카「응. 열심히 만들었어. 맛있게 됐는지는 모르겠지만 한번 먹어 봐」",
    "7705": "아스카「하아… 이제 됐어. …정말, 퍼스트는 이래서 말이야…」",
    "7707": "아스카「글쎄, 앞으로 15바퀴 정도일까?」",
    "8409": r"\1「할수없지…하나둘셋」",
    "8422": r"\1「나나라면괜찮다면…」",
    "8820": r"\1「이건아오바중위에게…」",
    "9511": r"리츠코「\1소위.최근들어,아스카의싱크로율이떨어지기만하는군요」",
    "9617": r"레이「아, \1소위! 언제부터 거기에?」",
    "9629": "나와카츠라기대위의간청덕분인지,아스카일행수학여행참가허가.",
    "9895": r"\1「이젠너와헤어질일없어」",
    "9964": r"리츠코「\1소위,지금부터본부로와줄수있겠어?」",
    "10190": "아스카「어때♪ 소위가 보기에도 나 매력적이야? 말 걸고 싶어지지?」",
    "10329": r"미사토「그래서,\1소위.미안하지만,엔트리플러그를회수해서,세사람을구해다줄수있을까?」",
    "10560": "카츠라기대위는의미심장한미소를띠며아스카에게속삭였다.",
    "10584": r"카지「뭐,숨돌리고놀면서즐기는건인생에서중요한일이니까,\1소위에게잘보살핌을받는게좋을거야」",
    "10797": r"\1「내가옆에서간호할테니아무생각말고쉬어」",
    "10862": r"\1「아,아카기박사님.날씨가좋아서잠깐산책하려고요」",
    "10884": r"\1「…이상한녀석이군」",
    "10927": r"\1「요즘신지군얘기를자주하던데무슨일있었어?」",
    "10950": r"\1「레이가소풍왔던곳은분명이산이었지.그때만들어준도시락은…」",
    "1694": "【소지품과다.\n하나만더쇼핑가능.】",
    "1938": "\n레이「…볼래」",
    "2919": "그말을듣고,나는레이의발밑으로시선을옮겼다.\n그때.",
    "2927": "\n레이「그래서?뭐어쨌다고?」",
    "3486": "\n레이「…할래」",
    "3638": "\n레이「…읽을래」",
    "8684": r"「\i임」",
    "9162": r"레이「\1…\2」",
}


def replace_control_bytes_with_escapes(source, translation):
    for number in range(1, 10):
        escape = f"\\{number}"
        control = chr(number)
        expected = source.count(escape)
        present = translation.count(escape)
        replacements = min(
            max(expected - present, 0),
            translation.count(control),
        )
        for _ in range(replacements):
            translation = translation.replace(control, escape, 1)
    return translation


def repair_rows(rows):
    changed = []

    for row in rows:
        row_id = row["ID"]
        source = row["Japanese"]
        original = row["Korean"]
        repaired = replace_control_bytes_with_escapes(source, original)

        if BINARY_FALSE_POSITIVE_PATTERN.fullmatch(source):
            repaired = source

        if row_id == "424" and repaired.startswith(r"\1"):
            repaired = repaired[2:]

        if row_id in {"1863", "4112"}:
            repaired = repaired.replace(r"\n", "\n")

        if row_id in MANUAL_FIXES:
            repaired = MANUAL_FIXES[row_id]

        from repair_translation_review import reviewed_translation
        repaired = reviewed_translation(row, repaired)

        if repaired != original:
            row["Korean"] = repaired
            changed.append(row_id)

    return changed


def write_csv_atomic(path, rows):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["ID", "Japanese", "Korean"])
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp_path, path)


def main():
    parser = argparse.ArgumentParser(
        description="Apply deterministic translation-integrity repairs."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write repairs to translation_work.csv. The default is a dry run.",
    )
    args = parser.parse_args()

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    changed = repair_rows(rows)
    print(f"Rows requiring repair: {len(changed)}")
    print("IDs:", ",".join(changed))

    if args.write:
        write_csv_atomic(CSV_PATH, rows)
        print(f"Updated {CSV_PATH}")
    else:
        print("Dry run only. Pass --write to update the CSV.")


if __name__ == "__main__":
    main()
