import sys
import json
import os
import time
from deep_translator import GoogleTranslator

sys.stdout.reconfigure(encoding='utf-8')

CACHE_FILE = 'translation_cache.json'
INPUT_FILE = 'extracted_texts.jsonl'
OUTPUT_FILE = 'translated_texts.jsonl'

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def main():
    cache = load_cache()
    
    unique_texts = set()
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            text = item.get('text', '')
            if text:
                unique_texts.add(text)
                
    to_translate = [t for t in unique_texts if t not in cache]
    print(f"Total unique texts: {len(unique_texts)}")
    print(f"Already cached: {len(cache)}")
    print(f"To translate: {len(to_translate)}")
    
    translator = GoogleTranslator(source='ja', target='ko')
    
    batch = []
    batch_len = 0
    MAX_LEN = 2000
    
    def process_batch(current_batch):
        if not current_batch:
            return
        
        # We need a delimiter that is unlikely to be in the text and preserved by MT
        delim = '\n@@@\n'
        combined = delim.join(current_batch)
        
        retries = 3
        for r in range(retries):
            try:
                translated = translator.translate(combined)
                
                # Check if it split properly
                parts = [p.strip() for p in translated.split('@@@')]
                
                # If length matches, we assume 1:1 mapping
                if len(parts) == len(current_batch):
                    for i, orig in enumerate(current_batch):
                        cache[orig] = parts[i]
                    save_cache(cache)
                    break
                else:
                    # length mismatch, maybe MT messed up delimiter. Fallback to 1 by 1
                    for orig in current_batch:
                        for r2 in range(3):
                            try:
                                res = translator.translate(orig)
                                cache[orig] = res
                                break
                            except Exception as e:
                                time.sleep(1)
                    save_cache(cache)
                    break
                    
            except Exception as e:
                print(f"Error: {e}, retrying...")
                time.sleep(2)
        
        print(f"Translated {len(cache)} / {len(unique_texts)}")

    for t in to_translate:
        if batch_len + len(t) > MAX_LEN and batch:
            process_batch(batch)
            batch = []
            batch_len = 0
            time.sleep(0.5) # Sleep to avoid rate limit
        
        batch.append(t)
        batch_len += len(t) + 5
        
    if batch:
        process_batch(batch)
        
    print("Translation phase complete. Re-generating JSONL...")
    
    # Generate translated_texts.jsonl
    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            item = json.loads(line)
            text = item.get('text', '')
            if text in cache:
                item['translated_text'] = cache[text]
                
                # If the text is empty or just special chars, handle it?
                # The text_packer will use translated_text
            
            f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
            count += 1
            
    print(f"Generated {OUTPUT_FILE} with {count} lines.")

if __name__ == '__main__':
    main()
