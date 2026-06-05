import csv
import json
import time
import os
import google.generativeai as genai
from pydantic import BaseModel, Field

# Setup AI
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

class TranslationResponse(BaseModel):
    shortened_korean: str = Field(description="The shortened Korean translation fitting the byte limit.")

def main():
    with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as f:
        korean_mapping = json.load(f)

    def calc_bytes(text):
        length = 0
        for c in text:
            if c in korean_mapping: length += 2
            else:
                try: length += len(c.encode('shift_jis'))
                except: length += 1
        return length

    # Read the 43 exceeding lines
    with open('exceeding_lines.csv', 'r', encoding='utf-8-sig') as f:
        reader = list(csv.DictReader(f))
        
    # Read the main translation_work.csv
    with open('translation_work.csv', 'r', encoding='utf-8-sig') as f:
        main_data = list(csv.DictReader(f))
        fieldnames = main_data[0].keys()
        
    print(f"Loaded {len(reader)} lines to shorten.")
    
    fixed_count = 0
    for row in reader:
        jp = row['Japanese']
        kr = row['Korean']
        max_bytes = int(row['MaxBytes'])
        
        prompt = f"""
        You are an expert localizer for a DS game.
        The following Korean translation exceeds the strict game engine byte limit.
        Japanese Original: {jp}
        Korean Translation: {kr}
        Max Bytes Allowed: {max_bytes}
        Current Bytes: {row['CalculatedLen']}

        RULES:
        1. Shorten the Korean text so it fits within {max_bytes} bytes.
        2. Keep the dialogue brackets 「」 intact! DO NOT use colons.
        3. Keep the character name the same! (e.g. 아스카, 레이)
        4. Omit spacing, periods, change verb endings, or summarize to save bytes.
        5. "아스카" takes 6 bytes, "「" takes 2 bytes, "」" takes 2 bytes. Every Korean letter takes 2 bytes. 
        """
        
        retries = 3
        best_translation = kr
        
        while retries > 0:
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        response_mime_type="application/json",
                        response_schema=TranslationResponse,
                        temperature=0.3
                    )
                )
                result = json.loads(response.text)
                candidate = result['shortened_korean']
                c_bytes = calc_bytes(candidate)
                
                if c_bytes <= max_bytes:
                    print(f"Success! {c_bytes}/{max_bytes} bytes. KR: {candidate}")
                    best_translation = candidate
                    break
                else:
                    prompt += f"\n\nYour previous attempt '{candidate}' was {c_bytes} bytes. It must be <= {max_bytes} bytes! Try making it even shorter!"
                    retries -= 1
            except Exception as e:
                print("API Error:", e)
                time.sleep(5)
                retries -= 1
                
        # Apply the fix to main_data
        for main_row in main_data:
            if main_row['Japanese'] == jp and main_row['Korean'] == kr:
                main_row['Korean'] = best_translation
                fixed_count += 1
                break
                
    # Save back to CSV
    with open('translation_work.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(main_data)
        
    print(f"Successfully shortened {fixed_count} lines and updated translation_work.csv!")

if __name__ == '__main__':
    main()
