import json
from base64 import b64decode, b64encode
from pathlib import Path

from cryptography.hazmat.primitives import serialization, asymmetric, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class Encryption:
    def __init__(self):
        self.private_key = Path('cbc_cert.pem').read_text()

    def decrypt_data(self, encrypted_flow_data_b64, encrypted_aes_key_b64,
                     initial_vector_b64):
        encrypted_aes_key = b64decode(encrypted_aes_key_b64)
        private_key = serialization.load_pem_private_key(
            self.private_key.encode("utf-8"),
            password=None,
        )
        aes_key = private_key.decrypt(
            encrypted_aes_key,
            asymmetric.padding.OAEP(
                mgf=asymmetric.padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        aes_key_b64 = b64encode(aes_key)
        flow_data = b64decode(encrypted_flow_data_b64)
        key = b64decode(aes_key_b64)
        iv = b64decode(initial_vector_b64)

        encrypted_flow_data_body = flow_data[:-16]
        encrypted_flow_data_tag = flow_data[-16:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, encrypted_flow_data_tag))
        decryptor = cipher.decryptor()
        decrypted_data = decryptor.update(
            encrypted_flow_data_body) + decryptor.finalize()
        return decrypted_data.decode("utf-8"), key, iv

    @staticmethod
    def encrypt_data(data, key, iv):
        flipped_bytes = []
        for byte in iv:
            flipped_byte = byte ^ 0xFF
            flipped_bytes.append(flipped_byte)

        response = json.dumps(data)
        cipher_respond = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher_respond.encryptor()
        encrypted = (
                encryptor.update(response.encode("utf-8")) +\
                encryptor.finalize() +\
                encryptor.tag
        )
        return b64encode(encrypted).decode("utf-8")

