import csv
import json
import os

CSV_FILE = 'translation_work.csv'
JSON_FILE = 'extracted_texts.jsonl'
OUTPUT_JSON = 'translated_texts.jsonl'

def main():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found.")
        return
        
    translation_map = {}
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader) # Skip header
        for row in reader:
            if len(row) >= 3:
                orig_text = row[1]
                trans_text = row[2]
                # If translation exists, add to map. Else keep original or fallback
                if trans_text.strip():
                    translation_map[orig_text] = trans_text

    print(f"Loaded {len(translation_map)} translations from CSV.")
    
    count = 0
    with open(JSON_FILE, 'r', encoding='utf-8') as f_in, open(OUTPUT_JSON, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            item = json.loads(line)
            orig_text = item.get('text', '')
            
            if orig_text in translation_map:
                item['translated_text'] = translation_map[orig_text]
            else:
                # If no translation, we can just leave it or set it to original
                pass
                
            f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
            count += 1
            
    print(f"Generated {OUTPUT_JSON} with {count} lines.")
    print("Now you can run text_packer.py to inject the translations into the game!")

if __name__ == '__main__':
    main()
