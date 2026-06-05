import csv
import re
import shutil

def main():
    with open('translation_work.csv', 'r', encoding='utf-8-sig') as f:
        reader = list(csv.DictReader(f))
        fieldnames = reader[0].keys()

    fixed_count = 0
    for row in reader:
        jp = row['Japanese']
        kr = row['Korean']
        orig_kr = kr
        
        # 1. Fix Colons -> Brackets if Japanese has brackets
        if '「' in jp:
            # Match 'Name: Text' or 'Name : Text'
            kr = re.sub(r'^([^:：「]+)[:：]\s*(.*)$', r'\1「\2」', kr)
            # Sometimes there might just be a missing bracket at the end
            if '「' in kr and '」' not in kr:
                kr += '」'
        
        # 2. Fix Ayanami / Rei Safely
        if '綾波' in jp and 'レイ' not in jp:
            # Replace '레이' followed by brackets, colons, or specific Korean postpositions
            kr = re.sub(r'레이([「:：\s가는를의야도만에게한테]|$)', r'아야나미\1', kr)
            
        if 'レイ' in jp and '綾波' not in jp:
            kr = re.sub(r'아야나미([「:：\s가는를의야도만에게한테]|$)', r'레이\1', kr)

        if orig_kr != kr:
            row['Korean'] = kr
            fixed_count += 1

    # Save backup
    shutil.copy('translation_work.csv', 'translation_work.csv.bak2')
    
    with open('translation_work_fixed.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(reader)
        
    print(f'Successfully fixed {fixed_count} lines.')

if __name__ == '__main__':
    main()
