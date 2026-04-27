# Secure File Transfer System

A production-ready, end-to-end encrypted file transfer tool built with Python.
It implements a **Digital Envelope** pattern: RSA-4096 for session-key exchange
and AES-256-GCM for bulk data encryption, authenticated with a self-signed
X.509 certificate.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DIGITAL ENVELOPE                             │
│                                                                     │
│  Client                                   Server                   │
│  ──────                                   ──────                   │
│  1. ◄──────── server.crt (PEM) ─────────────────                  │
│  2. Verify cert public key against trusted copy                     │
│  3. Generate random 32-byte AES session key                         │
│  4. ──── RSA-OAEP-SHA256(session_key) [512 B] ──────►             │
│                                          Decrypt with RSA priv key  │
│  5. ──── [nonce‖AES-GCM-256(chunk)‖tag] ──────────►  (per chunk) │
│  6. ──── empty sentinel frame ─────────────────────►              │
│  7. ◄──────── "OK" ──────────────────────────────────             │
└─────────────────────────────────────────────────────────────────────┘
```

### Why this combination?

| Layer | Algorithm | Purpose |
|-------|-----------|---------|
| Key exchange | RSA-4096 / OAEP-SHA256 | Asymmetric wrap of ephemeral key |
| Bulk encryption | AES-256-GCM | Fast, authenticated encryption |
| Authentication | X.509 / SHA-256 | Server identity (cert pinning) |
| Integrity | GCM authentication tag (128-bit) | Per-chunk tamper detection |

Each chunk uses a **freshly generated 96-bit (12-byte) random nonce**, making
nonce reuse statistically impossible.

---

## File Structure

```
secure_file_transfer/
├── generate_certs.py   # One-time: generate RSA-4096 key + self-signed cert
├── server.py           # Receiving end – decrypt and save files
├── client.py           # Sending end – encrypt and transmit files
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## Quick Start

### Prerequisites

- Python 3.10 or later
- pip

### 1 – Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2 – Generate the server certificate (run once on the server machine)

```bash
python generate_certs.py
```

This creates:
- `server.key` – RSA-4096 private key (**never share this**)
- `server.crt` – Self-signed X.509 certificate (share with clients)

### 3 – Start the server

```bash
python server.py
```

Options:
```
--host        Bind address        (default: 0.0.0.0)
--port        TCP port            (default: 9000)
--output-dir  Save directory      (default: received_files/)
--cert        Certificate path    (default: server.crt)
--key         Private key path    (default: server.key)
```

### 4 – Copy the certificate to the client machine

```bash
# Example using scp
scp user@server-host:/path/to/project/server.crt ./server.crt
```

The client uses this file to **pin** (verify) the server's identity.

### 5 – Send a file from the client

```bash
python client.py --file /path/to/secret_document.pdf --host <server-ip>
```

Options:
```
--file          File to transfer (required)
--host          Server IP/hostname    (default: 127.0.0.1)
--port          TCP port              (default: 9000)
--trusted-cert  Trusted cert path     (default: server.crt)
```

### Expected output

**Server side:**
```
2024-01-15 10:00:01 [INFO] Server listening on 0.0.0.0:9000
2024-01-15 10:00:05 [INFO] Accepted connection from 192.168.1.42:54321
2024-01-15 10:00:05 [INFO] Certificate sent (1842 bytes).
2024-01-15 10:00:05 [INFO] Session key decrypted successfully.
2024-01-15 10:00:05 [INFO] Receiving file: 'secret_document.pdf'
2024-01-15 10:00:06 [INFO] Transfer complete. Saved 'received_files/secret_document.pdf' (2097152 bytes).
```

**Client side:**
```
2024-01-15 10:00:05 [INFO] Connecting to 192.168.1.100:9000 …
2024-01-15 10:00:05 [INFO] Certificate verified. Subject: CN=localhost,O=Secure File Transfer,...
2024-01-15 10:00:05 [INFO] Generated 256-bit AES-GCM session key.
2024-01-15 10:00:05 [INFO] Encrypted session key sent (512 bytes).
2024-01-15 10:00:05 [INFO] Sending file 'secret_document.pdf' …
2024-01-15 10:00:06 [INFO]   … 2097152 / 2097152 bytes (100.0%)
2024-01-15 10:00:06 [INFO] [✓] Transfer confirmed by server. Done.
```

---

## Production Deployment

The Quick Start is intentionally minimal. Before deploying in a production
environment, apply the following hardening measures.

### 1 – Certificate Authority

Replace the self-signed certificate with one issued by a trusted CA:

```bash
# Generate a CSR (Certificate Signing Request)
openssl req -new -newkey rsa:4096 -keyout server.key \
    -out server.csr -sha256 -subj "/CN=yourdomain.com"

# Submit server.csr to your CA (Let's Encrypt, internal PKI, etc.)
# The CA returns: server.crt  (+ optional chain.crt)
```

Update the client to verify against the CA bundle instead of pinning a single
certificate:
```python
# In client.py – replace the public-key-pin check with:
from cryptography.x509 import verification
# ... or delegate to ssl.SSLContext with a CA bundle
```

### 2 – Private key protection

Encrypt the server private key at rest:
```bash
# Re-encrypt with AES-256
openssl rsa -aes256 -in server.key -out server.key.enc
# Update load_private_key() in server.py to pass the password
```
Use a secrets manager (HashiCorp Vault, AWS Secrets Manager) rather than a
file on disk wherever possible.

### 3 – Concurrent connections

The server currently handles clients sequentially. For production use, enable
concurrency via `ThreadingMixIn` or `asyncio`:

```python
import threading

# Inside run_server(), replace handle_client(...) with:
t = threading.Thread(
    target=handle_client,
    args=(conn, addr, private_key, cert_pem, output_dir),
    daemon=True,
)
t.start()
```

### 4 – Firewall / network controls

- Bind `--host` to a specific interface rather than `0.0.0.0`.
- Restrict TCP port 9000 (or your chosen port) to known client IP ranges via
  your firewall / security group rules.
- Run the server as a non-root user with the minimum required filesystem
  permissions.

### 5 – Systemd service (Linux)

```ini
# /etc/systemd/system/secure-file-transfer.service
[Unit]
Description=Secure File Transfer Server
After=network.target

[Service]
Type=simple
User=sft
WorkingDirectory=/opt/secure_file_transfer
ExecStart=/opt/secure_file_transfer/.venv/bin/python server.py \
    --host 0.0.0.0 --port 9000 --output-dir /var/sft/received
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
ProtectSystem=strict
ReadWritePaths=/var/sft/received

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now secure-file-transfer
```

### 6 – Logging and monitoring

- Redirect logs to a SIEM (Splunk, Datadog, etc.) by replacing the
  `logging.basicConfig` handler with a `SysLogHandler` or JSON formatter.
- Alert on repeated certificate verification failures (potential MITM probes).
- Set up disk-usage monitoring on the `--output-dir` directory.

### 7 – Key rotation

Rotate `server.key` and `server.crt` at least annually:
1. Run `generate_certs.py` on the server.
2. Distribute the new `server.crt` to all clients.
3. Restart the server service.

---

## Security Considerations

| Threat | Mitigation |
|--------|-----------|
| Eavesdropping | AES-256-GCM encryption in transit |
| MITM / server impersonation | Certificate public-key pinning on client |
| Data tampering | GCM authentication tag per chunk; `InvalidTag` exception on failure |
| Replay attack | Fresh random nonce per chunk; ephemeral session key per connection |
| Key compromise | RSA-4096 for key encapsulation; rotate cert + key regularly |
| Path traversal (server) | `os.path.basename()` strips all directory components from filenames |

---

## License

MIT License – see your organisation's policy before deploying.
#   s e c u r i t y - s e c u r e - f i l e - t r a n s f e r  
 