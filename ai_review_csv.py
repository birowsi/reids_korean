import csv
import json
import time
import argparse
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

CSV_FILE = 'translation_work.csv'
REPORT_FILE = 'review_report.md'

SYSTEM_INSTRUCTION = """
당신은 '신세기 에반게리온: 아야나미 육성계획 with 아스카 보완계획' (Nintendo DS)의 전문 한국어 번역 검수자입니다.
제공되는 [ID, 원문(일본어), 현재번역(한국어)] 목록을 읽고, 다음 기준에 따라 **게임 플레이나 몰입에 치명적인 영향을 주는 중대한 오류**만 꼼꼼히 찾아내세요.

[검수 핵심 기준]
1. 명백한 오역 및 의미 왜곡
   - 원문의 의미가 완전히 반대로 번역되었거나, 상황에 전혀 맞지 않는 엉뚱한 단어/오타로 번역된 경우.
2. 에반게리온 캐릭터성 붕괴 (매우 중요)
   - 아스카: 프라이드가 높고 당돌하며 공격적인 말투. (예: "바보 아냐?", "~잖아!")
   - 레이: 감정이 없고 기계적이며 무미건조한 말투. (예: "~할게.", "~야.")
   - 신지: 소극적이고 우물쭈물하는 말투.
   - 미사토: 밝고 호쾌하면서도 때론 진지한 어른/보호자의 말투.
   - 리츠코: 이성적이고 차분하며 전문적인 연구원의 말투.
   - 겐도: 냉혹하고 권위적인 사령관의 말투.
   - 원문 화자의 성격에 명백히 위배되는 어조(존댓말/반말의 심각한 혼동 포함)가 사용된 경우만 지적하세요.
3. 제어문자 및 시스템 기호 누락/훼손 (치명적)
   - 원문에 있는 제어문자(\\n, \\1, \\2 등)나 특수 괄호(「」, 『』)가 번역문에서 빠지거나 엉뚱한 기호로 변형된 경우.
   - 시스템 제어문자 누락은 게임 크래시를 유발하므로 1순위로 찾아내세요.
4. 띄어쓰기 및 단순 맞춤법 (절대 무시)
   - 띄어쓰기 누락, 사소한 맞춤법 오류, 약간의 어색함 등은 **절대 지적하지 마세요.**
   - 닌텐도 DS 롬 용량 및 메모리 한계로 인해 의도적으로 띄어쓰기를 생략하거나 문장을 욱여넣은 경우가 많기 때문입니다.

문제가 발견된 항목들만 추려서 아래 형식의 JSON 배열로 반환하세요.
[
  {
    "ID": "행 번호",
    "Issue": "발견된 문제점 설명 (예: 아스카의 말투가 아님, 제어문자 \\1 누락, 심각한 오역 등)",
    "Suggestion": "더 자연스럽고 정확한 번역 제안"
  }
]
문제가 없는 항목은 절대 포함하지 마세요. 모든 항목이 정상이라면 빈 배열 [] 을 반환하세요.
응답은 반드시 JSON 배열로만 출력해야 합니다. Markdown 백틱(```) 없이 순수 JSON만 출력하는 것을 권장합니다.
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

import concurrent.futures

def main():
    parser = argparse.ArgumentParser(description="AI Translation Reviewer")
    parser.add_argument("project_id", help="Your GCP Project ID")
    parser.add_argument("--batch-size", type=int, default=150, help="Number of rows per API call")
    parser.add_argument("--workers", type=int, default=10, help="Number of parallel threads")
    args = parser.parse_args()

    vertexai.init(project=args.project_id)
    model = GenerativeModel("gemini-2.5-flash", system_instruction=[SYSTEM_INSTRUCTION])

    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    print(f"Starting review of {len(rows)} lines with {args.workers} workers...")
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# 번역 검수 리포트\n\n")
        f.write("AI가 전체 번역을 훑어보고 발견한 의심스러운 오역 및 제안 사항입니다.\n\n")

    batches = []
    current_batch = []
    for row in rows:
        if len(row) >= 3:
            current_batch.append({"ID": row[0], "Original": row[1], "Current": row[2]})
        if len(current_batch) >= args.batch_size:
            batches.append(current_batch)
            current_batch = []
    if current_batch:
        batches.append(current_batch)

    total_issues = 0
    completed_batches = 0

    def process_and_write(batch_data):
        issues = review_batch(model, batch_data)
        return issues

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_batch = {executor.submit(process_and_write, b): b for b in batches}
        
        for future in concurrent.futures.as_completed(future_to_batch):
            try:
                issues = future.result()
                completed_batches += 1
                print(f"Progress: {completed_batches}/{len(batches)} batches completed.")
                
                if issues:
                    # Write to file immediately; appending is thread-safe enough for this simple script, 
                    # but since we're in as_completed, the main thread does the writing sequentially anyway.
                    with open(REPORT_FILE, 'a', encoding='utf-8') as f:
                        for issue in issues:
                            f.write(f"### ID: {issue.get('ID')}\n")
                            f.write(f"- **문제점:** {issue.get('Issue')}\n")
                            f.write(f"- **수정 제안:** {issue.get('Suggestion')}\n\n")
                            total_issues += 1
            except Exception as exc:
                print(f"A batch generated an exception: {exc}")

    print(f"Review complete! Found {total_issues} potential issues.")
    print(f"Results saved to {REPORT_FILE}")

if __name__ == '__main__':
    main()
