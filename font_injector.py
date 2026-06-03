import json
import struct
import os
from PIL import Image, ImageDraw, ImageFont

def pack_16x16(img):
    img_rot = img.rotate(-90)
    packed = bytearray()
    for y in range(16):
        b1 = 0
        for x in range(8):
            if img_rot.getpixel((x, y)): b1 |= (1 << (7 - x))
        b2 = 0
        for x in range(8, 16):
            if img_rot.getpixel((x, y)): b2 |= (1 << (15 - x))
        packed.extend([b1, b2])
    return packed

def pack_12x12(img):
    img_rot = img.rotate(-90)
    bits = ''
    for y in range(12):
        for x in range(12):
            bits += '1' if img_rot.getpixel((x, y)) else '0'
    
    packed = bytearray()
    for i in range(18):
        chunk = bits[i*8:(i+1)*8]
        packed.append(int(chunk, 2))
    return packed

def render_char(char, font, size):
    img = Image.new('1', (size, size), 0)
    draw = ImageDraw.Draw(img)
    # Get bounding box to center the character
    bbox = draw.textbbox((0, 0), char, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    
    draw.text((x, y), char, font=font, fill=1)
    return img

def main():
    if not os.path.exists('korean_mapping.json'):
        print("korean_mapping.json not found!")
        return

    with open('korean_mapping.json', 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    with open('arm9.bin', 'rb') as f:
        arm9 = bytearray(f.read())

    # Sizes we tested to look good with GalmuriMono7.ttf
    font_16 = ImageFont.truetype('GalmuriMono7.ttf', 14)
    font_12 = ImageFont.truetype('GalmuriMono7.ttf', 12)

    offset_16x16 = 0x1a3bc
    offset_12x12 = 0x6fa18

    print(f"Injecting {len(mapping)} characters...")
    count = 0
    for char, info in mapping.items():
        idx = info['font_index']
        
        # 16x16
        img_16 = render_char(char, font_16, 16)
        packed_16 = pack_16x16(img_16)
        pos_16 = offset_16x16 + idx * 32
        arm9[pos_16:pos_16+32] = packed_16
        
        # 12x12 font offset was wrong, disabling for now.
        # img_12 = render_char(char, font_12, 12)
        # packed_12 = pack_12x12(img_12)
        # pos_12 = offset_12x12 + idx * 18
        # arm9[pos_12:pos_12+18] = packed_12
        
        count += 1
        if count % 500 == 0:
            print(f"Injected {count} characters...")

    with open('arm9.bin', 'wb') as f:
        f.write(arm9)

    print("Done injecting Korean fonts to arm9.bin!")

if __name__ == '__main__':
    main()
