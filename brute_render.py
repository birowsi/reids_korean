import struct
import os
from PIL import Image

def decode_gba_palette(pal_data):
    colors = []
    for i in range(0, len(pal_data)-1, 2):
        c = struct.unpack('<H', pal_data[i:i+2])[0]
        r = (c & 0x1F) * 8
        g = ((c >> 5) & 0x1F) * 8
        b = ((c >> 10) & 0x1F) * 8
        colors.append((r, g, b))
    return colors

def brute_force_render(bin_path, out_prefix):
    with open(bin_path, 'rb') as f:
        data = f.read()

    # Offsets are stored in header
    offsets = []
    for i in range(1, 5):
        offsets.append(struct.unpack('<I', data[i*4:(i+1)*4])[0])
        
    pal_data = data[offsets[0]:offsets[1]]
    colors = decode_gba_palette(pal_data)
    while len(colors) < 256:
        colors.append((0,0,0))
        
    tiles_data = data[offsets[2]:offsets[3]]
    tiles = []
    for i in range(0, len(tiles_data), 32):
        tile = tiles_data[i:i+32]
        if len(tile) == 32:
            tiles.append(tile)

    map_data = data[offsets[3]:]
    map_entries = []
    for i in range(0, len(map_data)-1, 2):
        entry = struct.unpack('<H', map_data[i:i+2])[0]
        tile_idx = entry & 0x3FF
        fh = (entry >> 10) & 1
        fv = (entry >> 11) & 1
        pb = (entry >> 12) & 0xF
        map_entries.append((tile_idx, fh, fv, pb))

    # NDS screens are 256x192 (32x24 tiles). Try different map widths.
    for map_w in [32]: # mostly 32 for screen
        map_h = len(map_entries) // map_w
        if map_h == 0: continue
        
        img = Image.new('RGB', (map_w * 8, map_h * 8))
        for i, (t_idx, fh, fv, pb) in enumerate(map_entries):
            tx = i % map_w
            ty = i // map_w
            
            # Mobiclip is special, maybe tile_idx is offset by some value?
            # if tile_idx is out of bounds, maybe it uses a different tile base.
            if t_idx < len(tiles):
                tile = tiles[t_idx]
                for py in range(8):
                    for px in range(4):
                        b = tile[py*4 + px]
                        p1 = b & 0x0F
                        p2 = (b >> 4) & 0x0F
                        
                        r_py1 = 7 - py if fv else py
                        r_px1 = 7 - (px*2) if fh else px*2
                        
                        r_py2 = 7 - py if fv else py
                        r_px2 = 7 - (px*2+1) if fh else px*2+1
                        
                        if fh:
                            p1, p2 = p2, p1
                            
                        c1 = colors[pb*16 + p1]
                        c2 = colors[pb*16 + p2]
                        
                        img.putpixel((tx*8 + r_px1, ty*8 + r_py1), c1)
                        img.putpixel((tx*8 + r_px2, ty*8 + r_py2), c2)
        
        out_name = f"{out_prefix}_map_{map_w}.png"
        img.save(out_name)
        print(f"Saved {out_name}")

if __name__ == '__main__':
    brute_force_render('data/cg_logo.bin', 'cglogo')
    brute_force_render('data/MobiclipLogo.bin', 'mobiclip')
