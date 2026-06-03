import struct
from lz77 import compress_lz77
from test_lz77 import decompress_lz77

def process_cg_logo(mode):
    with open('data/cg_logo.bin.bak2', 'rb') as f:
        data = f.read()
        
    offsets = [struct.unpack('<I', data[i*4:(i+1)*4])[0] for i in range(1, 5)]
    sections = [
        bytearray(data[offsets[0]:offsets[1]]),
        bytearray(data[offsets[1]:offsets[2]]),
        bytearray(data[offsets[2]:offsets[3]]),
        bytearray(data[offsets[3]:])
    ]
    
    # --- Process sec0 (Palette) ---
    sec0_lz1_data = sections[0][16:31] # Original size is 15
    sec0_decomp = decompress_lz77(sec0_lz1_data)
    
    if mode == 'B':
        sec0_decomp[16] = 0x1F # Red
        sec0_decomp[17] = 0x00
        sec0_decomp[18] = 0x00
        sec0_decomp[19] = 0x7C # Blue
    
    sec0_recomp = compress_lz77(sec0_decomp)
    
    # Original stream 2 starts at offset 32
    if len(sec0_recomp) > 16:
        raise ValueError(f"sec0_recomp too large: {len(sec0_recomp)}")
        
    new_sec0 = sections[0][:16] + sec0_recomp
    # Pad to offset 32
    new_sec0.extend(b'\x00' * (32 - len(new_sec0)))
    # Add leftover starting from offset 32
    new_sec0.extend(sections[0][32:])
    
    # Ensure length matches original sec0
    if len(new_sec0) != len(sections[0]):
        print(f"Warning: sec0 length changed from {len(sections[0])} to {len(new_sec0)}")
    sections[0] = new_sec0

    # --- Process sec2 (Tiles) ---
    sec2_lz1_data = sections[2][16:16+4906] # Original size is 4906
    sec2_decomp = decompress_lz77(sec2_lz1_data)
    
    if mode == 'C':
        for i in range(128):
            sec2_decomp[i] = 0x00
            
    sec2_recomp = compress_lz77(sec2_decomp)
    
    # Original stream 2 starts at offset 4924
    if len(sec2_recomp) > (4924 - 16):
        raise ValueError(f"sec2_recomp too large: {len(sec2_recomp)}")
        
    new_sec2 = sections[2][:16] + sec2_recomp
    # Pad to offset 4924
    new_sec2.extend(b'\x00' * (4924 - len(new_sec2)))
    # Add leftover starting from offset 4924
    new_sec2.extend(sections[2][4924:])
    
    # Ensure length matches original sec2
    if len(new_sec2) != len(sections[2]):
        print(f"Warning: sec2 length changed from {len(sections[2])} to {len(new_sec2)}")
    sections[2] = new_sec2
    
    # --- Reassemble ---
    re_data = bytearray(data[:20])
    for sec in sections:
        re_data.extend(sec)
        
    with open(f'data/cg_logo_test_{mode}.bin', 'wb') as f:
        f.write(re_data)
        
    print(f"Mode {mode} processed! Target size: {len(data)}, Actual size: {len(re_data)}")

if __name__ == '__main__':
    try:
        process_cg_logo('A')
        process_cg_logo('B')
        process_cg_logo('C')
    except Exception as e:
        print(f"Error: {e}")
