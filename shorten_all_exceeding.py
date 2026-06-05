import csv
import json
import time
import argparse
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import concurrent.futures

CSV_FILE = 'translation_work.csv'
JSON_FILE = 'extracted_texts.jsonl'
MAPPING_FILE = 'nftr_korean_mapping.json'

GLOSSARY = """
[에반게리온 특화 고유명사 용어집 (엄격 준수)]
- 三尉 -> 소위 (삼위 절대 금지)
- 一尉 -> 대위 (일위 절대 금지)
- ケンスケ -> 켄스케 (케ンスケ 등 일본어 혼용 절대 금지)
- トウジ -> 토우지
- 委員長 -> 위원장
"""

PROMPT_SHORTEN = f"""
당신은 게임 번역 문장 압축 전문가입니다. 
다음 제공된 대사는 롬 파일에 들어갈 최대 허용 바이트(MaxBytes)를 초과하여 게임을 튕기게 만듭니다.
원문의 의미와 중요한 고유명사를 유지하면서, 한국어 번역문의 길이를 **반드시 MaxBytes 이하**로 줄여야 합니다.

[압축 지침]
1. 띄어쓰기를 모두 없애서라도 길이를 줄이세요.
2. 부사, 꾸밈말을 과감히 생략하세요.
3. 뜻만 통하면 가장 짧은 단어로 교체하세요. (예: 안녕하십니까 -> 안녕, 그렇습니다 -> 그래)
{GLOSSARY}

결과는 반드시 아래 JSON 형식 하나만 반환하세요:
{{
  "Suggestion": "가장 짧게 압축된 번역문"
}}
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

def shorten_batch(model, items, korean_mapping):
    results = []
    for item in items:
        prompt = PROMPT_SHORTEN + f"\n\nMaxBytes: {item['MaxBytes']}\nOriginal: {item['Original']}\nCurrent Exceeding: {item['Current']}"
        
        best_suggestion = item['Current']
        for _ in range(3):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=GenerationConfig(temperature=0.7, response_mime_type="application/json")
                )
                res_text = response.text.strip()
                if res_text.startswith("```json"): res_text = res_text[7:]
                if res_text.startswith("```"): res_text = res_text[3:]
                if res_text.endswith("```"): res_text = res_text[:-3]
                
                sug = json.loads(res_text.strip())["Suggestion"]
                if get_byte_len(sug, korean_mapping) <= item['MaxBytes']:
                    best_suggestion = sug
                    break
            except Exception as e:
                time.sleep(1)
        
        # If AI failed to shorten enough, fallback to aggressive truncation
        if get_byte_len(best_suggestion, korean_mapping) > item['MaxBytes']:
            sug = best_suggestion.replace(" ", "")
            while get_byte_len(sug, korean_mapping) > item['MaxBytes']:
                sug = sug[:-1]
            best_suggestion = sug
            
        results.append({"ID": item["ID"], "Shortened": best_suggestion})
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id")
    parser.add_argument("--workers", type=int, default=15)
    args = parser.parse_args()

    vertexai.init(project=args.project_id, location='global')
    model = GenerativeModel("gemini-3.5-flash")

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

    exceeding_items = []
    for row in rows:
        if len(row) < 3:
            continue
        row_id, orig, trans = row[0], row[1], row[2]
        max_bytes = orig_lens.get(orig, 999)
        cur_len = get_byte_len(trans, korean_mapping)
        
        if cur_len > max_bytes:
            exceeding_items.append({
                "ID": row_id,
                "Original": orig,
                "Current": trans,
                "MaxBytes": max_bytes,
                "rowIndex": rows.index(row)
            })

    print(f"Found {len(exceeding_items)} items exceeding MaxBytes. Starting AI shortening...")

    batch_size = 50
    batches = [exceeding_items[i:i + batch_size] for i in range(0, len(exceeding_items), batch_size)]
    
    fixes = {}
    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(shorten_batch, model, b, korean_mapping): b for b in batches}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            for r in res:
                fixes[r["ID"]] = r["Shortened"]
            completed += 1
            print(f"Progress: {completed}/{len(batches)} batches done.")

    # Apply fixes
    for item in exceeding_items:
        idx = item["rowIndex"]
        row_id = item["ID"]
        if row_id in fixes:
            rows[idx][2] = fixes[row_id]

    with open(CSV_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print("Successfully shortened all exceeding items and updated CSV.")

if __name__ == '__main__':
    main()
