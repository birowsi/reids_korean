import csv
import json
import re
import time
import argparse
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import concurrent.futures

CSV_FILE = 'translation_work.csv'
REPORT_FILE = 'review_report.md'
JSON_FILE = 'extracted_texts.jsonl'
MAPPING_FILE = 'nftr_korean_mapping.json'

SYSTEM_INSTRUCTION = """
당신은 고전 게임 한글화 번역가입니다.
제공되는 [ID, 원문, 제안된번역, 최대허용바이트] 정보를 바탕으로, 제안된 번역을 최대 허용 바이트(MaxBytes) 안에 들어가도록 극단적으로 압축하세요.
- 한국어 1글자는 2바이트, 영어/숫자/기호는 1바이트입니다.
- 캐릭터의 성격(말투)과 특수 기호(\1 등)는 반드시 유지해야 합니다.
- 바이트 수를 줄이기 위해 띄어쓰기를 완전히 없애는 것을 권장합니다.
- 의미가 통하는 선에서 짧은 유의어로 바꾸거나 과감히 생략하세요.

반드시 아래 형식의 JSON 배열로만 응답하세요.
[
  {
    "ID": "요청받은 ID",
    "ShortTranslation": "압축된 번역문"
  }
]
응답은 반드시 Markdown 백틱(```) 없이 순수 JSON만 출력하세요.
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

def shorten_batch(model, batch):
    prompt = "다음 문장들을 최대 바이트 수에 맞게 압축하여 번역하세요:\n"
    for item in batch:
        prompt += f"ID: {item['ID']}, MaxBytes: {item['MaxBytes']}, Original: {item['Original']}, Suggestion: {item['Suggestion']}\n"
        
    for _ in range(3):
        try:
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(temperature=0.2, response_mime_type="application/json")
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
    parser.add_argument("project_id", help="Your GCP Project ID")
    parser.add_argument("--workers", type=int, default=10)
    args = parser.parse_args()

    vertexai.init(project=args.project_id)
    model = GenerativeModel("gemini-2.5-flash", system_instruction=[SYSTEM_INSTRUCTION])

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

    with open(REPORT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = re.findall(r'### ID: (\d+)\n- \*\*문제점:\*\* (.*?)\n- \*\*수정 제안:\*\* (.*?)(?=\n\n|\Z)', content, re.DOTALL)
    
    direct_applies = 0
    needs_shortening = []
    
    # Process blocks
    suggestions = {b[0]: b[2].strip() for b in blocks}
    
    for row in rows:
        row_id = row[0]
        if row_id in suggestions:
            orig = row[1]
            sug = suggestions[row_id]
            max_bytes = orig_lens.get(orig, 999)
            
            sug_len = get_byte_len(sug, korean_mapping)
            if sug_len <= max_bytes:
                row[2] = sug
                direct_applies += 1
            else:
                needs_shortening.append({
                    "row_ref": row,
                    "ID": row_id,
                    "Original": orig,
                    "Suggestion": sug,
                    "MaxBytes": max_bytes
                })

    print(f"Directly applied {direct_applies} suggestions (within byte limits).")
    print(f"Found {len(needs_shortening)} suggestions that exceed byte limits and need AI shortening.")

    if needs_shortening:
        batches = []
        batch_size = 50
        for i in range(0, len(needs_shortening), batch_size):
            batches.append(needs_shortening[i:i+batch_size])

        completed = 0
        def process_and_apply(batch_data):
            results = shorten_batch(model, batch_data)
            result_dict = {str(item['ID']): item.get('ShortTranslation', '') for item in results if 'ID' in item}
            for b in batch_data:
                if str(b['ID']) in result_dict and result_dict[str(b['ID'])]:
                    # Strip spaces just to be safe if it's tight
                    shortened = result_dict[str(b['ID'])]
                    if get_byte_len(shortened, korean_mapping) > b['MaxBytes']:
                        shortened = shortened.replace(' ', '')
                    b['row_ref'][2] = shortened
            return len(batch_data)

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            future_to_batch = {executor.submit(process_and_apply, b): b for b in batches}
            for future in concurrent.futures.as_completed(future_to_batch):
                completed += 1
                print(f"Shortening progress: {completed}/{len(batches)} batches done.")

    with open(CSV_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
        
    print("Done! CSV has been fully updated.")

if __name__ == '__main__':
    main()
