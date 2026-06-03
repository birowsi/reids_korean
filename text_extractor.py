import os
import struct
import json
import glob

def extract_strings(data, start_offset, size):
    strings = []
    current_offset = start_offset
    end_offset = start_offset + size
    
    while current_offset < end_offset:
        null_index = data.find(b'\x00', current_offset, end_offset)
        if null_index == -1:
            break
            
        string_data = data[current_offset:null_index]
        
        if len(string_data) > 0:
            try:
                # SJIS 디코딩 후 터미널 출력용으로 ascii가 아닌건 \u 형식으로 보게 함 (테스트용)
                decoded_text = string_data.decode('shift_jis', errors='strict')
                
                # 히라가나, 가타카나, 한자, 일본식 특수기호만 엄격하게 매칭
                # (쓰레기 데이터 필터링)
                has_valid_chars = any(
                    0x3040 <= ord(c) <= 0x309F or  # Hiragana
                    0x30A0 <= ord(c) <= 0x30FF or  # Katakana
                    0x4E00 <= ord(c) <= 0x9FBF or  # Kanji
                    c in '「」『』【】（）！？、。…'
                    for c in decoded_text
                )
                
                if has_valid_chars:
                    strings.append({
                        "offset": current_offset,
                        "hex": string_data.hex(),
                        "text": decoded_text
                    })
            except UnicodeDecodeError:
                pass
                
        current_offset = null_index + 1
        
    return strings

def parse_scd(filepath, output_jsonl):
    with open(filepath, 'rb') as f:
        data = f.read()

    magic = data[:4]
    if magic != b'SCR\x00':
        return False
        
    num_entries = struct.unpack('<I', data[4:8])[0]
    header_size = struct.unpack('<I', data[8:12])[0]
    
    offset = 16
    script_blocks = []
    
    for i in range(num_entries):
        name_bytes = data[offset:offset+12]
        name = name_bytes.rstrip(b'\x00').decode('ascii', errors='ignore')
        script_offset = struct.unpack('<I', data[offset+12:offset+16])[0]
        
        actual_offset = header_size + script_offset
        script_blocks.append({"index": i, "name": name, "offset": actual_offset})
        offset += 16

    results = []
    
    for i, block in enumerate(script_blocks):
        start_offset = block["offset"]
        if i + 1 < len(script_blocks):
            end_offset = script_blocks[i+1]["offset"]
        else:
            end_offset = len(data)
            
        block_size = end_offset - start_offset
        
        if start_offset < len(data) and block_size > 0:
            extracted = extract_strings(data, start_offset, block_size)
            for item in extracted:
                results.append({
                    "file": os.path.basename(filepath),
                    "block_index": block["index"],
                    "block_name": block["name"],
                    "original_offset": item["offset"],
                    "raw_hex": item["hex"],
                    "text": item["text"]
                })
                
    if results:
        with open(output_jsonl, 'a', encoding='utf-8') as f:
            for res in results:
                f.write(json.dumps(res, ensure_ascii=False) + '\n')
                
    return len(results)

if __name__ == '__main__':
    scd_files = glob.glob('data/*.scd')
    output_file = 'extracted_texts.jsonl'
    
    if os.path.exists(output_file):
        os.remove(output_file)
        
    total_strings = 0
    for f in scd_files:
        print(f"Processing {f}...")
        count = parse_scd(f, output_file)
        if count is not False:
             total_strings += count
             
    print(f"Total extracted text strings: {total_strings}")
    print(f"Output saved to {output_file}")
