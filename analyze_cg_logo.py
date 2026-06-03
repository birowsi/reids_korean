import struct
import os

def analyze_cg_logo():
    path = 'data/cg_logo.bin'
    data = open(path, 'rb').read()
    total_len = len(data)
    print(f"[{path}] Total size: {total_len} bytes")
    print(f"Header first 32 bytes (0x20): {data[:32].hex()}")
    
    offsets = [struct.unpack('<I', data[i*4:(i+1)*4])[0] for i in range(1, 5)]
    print(f"Offsets: {offsets}")
    
    sections = []
    sections.append(data[offsets[0]:offsets[1]])
    sections.append(data[offsets[1]:offsets[2]])
    sections.append(data[offsets[2]:offsets[3]])
    sections.append(data[offsets[3]:])
    
    for i, sec in enumerate(sections):
        size = len(sec)
        hex_preview = sec[:32].hex()
        
        guess = "Unknown"
        if size == 32:
            guess = "16-color Palette"
        elif size == 512:
            guess = "256-color Palette"
        elif size % 32 == 0:
            guess = f"4bpp Tiles ({size//32} tiles)"
        elif size == 1536:
            guess = "32x24 Map"
        elif size == 2048:
            guess = "32x32 Map"
            
        # some custom sizes:
        if size == 652:
            guess = "Palette with padding? Or multiple palettes? 652/32 = 20.375"
        elif size == 692:
            guess = "Map data? 692/2 = 346 entries"
        elif size == 5100:
            guess = "Tiles? 5100/32 = 159.375"
            
        print(f"\n[sec{i}]")
        print(f"Size: {size} bytes")
        print(f"First 32 bytes (0x20): {hex_preview}")
        print(f"Guess: {guess}")

        open(f'data/cg_logo.bin_sec{i}.bin', 'wb').write(sec)
        
    # Reassemble without modification test
    re_data = bytearray(data[:20])
    for sec in sections:
        re_data.extend(sec)
        
    open('data/cg_logo_rebuilt.bin', 'wb').write(re_data)
    
    import hashlib
    orig_hash = hashlib.sha256(data).hexdigest()
    re_hash = hashlib.sha256(re_data).hexdigest()
    print(f"\n[Rebuild Test]")
    print(f"Original SHA-256: {orig_hash}")
    print(f"Rebuilt  SHA-256: {re_hash}")
    print("Match!" if orig_hash == re_hash else "Mismatch!")

if __name__ == '__main__':
    analyze_cg_logo()
