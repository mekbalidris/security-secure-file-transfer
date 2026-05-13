# 🎯 Guide de Présentation du Projet

## Comment Prouver que le Chiffrement Fonctionne

Votre professeur veut **voir** que les données sont vraiment chiffrées. Voici 4 méthodes pour le démontrer visuellement.

---

## Méthode 1 : Mode Démonstration (Le Plus Simple) ✨

### Étape 1 : Lancer le script de démonstration

```bash
python demo_mode.py
```

### Ce que vous verrez :

```
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║        MODE DÉMONSTRATION - VISUALISATION DU CHIFFREMENT           ║
║              Projet ISEC - Secure File Transfer                    ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝

======================================================================
  🔑 CLÉ DE SESSION (256 bits - EN CLAIR)
======================================================================
Taille: 32 bytes

Hexadécimal (premiers 32 bytes):
  a3f5e8d2c1b4a7f9e2d5c8b1a4f7e0d3
  c6b9acf2e5d8cbbea1f4e7dad0c3b6a9

ASCII (premiers 32 bytes):
  ................................

======================================================================

======================================================================
  🔒 CLÉ DE SESSION CHIFFRÉE (RSA-4096)
======================================================================
Taille: 512 bytes

Hexadécimal (premiers 64 bytes):
  8f3a2e1d9c7b5a4f3e2d1c0b9a8f7e6d
  5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f
  ...
```

### Points à montrer au professeur :
1. **Clé en clair** : 32 bytes lisibles
2. **Clé chiffrée** : 512 bytes de "bruit" illisible
3. **Message en clair** : Texte lisible
4. **Message chiffré** : Complètement illisible
5. **Fichiers de comparaison** : Ouvrez `demo_test.txt` (lisible) et `demo_test_encrypted.bin` (illisible)

---

## Méthode 2 : Capture Réseau avec Wireshark 🦈

### Installation de Wireshark

**Windows :**
1. Téléchargez depuis https://www.wireshark.org/download.html
2. Installez avec les options par défaut
3. Installez aussi Npcap quand demandé

### Étape 1 : Démarrer la capture

1. Ouvrez Wireshark
2. Sélectionnez l'interface **Loopback** (ou **lo0** sur Mac/Linux)
3. Cliquez sur l'icône aileron de requin bleu pour démarrer la capture
4. Ajoutez un filtre : `tcp.port == 9000`

### Étape 2 : Lancer le transfert

```bash
# Terminal 1 : Serveur
python server.py

# Terminal 2 : Client
python client.py --file test.txt
```

### Étape 3 : Analyser la capture

Dans Wireshark, vous verrez :

```
1. TCP Handshake (SYN, SYN-ACK, ACK)
2. [PSH] Data: Certificat X.509 (serveur → client)
3. [PSH] Data: Clé chiffrée RSA (client → serveur)
4. [PSH] Data: Nom du fichier (client → serveur)
5. [PSH] Data: Chunks chiffrés AES-GCM (client → serveur)
6. [PSH] Data: "OK" (serveur → client)
```

### Étape 4 : Examiner les données chiffrées

1. Cliquez sur un paquet de données
2. Faites clic droit → **Follow** → **TCP Stream**
3. Vous verrez des données binaires illisibles :

```
....@.....BEGIN CERTIFICATE.....
[données binaires illisibles]
.....END CERTIFICATE.....
[plus de données binaires illisibles]
```

### Points à montrer :
- ✅ Les données sont **binaires et illisibles**
- ✅ Impossible de voir le contenu du fichier
- ✅ Seuls les headers TCP/IP sont en clair

---

## Méthode 3 : Logs Verbeux avec Hexdump 📝

J'ai créé une version modifiée du client et serveur qui affiche les données.

### Créer `client_verbose.py` :

```bash
python client_verbose.py --file test.txt
```

Vous verrez :

```
[INFO] Connecting to 127.0.0.1:9000 …
[INFO] Certificate received (1234 bytes)
[HEX] 30 82 04 d2 30 82 03 ba a0 03 02 01 02 02 14 78 ...
[INFO] Certificate verified ✓
[INFO] Generated session key (32 bytes)
[HEX] a3 f5 e8 d2 c1 b4 a7 f9 e2 d5 c8 b1 a4 f7 e0 d3 ...
[INFO] Encrypted session key (512 bytes)
[HEX] 8f 3a 2e 1d 9c 7b 5a 4f 3e 2d 1c 0b 9a 8f 7e 6d ...
[INFO] Sending file 'test.txt' …
[INFO] Chunk 1: plaintext (64 KB)
[HEX] 54 68 69 73 20 69 73 20 61 20 74 65 73 74 ...
[INFO] Chunk 1: encrypted (64 KB + 28 bytes overhead)
[HEX] a7 3f 2e 8d 1c 9b 4a 7f 2e 5d 8c 0b 3a 9f ...
```

---

## Méthode 4 : Comparaison de Fichiers 📂

### Créer un fichier de test lisible :

```bash
echo "Ceci est un message secret ISEC 2026" > test_original.txt
```

### Envoyer le fichier :

```bash
python server.py  # Terminal 1
python client.py --file test_original.txt  # Terminal 2
```

### Intercepter les données réseau :

Pendant le transfert, capturez avec Wireshark et sauvegardez le flux TCP dans `captured_data.bin`.

### Comparer :

```bash
# Ouvrir avec un éditeur hexadécimal ou :
xxd test_original.txt > original_hex.txt
xxd captured_data.bin > captured_hex.txt

# Comparer visuellement
notepad original_hex.txt
notepad captured_hex.txt
```

**Résultat :**
- `original_hex.txt` : Texte lisible en ASCII
- `captured_hex.txt` : Données binaires illisibles

---

## 🎬 Scénario de Présentation Recommandé

### Introduction (2 minutes)
```
"Notre projet implémente un protocole de transfert de fichiers sécurisé
utilisant les concepts du cours ISEC :
- Cryptographie asymétrique (RSA-4096)
- Cryptographie symétrique (AES-256-GCM)
- Certificats numériques (X.509)
- Infrastructure PKI"
```

### Démonstration 1 : Mode Démo (3 minutes)
```bash
python demo_mode.py
```
**Montrez :**
1. Clé de session en clair vs chiffrée
2. Message en clair vs chiffré
3. Fichiers `demo_test.txt` vs `demo_test_encrypted.bin`

### Démonstration 2 : Transfert Réel (3 minutes)
```bash
# Terminal 1
python server.py

# Terminal 2
python client.py --file rapport.pdf
```
**Montrez :**
1. Les logs du serveur et client
2. Le fichier reçu dans `received_files/`
3. Que le fichier est identique à l'original

### Démonstration 3 : Wireshark (3 minutes)
**Montrez :**
1. La capture réseau en temps réel
2. Le flux TCP avec données chiffrées
3. Que le contenu du fichier est illisible

### Démonstration 4 : Interface Graphique (2 minutes)
```bash
python gui.py
```
**Montrez :**
1. Démarrage du serveur
2. Envoi d'un fichier
3. Envoi de plusieurs fichiers (zippés)

### Conclusion (2 minutes)
```
"Notre implémentation garantit :
✅ Confidentialité : AES-256-GCM
✅ Intégrité : Tags d'authentification GCM
✅ Authentification : Vérification du certificat
✅ Conformité ISEC : Tous les concepts du cours appliqués"
```

---

## 📋 Checklist Avant la Présentation

### Préparation Technique
- [ ] Wireshark installé et testé
- [ ] `demo_mode.py` fonctionne
- [ ] Certificats générés (`server.crt`, `server.key`)
- [ ] Fichiers de test préparés (PDF, TXT, images)
- [ ] Les deux terminaux prêts (serveur + client)

### Fichiers à Montrer
- [ ] `demo_test.txt` (lisible)
- [ ] `demo_test_encrypted.bin` (illisible)
- [ ] Capture Wireshark sauvegardée
- [ ] `server.crt` (certificat)
- [ ] Code source commenté

### Points Clés à Expliquer
- [ ] Pourquoi RSA pour la clé de session
- [ ] Pourquoi AES pour le fichier
- [ ] Comment fonctionne le mode GCM
- [ ] Rôle du certificat X.509
- [ ] Concept d'enveloppe digitale

---

## 🎯 Questions Probables du Professeur

### Q1 : "Comment savez-vous que c'est vraiment chiffré ?"
**Réponse :**
```
"Nous pouvons le prouver de 3 façons :
1. Le script demo_mode.py montre les données avant/après chiffrement
2. Wireshark capture le trafic réseau : les données sont illisibles
3. Les fichiers demo_test_encrypted.bin sont du bruit binaire"
```

### Q2 : "Pourquoi utilisez-vous RSA ET AES ?"
**Réponse :**
```
"C'est le concept d'enveloppe digitale du cours (chapitre 3.4.1) :
- RSA : Lent mais sécurise l'échange de clé (512 bytes)
- AES : Rapide pour chiffrer les gros fichiers (plusieurs MB)
C'est exactement comme SSL/TLS fait"
```

### Q3 : "Comment le client vérifie-t-il le serveur ?"
**Réponse :**
```
"Par key pinning (chapitre 4.2.1) :
1. Le client a une copie de server.crt
2. Il compare les clés publiques byte par byte
3. Si différent → attaque MITM détectée → connexion refusée"
```

### Q4 : "Quelle est la différence avec SSL/TLS ?"
**Réponse :**
```
"Notre protocole est une version simplifiée de SSL/TLS :
✅ Similaire : Handshake, échange de clé, chiffrement hybride
❌ Différent : Pas d'authentification client, pas de forward secrecy
C'est un SSL/TLS pédagogique pour comprendre les concepts"
```

### Q5 : "Pourquoi un nonce par chunk ?"
**Réponse :**
```
"Pour la sécurité du mode GCM :
- Même données + même clé + nonce différent = ciphertext différent
- Empêche l'analyse de patterns
- Conforme aux recommandations NIST pour AES-GCM"
```

---

## 💡 Astuces de Présentation

### 1. Préparez des Captures d'Écran
Prenez des screenshots de :
- Wireshark avec données chiffrées
- `demo_mode.py` en action
- Fichiers avant/après chiffrement
- Interface graphique

### 2. Créez un Fichier de Test Évident
```bash
echo "MESSAGE SECRET ISEC - NE PAS LIRE !" > secret.txt
```
Montrez que ce texte est illisible dans Wireshark.

### 3. Préparez une Vidéo de Backup
Si la démo live échoue, ayez une vidéo de 2 minutes montrant :
1. Lancement du serveur
2. Envoi d'un fichier
3. Capture Wireshark
4. Fichier reçu

### 4. Imprimez les Hexdumps
Imprimez les sorties de `demo_mode.py` pour les montrer physiquement.

---

## 🚀 Commandes Rapides pour la Démo

```bash
# 1. Génération des certificats
python generate_certs.py

# 2. Mode démonstration
python demo_mode.py

# 3. Démarrer Wireshark
wireshark -i Loopback -k -f "tcp port 9000"

# 4. Serveur (Terminal 1)
python server.py

# 5. Client (Terminal 2)
python client.py --file test.pdf

# 6. Interface graphique
python gui.py
```

---

## ✅ Résumé : Preuves du Chiffrement

| Méthode | Difficulté | Impact Visuel | Temps |
|---------|-----------|---------------|-------|
| `demo_mode.py` | ⭐ Facile | ⭐⭐⭐⭐⭐ | 3 min |
| Wireshark | ⭐⭐ Moyen | ⭐⭐⭐⭐ | 5 min |
| Comparaison fichiers | ⭐ Facile | ⭐⭐⭐ | 2 min |
| Logs verbeux | ⭐⭐⭐ Difficile | ⭐⭐⭐ | 5 min |

**Recommandation :** Utilisez `demo_mode.py` + Wireshark pour une présentation complète et convaincante !

---

Bonne présentation ! 🎓
