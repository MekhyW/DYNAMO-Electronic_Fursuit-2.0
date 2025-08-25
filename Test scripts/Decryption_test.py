import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv
import hashlib

def encrypt_system_prompt(input_file="Main software/models/system_prompt.txt", output_file="Main software/models/system_prompt_encrypted.txt"):
    """
    Encrypt a system prompt file using AES encryption with OpenSSL-compatible format.
    Uses the same encryption method that can be decrypted by decrypt_system_prompt().
    """
    load_dotenv(".env")
    encryption_key = os.getenv("prompt_encryption_key")
    if not encryption_key:
        raise ValueError("prompt_encryption_key not found in environment variables")
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' not found")
    with open(input_file, "r", encoding='utf-8') as f:
        plaintext = f.read()
    salt = os.urandom(8)
    password = encryption_key.encode('utf-8')
    key_iv = hashlib.pbkdf2_hmac('sha256', password, salt, 10000, 48)  # 32 + 16
    key = key_iv[:32]
    iv = key_iv[32:48]
    def pkcs7_pad(data, block_size=16):
        padding_length = block_size - (len(data) % block_size)
        padding = bytes([padding_length] * padding_length)
        return data + padding
    plaintext_bytes = plaintext.encode('utf-8')
    padded_plaintext = pkcs7_pad(plaintext_bytes)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    encrypted_content = encryptor.update(padded_plaintext) + encryptor.finalize()
    salted_encrypted = b"Salted__" + salt + encrypted_content # Create OpenSSL-compatible format: "Salted__" + salt + encrypted_content
    encrypted_b64 = base64.b64encode(salted_encrypted).decode('utf-8') # Base64 encode the result
    with open(output_file, "w", encoding='utf-8') as f:
        f.write(encrypted_b64)
    print(f"Successfully encrypted '{input_file}' to '{output_file}'")
    return encrypted_b64

def decrypt_system_prompt():
    load_dotenv(".env")
    encryption_key = os.getenv("prompt_encryption_key")
    if not encryption_key:
        raise ValueError("prompt_encryption_key not found in environment variables")
    with open("Main software/models/system_prompt_encrypted.txt", "r", encoding='utf-8') as f:
        encrypted_data = f.read().strip()
    try:
        password = encryption_key.encode('utf-8')
        encrypted_bytes = base64.b64decode(encrypted_data)
        if encrypted_bytes.startswith(b"Salted__"):
            salt = encrypted_bytes[8:16]
            encrypted_content = encrypted_bytes[16:]
            import hashlib
            key_iv = hashlib.pbkdf2_hmac('sha256', password, salt, 10000, 48)  # 32 + 16
            key = key_iv[:32]
            iv = key_iv[32:48]
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(encrypted_content) + decryptor.finalize()
            padding_length = decrypted_padded[-1]
            if padding_length <= 16:
                decrypted_text = decrypted_padded[:-padding_length].decode('utf-8')
                return decrypted_text
        raise ValueError("All decryption approaches failed")
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None

def main():
    try:
        print(encrypt_system_prompt())
        print("\nEncryption completed successfully!\n")
        print(decrypt_system_prompt())
        print("\nDecryption completed successfully!\n")
    except Exception as e:
        print(f"Encryption failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())