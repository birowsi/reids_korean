import os

def inject_file(rom_data, original_file_path, new_file_path):
    with open(original_file_path, 'rb') as f:
        orig_data = f.read()
    with open(new_file_path, 'rb') as f:
        new_data = f.read()
        
    if len(orig_data) != len(new_data):
        print(f"Error: sizes differ.")
        return rom_data, False
        
    offset = rom_data.find(orig_data)
    if offset == -1:
        print(f"Error: Could not find exact bytes of {original_file_path}")
        return rom_data, False
        
    print(f"Injecting {os.path.basename(original_file_path)} at offset 0x{offset:X}...")
    rom_data[offset:offset+len(new_data)] = new_data
    return rom_data, True

def main():
    original_rom = "2618 - Shinseiki Evangelion - Ayanami Ikusei Keikaku DS with Asuka Hokan Keikaku (Japan) [b].nds"
    output_rom = "test_boot.nds"
    
    with open(original_rom, 'rb') as f:
        rom_data = bytearray(f.read())
        
    files_to_inject = [
        ("pristine_data/aya.scd", "data/aya.scd"),
        ("pristine_data/asuka.scd", "data/asuka.scd"),
        ("pristine_data/title.scd", "data/title.scd"),
    ]
    
    for orig, new in files_to_inject:
        rom_data, success = inject_file(rom_data, orig, new)
        
    with open(output_rom, 'wb') as f:
        f.write(rom_data)
    print("Done")

if __name__ == '__main__':
    main()
