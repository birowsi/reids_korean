import json
import struct
import os
from PIL import Image, ImageDraw, ImageFont

def pack_3bpp(img):
    img_rot = img.rotate(-90, expand=True)
    bit_str = ''
    for y in range(12):
        for x in range(13):
            px = img_rot.getpixel((x, y))
            val = px // 36
            bit_str += format(val, '03b')
            
    # Pad to 472 bits (59 bytes * 8)
    bit_str += '0' * (472 - len(bit_str))
    
    packed = bytearray()
    for i in range(59):
        chunk = bit_str[i*8:(i+1)*8]
        packed.append(int(chunk, 2))
    return packed

def render_char(char, font, size):
    img = Image.new('L', (12, 13), 0)
    draw = ImageDraw.Draw(img)
    draw.text((1, 1), char, font=font, fill=255)
    return img

def main():
    if not os.path.exists('nftr_korean_mapping.json'):
        return

    with open('nftr_korean_mapping.json', 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    with open('arm9.bin', 'rb') as f:
        arm9 = bytearray(f.read())

    # Switch to GalmuriMono11.ttf with anti-aliasing to provide a naturally smooth and slightly thicker stroke without being fully bold
    font_11 = ImageFont.truetype('GalmuriMono11.ttf', 11)
    cwdh_base = 0xf3ff4
    width_array = cwdh_base + 16
    font_base_offset = 0x87ebc

    print(f'Injecting {len(mapping)} 3BPP font characters into arm9.bin...')
    for char, info in mapping.items():
        idx = info['glyph']
        img_11 = render_char(char, font_11, 11)
        packed_59 = pack_3bpp(img_11)
        pos = font_base_offset + idx * 59
        arm9[pos:pos+59] = packed_59
        
        # Patch the CWDH width table to 12px width for Korean characters
        w_pos = width_array + idx * 3
        arm9[w_pos:w_pos+3] = struct.pack('<bbb', 0, 12, 12)

    with open('arm9.bin', 'wb') as f:
        f.write(arm9)

if __name__ == '__main__':
    main()
