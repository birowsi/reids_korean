import struct
import math

def align_rom(input_path, output_path, alignment=512):
    with open(input_path, 'rb') as f:
        rom = bytearray(f.read())
        
    fat_offset = struct.unpack('<I', rom[0x48:0x4C])[0]
    fat_size = struct.unpack('<I', rom[0x4C:0x50])[0]
    file_count = fat_size // 8
    
    # Get the start of the first file to know where data begins
    first_file_start = struct.unpack('<I', rom[fat_offset : fat_offset + 4])[0]
    
    # We will build the new ROM
    new_rom = bytearray(rom[:first_file_start])
    
    # We also need a new FAT
    new_fat = bytearray()
    
    current_offset = first_file_start
    
    for i in range(file_count):
        start, end = struct.unpack('<II', rom[fat_offset + i*8 : fat_offset + i*8 + 8])
        length = end - start
        
        # Calculate padding to align
        remainder = current_offset % alignment
        if remainder != 0:
            padding = alignment - remainder
            new_rom.extend(b'\x00' * padding)
            current_offset += padding
            
        # Optional: Align Mobiclip files to 4096 (they are usually large)
        if length > 1000000: # Movies are > 1MB
            remainder = current_offset % 4096
            if remainder != 0:
                padding = 4096 - remainder
                new_rom.extend(b'\x00' * padding)
                current_offset += padding
                
        # Write FAT entry
        new_start = current_offset
        new_end = current_offset + length
        new_fat.extend(struct.pack('<II', new_start, new_end))
        
        # Copy file data
        new_rom.extend(rom[start:end])
        current_offset += length
        
    # Overwrite FAT in the new ROM
    new_rom[fat_offset : fat_offset + fat_size] = new_fat
    
    # Update ROM size in the header
    rom_capacity = len(new_rom)
    # The device capacity in header is usually just the power of 2, but we update the total used size at 0x80
    new_rom[0x80:0x84] = struct.pack('<I', rom_capacity)
    
    # Fix header CRC
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
        
    header_data = new_rom[0x00:0x15E]
    new_header_crc = crc16(header_data)
    new_rom[0x15E:0x160] = struct.pack('<H', new_header_crc)
    
    with open(output_path, 'wb') as f:
        f.write(new_rom)
        
    print(f"Aligned ROM created: {output_path} (Size: {rom_capacity} bytes)")

import sys
if __name__ == '__main__':
    if len(sys.argv) > 2:
        align_rom(sys.argv[1], sys.argv[2])
    else:
        align_rom('korean_release_v1.nds', 'korean_aligned.nds')
