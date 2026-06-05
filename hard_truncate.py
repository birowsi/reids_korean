import csv
import json

def get_len(text, mapping):
    l = 0
    for c in text:
        if c in mapping: l += 2
        else:
            try: l += len(c.encode('shift_jis'))
            except: l += 1
    return l

def main():
    try:
        with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as mf:
            korean_mapping = json.load(mf)
    except:
        korean_mapping = {}

    orig_lens = {}
    with open('extracted_texts.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            orig_text = item.get('text', '')
            orig_len = len(item['raw_hex']) // 2
            if orig_text not in orig_lens or orig_len < orig_lens[orig_text]:
                orig_lens[orig_text] = orig_len

    with open('translation_work.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    fixed = 0
    for row in rows:
        if len(row) >= 3:
            orig = row[1]
            trans = row[2]
            if orig not in orig_lens: continue
            olen = orig_lens[orig]
            tlen = get_len(trans, korean_mapping)
            
            if tlen > olen:
                # Compression steps
                t = trans.replace(' ', '').replace('"', '').replace("'", '').replace('.', '').replace(',', '')
                t = t.replace('습니다', '다').replace('합니다', '한다')
                
                # Check len again
                while get_len(t, korean_mapping) > olen and len(t) > 0:
                    t = t[:-1]
                
                row[2] = t
                fixed += 1

    with open('translation_work.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
        
    print(f'Hard truncated {fixed} lines.')

if __name__ == '__main__':
    main()
