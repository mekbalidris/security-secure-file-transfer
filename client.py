import argparse
import logging
import os
import struct
import socket
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9000
CHUNK_SIZE = 64 * 1024
HEADER_FMT = ">I"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
NONCE_SIZE = 12
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


def send_framed(sock: socket.socket, payload: bytes) -> None:
    header = struct.pack(HEADER_FMT, len(payload))
    sock.sendall(header + payload)


def receive_and_verify_cert(
    sock: socket.socket, trusted_cert_path: str
) -> x509.Certificate:
    raw_len = recv_exact(sock, HEADER_SIZE)
    (cert_len,) = struct.unpack(HEADER_FMT, raw_len)
    cert_pem = recv_exact(sock, cert_len)

    received_cert = x509.load_pem_x509_certificate(cert_pem)

    with open(trusted_cert_path, "rb") as fh:
        trusted_cert = x509.load_pem_x509_certificate(fh.read())

    received_pub = received_cert.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    trusted_pub = trusted_cert.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    if received_pub != trusted_pub:
        raise RuntimeError(
            "Certificate verification FAILED: public key mismatch. "
            "Possible MITM attack – aborting."
        )

    log.info(
        "Certificate verified. Subject: %s",
        received_cert.subject.rfc4514_string(),
    )
    return received_cert


def generate_session_key() -> bytes:
    return os.urandom(32)


def encrypt_session_key(cert: x509.Certificate, session_key: bytes) -> bytes:
    pub_key = cert.public_key()
    return pub_key.encrypt(
        session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def encrypt_chunk(aesgcm: AESGCM, plaintext: bytes) -> bytes:
    nonce = os.urandom(NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def send_file(
    sock: socket.socket,
    file_path: str,
    aesgcm: AESGCM,
) -> None:
    filename = os.path.basename(file_path)
    filename_bytes = filename.encode("utf-8")
    if len(filename_bytes) > 0xFFFF:
        raise ValueError("Filename is too long (max 65535 bytes).")

    sock.sendall(struct.pack(FILENAME_LEN_FMT, len(filename_bytes)))
    sock.sendall(filename_bytes)
    log.info("Sending file '%s' …", filename)

    file_size = os.path.getsize(file_path)
    bytes_sent = 0

    with open(file_path, "rb") as fh:
        while True:
            plaintext = fh.read(CHUNK_SIZE)
            if not plaintext:
                break
            frame = encrypt_chunk(aesgcm, plaintext)
            send_framed(sock, frame)
            bytes_sent += len(plaintext)
            progress = (bytes_sent / file_size * 100) if file_size else 100
            log.info("  … %d / %d bytes  (%.1f%%)", bytes_sent, file_size, progress)

    send_framed(sock, b"")
    log.info("All chunks sent.")


def run_client(
    host: str,
    port: int,
    file_path: str,
    trusted_cert_path: str,
) -> None:
    if not os.path.isfile(file_path):
        log.error("File not found: '%s'", file_path)
        sys.exit(1)

    if not os.path.isfile(trusted_cert_path):
        log.error("Trusted certificate not found: '%s'", trusted_cert_path)
        log.error(
            "Copy 'server.crt' from the server to this machine first."
        )
        sys.exit(1)

    log.info("Connecting to %s:%d …", host, port)

    with socket.create_connection((host, port), timeout=30) as sock:
        sock.settimeout(60)

        try:
            cert = receive_and_verify_cert(sock, trusted_cert_path)

            session_key = generate_session_key()
            aesgcm = AESGCM(session_key)
            log.info("Generated 256-bit AES-GCM session key.")

            encrypted_key = encrypt_session_key(cert, session_key)
            sock.sendall(encrypted_key)
            log.info("Encrypted session key sent (%d bytes).", len(encrypted_key))

            send_file(sock, file_path, aesgcm)

            ack = recv_exact(sock, 2)
            if ack == b"OK":
                log.info("[✓] Transfer confirmed by server. Done.")
            else:
                log.error("[✗] Server returned error: %s", ack)
                sys.exit(1)

        except RuntimeError as exc:
            log.error("Security error: %s", exc)
            sys.exit(1)
        except ConnectionError as exc:
            log.error("Network error: %s", exc)
            sys.exit(1)
        except TimeoutError:
            log.error("Connection timed out.")
            sys.exit(1)
        except Exception as exc:
            log.error("Unexpected error: %s", exc, exc_info=True)
            sys.exit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Secure File Transfer – Client"
    )
    parser.add_argument(
        "--file", required=True, help="Path to the file to transfer"
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--trusted-cert",
        default="server.crt",
        help="Path to the server's trusted certificate (PEM)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_client(args.host, args.port, args.file, args.trusted_cert)


if __name__ == "__main__":
    main()
