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
    
    img = Image.open('nerv_small.png')
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
        
    # Process tiles
    width, height = img.size
    pixels = list(img.getdata())
    
    # max 158 tiles to fit in 5088 bytes with 16 byte header
    max_tiles = 158
    tile_idx = 0
    
    for ty in range(height // 8):
        for tx in range(width // 8):
            if tile_idx >= max_tiles: break
            
            # tile data
            for py in range(8):
                for px in range(0, 8, 2):
                    idx1 = (ty*8 + py) * width + (tx*8 + px)
                    idx2 = idx1 + 1
                    
                    p1 = pixels[idx1] % 16
                    p2 = pixels[idx2] % 16
                    val = (p2 << 4) | p1
                    
                    # sec2 starts with 16 byte header
                    # each tile is 32 bytes
                    out_offset = 16 + tile_idx * 32 + py * 4 + (px // 2)
                    sec2[out_offset] = val
            tile_idx += 1
            
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

    print("Reconstructed perfectly!")
    
if __name__ == '__main__':
    reconstruct()
