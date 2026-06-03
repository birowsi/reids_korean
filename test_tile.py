import struct

def test_tile():
    data = open('data/cg_logo.bin.bak2', 'rb').read()
    offsets = [struct.unpack('<I', data[i*4:(i+1)*4])[0] for i in range(1, 5)]
    
    sections = []
    sections.append(bytearray(data[offsets[0]:offsets[1]]))
    sections.append(bytearray(data[offsets[1]:offsets[2]]))
    sections.append(bytearray(data[offsets[2]:offsets[3]]))
    sections.append(bytearray(data[offsets[3]:]))
    
    # Palette Test (Red & Blue)
    sections[0][16] = 0x1F
    sections[0][17] = 0x00
    sections[0][18] = 0x00
    sections[0][19] = 0x7C
    
    # Tile Test (sec2)
    # The header seems to be 16 bytes.
    # Let's corrupt the first 32 bytes of the first tile (bytes 16 to 48) to 0x11 (Color index 1).
    for i in range(16, 16 + 128): # Corrupt first 4 tiles
        sections[2][i] = 0x11
    
    re_data = bytearray(data[:20])
    for sec in sections:
        re_data.extend(sec)
        
    open('data/cg_logo.bin', 'wb').write(re_data)
    print("Created cg_logo.bin with modified palette and corrupted tiles!")

if __name__ == '__main__':
    test_tile()
