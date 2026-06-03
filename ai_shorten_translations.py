import csv
import json
import time
import argparse
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

CSV_FILE = 'translation_work.csv'
JSON_FILE = 'extracted_texts.jsonl'

SYSTEM_INSTRUCTION = """
당신은 고전 게임 한글화 번역가입니다.
주어진 일본어 대사를 한국어로 번역하되, '최대 허용 바이트(MaxBytes)'를 절대 넘지 않도록 극단적으로 요약하고 압축해야 합니다.
- 한국어 1글자는 2바이트, 영어/숫자/기호는 1바이트로 계산됩니다.
- 바이트 수를 줄이기 위해 띄어쓰기는 완전히 없애세요.
- '~습니다' 보다는 '~다', '~음' 등 짧은 말투를 쓰세요.
- 의미가 통하는 선에서 단어를 과감하게 생략하거나 가장 짧은 유의어로 바꾸세요.

반드시 아래 형식의 JSON 배열로만 응답하세요.
[
  {
    "ID": "요청받은 ID",
    "ShortTranslation": "압축된 번역문"
  }
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

def shorten_batch(model, batch):
    prompt = "다음 문장들을 극단적으로 짧게 압축하여 번역하세요:\n"
    for item in batch:
        prompt += f"ID: {item['ID']}, MaxBytes: {item['MaxBytes']}, Original: {item['Original']}\n"
        
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
    args = parser.parse_args()

    vertexai.init(project=args.project_id)
    model = GenerativeModel("gemini-2.5-flash", system_instruction=[SYSTEM_INSTRUCTION])

    try:
        with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as mf:
            korean_mapping = json.load(mf)
    except:
        korean_mapping = {}

    # Get original byte limits
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

    # Find rows that still exceed
    targets = []
    for row in rows:
        if len(row) >= 3:
            orig = row[1]
            trans = row[2]
            if orig in orig_lens:
                max_bytes = orig_lens[orig]
                if get_byte_len(trans, korean_mapping) > max_bytes:
                    targets.append({
                        "row_ref": row,
                        "ID": row[0],
                        "Original": orig,
                        "MaxBytes": max_bytes
                    })

    print(f"Found {len(targets)} lines to shorten via AI.")

    batch_size = 50
    batch = []
    
    for i, target in enumerate(targets):
        batch.append(target)
        if len(batch) >= batch_size or i == len(targets) - 1:
            print(f"Processing {i - len(batch) + 1} to {i}...")
            results = shorten_batch(model, batch)
            
            # Apply results
            result_dict = {str(item['ID']): item.get('ShortTranslation', '') for item in results if 'ID' in item}
            for b in batch:
                if str(b['ID']) in result_dict and result_dict[str(b['ID'])]:
                    b['row_ref'][2] = result_dict[str(b['ID'])].replace(' ', '') # Force remove spaces just in case
            
            # Save progress incrementally
            with open(CSV_FILE, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(rows)
                
            batch = []
            time.sleep(1)

    print("Finished AI shortening!")

if __name__ == '__main__':
    main()
