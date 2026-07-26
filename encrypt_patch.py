import hashlib
import argparse
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

def encrypt_patch(pin, input_file, output_file):
    # Derive a 256-bit key from the PIN using SHA-256
    key = hashlib.sha256(pin.encode('utf-8')).digest()
    
    # Generate a random 16-byte IV
    iv = os.urandom(16)
    
    # Read the input file
    with open(input_file, 'rb') as f:
        data = f.read()
        
    # PKCS7 padding
    pad_len = 16 - (len(data) % 16)
    data += bytes([pad_len] * pad_len)
    
    # Encrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(data) + encryptor.finalize()
    
    # Write IV + Ciphertext to the output file
    with open(output_file, 'wb') as f:
        f.write(iv + ciphertext)
        
    print(f"Successfully encrypted {input_file} to {output_file}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Encrypt the release xdelta patch.")
    parser.add_argument("--pin", default="0314")
    parser.add_argument("--input", default="korean_patch_v6.xdelta")
    parser.add_argument("--output", default="korean_patch_v6.dat")
    args = parser.parse_args()
    encrypt_patch(args.pin, args.input, args.output)
