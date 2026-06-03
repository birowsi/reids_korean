import json

def index_to_sjis(idx):
    hi = idx // 188
    lo = idx % 188
    lo += 0x40
    if lo >= 0x7F:
        lo += 1
    hi += 0x81
    if hi >= 0xA1:
        hi += 0x40
    return (hi << 8) | lo

# 1. Collect all used SJIS indices in the original script
used_indices = set()
try:
    with open('extracted_texts.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            obj = json.loads(line)
            if 'text' in obj:
                for c in obj['text']:
                    try:
                        sjis_val = c.encode('shift_jis')
                        if len(sjis_val) == 2:
                            val = (sjis_val[0] << 8) | sjis_val[1]
                            
                            hi = val >> 8
                            lo = val & 0xFF
                            if hi >= 0xE0: hi -= 0x40
                            hi -= 0x81
                            if lo >= 0x80: lo -= 1
                            lo -= 0x40
                            idx = hi * 188 + lo
                            used_indices.add(idx)
                    except: pass
except Exception as e:
    print(e)

print(f"Original script uses {len(used_indices)} unique SJIS indices.")

# 2. Get the 2350 KSC5601 syllables
ksc5601 = []
for b1 in range(0xB0, 0xC9):
    for b2 in range(0xA1, 0xFF):
        try:
            char = bytes([b1, b2]).decode('euc-kr')
            ksc5601.append(char)
        except: pass

# 3. Find 2350 unused indices starting from a high index (e.g. 8500) to avoid overwriting kanji
available_indices = []
for i in range(8500, 10930):
    if i not in used_indices:
        available_indices.append(i)

if len(available_indices) < len(ksc5601):
    print("Error: Not enough unused indices!")
    exit(1)

# 4. Map them
mapping = {}
for i, char in enumerate(ksc5601):
    idx = available_indices[i]
    sjis = index_to_sjis(idx)
    mapping[char] = {
        'sjis_hex': hex(sjis),
        'sjis_int': sjis,
        'font_index': idx
    }

# Also map basic ASCII characters to themselves just in case? 
# Usually ASCII is 1-byte, we only map 2-byte Korean characters here.

with open('korean_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Successfully mapped {len(mapping)} Korean characters to unused SJIS slots.")
print("Mapping saved to korean_mapping.json")
