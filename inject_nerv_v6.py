import struct
from PIL import Image
import ndspy.lz10 as lz10

def align4(data):
    pad = (4 - (len(data) % 4)) % 4
    return data + (b'\x00' * pad)

def generate_top_screen_data():
    # Tile 0: Filled with color index 1
    top_tiles_data = bytes([0x01] * 64)
    s0_lz1 = align4(lz10.compress(top_tiles_data))

    # Map: 256x192 (768 words) using Tile 0
    top_map_data = bytearray()
    for i in range(768):
        top_map_data.extend(struct.pack('<H', 0x0000))
    s0_lz2 = align4(lz10.compress(top_map_data))

    # Palette: 448 bytes
    top_pal_data = bytearray(448)
    # Fill everything with White
    for i in range(224):
        top_pal_data[i*2] = 0xFF
        top_pal_data[i*2+1] = 0x7F

    sec0_header = struct.pack('<4I', 3, len(s0_lz1)//4, len(s0_lz2)//4, len(top_pal_data)//4)
    new_sec01 = sec0_header + s0_lz1 + s0_lz2 + top_pal_data
    return new_sec01

def generate_bottom_screen_data(img_path):
    img = Image.open(img_path).convert('RGBA')
    img.thumbnail((256, 192), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (256, 192), (0, 0, 0, 0))
    x = (256 - img.width) // 2
    y = (192 - img.height) // 2
    canvas.paste(img, (x, y), img)
    
    tiles = []
    tile_map = {}
    map_entries = []
    
    # 8BPP Tiles
    # Tile 0: Background color (Color 1)
    blank_tile = bytes([0x01] * 64)
    tiles.append(blank_tile)
    tile_map[blank_tile] = 0
    
    for ty in range(24):
        for tx in range(32):
            tile_data = bytearray(64)
            for py in range(8):
                for px in range(8):
                    ix = tx*8 + px
                    iy = ty*8 + py
                    
                    r, g, b, a = canvas.getpixel((ix, iy))
                    
                    # 0x02 = Black, 0x01 = Background (White)
                    # If transparent OR very bright, make it white. Otherwise make it black.
                    brightness = (r + g + b) / 3
                    if a < 128 or brightness > 200:
                        tile_data[py*8 + px] = 0x01
                    else:
                        tile_data[py*8 + px] = 0x02
                        
            tile_bytes = bytes(tile_data)
            if tile_bytes not in tile_map:
                tile_map[tile_bytes] = len(tiles)
                tiles.append(tile_bytes)
                
            tile_idx = tile_map[tile_bytes]
            map_entries.append(tile_idx)
            
    tiles_data = bytearray()
    for t in tiles: tiles_data.extend(t)
    s2_lz1 = lz10.compress(tiles_data)
    
    map_data = bytearray()
    for e in map_entries:
        map_data.extend(struct.pack('<H', e))
    s2_lz2 = lz10.compress(map_data)
    
    # Bottom Screen Palette (448 bytes = 224 colors)
    pal_data = bytearray(448)
    
    # Fill with White
    for i in range(224):
        pal_data[i*2] = 0xFF
        pal_data[i*2+1] = 0x7F
        
    # Color 2: Black
    pal_data[2*2] = 0x00
    pal_data[2*2+1] = 0x00
    
    return align4(s2_lz1), align4(s2_lz2), bytes(pal_data)

def inject():
    new_sec01 = generate_top_screen_data()
    s2_lz1, s2_lz2, bot_palette = generate_bottom_screen_data('2.png')
    
    sec23_header = struct.pack('<4I', 3, len(s2_lz1)//4, len(s2_lz2)//4, len(bot_palette)//4)
    sec23_payload = s2_lz1 + s2_lz2 + bot_palette
    sec23 = sec23_header + sec23_payload
    
    off0 = 20
    off2 = off0 + len(new_sec01)
    off1 = off2 - 20 # Keep off1 20 bytes before off2, just like original
    
    # Bottom screen logic
    if len(sec23) <= 5100:
        sec2 = sec23.ljust(5100, b'\x00')
        sec3 = b''
    else:
        sec2 = sec23[:5100]
        sec3 = sec23[5100:]
        
    off3 = off2 + 5100
    new_global_header = struct.pack('<I', 0x80000001) + struct.pack('<4I', off0, off1, off2, off3)
    
    final_bin = new_global_header + new_sec01 + sec2 + sec3
    
    if len(final_bin) < 6484:
        final_bin = final_bin.ljust(6484, b'\x00')
        
    with open('data/cg_logo.bin', 'wb') as f:
        f.write(final_bin)
        
    print(f"Injected nerv.png! New file size: {len(final_bin)}")

if __name__ == '__main__':
    inject()
