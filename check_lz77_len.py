import struct

def check_lz77_size(data):
    if data[0] != 0x10:
        return 0
    decompressed_size = int.from_bytes(data[1:4], 'little')
    
    pos = 4
    out = 0
    while out < decompressed_size and pos < len(data):
        flags = data[pos]
        pos += 1
        for i in range(8):
            if flags & (0x80 >> i):
                if pos + 1 >= len(data): break
                block = int.from_bytes(data[pos:pos+2], 'big')
                pos += 2
                length = (block >> 12) + 3
                out += length
            else:
                if pos >= len(data): break
                pos += 1
                out += 1
            if out >= decompressed_size:
                break
    return pos

if __name__ == '__main__':
    for sec_idx in [0, 2]:
        path = f'data/cg_logo.bin_sec{sec_idx}.bin'
        sec_data = open(path, 'rb').read()
        lz77_data = sec_data[16:]
        consumed = check_lz77_size(lz77_data)
        print(f"Section {sec_idx}: Total size {len(sec_data)}, Header 16, LZ77 consumed {consumed}, Leftover {len(sec_data) - 16 - consumed}")
