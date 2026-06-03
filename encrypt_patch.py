import hashlib
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
        
    print(f"Successfully encrypted {input_file} to {output_file} using PIN: {pin}")

if __name__ == '__main__':
    encrypt_patch("0314", "korean_patch_v2.xdelta", "korean_patch_v2.dat")
