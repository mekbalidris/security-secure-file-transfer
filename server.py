import argparse
import logging
import os
import socket
import struct
import sys

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 9000
DEFAULT_OUTPUT_DIR = "received_files"
CHUNK_SIZE = 64 * 1024
HEADER_FMT = ">I"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
NONCE_SIZE = 12
RSA_KEY_FRAME = 512
FILENAME_LEN_FMT = ">H"
FILENAME_LEN_SIZE = struct.calcsize(FILENAME_LEN_FMT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError(
                f"Connection closed after {len(buf)}/{n} bytes."
            )
        buf.extend(chunk)
    return bytes(buf)


def recv_framed(sock: socket.socket) -> bytes:
    raw_len = recv_exact(sock, HEADER_SIZE)
    (frame_len,) = struct.unpack(HEADER_FMT, raw_len)
    return recv_exact(sock, frame_len)


def load_private_key(key_path: str):
    with open(key_path, "rb") as fh:
        return serialization.load_pem_private_key(fh.read(), password=None)


def decrypt_session_key(private_key, ciphertext: bytes) -> bytes:
    return private_key.decrypt(
        ciphertext,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def decrypt_chunk(aesgcm: AESGCM, frame: bytes) -> bytes:
    if len(frame) < NONCE_SIZE:
        raise ValueError("Frame too short to contain a nonce.")
    nonce = frame[:NONCE_SIZE]
    ciphertext_with_tag = frame[NONCE_SIZE:]
    return aesgcm.decrypt(nonce, ciphertext_with_tag, None)


def handle_client(
    conn: socket.socket,
    addr: tuple,
    private_key,
    cert_pem: bytes,
    output_dir: str,
) -> None:
    peer = f"{addr[0]}:{addr[1]}"
    log.info("Accepted connection from %s", peer)

    try:
        cert_len = struct.pack(HEADER_FMT, len(cert_pem))
        conn.sendall(cert_len + cert_pem)
        log.info("[%s] Certificate sent (%d bytes).", peer, len(cert_pem))

        encrypted_key = recv_exact(conn, RSA_KEY_FRAME)
        log.info("[%s] Received encrypted session key.", peer)

        session_key = decrypt_session_key(private_key, encrypted_key)
        if len(session_key) != 32:
            raise ValueError("Session key must be 256 bits (32 bytes).")
        aesgcm = AESGCM(session_key)
        log.info("[%s] Session key decrypted successfully.", peer)

        raw_fn_len = recv_exact(conn, FILENAME_LEN_SIZE)
        (fn_len,) = struct.unpack(FILENAME_LEN_FMT, raw_fn_len)
        filename_bytes = recv_exact(conn, fn_len)
        filename = filename_bytes.decode("utf-8")
        filename = os.path.basename(filename)
        if not filename:
            raise ValueError("Received an empty or invalid filename.")
        out_path = os.path.join(output_dir, filename)
        
        # Créer aussi un fichier pour la version chiffrée (pour la démo)
        encrypted_path = os.path.join(output_dir, filename + ".encrypted")
        
        log.info("[%s] Receiving file: '%s'", peer, filename)

        bytes_written = 0
        encrypted_bytes_written = 0
        
        # Ouvrir les deux fichiers : déchiffré ET chiffré
        with open(out_path, "wb") as out_file, open(encrypted_path, "wb") as enc_file:
            while True:
                frame = recv_framed(conn)
                if len(frame) == 0:
                    break
                
                # Sauvegarder la version CHIFFRÉE (pour la démo)
                enc_file.write(frame)
                encrypted_bytes_written += len(frame)
                
                # Déchiffrer et sauvegarder la version DÉCHIFFRÉE
                plaintext = decrypt_chunk(aesgcm, frame)
                out_file.write(plaintext)
                bytes_written += len(plaintext)

        log.info(
            "[%s] Transfer complete. Saved '%s' (%d bytes).",
            peer,
            out_path,
            bytes_written,
        )
        log.info(
            "[%s] Encrypted version saved: '%s' (%d bytes).",
            peer,
            encrypted_path,
            encrypted_bytes_written,
        )

        conn.sendall(b"OK")

    except ConnectionError as exc:
        log.error("[%s] Network error: %s", peer, exc)
    except Exception as exc:
        log.error("[%s] Unexpected error: %s", peer, exc, exc_info=True)
        try:
            conn.sendall(b"ERR")
        except OSError:
            pass
    finally:
        conn.close()
        log.info("[%s] Connection closed.", peer)


def run_server(
    host: str,
    port: int,
    cert_path: str,
    key_path: str,
    output_dir: str,
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    private_key = load_private_key(key_path)
    with open(cert_path, "rb") as fh:
        cert_pem = fh.read()

    log.info("Certificate loaded from '%s'.", cert_path)
    log.info("Private key   loaded from '%s'.", key_path)
    log.info("Output directory: '%s'.", output_dir)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(5)
        log.info("Server listening on %s:%d – waiting for clients …", host, port)

        try:
            while True:
                conn, addr = srv.accept()
                handle_client(conn, addr, private_key, cert_pem, output_dir)
        except KeyboardInterrupt:
            log.info("Server shutting down (KeyboardInterrupt).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Secure File Transfer – Server"
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cert", default="server.crt")
    parser.add_argument("--key", default="server.key")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    for required in (args.cert, args.key):
        if not os.path.exists(required):
            log.error("Required file not found: '%s'", required)
            log.error("Run 'python generate_certs.py' first.")
            sys.exit(1)

    run_server(args.host, args.port, args.cert, args.key, args.output_dir)


if __name__ == "__main__":
    main()
