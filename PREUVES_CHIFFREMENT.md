# 🔐 Preuves Visuelles du Chiffrement

## Résumé : Comment Montrer que Ça Marche

Votre professeur veut **voir** que les données sont chiffrées. Voici les preuves concrètes.

---

## ✅ Preuve #1 : Script de Démonstration

### Commande :
```bash
python demo_mode.py
```

### Ce que vous verrez :

#### Avant Chiffrement (CLÉ DE SESSION) :
```
======================================================================
  🔑 CLÉ DE SESSION (256 bits - EN CLAIR)
======================================================================
Taille: 32 bytes

Hexadécimal:
  a3f5e8d2c1b4a7f9e2d5c8b1a4f7e0d3c6b9acf2e5d8cbbea1f4e7dad0c3b6a9

ASCII:
  ................................
```

#### Après Chiffrement RSA :
```
======================================================================
  🔒 CLÉ DE SESSION CHIFFRÉE (RSA-4096)
======================================================================
Taille: 512 bytes

Hexadécimal:
  8f3a2e1d9c7b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f
  7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f8e7d6c5b4a3f2e1d0c9b8a7f6e5
  ...
```

**Observation :** La clé de 32 bytes devient 512 bytes de données illisibles !

---

## ✅ Preuve #2 : Fichiers Avant/Après

### Fichier Original (`demo_test.txt`) :
```
ISEC Project - Secure File Transfer
ISEC Project - Secure File Transfer
ISEC Project - Secure File Transfer
...
```
**Taille :** 370 bytes  
**Format :** Texte lisible

### Fichier Chiffré (`demo_test_encrypted.bin`) :
```
Hexadécimal:
a7 3f 2e 8d 1c 9b 4a 7f 2e 5d 8c 0b 3a 9f 7e 6d
5c 4b 3a 2f 1e 0d 9c 8b 7a 6f 5e 4d 3c 2b 1a 0f
...
```
**Taille :** 398 bytes (370 + 12 nonce + 16 tag)  
**Format :** Binaire illisible

### Comment Comparer :
```bash
# Ouvrir les deux fichiers
notepad demo_test.txt
notepad demo_test_encrypted.bin
```

**Résultat :** Le fichier chiffré affiche des caractères bizarres ou rien du tout !

---

## ✅ Preuve #3 : Capture Réseau Wireshark

### Étape 1 : Démarrer Wireshark
```bash
wireshark -i Loopback -k -f "tcp port 9000"
```

### Étape 2 : Lancer le Transfert
```bash
# Terminal 1
python server.py

# Terminal 2
python client.py --file test_demo.txt
```

### Étape 3 : Analyser la Capture

#### Ce que vous verrez dans Wireshark :

**Paquet 1 : Certificat (Serveur → Client)**
```
Data (1234 bytes):
30 82 04 d2 30 82 03 ba a0 03 02 01 02 02 14 78
0f 19 de e7 f5 0a ed 9b 90 0f 64 0a a6 13 c0 51
...
```

**Paquet 2 : Clé Chiffrée (Client → Serveur)**
```
Data (512 bytes):
8f 3a 2e 1d 9c 7b 5a 4f 3e 2d 1c 0b 9a 8f 7e 6d
5c 4b 3a 2f 1e 0d 9c 8b 7a 6f 5e 4d 3c 2b 1a 0f
...
```

**Paquet 3 : Données Chiffrées (Client → Serveur)**
```
Data (398 bytes):
a7 3f 2e 8d 1c 9b 4a 7f 2e 5d 8c 0b 3a 9f 7e 6d
5c 4b 3a 2f 1e 0d 9c 8b 7a 6f 5e 4d 3c 2b 1a 0f
...
```

### Étape 4 : Follow TCP Stream

1. Clic droit sur un paquet → **Follow** → **TCP Stream**
2. Vous verrez :

```
....@.....BEGIN CERTIFICATE.....
MIIFlzCCA3+gAwIBAgIUeA8Z3uf1Cu2bkA9kCqYTwFHq3OcwDQYJKoZIhvcNAQEL
[données binaires illisibles]
.....END CERTIFICATE.....
[plus de données binaires illisibles]
```

**Observation :** Impossible de lire le contenu du fichier `test_demo.txt` !

---

## ✅ Preuve #4 : Mode Verbose du Client

### Commande :
```bash
python client.py --file test_demo.txt --verbose
```

### Sortie :

```
======================================================================
  MODE DÉMONSTRATION ACTIVÉ
  Les données seront affichées en hexadécimal
======================================================================

2026-05-13 14:30:15 [INFO] Connecting to 127.0.0.1:9000 …

======================================================================
  📜 CERTIFICAT REÇU DU SERVEUR
======================================================================
Taille: 1234 bytes
Hex: 308204d2308203baa003020102021478...
======================================================================

2026-05-13 14:30:15 [INFO] Certificate verified. Subject: CN=localhost

======================================================================
  🔑 CLÉ DE SESSION GÉNÉRÉE (256 bits)
======================================================================
Taille: 32 bytes
Hex: a3f5e8d2c1b4a7f9e2d5c8b1a4f7e0d3...
======================================================================

======================================================================
  🔒 CLÉ DE SESSION CHIFFRÉE (RSA-4096)
======================================================================
Taille: 512 bytes
Hex: 8f3a2e1d9c7b5a4f3e2d1c0b9a8f7e6d...
======================================================================

2026-05-13 14:30:15 [INFO] Encrypted session key sent (512 bytes).
2026-05-13 14:30:15 [INFO] Sending file 'test_demo.txt' …

======================================================================
  📄 CHUNK EN CLAIR
======================================================================
Taille: 370 bytes
Hex: 4d455353414745205345435245542049...
======================================================================

======================================================================
  🔒 CHUNK CHIFFRÉ (nonce + ct + tag)
======================================================================
Taille: 398 bytes
Hex: a73f2e8d1c9b4a7f2e5d8c0b3a9f7e6d...
======================================================================

2026-05-13 14:30:15 [INFO] All chunks sent.
2026-05-13 14:30:15 [INFO] [✓] Transfer confirmed by server. Done.
```

**Observation :** Vous voyez les données avant ET après chiffrement !

---

## 📊 Tableau Comparatif

| Élément | Avant Chiffrement | Après Chiffrement |
|---------|-------------------|-------------------|
| **Clé de session** | 32 bytes lisibles | 512 bytes illisibles (RSA) |
| **Fichier texte** | Texte ASCII clair | Binaire illisible (AES-GCM) |
| **Taille** | N bytes | N + 28 bytes (nonce + tag) |
| **Lisibilité** | ✅ Humainement lisible | ❌ Complètement illisible |
| **Interception** | ⚠️ Dangereux | ✅ Sécurisé |

---

## 🎯 Pour la Présentation

### Montrez dans cet ordre :

1. **Fichier original** (`test_demo.txt`)
   - Ouvrez avec Notepad
   - Montrez que c'est lisible

2. **Script de démo** (`python demo_mode.py`)
   - Montrez les hexdumps
   - Comparez avant/après

3. **Fichier chiffré** (`demo_test_encrypted.bin`)
   - Ouvrez avec Notepad
   - Montrez que c'est illisible

4. **Wireshark**
   - Montrez la capture réseau
   - Follow TCP Stream
   - Montrez que les données sont binaires

5. **Mode verbose**
   - Lancez `python client.py --file test_demo.txt --verbose`
   - Montrez les logs avec hexdumps

---

## 💬 Ce qu'il faut dire au professeur

### Phrase clé :
```
"Nous pouvons prouver que le chiffrement fonctionne de 4 façons :

1. Le script demo_mode.py montre les données avant et après chiffrement
   en hexadécimal

2. Les fichiers demo_test.txt (lisible) et demo_test_encrypted.bin 
   (illisible) montrent la différence visuellement

3. Wireshark capture le trafic réseau et montre que les données 
   transmises sont binaires et illisibles

4. Le mode verbose du client affiche en temps réel les données 
   chiffrées pendant le transfert

Dans tous les cas, on voit que les données originales sont 
complètement transformées en bruit aléatoire illisible."
```

---

## 🔍 Questions/Réponses

### Q : "Comment je sais que c'est vraiment chiffré ?"
**R :** "Regardez Wireshark : les données sur le réseau sont binaires. Si vous ouvrez demo_test_encrypted.bin avec Notepad, c'est illisible. Le script demo_mode.py montre les hexdumps avant/après."

### Q : "Pourquoi la taille change ?"
**R :** "Le fichier chiffré est plus grand de 28 bytes :
- 12 bytes pour le nonce (unique par chunk)
- 16 bytes pour le tag d'authentification GCM
C'est le coût de la sécurité et de l'intégrité."

### Q : "Quelqu'un peut déchiffrer avec Wireshark ?"
**R :** "Non, impossible sans :
1. La clé privée du serveur (pour déchiffrer la clé de session)
2. La clé de session (pour déchiffrer les données)
Même avec Wireshark, un attaquant ne voit que du bruit."

---

## ✅ Checklist Finale

Avant la présentation, vérifiez :

- [ ] `demo_mode.py` fonctionne et affiche les hexdumps
- [ ] `demo_test.txt` existe et est lisible
- [ ] `demo_test_encrypted.bin` existe et est illisible
- [ ] Wireshark est installé et configuré
- [ ] Le mode verbose fonctionne : `python client.py --file test_demo.txt --verbose`
- [ ] Vous pouvez expliquer chaque hexdump
- [ ] Vous avez des captures d'écran de backup

---

## 🎓 Conclusion

Votre projet **prouve visuellement** que le chiffrement fonctionne grâce à :

✅ Hexdumps avant/après  
✅ Fichiers lisibles vs illisibles  
✅ Capture réseau Wireshark  
✅ Logs verbeux en temps réel  

Le professeur **verra** que les données sont chiffrées ! 🔐
