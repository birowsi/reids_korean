import sys

def render_4bpp(data, width):
    # data: bytes
    # width: pixels (must be even, as 1 byte = 2 pixels)
    if width % 2 != 0:
        return
        
    stride = width // 2
    height = len(data) // stride
    
    chars = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@', '&', '8', 'B', 'M', 'W', 'Q']
    
    out = []
    out.append(f"--- Width: {width} ---")
    
    # 4bpp in NDS is usually tiled (8x8 blocks). 
    # If it's linear (rare for NDS, but possible for some logos):
    for y in range(min(height, 40)): # limit to 40 lines
        line = ""
        for x in range(stride):
            idx = y * stride + x
            if idx < len(data):
                b = data[idx]
                p1 = b & 0x0F
                p2 = (b >> 4) & 0x0F
                line += chars[p1] + chars[p2]
        out.append(line)
        
    return "\n".join(out)

def render_4bpp_tiled(data, width_tiles):
    # NDS uses 8x8 tiles. 
    # 1 tile = 8x8 pixels = 64 pixels = 32 bytes.
    tiles = []
    for i in range(0, len(data), 32):
        tiles.append(data[i:i+32])
        
    if not tiles: return ""
    
    chars = [' ', '.', ':', '-', '=', '+', '*', '#', '%', '@', '&', '8', 'B', 'M', 'W', 'Q']
    
    height_tiles = len(tiles) // width_tiles
    if height_tiles == 0: return ""
    
    out = []
    out.append(f"--- Tiled Width: {width_tiles * 8} pixels ({width_tiles} tiles) ---")
    
    for ty in range(min(height_tiles, 10)): # limit to 10 tile rows = 80 pixels
        for py in range(8):
            line = ""
            for tx in range(width_tiles):
                tile_idx = ty * width_tiles + tx
                if tile_idx < len(tiles):
                    tile_data = tiles[tile_idx]
                    if len(tile_data) == 32:
                        for px in range(4): # 4 bytes = 8 pixels
                            b = tile_data[py * 4 + px]
                            p1 = b & 0x0F
                            p2 = (b >> 4) & 0x0F
                            line += chars[p1] + chars[p2]
                    else:
                        line += " " * 8
                else:
                    line += " " * 8
            out.append(line)
            
    return "\n".join(out)

if __name__ == '__main__':
    with open('data/MobiclipLogo.bin_sec2.bin', 'rb') as f:
        data = f.read()
        
    # skip some header bytes if it's not pure pixel data?
    # Section 2 starts with 03 00 00 00 a6 04 00 00 ... maybe 16 byte header?
    data = data[16:]
    
    with open('mobiclip_render.txt', 'w') as f:
        # Try some widths for tiled
        for w in [8, 16, 32, 64, 128, 256]:
            f.write(render_4bpp_tiled(data, w // 8))
            f.write("\n\n")
