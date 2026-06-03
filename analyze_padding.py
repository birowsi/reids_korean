from check_lz77_len import check_lz77_size

data = open('data/cg_logo.bin_sec0.bin', 'rb').read()
lz1_len = check_lz77_size(data[16:])
print(f"Sec0 LZ1 length: {lz1_len}")

# Let's see if there's a padding byte between streams
offset = 16 + lz1_len
if data[offset] == 0:
    print("Zero byte between streams found!")
    offset += 1

lz2_len = check_lz77_size(data[offset:])
print(f"Sec0 LZ2 length: {lz2_len}")

total_consumed = offset + lz2_len
padding = data[total_consumed:]
print(f"Sec0 Padding length: {len(padding)}")
print(f"Is sec0 padding all zeros? {all(b == 0 for b in padding)}")

# Check Sec2
data2 = open('data/cg_logo.bin_sec2.bin', 'rb').read()
lz1_len2 = check_lz77_size(data2[16:])
print(f"\nSec2 LZ1 length: {lz1_len2}")
padding2 = data2[16+lz1_len2:]
print(f"Sec2 Padding length: {len(padding2)}")
print(f"Is sec2 padding all zeros? {all(b == 0 for b in padding2)}")
