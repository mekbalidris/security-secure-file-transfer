"""
Mode Démonstration - Visualisation du Chiffrement
Ce script permet de voir les données avant et après chiffrement
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
    
    # Affiche en hexadécimal
    hex_str = data[:max_bytes].hex()
    print(f"\nHexadécimal (premiers {min(max_bytes, len(data))} bytes):")
    for i in range(0, len(hex_str), 32):
        print(f"  {hex_str[i:i+32]}")
    
    # Affiche en ASCII (caractères imprimables seulement)
    print(f"\nASCII (premiers {min(max_bytes, len(data))} bytes):")
    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[:max_bytes])
    for i in range(0, len(ascii_str), 64):
        print(f"  {ascii_str[i:i+64]}")
    
    if len(data) > max_bytes:
        print(f"\n  ... ({len(data) - max_bytes} bytes supplémentaires)")
    print(f"{'='*70}\n")


def demo_rsa_encryption():
    """Démontre le chiffrement RSA de la clé de session"""
    print("\n" + "█"*70)
    print("█  DÉMONSTRATION 1 : CHIFFREMENT RSA DE LA CLÉ DE SESSION")
    print("█"*70)
    
    # Charge le certificat
    with open("server.crt", "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read())
    
    # Génère une clé de session
    session_key = os.urandom(32)
    print_hex_dump(session_key, "🔑 CLÉ DE SESSION (256 bits - EN CLAIR)", 32)
    
    # Chiffre avec RSA
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
    
    print("✅ Observation : La clé de session est maintenant illisible !")
    print("   → Seul le serveur avec la clé privée peut la déchiffrer\n")
    
    return session_key, encrypted_key


def demo_aes_encryption(session_key: bytes):
    """Démontre le chiffrement AES-GCM d'un message"""
    print("\n" + "█"*70)
    print("█  DÉMONSTRATION 2 : CHIFFREMENT AES-GCM DU FICHIER")
    print("█"*70)
    
    # Message en clair
    plaintext = b"Ceci est un message secret tres confidentiel !"
    print_hex_dump(plaintext, "📄 MESSAGE EN CLAIR", len(plaintext))
    
    # Génère un nonce
    nonce = os.urandom(12)
    print_hex_dump(nonce, "🎲 NONCE ALÉATOIRE (12 bytes)", 12)
    
    # Chiffre avec AES-GCM
    aesgcm = AESGCM(session_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    
    # Le ciphertext contient : données chiffrées + tag (16 bytes)
    encrypted_data = ciphertext[:-16]
    auth_tag = ciphertext[-16:]
    
    print_hex_dump(encrypted_data, "🔒 DONNÉES CHIFFRÉES (AES-256-GCM)", len(encrypted_data))
    print_hex_dump(auth_tag, "🛡️  TAG D'AUTHENTIFICATION (16 bytes)", 16)
    
    # Frame complète envoyée sur le réseau
    frame = nonce + ciphertext
    print_hex_dump(frame, "📦 FRAME COMPLÈTE ENVOYÉE SUR LE RÉSEAU", len(frame))
    
    print("✅ Observation : Le message est complètement illisible !")
    print("   → Même si quelqu'un intercepte le réseau, il ne voit que du bruit")
    print("   → Le tag garantit que personne n'a modifié les données\n")
    
    return plaintext, frame


def demo_certificate():
    """Affiche les informations du certificat"""
    print("\n" + "█"*70)
    print("█  DÉMONSTRATION 3 : CERTIFICAT NUMÉRIQUE X.509")
    print("█"*70)
    
    with open("server.crt", "rb") as f:
        cert_pem = f.read()
        cert = x509.load_pem_x509_certificate(cert_pem)
    
    print("\n📜 CERTIFICAT DU SERVEUR :")
    print(f"   Subject: {cert.subject.rfc4514_string()}")
    print(f"   Issuer: {cert.issuer.rfc4514_string()}")
    print(f"   Valide du: {cert.not_valid_before_utc}")
    print(f"   Valide jusqu'au: {cert.not_valid_after_utc}")
    print(f"   Numéro de série: {cert.serial_number}")
    
    # Affiche la clé publique
    pub_key_pem = cert.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    print("\n🔑 CLÉ PUBLIQUE RSA-4096 (extrait) :")
    print(pub_key_pem.decode()[:300] + "...")
    
    print("\n✅ Observation : Le certificat contient la clé publique du serveur")
    print("   → Le client vérifie ce certificat avant d'envoyer des données\n")


def demo_comparison():
    """Compare un fichier avant et après chiffrement"""
    print("\n" + "█"*70)
    print("█  DÉMONSTRATION 4 : COMPARAISON FICHIER ORIGINAL vs CHIFFRÉ")
    print("█"*70)
    
    # Crée un fichier de test
    test_file = "demo_test.txt"
    original_content = b"ISEC Project - Secure File Transfer\n" * 10
    
    with open(test_file, "wb") as f:
        f.write(original_content)
    
    print(f"\n📄 Fichier original créé : {test_file}")
    print_hex_dump(original_content, "CONTENU ORIGINAL", 128)
    
    # Chiffre le contenu
    session_key = os.urandom(32)
    aesgcm = AESGCM(session_key)
    nonce = os.urandom(12)
    encrypted_content = nonce + aesgcm.encrypt(nonce, original_content, None)
    
    # Sauvegarde la version chiffrée
    encrypted_file = "demo_test_encrypted.bin"
    with open(encrypted_file, "wb") as f:
        f.write(encrypted_content)
    
    print(f"\n🔒 Fichier chiffré créé : {encrypted_file}")
    print_hex_dump(encrypted_content, "CONTENU CHIFFRÉ", 128)
    
    print("\n✅ Observation : Comparez les deux fichiers !")
    print(f"   → Original : {test_file} ({len(original_content)} bytes)")
    print(f"   → Chiffré  : {encrypted_file} ({len(encrypted_content)} bytes)")
    print("   → Le fichier chiffré est complètement illisible\n")
    
    return test_file, encrypted_file


def main():
    """Lance toutes les démonstrations"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  MODE DÉMONSTRATION - VISUALISATION DU CHIFFREMENT".center(68) + "║")
    print("║" + "  Projet ISEC - Secure File Transfer".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    
    input("\nAppuyez sur ENTRÉE pour commencer la démonstration...")
    
    # Démo 1 : RSA
    session_key, encrypted_key = demo_rsa_encryption()
    input("\nAppuyez sur ENTRÉE pour continuer...")
    
    # Démo 2 : AES-GCM
    plaintext, frame = demo_aes_encryption(session_key)
    input("\nAppuyez sur ENTRÉE pour continuer...")
    
    # Démo 3 : Certificat
    demo_certificate()
    input("\nAppuyez sur ENTRÉE pour continuer...")
    
    # Démo 4 : Comparaison fichiers
    test_file, encrypted_file = demo_comparison()
    
    print("\n" + "█"*70)
    print("█  RÉSUMÉ DE LA DÉMONSTRATION")
    print("█"*70)
    print("""
✅ Vous avez vu :
   1. La clé de session (32 bytes) chiffrée avec RSA-4096 (512 bytes)
   2. Les données chiffrées avec AES-256-GCM + nonce + tag
   3. Le certificat X.509 contenant la clé publique du serveur
   4. La différence entre un fichier original et chiffré

🎯 Pour votre présentation :
   1. Lancez ce script : python demo_mode.py
   2. Montrez les dumps hexadécimaux au professeur
   3. Ouvrez les fichiers demo_test.txt et demo_test_encrypted.bin
   4. Utilisez Wireshark pour capturer le trafic réseau (voir guide)

📝 Fichiers créés pour la démo :
   - demo_test.txt (fichier original lisible)
   - demo_test_encrypted.bin (fichier chiffré illisible)
""")
    
    print("█"*70 + "\n")


if __name__ == "__main__":
    main()
