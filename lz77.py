import struct

def compress_lz77(data):
    """Simple NDS BIOS compatible LZ77 compressor."""
    out = bytearray()
    out.append(0x10)
    out.extend(struct.pack('<I', len(data))[:3])
    
    pos = 0
    while pos < len(data):
        flags_pos = len(out)
        out.append(0)
        flags = 0
        
        for i in range(8):
            if pos >= len(data):
                break
                
            # Search for longest match
            match_len = 0
            match_offset = 0
            
            # The NDS BIOS LZ77 requires length between 3 and 18
            # offset between 1 and 4096
            max_len = min(18, len(data) - pos)
            max_offset = min(4096, pos)
            
            if max_len >= 3 and max_offset > 0:
                best_len = 0
                for off in range(2, max_offset + 1):
                    l = 0
                    while l < max_len and data[pos - off + l] == data[pos + l]:
                        l += 1
                    if l > best_len:
                        best_len = l
                        best_off = off
                        if best_len == max_len:
                            break
                            
                if best_len >= 3:
                    match_len = best_len
                    match_offset = best_off
                    
            if match_len >= 3:
                # Compressed block
                flags |= (0x80 >> i)
                block = (((match_len - 3) & 0xF) << 12) | ((match_offset - 1) & 0xFFF)
                out.extend(struct.pack('>H', block))
                pos += match_len
            else:
                # Raw byte
                out.append(data[pos])
                pos += 1
                
        out[flags_pos] = flags
        
    return out

if __name__ == '__main__':
    # Test compressor by compressing and then decompressing
    test_data = b"Hello, World! This is a test string to test the LZ77 compressor. Hello, World!"
    comp = compress_lz77(test_data)
    print(f"Original size: {len(test_data)}, Compressed size: {len(comp)}")
    
    # Simple decompress to verify
    from test_lz77 import decompress_lz77
    decomp = decompress_lz77(comp)
    assert decomp == test_data, "Compression failed!"
    print("LZ77 Compressor verified!")
