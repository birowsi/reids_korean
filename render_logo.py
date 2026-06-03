from PIL import Image
import struct

def render_logo():
    # Use grayscale palette to visualize the image structure
    colors = [(i*16, i*16, i*16) for i in range(16)]
    print(f"Using grayscale palette")
        
    # Load Tiles (7552 bytes = 236 tiles of 4bpp)
    # Each tile is 32 bytes (8x8 pixels)
    tiles_data = open('data/dump_s2_lz1.bin', 'rb').read()
    tiles = []
    for i in range(len(tiles_data) // 32):
        tile_bytes = tiles_data[i*32:(i+1)*32]
        tile = []
        for py in range(8):
            for px in range(0, 8, 2):
                b = tile_bytes[py*4 + px//2]
                tile.append(b & 0x0F)
                tile.append(b >> 4)
        tiles.append(tile)
        
    print(f"Loaded {len(tiles)} tiles")
        
    # Try rendering with s0_lz2 as Map (1536 bytes = 768 entries = 32x24 map)
    # 32x24 map is 256x192 pixels! Exact screen size!
    map_data = open('data/dump_s0_lz2.bin', 'rb').read()
    img = Image.new('RGB', (256, 192))
    pixels = img.load()
    
    entries = struct.unpack(f'<{len(map_data)//2}H', map_data)
    for i, entry in enumerate(entries):
        tile_idx = entry & 0x03FF
        flip_h = (entry >> 10) & 1
        flip_v = (entry >> 11) & 1
        pal_idx = (entry >> 12) & 0xF
        
        tx = (i % 32) * 8
        ty = (i // 32) * 8
        
        if tile_idx < len(tiles):
            tile = tiles[tile_idx]
            for py in range(8):
                for px in range(8):
                    src_px = px if not flip_h else 7 - px
                    src_py = py if not flip_v else 7 - py
                    color_idx = tile[src_py * 8 + src_px]
                    pixels[tx + px, ty + py] = colors[color_idx]
                    
    img.save('data/rendered_s0_map.png')
    
    # Try rendering with sec3 as Map
    try:
        map_data3 = open('data/dump_sec3.bin', 'rb').read()
        img3 = Image.new('RGB', (256, 192))
        pixels3 = img3.load()
        entries3 = struct.unpack(f'<{len(map_data3)//2}H', map_data3)
        for i, entry in enumerate(entries3):
            if i >= 32*24: break
            tile_idx = entry & 0x03FF
            tx = (i % 32) * 8
            ty = (i // 32) * 8
            if tile_idx < len(tiles):
                tile = tiles[tile_idx]
                for py in range(8):
                    for px in range(8):
                        color_idx = tile[py * 8 + px]
                        pixels3[tx + px, ty + py] = colors[color_idx]
        img3.save('data/rendered_sec3_map.png')
    except Exception as e:
        print(f"Failed sec3 map: {e}")

if __name__ == '__main__':
    render_logo()
