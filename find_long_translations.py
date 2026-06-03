import json
import csv

def main():
    try:
        with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as mf:
            korean_mapping = json.load(mf)
    except:
        korean_mapping = {}

    long_lines = []
    
    with open('translated_texts.jsonl', 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            item = json.loads(line)
            if 'translated_text' not in item:
                continue
                
            orig_hex = item['raw_hex']
            orig_len = len(orig_hex) // 2
            
            trans_text = item['translated_text']
            trans_len = 0
            for c in trans_text:
                if c in korean_mapping:
                    trans_len += 2
                else:
                    try:
                        encoded = c.encode('shift_jis')
                        trans_len += len(encoded)
                    except:
                        trans_len += 1 # '?' fallback
                        
            if trans_len > orig_len:
                long_lines.append({
                    'line_num': line_num, # Roughly matches CSV ID if 1-to-1
                    'original': item.get('text', ''),
                    'translated': trans_text,
                    'orig_len': orig_len,
                    'trans_len': trans_len,
                    'diff': trans_len - orig_len
                })
                
    # Sort by the most exceeded bytes first
    long_lines.sort(key=lambda x: x['diff'], reverse=True)
    
    out_csv = 'long_translations_report.csv'
    with open(out_csv, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Original Text', 'Translated Text', 'Original Bytes', 'Translated Bytes', 'Exceeded By'])
        for row in long_lines:
            writer.writerow([row['original'], row['translated'], row['orig_len'], row['trans_len'], row['diff']])
            
    print(f"Found {len(long_lines)} lines where Korean translation is longer than the original Japanese.")
    print(f"Report saved to {out_csv}")
    
    if long_lines:
        print("\nTop 5 longest exceeded lines:")
        for row in long_lines[:5]:
            print(f"- [+{row['diff']} bytes] {repr(row['translated'])}")

if __name__ == '__main__':
    main()
