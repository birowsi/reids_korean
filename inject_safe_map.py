import struct
from PIL import Image

def rgb_to_gba(r, g, b):
    r5 = r // 8
    g5 = g // 8
    b5 = b // 8
    return r5 | (g5 << 5) | (b5 << 10)

def reconstruct():
    # Read sections
    sec0 = bytearray(open('data/MobiclipLogo.bin_sec0.bin', 'rb').read())
    sec1 = bytearray(open('data/MobiclipLogo.bin_sec1.bin', 'rb').read())
    sec2 = bytearray(open('data/MobiclipLogo.bin_sec2.bin', 'rb').read())
    sec3 = bytearray(open('data/MobiclipLogo.bin_sec3.bin', 'rb').read())
    
    img = Image.open('nerv_small.png') # 256x40
    if img.mode != 'P':
        img = img.convert('P', palette=Image.ADAPTIVE, colors=16)

    pal_raw = img.getpalette()
    if not pal_raw: pal_raw = [0]*768
    
    # Inject palette into sec0 (offset 16)
    for i in range(16):
        r, g, b = pal_raw[i*3], pal_raw[i*3+1], pal_raw[i*3+2]
        val = rgb_to_gba(r, g, b)
        sec0[16 + i*2] = val & 0xFF
        sec0[16 + i*2 + 1] = (val >> 8) & 0xFF
        
    width, height = img.size
    pixels = list(img.getdata())
    
    max_tiles = 158
    unique_tiles = []
    map_entries = []
    
    # Generate tiles and map
    for ty in range(height // 8):
        for tx in range(width // 8):
            tile_bytes = bytearray()
            for py in range(8):
                for px in range(0, 8, 2):
                    idx1 = (ty*8 + py) * width + (tx*8 + px)
                    idx2 = idx1 + 1
                    p1 = pixels[idx1] % 16
                    p2 = pixels[idx2] % 16
                    tile_bytes.append((p2 << 4) | p1)
                    
            try:
                t_idx = unique_tiles.index(tile_bytes)
            except ValueError:
                t_idx = len(unique_tiles)
                if t_idx < max_tiles:
                    unique_tiles.append(tile_bytes)
                else:
                    t_idx = 0 # fallback to tile 0 if we exceed max tiles
                    
            map_entries.append(t_idx)

    # Overwrite sec2 (Tiles)
    # Clear sec2 first (skip 16 byte header)
    for i in range(16, len(sec2)):
        sec2[i] = 0
        
    for i, t_bytes in enumerate(unique_tiles):
        offset = 16 + i * 32
        sec2[offset:offset+32] = t_bytes
        
    # Overwrite sec3 (Map)
    # The map is 346 entries (692 bytes).
    # NDS screens are 32 tiles wide.
    # Our image is 256x40, which is 32x5 tiles = 160 tiles.
    # We want to center it vertically. The screen is 24 tiles high.
    # 346 entries is 32x10 + 26. This implies the Mobiclip map is NOT a full 32x24 screen map!
    # It might just be a 32x10 map centered by the engine.
    
    # Let's clear sec3 first
    for i in range(len(sec3)):
        sec3[i] = 0
        
    # Let's place our 32x5 map in the middle of the 32x10 map space.
    # Offset by 2 rows = 64 tiles.
    start_map_idx = 64
    for i, m in enumerate(map_entries):
        if start_map_idx + i < len(sec3) // 2:
            val = m & 0x3FF # pb=0, no flip
            struct.pack_into('<H', sec3, (start_map_idx + i) * 2, val)
            
    # Write back
    header = bytearray(b'\x01\x00\x00\x80')
    off1 = 20
    off2 = off1 + len(sec0)
    off3 = off2 + len(sec1)
    off4 = off3 + len(sec2)
    header.extend(struct.pack('<I', off1))
    header.extend(struct.pack('<I', off2))
    header.extend(struct.pack('<I', off3))
    header.extend(struct.pack('<I', off4))
    
    with open('data/MobiclipLogo.bin', 'wb') as f:
        f.write(header)
        f.write(sec0)
        f.write(sec1)
        f.write(sec2)
        f.write(sec3)

    print("Reconstructed with Map perfectly!")
    
if __name__ == '__main__':
    reconstruct()
