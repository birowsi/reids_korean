import json

count = 0
with open('extracted_texts.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if 'リツコ' in obj.get('text', '') and obj['file'] != 'asuka.scd':
            print(f"{obj['file']} - {obj['text']}".encode('utf-8', 'ignore').decode('utf-8'))
            count += 1
            if count >= 10:
                break
