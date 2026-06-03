import csv
import re

CSV_FILE = 'translation_work.csv'

def fix_quotes():
    with open(CSV_FILE, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    fixed_count = 0
    for row in rows:
        if len(row) >= 3:
            orig = row[1]
            trans = row[2]
            
            # If original uses 낫표 but translation uses standard quotes
            if ('「' in orig or '」' in orig) and ('"' in trans or "'" in trans or '“' in trans or '”' in trans):
                # Replace double quotes
                trans = re.sub(r'["“](.*?)["”]', r'「\1」', trans)
                # Replace single quotes if they seem to be used as dialogue (basic heuristic)
                trans = re.sub(r"['‘](.*?)['’]", r'「\1」', trans)
                
                if trans != row[2]:
                    row[2] = trans
                    fixed_count += 1

    with open(CSV_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
        
    print(f"Fixed quotes in {fixed_count} lines. Replaced '\"' with '「」'.")

if __name__ == '__main__':
    fix_quotes()
