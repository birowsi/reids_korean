import csv
import json
import time
import argparse
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

CSV_FILE = 'translation_work.csv'
REPORT_FILE = 'review_report.md'

SYSTEM_INSTRUCTION = """
당신은 '신세기 에반게리온: 아야나미 육성계획 with 아스카 보완계획'의 전문 한국어 번역 검수자입니다.
제공되는 [ID, 원문(일본어), 현재번역(한국어)] 목록을 읽고, 다음 기준에 따라 명백한 '오역'이나 '문제가 있는 번역'만 꼼꼼히 찾아내세요.
1. 명백한 오역 (의미가 완전히 다름)
2. 캐릭터 붕괴 (아스카의 당돌함, 레이의 무미건조함, 리츠코/미사토의 성격 등)
3. 누락된 제어문자 (\n, \1, \2 등 기호가 빠지거나 깨짐)

문제가 발견된 항목들만 추려서 아래 형식의 JSON 배열로 반환하세요.
[
  {
    "ID": "행 번호",
    "Issue": "발견된 문제점 설명 (예: 아스카의 말투가 아님, 오역 등)",
    "Suggestion": "더 자연스럽고 정확한 번역 제안"
  }
]
문제가 없는 항목은 절대 포함하지 마세요. 모든 항목이 정상이라면 빈 배열 [] 을 반환하세요.
응답은 반드시 JSON 배열로만 출력해야 합니다.
"""

def review_batch(model, batch):
    prompt = "Review the following translations:\n"
    prompt += json.dumps(batch, ensure_ascii=False)
    
    for _ in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(temperature=0.1, response_mime_type="application/json")
            )
            res_text = response.text.strip()
            
            if res_text.startswith("```json"):
                res_text = res_text[7:]
            if res_text.startswith("```"):
                res_text = res_text[3:]
            if res_text.endswith("```"):
                res_text = res_text[:-3]
                
            issues = json.loads(res_text.strip())
            return issues
        except Exception as e:
            time.sleep(2)
            
    return []

def main():
    parser = argparse.ArgumentParser(description="AI Translation Reviewer")
    parser.add_argument("project_id", help="Your GCP Project ID")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of rows per API call")
    args = parser.parse_args()

    vertexai.init(project=args.project_id)
    model = GenerativeModel("gemini-2.5-flash", system_instruction=[SYSTEM_INSTRUCTION])

    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    print(f"Starting review of {len(rows)} lines...")
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# 번역 검수 리포트\n\n")
        f.write("AI가 전체 번역을 훑어보고 발견한 의심스러운 오역 및 제안 사항입니다.\n\n")

    batch = []
    total_issues = 0
    
    for i, row in enumerate(rows):
        if len(row) >= 3:
            batch.append({"ID": row[0], "Original": row[1], "Current": row[2]})
            
        if len(batch) >= args.batch_size or i == len(rows) - 1:
            print(f"Reviewing batch {i - len(batch) + 1} to {i}...")
            issues = review_batch(model, batch)
            
            if issues:
                with open(REPORT_FILE, 'a', encoding='utf-8') as f:
                    for issue in issues:
                        f.write(f"### ID: {issue.get('ID')}\n")
                        f.write(f"- **문제점:** {issue.get('Issue')}\n")
                        f.write(f"- **수정 제안:** {issue.get('Suggestion')}\n\n")
                        total_issues += 1
                        
            batch = []
            time.sleep(1)

    print(f"Review complete! Found {total_issues} potential issues.")
    print(f"Results saved to {REPORT_FILE}")

if __name__ == '__main__':
    main()
