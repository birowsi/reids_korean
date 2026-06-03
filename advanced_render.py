import struct
from PIL import Image

def analyze_and_extract():
    with open('data/MobiclipLogo.bin', 'rb') as f:
        data = f.read()

    # Section 0: Palette
    # Section 2: Tiles
    # Section 3: Map?
    
    pal_data = data[20:672]
    # NDS Palette is usually 15-bit BGR. 
    colors = []
    # Let's search for where the palette actually starts.
    # A palette might start with some header. Let's just try to parse the whole 652 bytes as colors and see if any make sense.
    for i in range(0, len(pal_data)-1, 2):
        c = struct.unpack('<H', pal_data[i:i+2])[0]
        r = (c & 0x1F) * 8
        g = ((c >> 5) & 0x1F) * 8
        b = ((c >> 10) & 0x1F) * 8
        colors.append((r, g, b))

    # Output a palette image to see if colors make sense
    pal_img = Image.new('RGB', (16, 32))
    for i, col in enumerate(colors[:16*32]):
        if i < 16*32:
            pal_img.putpixel((i%16, i//16), col)
    pal_img.save('palette_test.png')

    # Section 2: Tiles
    # Offset 692, length 5088
    # 5088 / 32 = 159 tiles (4bpp)
    # 5088 / 64 = 79.5 tiles (8bpp) - so probably 4bpp!
    tiles_data = data[692:5780]
    tiles = []
    for i in range(0, len(tiles_data), 32):
        tile = tiles_data[i:i+32]
        if len(tile) == 32:
            tiles.append(tile)

    # Section 3: Map
    # Offset 5780, length 692
    map_data = data[5780:6472]
    map_entries = []
    for i in range(0, len(map_data)-1, 2):
        entry = struct.unpack('<H', map_data[i:i+2])[0]
        tile_idx = entry & 0x3FF
        flip_h = (entry >> 10) & 1
        flip_v = (entry >> 11) & 1
        pal_bank = (entry >> 12) & 0xF
        map_entries.append((tile_idx, flip_h, flip_v, pal_bank))

    print(f"Parsed {len(tiles)} tiles and {len(map_entries)} map entries.")
    print("First 10 map entries:", map_entries[:10])

    # Try to render Map
    # 346 map entries. Maybe 32x10 ?
    # Let's just render it linearly to see if there's any shape.
    img = Image.new('RGB', (32*8, 11*8))
    
    # Palette offset might be 16 bytes? Let's use colors[8:264] as 256 colors
    # Or just use the first 256 colors from some offset.
    pal = colors[8:] # guess
    
    for i, (t_idx, fh, fv, pb) in enumerate(map_entries):
        if t_idx < len(tiles):
            tile = tiles[t_idx]
            x_base = (i % 32) * 8
            y_base = (i // 32) * 8
            
            for py in range(8):
                for px in range(4):
                    b = tile[py*4 + px]
                    p1 = b & 0x0F
                    p2 = (b >> 4) & 0x0F
                    
                    real_py1 = 7 - py if fv else py
                    real_px1 = 7 - (px*2) if fh else px*2
                    
                    real_py2 = 7 - py if fv else py
                    real_px2 = 7 - (px*2+1) if fh else px*2+1
                    
                    if fh:
                        # swap pixels if flipped horizontally
                        p1, p2 = p2, p1

                    # Add palette bank offset (16 colors per bank)
                    c1 = pal[pb*16 + p1] if pb*16+p1 < len(pal) else (0,0,0)
                    c2 = pal[pb*16 + p2] if pb*16+p2 < len(pal) else (0,0,0)
                    
                    if y_base + real_py1 < img.height and x_base + real_px1 < img.width:
                        img.putpixel((x_base + real_px1, y_base + real_py1), c1)
                    if y_base + real_py2 < img.height and x_base + real_px2 < img.width:
                        img.putpixel((x_base + real_px2, y_base + real_py2), c2)

    img.save('map_render.png')
    print("Rendered map_render.png")

if __name__ == '__main__':
    analyze_and_extract()
