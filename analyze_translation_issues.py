import csv
import re

def main():
    ayanami_issues = []
    colon_issues = []
    
    with open('translation_work.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            jp = row['Japanese']
            kr = row['Korean']
            row_id = row['ID']
            
            # Check Ayanami issue
            if '綾波' in jp and '아야나미' not in kr:
                ayanami_issues.append((row_id, jp, kr))
                
            # Check bracket vs colon issue
            if '「' in jp and '」' in jp:
                if '「' not in kr or '」' not in kr:
                    if ':' in kr or '：' in kr:
                        colon_issues.append((row_id, jp, kr))
                    else:
                        # Maybe they just removed brackets, still an issue
                        colon_issues.append((row_id, jp, kr))
            
            # Also check if colon is used in Korean but NOT in Japanese
            elif (':' in kr or '：' in kr) and (':' not in jp and '：' not in jp):
                 colon_issues.append((row_id, jp, kr))

    print(f"Found {len(ayanami_issues)} issues with '綾波' missing '아야나미'.")
    for row_id, jp, kr in ayanami_issues[:5]:
        print(f"ID {row_id}:\nJP: {jp}\nKR: {kr}\n")
        
    print(f"\nFound {len(colon_issues)} issues with brackets/colons.")
    for row_id, jp, kr in colon_issues[:5]:
        print(f"ID {row_id}:\nJP: {jp}\nKR: {kr}\n")

if __name__ == '__main__':
    main()
