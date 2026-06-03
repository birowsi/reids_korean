import csv
import json

def main():
    try:
        with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as mf:
            korean_mapping = json.load(mf)
    except:
        korean_mapping = {}

    # Read original lengths from jsonl
    orig_lens = {}
    with open('extracted_texts.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            orig_text = item.get('text', '')
            orig_len = len(item['raw_hex']) // 2
            # If there are duplicates, we keep the smallest length to be safe
            if orig_text not in orig_lens or orig_len < orig_lens[orig_text]:
                orig_lens[orig_text] = orig_len

    with open('translation_work.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    fixed = 0
    for row in rows:
        if len(row) >= 3:
            orig_text = row[1]
            trans_text = row[2]
            
            if orig_text not in orig_lens: 
                continue
                
            orig_len = orig_lens[orig_text]
            
            # calculate trans_len
            trans_len = 0
            for c in trans_text:
                if c in korean_mapping: 
                    trans_len += 2
                else:
                    try: 
                        trans_len += len(c.encode('shift_jis'))
                    except: 
                        trans_len += 1
                    
            # If the translation is longer than original, try stripping spaces
            if trans_len > orig_len:
                # Remove standard spaces
                no_space_text = trans_text.replace(' ', '')
                if no_space_text != trans_text:
                    row[2] = no_space_text
                    fixed += 1
                    
    with open('translation_work.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
        
    print(f"Removed spaces from {fixed} translations to save bytes.")

if __name__ == '__main__':
    main()
