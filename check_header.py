import sys

def parse_header(filepath):
    with open(filepath, 'rb') as f:
        data = f.read(16)
    print("Header bytes:", data.hex())

if __name__ == '__main__':
    parse_header("data/asuka.scd")
