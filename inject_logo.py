import struct
from PIL import Image
import os

def rgb_to_gba(r, g, b):
    # Convert 8-bit RGB to 5-bit BGR for GBA/NDS
    r5 = r // 8
    g5 = g // 8
    b5 = b // 8
    return r5 | (g5 << 5) | (b5 << 10)

def inject_logo(img_path, original_bin_path, output_bin_path):
    img = Image.open(img_path)
    if img.mode != 'P':
        img = img.convert('P', palette=Image.ADAPTIVE, colors=16)

    pal_raw = img.getpalette()
    if not pal_raw:
        pal_raw = [0]*768
        
    # extract first 16 colors
    colors_rgb = []
    for i in range(16):
        r, g, b = pal_raw[i*3], pal_raw[i*3+1], pal_raw[i*3+2]
        colors_rgb.append((r, g, b))

    # Create GBA palette data (32 bytes = 16 colors * 2 bytes)
    pal_data = bytearray()
    for r, g, b in colors_rgb:
        val = rgb_to_gba(r, g, b)
        pal_data.extend(struct.pack('<H', val))
        
    # Pad palette to match original size (652 bytes) to be safe,
    # or just write 32 bytes and let offsets handle it.
    # The game might expect a specific size. Let's pad it to 652 bytes.
    # Actually, original was 652 bytes. Let's just create exactly 652 bytes.
    pal_data.extend(b'\x00' * (652 - len(pal_data)))

    # Process tiles and map
    width, height = img.size
    width_tiles = width // 8
    height_tiles = height // 8
    
    unique_tiles = []
    map_entries = []
    
    pixels = list(img.getdata())
    
    for ty in range(height_tiles):
        for tx in range(width_tiles):
            # Extract 8x8 pixel block
            tile_px = []
            for py in range(8):
                for px in range(8):
                    idx = (ty*8 + py) * width + (tx*8 + px)
                    color_idx = pixels[idx]
                    # Ensure color_idx is within 0-15
                    tile_px.append(color_idx % 16)
                    
            # Convert to 4bpp tile bytes (32 bytes)
            tile_bytes = bytearray()
            for py in range(8):
                for px in range(0, 8, 2):
                    p1 = tile_px[py*8 + px]
                    p2 = tile_px[py*8 + px + 1]
                    val = (p2 << 4) | p1
                    tile_bytes.append(val)
                    
            # Check for unique
            try:
                t_idx = unique_tiles.index(tile_bytes)
            except ValueError:
                t_idx = len(unique_tiles)
                unique_tiles.append(tile_bytes)
                
            # map entry: tile_idx (10 bits) + flip_h (1 bit) + flip_v (1 bit) + pal_bank (4 bits)
            # We don't use flips or pal_bank > 0 for now.
            map_entry = t_idx & 0x3FF
            map_entries.append(map_entry)
            
    # Pack tiles
    tiles_data = bytearray()
    for tb in unique_tiles:
        tiles_data.extend(tb)
        
    # Pack map
    map_data = bytearray()
    for entry in map_entries:
        map_data.extend(struct.pack('<H', entry))
        
    print(f"Unique tiles: {len(unique_tiles)}")
    print(f"Map entries: {len(map_entries)}")
    
    # Original header structure:
    # 0x00: 01 00 00 80
    # 0x04: Offset 1 (Palette start)
    # 0x08: Offset 2 (Palette end / Tiles start?)
    # 0x0C: Offset 3 (Tiles start)
    # 0x10: Offset 4 (Map start)
    
    # Original offsets were: 20, 672, 692, 5780
    off1 = 20
    off2 = off1 + len(pal_data) # 20 + 652 = 672
    # The space between 672 and 692 was 20 bytes of zeros (Section 1). Let's keep it.
    sec1 = b'\x00' * 20
    off3 = off2 + len(sec1) # 692
    off4 = off3 + len(tiles_data)
    
    header = bytearray(b'\x01\x00\x00\x80')
    header.extend(struct.pack('<I', off1))
    header.extend(struct.pack('<I', off2))
    header.extend(struct.pack('<I', off3))
    header.extend(struct.pack('<I', off4))
    
    with open(output_bin_path, 'wb') as f:
        f.write(header)
        f.write(pal_data)
        f.write(sec1)
        f.write(tiles_data)
        f.write(map_data)
        
    print(f"Successfully created {output_bin_path}")

if __name__ == '__main__':
    inject_logo('nerv.png', 'data/cg_logo.bin.bak', 'data/cg_logo.bin')
