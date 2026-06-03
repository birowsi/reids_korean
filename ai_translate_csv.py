import sys
import csv
import json
import time
import os
import argparse
import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting, HarmCategory, GenerationConfig

CSV_FILE = 'translation_work.csv'

SYSTEM_INSTRUCTION = """
당신은 '신세기 에반게리온: 아야나미 육성계획 with 아스카 보완계획' (닌텐도 DS) 게임의 전문 한국어 번역가입니다.
제공되는 일본어 텍스트들을 한국어로 번역하되 다음 규칙을 엄격히 지켜주세요:
1. 캐릭터 말투 유지 (아스카는 당돌하고 톡톡 튀는 말투, 레이는 무미건조한 말투, 리츠코는 어른스럽고 전문적인 말투, 미사토는 활기찬 말투 등).
2. 게임 특수기호 파괴 금지: \n (줄바꿈), \1, \2, @, % 등의 제어문자 및 특수 태그는 원본 위치 그대로 유지하세요.
3. 낫표(「, 」) 등 일본식 인용구는 가급적 유지하거나 자연스러운 따옴표로 변경하되 양식을 통일하세요.
4. 입력은 JSON 배열 형태의 문자열 목록입니다. 출력도 **반드시 동일한 길이의 JSON 배열 형태의 번역된 문자열 목록**만 반환해야 합니다. 다른 말은 절대 덧붙이지 마세요.
"""

def load_csv(filepath):
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            rows.append(row)
    return header, rows

def save_csv(filepath, header, rows):
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

def translate_batch(model, batch_texts):
    prompt = "Translate the following JSON array of Japanese texts to Korean according to the system instructions:\n"
    prompt += json.dumps(batch_texts, ensure_ascii=False)
    
    retries = 3
    for r in range(retries):
        try:
            # print(f"Requesting {len(batch_texts)} texts...")
            response = model.generate_content(
                prompt,
                generation_config=GenerationConfig(temperature=0.1, response_mime_type="application/json")
            )
            res_text = response.text.strip()
            
            # extract json array if markdown enclosed
            if res_text.startswith("```json"):
                res_text = res_text[7:]
            if res_text.startswith("```"):
                res_text = res_text[3:]
            if res_text.endswith("```"):
                res_text = res_text[:-3]
                
            translated_array = json.loads(res_text.strip())
            
            if len(translated_array) == len(batch_texts):
                return translated_array
            else:
                print(f"Length mismatch: {len(batch_texts)} in, {len(translated_array)} out. Retrying...")
                time.sleep(2)
        except Exception as e:
            print(f"Error during translation API call: {e}")
            time.sleep(3)
            
    print("Failed to translate batch after retries. Falling back to empty strings.")
    return ["" for _ in batch_texts]

def main():
    parser = argparse.ArgumentParser(description="AI Translation via Vertex AI")
    parser.add_argument("project_id", help="Your GCP Project ID")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Vertex AI Model to use (e.g. gemini-2.5-flash, gemini-2.5-pro)")
    parser.add_argument("--batch-size", type=int, default=50, help="Number of texts per API call")
    args = parser.parse_args()

    print(f"Initializing Vertex AI for project: {args.project_id}")
    vertexai.init(project=args.project_id)
    
    try:
        model = GenerativeModel(
            args.model,
            system_instruction=[SYSTEM_INSTRUCTION]
        )
    except Exception as e:
        print(f"Failed to load model {args.model}: {e}")
        print("Falling back to gemini-2.5-flash...")
        model = GenerativeModel("gemini-2.5-flash", system_instruction=[SYSTEM_INSTRUCTION])

    header, rows = load_csv(CSV_FILE)
    
    # Filter rows that need translation
    to_translate_indices = [i for i, row in enumerate(rows) if not row[2].strip()]
    print(f"Total rows: {len(rows)}, Remaining to translate: {len(to_translate_indices)}")
    
    if not to_translate_indices:
        print("Everything is already translated!")
        return
        
    batch_indices = []
    batch_texts = []
    
    translated_count = 0
    
    for count, idx in enumerate(to_translate_indices):
        batch_indices.append(idx)
        batch_texts.append(rows[idx][1])
        
        if len(batch_texts) >= args.batch_size or count == len(to_translate_indices) - 1:
            print(f"Translating batch of {len(batch_texts)} texts... ({translated_count}/{len(to_translate_indices)})")
            
            translated_batch = translate_batch(model, batch_texts)
            
            for i, translated_text in enumerate(translated_batch):
                row_idx = batch_indices[i]
                rows[row_idx][2] = translated_text
                
            translated_count += len(batch_texts)
            
            # Save progress after each batch
            save_csv(CSV_FILE, header, rows)
            
            batch_indices = []
            batch_texts = []
            time.sleep(1) # Simple rate limiting
            
    print("Translation complete!")

if __name__ == '__main__':
    main()
