# Secure File Transfer - Projet ISEC

## Description
Application client-serveur pour l'échange sécurisé de fichiers utilisant les concepts de cryptographie moderne et PKI étudiés dans le cours ISEC (Introduction à la Sécurité).

## Fonctionnalités de Sécurité Implémentées

### 1. Cryptographie Asymétrique (RSA-4096)
- **Génération de certificats X.509** auto-signés avec `generate_certs.py`
- **Chiffrement RSA-OAEP** de la clé de session avec SHA-256
- **Authentification du serveur** par vérification du certificat (key pinning)
- Conforme au chapitre "Cryptographie moderne" du cours

### 2. Cryptographie Symétrique (AES-256-GCM)
- **Chiffrement AES-256** en mode GCM pour les fichiers
- **Génération aléatoire de nonce** (12 octets) pour chaque chunk de 64 KB
- **Intégrité garantie** par le tag d'authentification GCM
- Conforme au chapitre "Cryptosystème à clé symétrique"

### 3. Infrastructure PKI
- **Certificat numérique X.509** pour le serveur (RSA-4096)
- **Vérification de l'authenticité** du certificat côté client
- **Période de validité** de 365 jours
- **Subject Alternative Names** (localhost, 127.0.0.1)
- Conforme au chapitre "Infrastructure de gestion des clés"

### 4. Protocole Sécurisé Hybride
- **Échange de clé de session** (concept d'enveloppe digitale)
- **Confidentialité** : AES-256-GCM pour les données
- **Intégrité** : Tag GCM détecte toute modification
- **Authentification** : Vérification du certificat serveur
- Conforme au chapitre "Protocoles sécurisés"

## Architecture du Protocole

```
1. Serveur → Client : Certificat X.509 (clé publique RSA-4096)
2. Client vérifie le certificat (key pinning)
3. Client génère une clé de session AES-256 aléatoire
4. Client → Serveur : Clé de session chiffrée avec RSA-OAEP
5. Client → Serveur : Nom du fichier
6. Client → Serveur : Chunks chiffrés (nonce + ciphertext + tag GCM)
7. Client → Serveur : Frame vide (EOF)
8. Serveur → Client : Accusé de réception "OK"
```

## Installation

### Prérequis
- Python 3.7+
- Bibliothèque `cryptography`

### Installation des dépendances
```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Génération des certificats (une seule fois)
```bash
python generate_certs.py
```
Cela crée :
- `server.key` : Clé privée RSA-4096 (à garder secrète)
- `server.crt` : Certificat X.509 (à distribuer aux clients)

### 2. Démarrage du serveur
```bash
python server.py
```
Le serveur écoute sur `0.0.0.0:9000` et sauvegarde les fichiers dans `received_files/`

### 3. Envoi d'un fichier (client)
```bash
python client.py --file chemin/vers/fichier.pdf
```

Options disponibles :
- `--host` : Adresse du serveur (défaut: 127.0.0.1)
- `--port` : Port du serveur (défaut: 9000)
- `--trusted-cert` : Chemin vers le certificat de confiance (défaut: server.crt)

### 4. Interface graphique (optionnel)
```bash
python gui.py
```
L'interface permet de :
- Démarrer/arrêter le serveur
- Envoyer un fichier unique
- Envoyer plusieurs fichiers (zippés automatiquement)
- Envoyer un dossier complet (zippé automatiquement)

## Concepts ISEC Appliqués

### Cryptographie Classique
- Compréhension des limites du chiffrement symétrique simple
- Nécessité d'un canal sécurisé pour l'échange de clés

### Cryptographie Moderne
- **Chiffrement par blocs** : AES-256 avec chunks de 64 KB
- **Mode GCM** : Confidentialité + Intégrité
- **RSA-4096** : Sécurité asymétrique robuste
- **Clé de session** : Compromis performance/sécurité

### Infrastructure PKI
- **Certificat X.509** : Identité numérique du serveur
- **Key pinning** : Vérification de la clé publique
- **Période de validité** : Gestion du cycle de vie

### Protocoles Sécurisés
- **Handshake** : Échange de certificat et de clé
- **Chiffrement hybride** : RSA pour la clé, AES pour les données
- **Framing** : Protocole de transport avec longueur préfixée

## Propriétés de Sécurité

### ✅ Garanties
- **Confidentialité** : AES-256-GCM avec nonces aléatoires
- **Intégrité** : Tags GCM détectent toute modification
- **Authentification du serveur** : Key pinning du certificat
- **Forward secrecy partielle** : Clé de session unique par connexion

### ⚠️ Limitations (pour usage pédagogique)
- Pas d'authentification du client
- Pas de protection contre le replay d'une session complète
- Certificat auto-signé (pas de CA externe)
- Serveur mono-thread (une connexion à la fois)

## Structure du Projet

```
secure_file_transfer/
├── client.py              # Client de transfert
├── server.py              # Serveur de réception
├── generate_certs.py      # Génération de certificats
├── gui.py                 # Interface graphique Tkinter
├── requirements.txt       # Dépendances Python
├── server.crt            # Certificat X.509 (généré)
├── server.key            # Clé privée RSA (généré)
├── received_files/       # Fichiers reçus par le serveur
└── README.md             # Cette documentation
```

## Détails Techniques

### Algorithmes Utilisés
- **RSA-4096** avec padding OAEP (MGF1-SHA256)
- **AES-256-GCM** (Galois/Counter Mode)
- **SHA-256** pour le hachage (dans OAEP)
- **Nonces de 12 octets** (recommandation GCM)

### Format des Messages
- **Header** : 4 octets big-endian (longueur du payload)
- **Certificat** : [len(4)][cert_pem]
- **Clé chiffrée** : 512 octets (RSA-4096)
- **Nom de fichier** : [len(2)][utf-8_bytes]
- **Chunk chiffré** : [len(4)][nonce(12) + ciphertext + tag(16)]
- **EOF** : [len=0]
- **ACK** : "OK" ou "ERR" (2 octets)

## Références du Cours ISEC

Ce projet implémente les concepts des chapitres suivants :
- **Chapitre 3** : Cryptographie classique et moderne
- **Chapitre 4** : Infrastructure de gestion des clés (PKI)
- **Chapitre 5** : Protocoles sécurisés (SSL/TLS, SSH)
- **Chapitre 6** : Services sécurisés (PGP)

## Auteurs
Projet réalisé dans le cadre du cours ISEC (Introduction à la Sécurité)

## Licence
Usage pédagogique uniquement
