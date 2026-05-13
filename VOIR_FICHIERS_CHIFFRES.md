# 🔐 Comment Voir les Fichiers Chiffrés

## ✅ Modification Apportée

J'ai modifié le **serveur** pour qu'il sauvegarde **DEUX versions** de chaque fichier reçu :

1. **Version déchiffrée** : `received_files/fichier.txt` (LISIBLE)
2. **Version chiffrée** : `received_files/fichier.txt.encrypted` (ILLISIBLE)

---

## 🎯 Test Complet

### Étape 1 : Créer un fichier de test

```bash
echo "MESSAGE SECRET ISEC 2026 - Ceci est confidentiel !" > test_secret.txt
```

### Étape 2 : Démarrer le serveur

```bash
python server.py
```

### Étape 3 : Envoyer le fichier

```bash
python client.py --file test_secret.txt
```

### Étape 4 : Vérifier les fichiers reçus

Vous aurez maintenant **DEUX fichiers** dans `received_files/` :

```
received_files/
├── test_secret.txt            ← Version DÉCHIFFRÉE (lisible)
└── test_secret.txt.encrypted  ← Version CHIFFRÉE (illisible)
```

---

## 📂 Comparaison Visuelle

### Fichier Original (`test_secret.txt`)
```
MESSAGE SECRET ISEC 2026 - Ceci est confidentiel !
```
**Taille :** ~50 bytes  
**Format :** Texte lisible

### Fichier Déchiffré (`received_files/test_secret.txt`)
```
MESSAGE SECRET ISEC 2026 - Ceci est confidentiel !
```
**Taille :** ~50 bytes  
**Format :** Texte lisible (identique à l'original)

### Fichier Chiffré (`received_files/test_secret.txt.encrypted`)
```
Hexadécimal:
a7 3f 2e 8d 1c 9b 4a 7f 2e 5d 8c 0b 3a 9f 7e 6d
5c 4b 3a 2f 1e 0d 9c 8b 7a 6f 5e 4d 3c 2b 1a 0f
...
```
**Taille :** ~78 bytes (50 + 12 nonce + 16 tag)  
**Format :** Binaire illisible

---

## 🔍 Comment Ouvrir les Fichiers

### Fichier Déchiffré (Normal)
```bash
notepad received_files\test_secret.txt
```
**Résultat :** Vous verrez le texte en clair

### Fichier Chiffré (Pour la Démo)
```bash
notepad received_files\test_secret.txt.encrypted
```
**Résultat :** Vous verrez des caractères bizarres ou rien du tout !

---

## 🎬 Pour la Présentation

### Démonstration en 3 Étapes

#### 1. Montrez le fichier original
```bash
notepad test_secret.txt
```
**Dites :** "Voici le fichier original avec un message secret"

#### 2. Envoyez le fichier
```bash
# Terminal 1
python server.py

# Terminal 2
python client.py --file test_secret.txt
```
**Dites :** "Le fichier est chiffré pendant le transfert"

#### 3. Comparez les deux versions reçues
```bash
# Version déchiffrée (lisible)
notepad received_files\test_secret.txt

# Version chiffrée (illisible)
notepad received_files\test_secret.txt.encrypted
```
**Dites :** "Le serveur a reçu les données chiffrées (fichier .encrypted) et les a déchiffrées (fichier normal)"

---

## 📊 Tableau Comparatif

| Fichier | Emplacement | Contenu | Lisible ? |
|---------|-------------|---------|-----------|
| `test_secret.txt` | Racine | Original | ✅ Oui |
| `received_files/test_secret.txt` | Serveur | Déchiffré | ✅ Oui |
| `received_files/test_secret.txt.encrypted` | Serveur | Chiffré | ❌ Non |

---

## 💡 Explication Technique

### Que Contient le Fichier `.encrypted` ?

Le fichier `.encrypted` contient les **frames brutes** reçues du réseau :

```
Frame 1: [nonce(12)] + [ciphertext] + [tag(16)]
Frame 2: [nonce(12)] + [ciphertext] + [tag(16)]
...
```

Chaque frame est exactement ce qui a été transmis sur le réseau, **avant déchiffrement**.

### Pourquoi Deux Fichiers ?

- **Fichier normal** : Pour que l'application fonctionne (le destinataire peut lire le fichier)
- **Fichier .encrypted** : Pour la **démonstration** (prouver que les données étaient chiffrées)

---

## 🎯 Logs du Serveur

Quand vous envoyez un fichier, vous verrez maintenant :

```
2026-05-13 15:30:15 [INFO] Accepted connection from 127.0.0.1:54321
2026-05-13 15:30:15 [INFO] [127.0.0.1:54321] Certificate sent (1234 bytes).
2026-05-13 15:30:15 [INFO] [127.0.0.1:54321] Received encrypted session key.
2026-05-13 15:30:15 [INFO] [127.0.0.1:54321] Session key decrypted successfully.
2026-05-13 15:30:15 [INFO] [127.0.0.1:54321] Receiving file: 'test_secret.txt'
2026-05-13 15:30:15 [INFO] [127.0.0.1:54321] Transfer complete. Saved 'received_files/test_secret.txt' (50 bytes).
2026-05-13 15:30:15 [INFO] [127.0.0.1:54321] Encrypted version saved: 'received_files/test_secret.txt.encrypted' (78 bytes).
2026-05-13 15:30:15 [INFO] [127.0.0.1:54321] Connection closed.
```

**Notez la nouvelle ligne :** "Encrypted version saved"

---

## 🔐 Preuve du Chiffrement

### Avant (Ancien Programme)
- ❌ Impossible de voir les données chiffrées stockées
- ✅ Visible seulement avec Wireshark

### Après (Nouveau Programme)
- ✅ Fichier `.encrypted` sauvegardé sur le disque
- ✅ Visible avec Wireshark
- ✅ Comparaison directe : fichier normal vs chiffré

---

## 📝 Commandes Rapides

```bash
# 1. Créer un fichier de test
echo "MESSAGE SECRET" > test.txt

# 2. Démarrer le serveur
python server.py

# 3. Envoyer le fichier
python client.py --file test.txt

# 4. Voir le fichier déchiffré (lisible)
notepad received_files\test.txt

# 5. Voir le fichier chiffré (illisible)
notepad received_files\test.txt.encrypted

# 6. Comparer les tailles
dir received_files\test.txt*
```

---

## ✅ Résumé

### Question : "Le fichier txt est-il chiffré et stocké quelque part ?"

**Réponse :**

**AVANT ma modification :**
- ❌ Non, le fichier chiffré n'était PAS stocké
- ✅ Seulement visible sur le réseau (Wireshark)

**APRÈS ma modification :**
- ✅ **OUI !** Le fichier chiffré est maintenant sauvegardé avec l'extension `.encrypted`
- ✅ Vous pouvez le comparer avec la version déchiffrée
- ✅ Parfait pour la démonstration au professeur !

---

## 🎓 Pour la Présentation

**Phrase clé :**

"Regardez, nous avons maintenant DEUX fichiers :
1. `test_secret.txt` - Le fichier déchiffré, lisible
2. `test_secret.txt.encrypted` - Les données brutes chiffrées reçues du réseau

Si vous ouvrez le fichier `.encrypted` avec Notepad, vous verrez que c'est complètement illisible. C'est la preuve que les données étaient chiffrées pendant le transfert !"

---

Bonne présentation ! 🔐🎓
