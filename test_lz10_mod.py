import struct
from check_lz77_len import check_lz77_size
from lz77 import compress_lz77
from test_lz77 import decompress_lz77

def process_cg_logo(mode):
    # mode: 'A' (no mod), 'B' (mod sec0 palette), 'C' (mod sec2 tiles)
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
    sec0_lz1_data = sections[0][16:]
    sec0_lz1_len = check_lz77_size(sec0_lz1_data)
    sec0_decomp = decompress_lz77(sec0_lz1_data[:sec0_lz1_len])
    
    if mode == 'B':
        # Modify first 2 colors to Red and Blue
        sec0_decomp[16] = 0x1F # Red
        sec0_decomp[17] = 0x00
        sec0_decomp[18] = 0x00
        sec0_decomp[19] = 0x7C # Blue
    
    sec0_recomp = compress_lz77(sec0_decomp)
    sec0_leftover = sec0_lz1_data[sec0_lz1_len:]
    
    target_sec0_len = len(sections[0])
    new_sec0 = sections[0][:16] + sec0_recomp + sec0_leftover
    if len(new_sec0) <= target_sec0_len:
        new_sec0.extend(b'\x00' * (target_sec0_len - len(new_sec0)))
    else:
        new_sec0 = new_sec0[:target_sec0_len] # Truncate padding at the end
    sections[0] = new_sec0

    # --- Process sec2 (Tiles) ---
    sec2_lz1_data = sections[2][16:]
    sec2_lz1_len = check_lz77_size(sec2_lz1_data)
    sec2_decomp = decompress_lz77(sec2_lz1_data[:sec2_lz1_len])
    
    if mode == 'C':
        # Corrupt first 128 bytes of tiles with zeros (better compression)
        for i in range(128):
            sec2_decomp[i] = 0x00
            
    sec2_recomp = compress_lz77(sec2_decomp)
    sec2_leftover = sec2_lz1_data[sec2_lz1_len:]
    
    target_sec2_len = len(sections[2])
    new_sec2 = sections[2][:16] + sec2_recomp + sec2_leftover
    if len(new_sec2) <= target_sec2_len:
        new_sec2.extend(b'\x00' * (target_sec2_len - len(new_sec2)))
    else:
        print(f"WARNING Mode {mode}: sec2 recompressed size ({len(new_sec2)}) exceeds target ({target_sec2_len}). Truncating!")
        new_sec2 = new_sec2[:target_sec2_len]
        
    sections[2] = new_sec2
    
    # --- Reassemble ---
    re_data = bytearray(data[:20])
    for sec in sections:
        re_data.extend(sec)
        
    with open(f'data/cg_logo_test_{mode}.bin', 'wb') as f:
        f.write(re_data)
        
    print(f"Mode {mode} processed! Target size: {len(data)}, Actual size: {len(re_data)}")

if __name__ == '__main__':
    process_cg_logo('A')
    process_cg_logo('B')
    process_cg_logo('C')
