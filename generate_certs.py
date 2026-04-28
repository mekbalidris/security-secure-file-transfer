import datetime
import ipaddress
import os
import sys

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


CERT_FILE = "server.crt"
KEY_FILE = "server.key"
VALIDITY_DAYS = 365

SUBJECT_INFO = {
    "country": "US",
    "state": "California",
    "locality": "San Francisco",
    "organization": "Secure File Transfer",
    "common_name": "localhost",
}

SAN_DNS_NAMES = ["localhost"]
SAN_IP_ADDRESSES = ["127.0.0.1"]


def generate_private_key() -> rsa.RSAPrivateKey:
    print("[*] Generating RSA-4096 private key …")
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
    )


def build_certificate(private_key: rsa.RSAPrivateKey) -> x509.Certificate:
    print("[*] Building self-signed X.509 certificate …")

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, SUBJECT_INFO["country"]),
            x509.NameAttribute(
                NameOID.STATE_OR_PROVINCE_NAME, SUBJECT_INFO["state"]
            ),
            x509.NameAttribute(
                NameOID.LOCALITY_NAME, SUBJECT_INFO["locality"]
            ),
            x509.NameAttribute(
                NameOID.ORGANIZATION_NAME, SUBJECT_INFO["organization"]
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME, SUBJECT_INFO["common_name"]
            ),
        ]
    )

    san_entries: list[x509.GeneralName] = [
        x509.DNSName(name) for name in SAN_DNS_NAMES
    ] + [
        x509.IPAddress(ipaddress.ip_address(ip)) for ip in SAN_IP_ADDRESSES
    ]

    now = datetime.datetime.now(datetime.timezone.utc)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=VALIDITY_DAYS))
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )
    return cert


def save_key(private_key: rsa.RSAPrivateKey, path: str) -> None:
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(path, "wb") as fh:
        fh.write(pem)
    os.chmod(path, 0o600)
    print(f"[+] Private key  → {path}  (permissions: 600)")


def save_cert(cert: x509.Certificate, path: str) -> None:
    pem = cert.public_bytes(serialization.Encoding.PEM)
    with open(path, "wb") as fh:
        fh.write(pem)
    print(f"[+] Certificate  → {path}")


def main() -> None:
    for existing in (KEY_FILE, CERT_FILE):
        if os.path.exists(existing):
            print(
                f"[!] '{existing}' already exists. Delete it first to "
                "regenerate.",
                file=sys.stderr,
            )
            sys.exit(1)

    private_key = generate_private_key()
    cert = build_certificate(private_key)
    save_key(private_key, KEY_FILE)
    save_cert(cert, CERT_FILE)

    print("\n[✓] Done.  Copy 'server.crt' to any client machine.")
    print(
        "    Keep 'server.key' secret and never transmit it over the network."
    )


if __name__ == "__main__":
    main()
