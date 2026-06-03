import struct

def check_map(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
        
    offsets = []
    for i in range(1, 5):
        offsets.append(struct.unpack('<I', data[i*4:(i+1)*4])[0])
        
    map_data = data[offsets[2]:offsets[3]]
    
    print(f"--- {filepath} Map Data ---")
    entries = []
    for i in range(0, len(map_data)-1, 2):
        val = struct.unpack('<H', map_data[i:i+2])[0]
        entries.append(val)
        
    print(f"Total entries: {len(entries)}")
    print("First 30:", [hex(x) for x in entries[:30]])
    
if __name__ == '__main__':
    check_map('data/cg_logo.bin')
