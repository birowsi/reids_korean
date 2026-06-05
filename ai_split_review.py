import csv
import json
import time
import argparse
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import concurrent.futures

CSV_FILE = 'translation_work.csv'
REPORT_FILE = 'review_report.md'
JSON_FILE = 'extracted_texts.jsonl'
MAPPING_FILE = 'nftr_korean_mapping.json'

GLOSSARY = """
[에반게리온 특화 고유명사 용어집 (엄격 준수)]
- 三尉 -> 소위 (삼위 절대 금지)
- 一尉 -> 대위 (일위 절대 금지)
- ケンスケ -> 켄스케 (케ンスケ 등 일본어 혼용 절대 금지)
- トウジ -> 토우지
- 委員長 -> 위원장
- 원문에 포함된 히라가나/가타카나/한자가 번역문에 1글자라도 남아있으면 무조건 치명적 오류로 지적할 것.
"""

PROMPT_NORMAL = f"""
당신은 '신세기 에반게리온: 아야나미 육성계획' (Nintendo DS)의 전문 번역 검수자입니다.
이 대사들은 **롬 용량(바이트)에 여유가 있는 그룹**입니다. 따라서 띄어쓰기, 맞춤법, 자연스러운 어순 등을 깐깐하게 검수해도 됩니다.

[검수 기준]
1. 오역 및 어색한 번역 교정.
2. 제어문자(\\n, \\1 등) 누락 복구.
3. 띄어쓰기 및 맞춤법 교정 허용.
{GLOSSARY}

문제가 발견된 항목만 아래 JSON 배열로 반환하세요:
[
  {{
    "ID": "행 번호",
    "Issue": "문제점",
    "Suggestion": "수정 제안 (자연스러운 한국어로 띄어쓰기 포함)"
  }}
]
"""

PROMPT_TIGHT = f"""
당신은 '신세기 에반게리온: 아야나미 육성계획' (Nintendo DS)의 전문 번역 검수자입니다.
이 대사들은 **롬 용량(바이트)이 꽉 차서 더 이상 길이를 늘릴 수 없는 포화 그룹**입니다.

[검수 기준]
1. 명백한 오역과 고유명사 오류만 지적하세요.
2. **띄어쓰기 누락이나 문장 부자연스러움은 절대 지적하지 마세요.** (롬 용량 한계 때문입니다)
3. 수정을 제안할 때, **기존 번역보다 길이가 절대 길어지면 안 됩니다.** (극단적 요약, 띄어쓰기 파괴 허용)
{GLOSSARY}

문제가 발견된 항목만 아래 JSON 배열로 반환하세요:
[
  {{
    "ID": "행 번호",
    "Issue": "명백한 오역/고유명사 오류",
    "Suggestion": "수정 제안 (길이를 늘리지 않고 압축, 띄어쓰기 무시)"
  }}
]
"""

def get_byte_len(text, korean_mapping):
    length = 0
    for c in text:
        if c in korean_mapping:
            length += 2
        else:
            try:
                length += len(c.encode('shift_jis'))
            except:
                length += 1
    return length

def review_batch(model, prompt_template, batch):
    prompt = prompt_template + "\n\nReview the following:\n"
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
                
            return json.loads(res_text.strip())
        except Exception as e:
            time.sleep(2)
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id")
    parser.add_argument("--workers", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=150)
    args = parser.parse_args()

    vertexai.init(project=args.project_id, location='global')
    
    model_normal = GenerativeModel("gemini-3.5-flash", system_instruction=[PROMPT_NORMAL])
    model_tight = GenerativeModel("gemini-3.5-flash", system_instruction=[PROMPT_TIGHT])

    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as mf:
            korean_mapping = json.load(mf)
    except:
        korean_mapping = {}

    orig_lens = {}
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            orig_text = item.get('text', '')
            orig_len = len(item['raw_hex']) // 2
            if orig_text not in orig_lens or orig_len < orig_lens[orig_text]:
                orig_lens[orig_text] = orig_len

    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    normal_batches = []
    tight_batches = []
    curr_normal = []
    curr_tight = []

    for row in rows:
        if len(row) < 3:
            continue
            
        row_id, orig, trans = row[0], row[1], row[2]
        max_bytes = orig_lens.get(orig, 999)
        
        # Calculate length of translation without spaces to see how tight it is
        base_len = get_byte_len(trans.replace(" ", ""), korean_mapping)
        
        item = {"ID": row_id, "Original": orig, "Current": trans, "MaxBytes": max_bytes}
        
        # If the optimal compressed length is close to max_bytes, it's tight
        if max_bytes - base_len < 4:
            curr_tight.append(item)
            if len(curr_tight) >= args.batch_size:
                tight_batches.append(curr_tight)
                curr_tight = []
        else:
            curr_normal.append(item)
            if len(curr_normal) >= args.batch_size:
                normal_batches.append(curr_normal)
                curr_normal = []

    if curr_tight: tight_batches.append(curr_tight)
    if curr_normal: normal_batches.append(curr_normal)

    total_tight = sum(len(b) for b in tight_batches)
    total_normal = sum(len(b) for b in normal_batches)
    
    print(f"Starting Split Review. Normal group: {total_normal} rows, Tight group: {total_tight} rows.")

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# 투트랙 번역 검수 리포트 (gemini-3.5-flash)\n\n")

    total_issues = 0
    completed = 0
    total_batches = len(normal_batches) + len(tight_batches)

    def process_batch(batch_data, model, prompt_template):
        return review_batch(model, prompt_template, batch_data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        for b in normal_batches:
            futures[executor.submit(process_batch, b, model_normal, PROMPT_NORMAL)] = b
        for b in tight_batches:
            futures[executor.submit(process_batch, b, model_tight, PROMPT_TIGHT)] = b
            
        for future in concurrent.futures.as_completed(futures):
            try:
                issues = future.result()
                completed += 1
                print(f"Progress: {completed}/{total_batches} batches done.")
                if issues:
                    with open(REPORT_FILE, 'a', encoding='utf-8') as f:
                        for issue in issues:
                            f.write(f"### ID: {issue.get('ID')}\n")
                            f.write(f"- **문제점:** {issue.get('Issue')}\n")
                            f.write(f"- **수정 제안:** {issue.get('Suggestion')}\n\n")
                            total_issues += 1
            except Exception as e:
                print(f"Batch failed: {e}")

    print(f"Split Review complete! Found {total_issues} issues. Saved to {REPORT_FILE}.")

if __name__ == '__main__':
    main()
