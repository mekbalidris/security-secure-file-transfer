# Comment Fonctionne l'Application - Explication Détaillée

## Vue d'Ensemble

Cette application implémente un **protocole de transfert de fichiers sécurisé** inspiré de SSL/TLS, en utilisant les concepts de cryptographie moderne étudiés dans le cours ISEC.

## Phase 1 : Préparation (Une seule fois)

### Génération des Certificats (`generate_certs.py`)

```
┌─────────────────────────────────────────┐
│  python generate_certs.py               │
└─────────────────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ 1. Génère clé privée RSA    │
    │    - Taille: 4096 bits      │
    │    - Exposant: 65537        │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ 2. Crée certificat X.509    │
    │    - Subject: CN=localhost  │
    │    - SAN: localhost,127.0.0.1│
    │    - Validité: 365 jours    │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ 3. Signe avec clé privée    │
    │    - Algorithme: SHA-256    │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ 4. Sauvegarde les fichiers  │
    │    - server.key (600)       │
    │    - server.crt (644)       │
    └─────────────────────────────┘
```

**Résultat** :
- `server.key` : Clé privée RSA-4096 (à garder SECRÈTE sur le serveur)
- `server.crt` : Certificat public (à distribuer aux clients)

## Phase 2 : Démarrage du Serveur (`server.py`)

```
┌─────────────────────────────────────────┐
│  python server.py                       │
└─────────────────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ 1. Charge server.key        │
    │    (clé privée RSA)         │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ 2. Charge server.crt        │
    │    (certificat PEM)         │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ 3. Crée socket TCP          │
    │    - Bind: 0.0.0.0:9000     │
    │    - Listen: 5 connexions   │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ 4. Attend les clients...    │
    │    (boucle accept)          │
    └─────────────────────────────┘
```

Le serveur est maintenant prêt à recevoir des connexions.

## Phase 3 : Transfert de Fichier (Protocole Complet)

### Étape 1 : Connexion et Handshake

```
CLIENT                                    SERVEUR
  │                                          │
  │  1. TCP connect(host:9000)              │
  ├─────────────────────────────────────────>│
  │                                          │
  │  2. Envoie certificat X.509             │
  │     [4 bytes len][cert_pem]             │
  │<─────────────────────────────────────────┤
  │                                          │
  │  3. Vérifie le certificat               │
  │     - Charge server.crt local           │
  │     - Compare clés publiques            │
  │     - Si différent → ABORT              │
  │                                          │
```

**Code client correspondant** :
```python
def receive_and_verify_cert(sock, trusted_cert_path):
    # Reçoit le certificat du serveur
    cert_len = struct.unpack(">I", recv_exact(sock, 4))[0]
    cert_pem = recv_exact(sock, cert_len)
    received_cert = x509.load_pem_x509_certificate(cert_pem)
    
    # Charge le certificat de confiance
    with open(trusted_cert_path, "rb") as fh:
        trusted_cert = x509.load_pem_x509_certificate(fh.read())
    
    # Compare les clés publiques (KEY PINNING)
    if received_pub != trusted_pub:
        raise RuntimeError("MITM attack detected!")
```

### Étape 2 : Échange de Clé de Session

```
CLIENT                                    SERVEUR
  │                                          │
  │  4. Génère clé de session               │
  │     session_key = os.urandom(32)        │
  │     (256 bits aléatoires)               │
  │                                          │
  │  5. Chiffre avec RSA-OAEP               │
  │     encrypted_key = RSA_encrypt(        │
  │         session_key,                    │
  │         server_public_key               │
  │     )                                   │
  │                                          │
  │  6. Envoie clé chiffrée (512 bytes)     │
  ├─────────────────────────────────────────>│
  │                                          │
  │                                          │  7. Déchiffre avec clé privée
  │                                          │     session_key = RSA_decrypt(
  │                                          │         encrypted_key,
  │                                          │         server_private_key
  │                                          │     )
  │                                          │
```

**Code client** :
```python
def encrypt_session_key(cert, session_key):
    pub_key = cert.public_key()
    return pub_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
```

**Code serveur** :
```python
def decrypt_session_key(private_key, ciphertext):
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
```

### Étape 3 : Transfert du Fichier

```
CLIENT                                    SERVEUR
  │                                          │
  │  8. Envoie nom du fichier               │
  │     [2 bytes len][filename_utf8]        │
  ├─────────────────────────────────────────>│
  │                                          │
  │  9. Lit fichier par chunks de 64KB      │
  │     Pour chaque chunk:                  │
  │                                          │
  │     a) Génère nonce aléatoire (12 bytes)│
  │        nonce = os.urandom(12)           │
  │                                          │
  │     b) Chiffre avec AES-256-GCM         │
  │        ciphertext = AES_GCM_encrypt(    │
  │            plaintext=chunk,             │
  │            key=session_key,             │
  │            nonce=nonce                  │
  │        )                                │
  │        # Produit: ciphertext + tag(16)  │
  │                                          │
  │     c) Envoie frame                     │
  │        [4 bytes len][nonce + ct + tag]  │
  ├─────────────────────────────────────────>│
  │                                          │  d) Déchiffre chunk
  │                                          │     - Extrait nonce (12 bytes)
  │                                          │     - Déchiffre avec AES-GCM
  │                                          │     - Vérifie tag (intégrité)
  │                                          │     - Écrit dans fichier
  │                                          │
  │  10. Envoie frame vide (EOF)            │
  │      [4 bytes: 0x00000000]              │
  ├─────────────────────────────────────────>│
  │                                          │
  │  11. Reçoit accusé de réception         │
  │<─────────────────────────────────────────┤
  │      "OK" (2 bytes)                     │
  │                                          │
  │  12. Ferme connexion                    │
  │                                          │
```

**Code client (chiffrement chunk)** :
```python
def encrypt_chunk(aesgcm, plaintext):
    nonce = os.urandom(12)  # Nonce unique par chunk
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext  # nonce + ct + tag
```

**Code serveur (déchiffrement chunk)** :
```python
def decrypt_chunk(aesgcm, frame):
    nonce = frame[:12]  # Extrait nonce
    ciphertext_with_tag = frame[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
    # Si le tag est invalide, decrypt() lève une exception
    return plaintext
```

## Détails Cryptographiques

### 1. Pourquoi RSA-4096 ?
- **Sécurité** : Résiste aux attaques par factorisation
- **Taille de clé** : 512 bytes de ciphertext
- **Usage** : Uniquement pour chiffrer la petite clé de session (32 bytes)

### 2. Pourquoi AES-256-GCM ?
- **Performance** : Très rapide pour les gros fichiers
- **Mode GCM** : Fournit confidentialité ET intégrité
- **Tag d'authentification** : 16 bytes ajoutés automatiquement
- **Nonce unique** : Chaque chunk a son propre nonce aléatoire

### 3. Pourquoi un Nonce par Chunk ?
```
Chunk 1: nonce₁ + AES(data₁, key, nonce₁) + tag₁
Chunk 2: nonce₂ + AES(data₂, key, nonce₂) + tag₂
Chunk 3: nonce₃ + AES(data₃, key, nonce₃) + tag₃
```

Même si deux chunks contiennent les mêmes données, ils produisent des ciphertexts différents grâce aux nonces uniques.

### 4. Vérification du Certificat (Key Pinning)

```python
# Le client compare les clés publiques byte par byte
received_pub = received_cert.public_key().public_bytes(...)
trusted_pub = trusted_cert.public_key().public_bytes(...)

if received_pub != trusted_pub:
    # Possible attaque MITM !
    raise RuntimeError("Certificate verification FAILED")
```

Cela empêche un attaquant de présenter un autre certificat valide.

## Format des Messages (Wire Protocol)

### Message 1 : Certificat
```
┌────────────┬──────────────────────────┐
│  4 bytes   │      N bytes             │
│  Length    │   Certificate PEM        │
│ (big-endian)│                          │
└────────────┴──────────────────────────┘
```

### Message 2 : Clé de Session Chiffrée
```
┌──────────────────────────────────────┐
│          512 bytes                   │
│   RSA-OAEP encrypted session key     │
└──────────────────────────────────────┘
```

### Message 3 : Nom de Fichier
```
┌────────────┬──────────────────────────┐
│  2 bytes   │      N bytes             │
│  Length    │   Filename (UTF-8)       │
│ (big-endian)│                          │
└────────────┴──────────────────────────┘
```

### Message 4 : Chunk Chiffré
```
┌────────────┬────────────┬──────────────┬────────────┐
│  4 bytes   │  12 bytes  │   N bytes    │  16 bytes  │
│  Length    │   Nonce    │  Ciphertext  │  GCM Tag   │
│(big-endian)│            │              │            │
└────────────┴────────────┴──────────────┴────────────┘
```

### Message 5 : EOF
```
┌────────────┐
│  4 bytes   │
│  0x00000000│
└────────────┘
```

### Message 6 : Accusé de Réception
```
┌────────────┐
│  2 bytes   │
│  "OK"      │
└────────────┘
```

## Propriétés de Sécurité Garanties

### ✅ Confidentialité
- **Clé de session** : Chiffrée avec RSA-4096, impossible à intercepter
- **Contenu du fichier** : Chiffré avec AES-256-GCM
- **Nonces aléatoires** : Empêchent l'analyse de patterns

### ✅ Intégrité
- **Tag GCM** : Chaque chunk a un tag de 16 bytes
- **Vérification automatique** : `aesgcm.decrypt()` lève une exception si le tag est invalide
- **Protection contre modification** : Impossible de modifier un seul bit sans être détecté

### ✅ Authentification du Serveur
- **Key pinning** : Le client vérifie que la clé publique correspond
- **Protection MITM** : Un attaquant ne peut pas présenter un autre certificat

### ⚠️ Limitations
- **Pas d'authentification du client** : Le serveur accepte n'importe quel client
- **Pas de forward secrecy parfaite** : Si `server.key` est volée, toutes les sessions passées peuvent être déchiffrées
- **Pas de protection replay** : Une session enregistrée peut être rejouée

## Comparaison avec les Concepts du Cours

### Enveloppe Digitale (Chapitre 3.4.1)
```
┌─────────────────────────────────────────────┐
│  Votre implémentation = Enveloppe digitale  │
├─────────────────────────────────────────────┤
│  1. Clé de session générée aléatoirement    │
│  2. Fichier chiffré avec clé symétrique     │
│  3. Clé de session chiffrée avec clé pub    │
│  4. Destinataire déchiffre avec clé privée  │
└─────────────────────────────────────────────┘
```

### Protocole SSL (Chapitre 5.1)
```
┌─────────────────────────────────────────────┐
│  Votre protocole ≈ SSL/TLS simplifié        │
├─────────────────────────────────────────────┤
│  1. Handshake: échange de certificat        │
│  2. Key exchange: RSA pour clé de session   │
│  3. Encrypted communication: AES-GCM        │
│  4. Integrity: GCM tags                     │
└─────────────────────────────────────────────┘
```

### PKI (Chapitre 4)
```
┌─────────────────────────────────────────────┐
│  Votre PKI = PKI simplifiée                 │
├─────────────────────────────────────────────┤
│  - Certificat X.509: ✓                      │
│  - Clé publique/privée: ✓                   │
│  - Vérification: ✓ (key pinning)            │
│  - CA externe: ✗ (auto-signé)               │
└─────────────────────────────────────────────┘
```

## Utilisation de l'Interface Graphique

L'interface `gui.py` simplifie l'utilisation :

```
┌─────────────────────────────────────────┐
│  [START SERVER]  [STOP SERVER]          │
├─────────────────────────────────────────┤
│  Mode: [Single File ▼]                  │
│  [SELECT]  [SEND]                       │
│  Selected: report.pdf                   │
├─────────────────────────────────────────┤
│  >> SYSTEM LOGS <<                      │
│  [LOG] Server started...                │
│  [LOG] Sending file 'report.pdf'...     │
│  [LOG] Transfer successful!             │
└─────────────────────────────────────────┘
```

### Modes disponibles :
1. **Single File** : Envoie un fichier tel quel
2. **Multiple Files** : Zippe plusieurs fichiers et envoie le .zip
3. **Folder** : Zippe un dossier complet et envoie le .zip

## Conclusion

Votre projet implémente correctement :
- ✅ Cryptographie asymétrique (RSA)
- ✅ Cryptographie symétrique (AES)
- ✅ Certificats numériques (X.509)
- ✅ Protocole sécurisé (handshake + encrypted transfer)
- ✅ Concepts PKI (génération, distribution, vérification)

C'est une excellente démonstration pratique des concepts ISEC !
