import csv
import json
import os
import re

CSV_FILE = 'translation_work.csv'
JSON_FILE = 'extracted_texts.jsonl'
OUTPUT_JSON = 'translated_texts.jsonl'


def canonical_source_text(text):
    """Normalize line endings only for source-text lookup."""
    return text.replace('\r\n', '\n').replace('\r', '\n')


def restore_source_line_endings(source_text, translated_text):
    """Keep the translation's line breaks byte-compatible with the source."""
    source_breaks = re.findall(r'\r\n|\r|\n', source_text)
    translated_breaks = re.findall(r'\r\n|\r|\n', translated_text)

    if len(source_breaks) != len(translated_breaks):
        return translated_text

    replacements = iter(source_breaks)
    return re.sub(
        r'\r\n|\r|\n',
        lambda _match: next(replacements),
        translated_text,
    )


def main():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found.")
        raise SystemExit(1)
        
    translation_map = {}
    with open(CSV_FILE, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            orig_text = row.get('Japanese', '')
            trans_text = row.get('Korean', '')
            if trans_text.strip():
                key = canonical_source_text(orig_text)
                if key in translation_map and translation_map[key] != trans_text:
                    raise ValueError(
                        f"Conflicting translations for normalized source: {orig_text!r}"
                    )
                translation_map[key] = trans_text

    print(f"Loaded {len(translation_map)} translations from CSV.")
    
    count = 0
    with open(JSON_FILE, 'r', encoding='utf-8') as f_in, open(OUTPUT_JSON, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            item = json.loads(line)
            orig_text = item.get('text', '')
            lookup_key = canonical_source_text(orig_text)
            
            if lookup_key not in translation_map:
                raise KeyError(f"No translation for source text: {orig_text!r}")

            item['translated_text'] = restore_source_line_endings(
                orig_text,
                translation_map[lookup_key],
            )
                
            f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
            count += 1
            
    print(f"Generated {OUTPUT_JSON} with {count} translated lines.")
    print("Now you can run text_packer.py to inject the translations into the game!")

if __name__ == '__main__':
    main()
