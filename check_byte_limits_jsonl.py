import json
import os
import csv
import sys

from translation_codec import TextEncodingError, encode_text, load_korean_mapping


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        korean_mapping = load_korean_mapping('nftr_korean_mapping.json')
    except Exception as e:
        print("Error loading mapping:", e)
        raise SystemExit(1)

    exceeding_count = 0
    total_lines = 0
    exceeding_rows = []
    
    with open('translated_texts.jsonl', 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            item = json.loads(line)
            total_lines += 1
            
            translated = item.get('translated_text', '')
            if not translated:
                continue
                
            raw_hex = item.get('raw_hex', '')
            if not raw_hex:
                continue
                
            max_bytes = len(bytes.fromhex(raw_hex))
            
            try:
                calculated_len = len(encode_text(translated, korean_mapping))
            except TextEncodingError as exc:
                exceeding_count += 1
                print(f"Line {i}: {exc}")
                continue
            
            if calculated_len > max_bytes:
                exceeding_count += 1
                exceeding_rows.append({
                    'LineIndex': i,
                    'Japanese': item.get('text', ''),
                    'Korean': translated,
                    'MaxBytes': max_bytes,
                    'CalculatedLen': calculated_len
                })
                print(f"Line {i} (Offset {item.get('original_offset')}): MaxBytes={max_bytes}, CalculatedLen={calculated_len}")
                print(f"JP: {item.get('text')}")
                print(f"KR: {translated}\n")
                
    if exceeding_count == 0:
        print(f"Success! All {total_lines} lines are within their MaxBytes limit.")
    else:
        print(f"Failed: Found {exceeding_count} translations exceeding MaxBytes limit.")
        with open('exceeding_lines.csv', 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['LineIndex', 'Japanese', 'Korean', 'MaxBytes', 'CalculatedLen'])
            writer.writeheader()
            writer.writerows(exceeding_rows)
        print("Saved exceeding lines to exceeding_lines.csv")
        raise SystemExit(1)

if __name__ == '__main__':
    main()
