import csv
import json

def main():
    try:
        with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as mf:
            korean_mapping = json.load(mf)
    except Exception as e:
        print("Error loading mapping:", e)
        return

    exceeding_count = 0
    
    with open('translation_work.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            translated = row.get('Korean', '')
            max_bytes = int(row.get('MaxBytes', 0))
            
            # calculate byte length
            calculated_len = 0
            for c in translated:
                if c in korean_mapping:
                    calculated_len += 2
                else:
                    try:
                        calculated_len += len(c.encode('shift_jis'))
                    except:
                        calculated_len += 1 # '?'
            
            if calculated_len > max_bytes:
                exceeding_count += 1
                print(f"Row {i+2} (ID {row.get('ID')}): MaxBytes={max_bytes}, CalculatedLen={calculated_len}")
                print(f"Text: {translated}\n")
                
    if exceeding_count == 0:
        print("Success! All translations are within their MaxBytes limit.")
    else:
        print(f"Failed: Found {exceeding_count} translations exceeding MaxBytes limit.")

if __name__ == '__main__':
    main()
