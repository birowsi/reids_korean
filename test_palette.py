import struct
import os

def test_palette():
    data = open('data/cg_logo.bin', 'rb').read()
    offsets = [struct.unpack('<I', data[i*4:(i+1)*4])[0] for i in range(1, 5)]
    
    sections = []
    sections.append(bytearray(data[offsets[0]:offsets[1]]))
    sections.append(bytearray(data[offsets[1]:offsets[2]]))
    sections.append(bytearray(data[offsets[2]:offsets[3]]))
    sections.append(bytearray(data[offsets[3]:]))
    
    # Modify sec0 (Palette)
    # The header seems to be 16 bytes. Let's change the color at offset 16 and 18.
    # 0xFFFF is white, 0x0000 is black, 0x001F is red
    sections[0][16] = 0x1F
    sections[0][17] = 0x00 # Color 0 to Red
    sections[0][18] = 0x00
    sections[0][19] = 0x7C # Color 1 to Blue
    
    re_data = bytearray(data[:20])
    for sec in sections:
        re_data.extend(sec)
        
    open('data/cg_logo.bin', 'wb').write(re_data)
    print("Created cg_logo.bin with modified palette!")

if __name__ == '__main__':
    # Make a backup first
    import shutil
    if not os.path.exists('data/cg_logo.bin.bak2'):
        shutil.copy('data/cg_logo.bin', 'data/cg_logo.bin.bak2')
    test_palette()
