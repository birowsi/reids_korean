import os
import struct
import json
from PIL import Image, ImageDraw, ImageFont
import shutil

def inject_file(rom_data, original_file_path, new_file_path):
    with open(original_file_path, 'rb') as f:
        orig_data = f.read()
    with open(new_file_path, 'rb') as f:
        new_data = f.read()
        
    if len(orig_data) != len(new_data):
        print(f"Error: {original_file_path} size ({len(orig_data)}) != {new_file_path} size ({len(new_data)}). Cannot inject directly!")
        return rom_data, False
        
    offset = rom_data.find(orig_data)
    if offset == -1:
        print(f"Error: Could not find exact bytes of {original_file_path} in the ROM.")
        return rom_data, False
        
    print(f"Found {os.path.basename(original_file_path)} at offset 0x{offset:X}. Injecting...")
    rom_data[offset:offset+len(new_data)] = new_data
    return rom_data, True

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

def render_char(char, font, size):
    img = Image.new('1', (size, size), 0)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), char, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    draw.text((x, y), char, font=font, fill=1)
    return img

def pack_3bpp(img):
    img_rot = img.rotate(-90)
    bit_str = ''
    for y in range(12):
        for x in range(13):
            # If width is 13 and we only render 12, the last column is 0
            if x < 12 and img_rot.getpixel((x, y)):
                bit_str += '111'
            else:
                bit_str += '000'
    bit_str += '0000' # pad 156*3=468 bits to 472 bits
    packed = bytearray()
    for i in range(59):
        chunk = bit_str[i*8:(i+1)*8]
        packed.append(int(chunk, 2))
    return packed

def render_char(char, font, size):
    img = Image.new('1', (size, size), 0)
    draw = ImageDraw.Draw(img)
    bbox = draw.textbbox((0, 0), char, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = (size - w) // 2 - bbox[0]
    y = (size - h) // 2 - bbox[1]
    draw.text((x, y), char, font=font, fill=1)
    return img

def inject_font(rom_data):
    if not os.path.exists('korean_mapping.json'):
        print("korean_mapping.json not found!")
        return rom_data, False

    with open('korean_mapping.json', 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    font_12 = ImageFont.truetype('GalmuriMono7.ttf', 12)
    
    arm9_offset = struct.unpack('<I', rom_data[0x20:0x24])[0]
    # The real font NFTR is at 0x87e80 in arm9.bin
    # PLGC block is at 0x87eac
    # PLGC header is 16 bytes, so pixel data starts at 0x87ebc
    font_base_offset = arm9_offset + 0x87ebc
    
    print(f"Injecting {len(mapping)} 3BPP font characters into ROM at offset 0x{font_base_offset:X}...")
    for char, info in mapping.items():
        idx = info['font_index']
        img_12 = render_char(char, font_12, 12)
        packed_59 = pack_3bpp(img_12)
        pos = font_base_offset + idx * 59
        rom_data[pos:pos+59] = packed_59
        
    return rom_data, True

def main():
    original_rom = "2618 - Shinseiki Evangelion - Ayanami Ikusei Keikaku DS with Asuka Hokan Keikaku (Japan) [b].nds"
    output_rom = "korean_final.nds"
    
    print(f"Reading original ROM: {original_rom}...")
    with open(original_rom, 'rb') as f:
        rom_data = bytearray(f.read())
        
    # Inject text scripts
    files_to_inject = [
        ("pristine_data/aya.scd", "data/aya.scd"),
        ("pristine_data/asuka.scd", "data/asuka.scd"),
        ("pristine_data/title.scd", "data/title.scd"),
    ]
    
    all_success = True
    for orig, new in files_to_inject:
        rom_data, success = inject_file(rom_data, orig, new)
        if not success:
            all_success = False
            
    # Inject font
    if all_success:
        rom_data, success = inject_font(rom_data)
        if not success:
            all_success = False

    if all_success:
        print(f"Writing fully injected ROM to {output_rom}...")
        with open(output_rom, 'wb') as f:
            f.write(rom_data)
        print("Direct injection successful! The ROM is perfectly identical to the original except for text and font.")
    else:
        print("Direct injection failed.")

if __name__ == '__main__':
    main()
