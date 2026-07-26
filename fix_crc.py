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

        # 0x6C is the secure-area CRC field, not an ARM9 checksum. Preserve it.
        # Recalculate the Nintendo logo and header checksums only.
        old_logo_crc = struct.unpack('<H', rom[0x15C:0x15E])[0]
        new_logo_crc = crc16(rom[0xC0:0x15C])
        print(f"Old Logo CRC: 0x{old_logo_crc:04X}, New Logo CRC: 0x{new_logo_crc:04X}")
        rom[0x15C:0x15E] = struct.pack('<H', new_logo_crc)

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
