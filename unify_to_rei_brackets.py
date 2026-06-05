import csv
import re
import shutil

def main():
    with open('translation_work.csv.bak2', 'r', encoding='utf-8-sig') as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    fixed_count = 0
    for row in reader:
        jp = row['Japanese']
        kr = row['Korean']
        orig_kr = kr
        
        # 1. Fix Colons -> Brackets if Japanese has brackets
        if '「' in jp:
            kr = re.sub(r'^([^:：「]+)[:：]\s*(.*)$', r'\1「\2」', kr)
            if '「' in kr and '」' not in kr:
                kr += '」'
        
        # 2. Fix Ayanami -> Rei safely
        # The user requested to unify all Ayanami references to '레이' to save space and keep brackets
        if '綾波' in jp or 'レイ' in jp:
            kr = re.sub(r'아야나미([「:：\s가는를의야도만에게한테]|$)', r'레이\1', kr)

        if orig_kr != kr:
            row['Korean'] = kr
            fixed_count += 1

    # Overwrite the main working CSV
    with open('translation_work.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)
        
    print(f'Successfully unified {fixed_count} lines to use Rei and Brackets.')

if __name__ == '__main__':
    main()
