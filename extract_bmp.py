import struct
import os

def create_bmp(filename, width, height, pixels, palette_rgb, bpp):
    # pixels: list of palette indices (0-255)
    # palette_rgb: list of (R, G, B) tuples
    
    # Pad width to multiple of 4 bytes
    row_bytes = (width * bpp + 7) // 8
    padding = (4 - (row_bytes % 4)) % 4
    
    file_size = 54 + (len(palette_rgb) * 4) + (row_bytes + padding) * height
    
    with open(filename, 'wb') as f:
        # BMP Header
        f.write(b'BM')
        f.write(struct.pack('<I', file_size))
        f.write(b'\x00\x00\x00\x00')
        f.write(struct.pack('<I', 54 + len(palette_rgb) * 4))
        
        # DIB Header
        f.write(struct.pack('<I', 40))
        f.write(struct.pack('<I', width))
        f.write(struct.pack('<i', -height)) # top-down
        f.write(struct.pack('<H', 1))
        f.write(struct.pack('<H', 8)) # Always write as 8bpp BMP for simplicity
        f.write(struct.pack('<I', 0))
        f.write(struct.pack('<I', (width + padding) * height))
        f.write(struct.pack('<I', 2835))
        f.write(struct.pack('<I', 2835))
        f.write(struct.pack('<I', len(palette_rgb)))
        f.write(struct.pack('<I', 0))
        
        # Palette
        for r, g, b in palette_rgb:
            f.write(struct.pack('BBBB', b, g, r, 0))
            
        # Pixel data
        for y in range(height):
            row_data = bytearray()
            for x in range(width):
                idx = y * width + x
                if idx < len(pixels):
                    row_data.append(pixels[idx])
                else:
                    row_data.append(0)
            row_data.extend(b'\x00' * padding)
            f.write(row_data)

def decode_gba_palette(pal_data):
    colors = []
    for i in range(0, len(pal_data), 2):
        if i+1 >= len(pal_data): break
        c = struct.unpack('<H', pal_data[i:i+2])[0]
        r = (c & 0x1F) * 8
        g = ((c >> 5) & 0x1F) * 8
        b = ((c >> 10) & 0x1F) * 8
        colors.append((r, g, b))
    return colors

def export_logo(bin_path, out_prefix):
    with open(bin_path, 'rb') as f:
        data = f.read()
        
    # offsets: 20, 672, 692, 5780 (Mobiclip)
    # let's extract palette from offset 36 (20 + 16)
    pal_data = data[36:672]
    colors = decode_gba_palette(pal_data)
    # Ensure 256 colors
    while len(colors) < 256:
        colors.append((0,0,0))
        
    # Extract image from offset 708 (692 + 16)
    img_data = data[708:5780]
    
    # Try 4bpp tiled decoding
    # 1 tile = 32 bytes (8x8 pixels)
    tiles_4bpp = []
    for i in range(0, len(img_data), 32):
        tile = img_data[i:i+32]
        if len(tile) == 32:
            tile_pixels = []
            for by in range(8):
                for bx in range(4):
                    b = tile[by*4 + bx]
                    tile_pixels.append(b & 0x0F)
                    tile_pixels.append((b >> 4) & 0x0F)
            tiles_4bpp.append(tile_pixels)
            
    # Assemble to image. Let's try widths: 128, 256
    for width in [128, 256]:
        width_tiles = width // 8
        height_tiles = len(tiles_4bpp) // width_tiles
        if height_tiles == 0: continue
        
        height = height_tiles * 8
        pixels = [0] * (width * height)
        
        for ty in range(height_tiles):
            for tx in range(width_tiles):
                tile_idx = ty * width_tiles + tx
                if tile_idx < len(tiles_4bpp):
                    t_px = tiles_4bpp[tile_idx]
                    for py in range(8):
                        for px in range(8):
                            pixels[(ty*8 + py) * width + (tx*8 + px)] = t_px[py*8 + px]
                            
        create_bmp(f"{out_prefix}_4bpp_{width}.bmp", width, height, pixels, colors, 8)
        
if __name__ == '__main__':
    export_logo('data/MobiclipLogo.bin', 'mobiclip')
    export_logo('data/cg_logo.bin', 'cglogo')
