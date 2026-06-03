import json
import csv

INPUT_FILE = 'extracted_texts.jsonl'
OUTPUT_CSV = 'translation_work.csv'

def export_to_csv():
    unique_texts = set()
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            text = item.get('text', '')
            if text:
                unique_texts.add(text)
                
    unique_list = list(unique_texts)
    
    with open(OUTPUT_CSV, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Japanese', 'Korean'])
        
        for i, text in enumerate(unique_list):
            writer.writerow([i, text, ''])
            
    print(f"Exported {len(unique_list)} unique lines to {OUTPUT_CSV}")

if __name__ == '__main__':
    export_to_csv()
