import sys
import codecs
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf8', buffering=1)

import csv
import re

with open('translation_work.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.reader(f)
    header = next(reader)
    cut_off_candidates = []
    quote_issues = []
    
    for row in reader:
        if len(row) >= 3:
            orig = row[1].strip()
            trans = row[2].strip()
            
            # Check for quotes consistency
            if ('「' in orig or '」' in orig) and ('\'' in trans or '"' in trans or '“' in trans or '”' in trans):
                quote_issues.append((row[0], orig, trans))
                
            # Check for cut off: original ends with punctuation, translation does not
            orig_ends_with_punc = re.search(r'[。！？！」』]$', orig)
            trans_ends_with_punc = re.search(r'[.!?!\」\”\'\"]$', trans)
            
            # If translation ends abruptly with no punctuation or ends with a weird character
            # Check if translation length is drastically shorter, or ends with incomplete syllable
            if orig_ends_with_punc and not trans_ends_with_punc and len(trans) > 0:
                cut_off_candidates.append((row[0], orig, trans))

    print(f'Found {len(quote_issues)} lines that use standard quotes instead of 낫표 (「 」).')
    print(f'Found {len(cut_off_candidates)} lines that might be cut off.')
    
    if quote_issues:
        print('\nSample of quote issues:')
        for line in quote_issues[:3]:
            print(f'ID {line[0]}: {line[2]}')

    if cut_off_candidates:
        print('\nSample of potentially cut-off sentences:')
        for line in cut_off_candidates[:5]:
            print(f'ID {line[0]}:')
            print(f'  Orig:  {line[1]}')
            print(f'  Trans: {line[2]}\n')
