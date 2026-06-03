import struct
import ndspy.lz10 as lz10

def dump_all_streams():
    with open('data/cg_logo.bin.bak2', 'rb') as f:
        data = f.read()
        
    offsets = [struct.unpack('<I', data[i*4:(i+1)*4])[0] for i in range(1, 5)]
    sec0 = data[offsets[0]:offsets[1]]
    sec2 = data[offsets[2]:offsets[3]]
    
    # Sec0
    s0_lz1 = sec0[16:31]
    with open('data/dump_s0_lz1.bin', 'wb') as f:
        f.write(lz10.decompress(s0_lz1))
        
    s0_lz2 = sec0[32:] # Stream 2
    # Find actual length of s0_lz2 by decompressing
    s0_lz2_dec = lz10.decompress(s0_lz2)
    with open('data/dump_s0_lz2.bin', 'wb') as f:
        f.write(s0_lz2_dec)
        
    # Sec2
    s2_lz1_data = sec2[16:]
    s2_lz1_dec = lz10.decompress(s2_lz1_data)
    with open('data/dump_s2_lz1.bin', 'wb') as f:
        f.write(s2_lz1_dec)
        
    # We need to find how many bytes s2_lz1 took to find s2_lz2
    # The lz10 module doesn't return consumed bytes easily.
    # We'll use our check_lz77_size
    def check_lz77_size(d):
        if d[0] != 0x10: return 0
        dec_size = int.from_bytes(d[1:4], 'little')
        pos=4; out=0
        while out < dec_size and pos < len(d):
            flags = d[pos]; pos+=1
            for i in range(8):
                if flags & (0x80>>i):
                    block = int.from_bytes(d[pos:pos+2], 'big')
                    pos+=2; out+=((block>>12)+3)
                else:
                    pos+=1; out+=1
                if out>=dec_size: break
        return pos
        
    s2_lz1_len = check_lz77_size(s2_lz1_data)
    
    # Let's check for alignment/padding before lz2
    pos = 16 + s2_lz1_len
    while pos < len(sec2) and sec2[pos] == 0:
        pos += 1
        
    if pos < len(sec2) and sec2[pos] == 0x10:
        s2_lz2_data = sec2[pos:]
        s2_lz2_dec = lz10.decompress(s2_lz2_data)
        with open('data/dump_s2_lz2.bin', 'wb') as f:
            f.write(s2_lz2_dec)
        print(f"Sec2 LZ2 decompressed! Size: {len(s2_lz2_dec)}")
    else:
        print("No Sec2 LZ2 found")
        
    print(f"Sec0 LZ1 (Palette?): {len(s0_lz1)} -> {len(lz10.decompress(s0_lz1))} bytes")
    print(f"Sec0 LZ2 (Map?): {len(s0_lz2)} -> {len(s0_lz2_dec)} bytes")
    print(f"Sec2 LZ1 (Tiles?): {s2_lz1_len} -> {len(s2_lz1_dec)} bytes")
    
    # Dump Sec3
    sec3 = data[offsets[3]:]
    with open('data/dump_sec3.bin', 'wb') as f:
        f.write(sec3)
    print(f"Sec3 (Uncompressed Map?): {len(sec3)} bytes")

if __name__ == '__main__':
    dump_all_streams()
