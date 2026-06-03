import struct

def decompress_lz77(data):
    if data[0] != 0x10:
        raise ValueError("Not LZ77 compressed (expected 0x10 at byte 0)")
    decompressed_size = int.from_bytes(data[1:4], 'little')
    print(f"Expected decompressed size: {decompressed_size}")
    
    out = bytearray()
    pos = 4
    while len(out) < decompressed_size and pos < len(data):
        flags = data[pos]
        pos += 1
        for i in range(8):
            if flags & (0x80 >> i):
                # Compressed block
                if pos + 1 >= len(data): break
                block = int.from_bytes(data[pos:pos+2], 'big')
                pos += 2
                
                length = (block >> 12) + 3
                offset = (block & 0x0FFF) + 1
                
                for _ in range(length):
                    out.append(out[-offset])
            else:
                # Uncompressed byte
                if pos >= len(data): break
                out.append(data[pos])
                pos += 1
                
            if len(out) >= decompressed_size:
                break
    return out

if __name__ == '__main__':
    for sec_idx in [0, 2]:
        path = f'data/cg_logo.bin_sec{sec_idx}.bin'
        sec_data = open(path, 'rb').read()
        
        # In our analysis, the first 16 bytes are some container header.
        # The LZ77 stream seems to start at offset 16 (0x10).
        lz77_data = sec_data[16:]
        
        try:
            decomp = decompress_lz77(lz77_data)
            print(f"Section {sec_idx} decompressed successfully! Output size: {len(decomp)}")
            with open(f'data/cg_logo_sec{sec_idx}_decomp.bin', 'wb') as f:
                f.write(decomp)
        except Exception as e:
            print(f"Section {sec_idx} failed: {e}")
