"""
Mode Démonstration Automatique - Sans interaction
"""
import os
import struct
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def print_hex_dump(data: bytes, label: str, max_bytes: int = 64):
    """Affiche un dump hexadécimal des données"""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    print(f"Taille: {len(data)} bytes")
    
    hex_str = data[:max_bytes].hex()
    print(f"\nHexadécimal (premiers {min(max_bytes, len(data))} bytes):")
    for i in range(0, len(hex_str), 32):
        print(f"  {hex_str[i:i+32]}")
    
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[:max_bytes])
    print(f"\nASCII (premiers {min(max_bytes, len(data))} bytes):")
    for i in range(0, len(ascii_str), 64):
        print(f"  {ascii_str[i:i+64]}")
    
    if len(data) > max_bytes:
        print(f"\n  ... ({len(data) - max_bytes} bytes supplémentaires)")
    print(f"{'='*70}\n")


print("\n" + "█"*70)
print("█  DÉMONSTRATION AUTOMATIQUE - CHIFFREMENT")
print("█"*70 + "\n")

# 1. RSA Encryption
print("\n[1/3] CHIFFREMENT RSA DE LA CLÉ DE SESSION\n")

with open("server.crt", "rb") as f:
    cert = x509.load_pem_x509_certificate(f.read())

session_key = os.urandom(32)
print_hex_dump(session_key, "🔑 CLÉ DE SESSION (256 bits - EN CLAIR)", 32)

pub_key = cert.public_key()
encrypted_key = pub_key.encrypt(
    session_key,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None,
    ),
)
print_hex_dump(encrypted_key, "🔒 CLÉ DE SESSION CHIFFRÉE (RSA-4096)", 64)

print("✅ La clé de session est maintenant illisible !\n")

# 2. AES-GCM Encryption
print("\n[2/3] CHIFFREMENT AES-GCM DU FICHIER\n")

plaintext = b"MESSAGE SECRET ISEC 2026 - Ceci est confidentiel !"
print_hex_dump(plaintext, "📄 MESSAGE EN CLAIR", len(plaintext))

nonce = os.urandom(12)
print_hex_dump(nonce, "🎲 NONCE ALÉATOIRE (12 bytes)", 12)

aesgcm = AESGCM(session_key)
ciphertext = aesgcm.encrypt(nonce, plaintext, None)

encrypted_data = ciphertext[:-16]
auth_tag = ciphertext[-16:]

print_hex_dump(encrypted_data, "🔒 DONNÉES CHIFFRÉES (AES-256-GCM)", len(encrypted_data))
print_hex_dump(auth_tag, "🛡️  TAG D'AUTHENTIFICATION (16 bytes)", 16)

frame = nonce + ciphertext
print_hex_dump(frame, "📦 FRAME COMPLÈTE ENVOYÉE SUR LE RÉSEAU", len(frame))

print("✅ Le message est complètement illisible !\n")

# 3. File Comparison
print("\n[3/3] COMPARAISON FICHIER ORIGINAL vs CHIFFRÉ\n")

test_file = "demo_test.txt"
original_content = b"ISEC Project - Secure File Transfer\n" * 10

with open(test_file, "wb") as f:
    f.write(original_content)

print(f"📄 Fichier original créé : {test_file}")
print_hex_dump(original_content, "CONTENU ORIGINAL", 128)

session_key2 = os.urandom(32)
aesgcm2 = AESGCM(session_key2)
nonce2 = os.urandom(12)
encrypted_content = nonce2 + aesgcm2.encrypt(nonce2, original_content, None)

encrypted_file = "demo_test_encrypted.bin"
with open(encrypted_file, "wb") as f:
    f.write(encrypted_content)

print(f"🔒 Fichier chiffré créé : {encrypted_file}")
print_hex_dump(encrypted_content, "CONTENU CHIFFRÉ", 128)

print("\n" + "█"*70)
print("█  RÉSUMÉ")
print("█"*70)
print(f"""
✅ Fichiers créés pour la démonstration :
   - {test_file} ({len(original_content)} bytes) - LISIBLE
   - {encrypted_file} ({len(encrypted_content)} bytes) - ILLISIBLE

🎯 Pour votre présentation :
   1. Ouvrez {test_file} avec Notepad → Texte lisible
   2. Ouvrez {encrypted_file} avec Notepad → Caractères bizarres
   3. Montrez les hexdumps ci-dessus au professeur
   4. Lancez Wireshark pour capturer le trafic réseau

📝 Commande pour le mode verbose :
   python client.py --file test_demo.txt --verbose
""")

print("█"*70 + "\n")
