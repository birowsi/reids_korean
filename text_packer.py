import os
import struct
import json
import glob

def dynamic_repack_scd(original_scd_path, jsonl_path, output_path):
    """
    SCD 파일의 헤더 구조(오프셋 테이블)를 완전히 분석하여,
    텍스트 길이가 변하더라도 블록 크기와 포인터를 자동으로 재계산해 재빌드합니다.
    """
    with open(original_scd_path, 'rb') as f:
        data = f.read()

    magic = data[:4]
    if magic != b'SCR\x00':
        print("Invalid magic number")
        return
        
    num_entries = struct.unpack('<I', data[4:8])[0]
    header_size = struct.unpack('<I', data[8:12])[0]
    
    # 1. 블록 정보 파싱
    offset = 16
    blocks = []
    for i in range(num_entries):
        name_bytes = data[offset:offset+12]
        script_offset = struct.unpack('<I', data[offset+12:offset+16])[0]
        actual_offset = header_size + script_offset
        blocks.append({
            "index": i,
            "name_bytes": name_bytes,
            "original_actual_offset": actual_offset,
            "original_script_offset": script_offset,
            "data": bytearray()
        })
        offset += 16
        
    # 각 블록의 데이터 추출
    for i, block in enumerate(blocks):
        start_offset = block["original_actual_offset"]
        if i + 1 < len(blocks):
            end_offset = blocks[i+1]["original_actual_offset"]
        else:
            end_offset = len(data)
        block["data"] = bytearray(data[start_offset:end_offset])

    # 2. 변경점(Replacements) 준비
    # 블록 인덱스별로 분류합니다.
    replacements_by_block = {i: [] for i in range(num_entries)}
    
    try:
        with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as mf:
            korean_mapping = json.load(mf)
    except:
        korean_mapping = {}

    target_jsonl = 'translated_texts.jsonl' if os.path.exists('translated_texts.jsonl') else jsonl_path

    with open(target_jsonl, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            # Remove .bak extension from original_scd_path for comparison
            base_name = os.path.basename(original_scd_path)
            if base_name.endswith('.bak'):
                base_name = base_name[:-4]
            if item["file"] == base_name:
                b_idx = item["block_index"]
                old_bytes = bytes.fromhex(item["raw_hex"])
                
                # 텍스트 인코딩 로직 (한글 매핑 적용)
                if "translated_text" in item:
                    text_to_encode = item["translated_text"]
                    new_bytes_list = bytearray()
                    for c in text_to_encode:
                        if c in korean_mapping:
                            sjis_int = korean_mapping[c]['sjis']
                            new_bytes_list.append(sjis_int >> 8)
                            new_bytes_list.append(sjis_int & 0xFF)
                        else:
                            try:
                                encoded = c.encode('shift_jis')
                                new_bytes_list.extend(encoded)
                            except:
                                new_bytes_list.extend(b'?')
                    
                    # Pad or truncate to match original length (MANDATORY due to internal script pointers)
                    expected_len = len(old_bytes)
                    if len(new_bytes_list) < expected_len:
                        diff = expected_len - len(new_bytes_list)
                        while diff > 1:
                            new_bytes_list.extend([0x81, 0x40])
                            diff -= 2
                        if diff == 1:
                            new_bytes_list.append(0x20)
                    elif len(new_bytes_list) > expected_len:
                        new_bytes_list = new_bytes_list[:expected_len]
                        
                    new_bytes = bytes(new_bytes_list)
                else:
                    new_bytes = old_bytes
                
                # 블록 내 상대 오프셋 계산
                rel_offset = item["original_offset"] - blocks[b_idx]["original_actual_offset"]
                
                replacements_by_block[b_idx].append({
                    "rel_offset": rel_offset,
                    "old_bytes": old_bytes,
                    "new_bytes": new_bytes
                })

    # 3. 블록 데이터 수정 (가변 길이 지원)
    for b_idx in range(num_entries):
        reps = replacements_by_block[b_idx]
        if not reps:
            continue
            
        # 뒤에서부터 수정해야 상대 오프셋이 안 꼬임
        reps.sort(key=lambda x: x["rel_offset"], reverse=True)
        block_data = blocks[b_idx]["data"]
        
        for rep in reps:
            ro = rep["rel_offset"]
            old_b = rep["old_bytes"]
            new_b = rep["new_bytes"]
            
            # 무결성 체크 (기존 데이터와 위치가 맞는지)
            if block_data[ro:ro+len(old_b)] == old_b:
                # 데이터 슬라이싱으로 길이 변환 교체
                block_data = block_data[:ro] + new_b + block_data[ro+len(old_b):]
            else:
                print(f"Warning: Data mismatch in block {b_idx} at relative offset {ro}")
                
        blocks[b_idx]["data"] = block_data

    # 4. 헤더 및 새 오프셋 테이블 구성
    new_file_data = bytearray()
    
    # 공통 헤더 16바이트
    new_file_data.extend(data[:16])
    
    # 5. 블록 데이터를 합치면서 새 오프셋 기록
    current_script_offset = 0
    header_entries_data = bytearray()
    blocks_data = bytearray()
    
    for block in blocks:
        # 엔트리 추가 (이름 12바이트 + 새 오프셋 4바이트)
        header_entries_data.extend(block["name_bytes"])
        header_entries_data.extend(struct.pack('<I', current_script_offset))
        
        # 블록 데이터 병합
        blocks_data.extend(block["data"])
        
        # 다음 블록 오프셋은 현재 블록 길이를 더함
        current_script_offset += len(block["data"])
        
    new_file_data.extend(header_entries_data)
    new_file_data.extend(blocks_data)

    with open(output_path, 'wb') as f:
        f.write(new_file_data)
        
    print(f"Dynamic repacked file saved to {output_path}")

if __name__ == '__main__':
    for scd_file in glob.glob("data/*.scd"):
        if not scd_file.endswith('.bak'):
            bak_path = scd_file + ".bak"
            if not os.path.exists(bak_path):
                os.rename(scd_file, bak_path)
            
            if os.path.exists(bak_path):
                print(f"Repacking {scd_file}...")
                dynamic_repack_scd(bak_path, "translated_texts.jsonl", scd_file)

