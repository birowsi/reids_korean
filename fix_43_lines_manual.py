import csv
import json

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
        
    fixed_count = 0
    for row in reader:
        jp = row['Japanese']
        kr = row['Korean']
        max_bytes = int(row['MaxBytes'])
        
        # 1. First remove punctuation
        candidate = kr
        candidate = candidate.replace(' ', '').replace('.', '').replace('!', '').replace('?', '').replace(',', '').replace('~', '')
        
        # 2. If it still exceeds, forcefully truncate characters BEFORE the closing bracket
        while calc_bytes(candidate) > max_bytes:
            if '「' in candidate and '」' in candidate:
                idx = candidate.rfind('」')
                if idx > 1:
                    candidate = candidate[:idx-1] + '」' + candidate[idx+1:]
                else:
                    candidate = candidate[:-1] # fallback
            else:
                candidate = candidate[:-1]
                
        # Apply the fix to main_data
        for main_row in main_data:
            if main_row['Japanese'] == jp and main_row['Korean'] == kr:
                main_row['Korean'] = candidate
                fixed_count += 1
                break
                
    # Save back to CSV
    with open('translation_work.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(main_data)
        
    print(f"Successfully truncated {fixed_count} lines and updated translation_work.csv!")

if __name__ == '__main__':
    main()
