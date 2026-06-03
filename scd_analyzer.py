import struct
import sys

def parse_scd(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    num_entries = struct.unpack('<I', data[4:8])[0]
    header_size = struct.unpack('<I', data[8:12])[0]
    
    offset = 16
    script_offsets = []
    
    # 0번 엔트리의 offset이 0이므로, 헤더 사이즈(3968)를 더해줘야 실제 위치일 수 있음.
    # 두번째 엔트리 offset이 0x76F(1903) 인데, 1903 + 3968 = 5871.
    for i in range(num_entries):
        name_bytes = data[offset:offset+12]
        name = name_bytes.rstrip(b'\x00').decode('ascii', errors='ignore')
        script_offset = struct.unpack('<I', data[offset+12:offset+16])[0]
        
        # 파일 내 실제 오프셋 = 헤더 크기 + 각 스크립트 오프셋
        actual_offset = header_size + script_offset
        script_offsets.append((name, actual_offset))
        offset += 16

    print(f"Total {num_entries} scripts found. Header size: {header_size}")
    
    # 첫 3개 스크립트 내용 (100바이트씩)
    for i in range(3):
        name, actual_offset = script_offsets[i]
        print(f"\n--- Script {i} : {name} (Offset 0x{actual_offset:X}) ---")
        if actual_offset < len(data):
            preview = data[actual_offset:actual_offset+100]
            print("Hex:", preview.hex())
            # Shift-JIS 디코딩 시도
            try:
                print("Text(SJIS):", preview.decode('shift_jis', errors='replace'))
            except Exception as e:
                print("Decode error:", e)

if __name__ == '__main__':
    parse_scd(sys.argv[1])
