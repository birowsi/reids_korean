import struct
from PIL import Image
import ndspy.lz10 as lz10

def generate_nds_data(img_path):
    img = Image.open(img_path).convert('RGBA')
    img.thumbnail((256, 192), Image.Resampling.LANCZOS)
    
    canvas = Image.new('RGBA', (256, 192), (0, 0, 0, 0))
    x = (256 - img.width) // 2
    y = (192 - img.height) // 2
    canvas.paste(img, (x, y), img)
    
    pal_img = canvas.convert('P', palette=Image.Palette.ADAPTIVE, colors=15)
    
    # Palette stream (32 bytes = 16 colors)
    # Color 0: Transparent/White
    # Color 1: Black
    s0_lz1 = b'\x10\x20\x00\x00\x0C\xFF\x7F\x00\x00\xF0\x01\x70\x01'
    s0_lz1 = s0_lz1.ljust(16, b'\x00') # exactly 4 words
    
    # Tiles and Map for 8BPP!
    tiles = []
    tile_map = {}
    map_entries = []
    
    # 8BPP blank tile (64 bytes of 0)
    blank_tile = bytes([0] * 64)
    tiles.append(blank_tile)
    tile_map[blank_tile] = 0
    
    pixels = pal_img.load()
    
    for ty in range(24):
        for tx in range(32):
            tile_data = bytearray(64)
            for py in range(8):
                for px in range(8):
                    ix = tx*8 + px
                    iy = ty*8 + py
                    
                    a = canvas.getpixel((ix, iy))[3]
                    # Index 1 if opaque, else 0
                    c = 1 if a > 128 else 0
                    
                    tile_data[py*8 + px] = c
                    
            tile_bytes = bytes(tile_data)
            if tile_bytes not in tile_map:
                tile_map[tile_bytes] = len(tiles)
                tiles.append(tile_bytes)
                
            tile_idx = tile_map[tile_bytes]
            map_entries.append(tile_idx) # No palette bits in 8bpp map entries? Wait, NDS map entries usually don't need palette index in 8bpp mode, but the format is the same (bits 0-9 are tile index). So we just append tile_idx!
            
    print(f"Generated {len(tiles)} 8BPP tiles.")
    
    # Compress tiles
    tiles_data = bytearray()
    for t in tiles: tiles_data.extend(t)
    s2_lz1 = lz10.compress(tiles_data)
    
    # Compress map
    map_data = bytearray()
    for e in map_entries:
        map_data.extend(struct.pack('<H', e))
    s2_lz2 = lz10.compress(map_data)
    
    return s0_lz1, s2_lz1, s2_lz2

def align4(data):
    pad = (4 - (len(data) % 4)) % 4
    return data + (b'\x00' * pad)

def inject():
    s0_lz1, s2_lz1, s2_lz2 = generate_nds_data('nerv.png')
    
    with open('data/cg_logo.bin.bak2', 'rb') as f:
        orig = f.read()
        
    # Original sec0 map (s0_lz2)
    # Starts at offset 32 in sec0.
    # Length was 620 bytes.
    orig_s0_lz2 = orig[20+32 : 20+652]
    
    # Build sec0
    s0_lz1_padded = align4(s0_lz1)
    s0_lz2_padded = align4(orig_s0_lz2)
    
    sec0_payload = s0_lz1_padded + s0_lz2_padded
    sec0_header = struct.pack('<4I', 3, len(s0_lz1_padded)//4, len(s0_lz2_padded)//4, 112)
    sec0 = sec0_header + sec0_payload
    
    # sec1
    sec1 = orig[672:692]
    
    # Build sec2
    s2_lz1_padded = align4(s2_lz1)
    s2_lz2_padded = align4(s2_lz2)
    
    sec2_payload = s2_lz1_padded + s2_lz2_padded
    sec2_header = struct.pack('<4I', 3, len(s2_lz1_padded)//4, len(s2_lz2_padded)//4, 112)
    sec2 = sec2_header + sec2_payload
    
    # Build global header
    # 01000080
    # 20 (sec0)
    # 20 + len(sec0) (sec1)
    # 20 + len(sec0) + 20 (sec2)
    # 20 + len(sec0) + 20 + len(sec2) (sec3)
    
    off0 = 20
    off1 = off0 + len(sec0)
    off2 = off1 + len(sec1)
    off3 = off2 + len(sec2)
    
    global_header = struct.pack('<I', 0x80000001) + struct.pack('<4I', off0, off1, off2, off3)
    
    final_bin = global_header + sec0 + sec1 + sec2
    
    # Pad to original size 6484 if smaller, just to be safe
    if len(final_bin) < 6484:
        final_bin = final_bin.ljust(6484, b'\x00')
        
    with open('data/cg_logo.bin', 'wb') as f:
        f.write(final_bin)
        
    print(f"Injected nerv.png! New file size: {len(final_bin)}")

if __name__ == '__main__':
    inject()
