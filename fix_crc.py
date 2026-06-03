import struct

def crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc

def fix_header_crc(rom_path):
    with open(rom_path, 'r+b') as f:
        rom = bytearray(f.read())
        
        # Recalculate ARM9 CRC
        arm9_offset = struct.unpack('<I', rom[0x20:0x24])[0]
        arm9_size = struct.unpack('<I', rom[0x2C:0x30])[0]
        
        print(f"ARM9 Offset: 0x{arm9_offset:X}, Size: 0x{arm9_size:X}")
        arm9_data = rom[arm9_offset:arm9_offset+arm9_size]
        new_arm9_crc = crc16(arm9_data)
        
        old_arm9_crc = struct.unpack('<H', rom[0x6C:0x6E])[0]
        print(f"Old ARM9 CRC: 0x{old_arm9_crc:04X}, New ARM9 CRC: 0x{new_arm9_crc:04X}")
        
        # Update ARM9 CRC in header
        rom[0x6C:0x6E] = struct.pack('<H', new_arm9_crc)
        
        # Recalculate Header CRC (covers offset 0x00 to 0x15D)
        header_data = rom[0x00:0x15E]
        new_header_crc = crc16(header_data)
        
        old_header_crc = struct.unpack('<H', rom[0x15E:0x160])[0]
        print(f"Old Header CRC: 0x{old_header_crc:04X}, New Header CRC: 0x{new_header_crc:04X}")
        
        rom[0x15E:0x160] = struct.pack('<H', new_header_crc)
        
        f.seek(0)
        f.write(rom)

import sys

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fix_header_crc(sys.argv[1])
    else:
        print("Usage: python fix_crc.py <rom.nds>")
