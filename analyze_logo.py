import sys
import struct

def analyze_bin(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    # 헤더 분석: 첫 4바이트는 01 00 00 80 이고 그 뒤로 오프셋들이 있는 것 같음
    offsets = []
    for i in range(1, 5): # 4개의 오프셋으로 추정
        offset = struct.unpack('<I', data[i*4:(i+1)*4])[0]
        offsets.append(offset)
        
    print(f"File: {filepath}")
    print(f"Offsets: {offsets}")
    
    # 각 오프셋 구간을 별도의 파일로 저장해봅시다.
    offsets.append(len(data)) # 마지막 끝 위치
    
    for i in range(len(offsets) - 1):
        start = offsets[i]
        end = offsets[i+1]
        section_data = data[start:end]
        out_name = f"{filepath}_sec{i}.bin"
        with open(out_name, 'wb') as out_f:
            out_f.write(section_data)
        print(f"Section {i}: {start} to {end} (size {end-start}), saved to {out_name}")
        if len(section_data) > 16:
            print(f"  Preview: {section_data[:16].hex()}")

if __name__ == '__main__':
    analyze_bin('data/MobiclipLogo.bin')
    analyze_bin('data/cg_logo.bin')
