def test_palette_direct():
    with open('data/cg_logo.bin.bak2', 'rb') as f:
        data = bytearray(f.read())
        
    # Offset 59, 60 is the first color in sec0 stream 2
    # 0x01f0 -> Red
    # Change it to pure Green: 0x03e0
    data[59] = 0xe0
    data[60] = 0x03
    
    # Change second color (offset 61, 62) to pure Blue: 0x7c00
    data[61] = 0x00
    data[62] = 0x7c
    
    with open('data/cg_logo.bin', 'wb') as f:
        f.write(data)
        
    print("Modified palette directly without compression!")

if __name__ == '__main__':
    test_palette_direct()
