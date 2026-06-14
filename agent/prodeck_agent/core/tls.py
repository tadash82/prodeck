"""TLS local: gera um CA próprio e um certificado de servidor para HTTPS.

Equivalente ao mkcert, porém embutido — não exige instalar nada no sistema nem
sudo. O certificado raiz (`rootCA.pem`) é instalado **uma vez** no celular para
que o Chrome confie no agente e ofereça a instalação da PWA em tela cheia (e
para liberar o Wake Lock nativo, que só funciona em contexto seguro).

Os arquivos ficam em `<config>/tls/`. O certificado do servidor é regenerado
quando o conjunto de IPs muda (DHCP, Wi-Fi novo); o CA é estável.
"""

import datetime
import ipaddress
import socket
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

_DAY = datetime.timedelta(days=1)


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _write_key(path: Path, key: rsa.RSAPrivateKey) -> None:
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    path.chmod(0o600)


def _load_or_make_ca(tls_dir: Path) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    cert_path = tls_dir / "rootCA.pem"
    key_path = tls_dir / "rootCA-key.pem"
    if cert_path.exists() and key_path.exists():
        key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
        return key, x509.load_pem_x509_certificate(cert_path.read_bytes())

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ProDeck Local CA")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(_now() - _DAY)
        .not_valid_after(_now() + 3650 * _DAY)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(
                digital_signature=False,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    tls_dir.mkdir(parents=True, exist_ok=True)
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    _write_key(key_path, key)
    return key, cert


def _san(ips: list[str]) -> x509.SubjectAlternativeName:
    names: list[x509.GeneralName] = [x509.DNSName("localhost")]
    try:
        names.append(x509.DNSName(socket.gethostname()))
    except OSError:
        pass
    seen_ips = {"127.0.0.1"}
    names.append(x509.IPAddress(ipaddress.ip_address("127.0.0.1")))
    for ip in ips:
        if ip in seen_ips:
            continue
        try:
            names.append(x509.IPAddress(ipaddress.ip_address(ip)))
            seen_ips.add(ip)
        except ValueError:
            pass
    return x509.SubjectAlternativeName(names)


def _san_keys(san: x509.SubjectAlternativeName) -> set[str]:
    keys: set[str] = set()
    for name in san:
        if isinstance(name, x509.DNSName):
            keys.add(f"dns:{name.value}")
        elif isinstance(name, x509.IPAddress):
            keys.add(f"ip:{name.value}")
    return keys


def ensure_certs(config_root: Path, ips: list[str]) -> tuple[Path, Path, Path]:
    """Garante CA + certificado de servidor cobrindo `ips`.

    Retorna (cert_path, key_path, ca_path). Reusa o certificado existente se ele
    já cobre exatamente os mesmos nomes/IPs; caso contrário, regenera.
    """
    tls_dir = config_root / "tls"
    ca_key, ca_cert = _load_or_make_ca(tls_dir)
    cert_path = tls_dir / "server.pem"
    key_path = tls_dir / "server-key.pem"
    ca_path = tls_dir / "rootCA.pem"
    san = _san(ips)

    if cert_path.exists() and key_path.exists():
        try:
            existing = x509.load_pem_x509_certificate(cert_path.read_bytes())
            current = existing.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
            ).value
            if _san_keys(current) == _san_keys(san):
                return cert_path, key_path, ca_path
        except (ValueError, x509.ExtensionNotFound):
            pass

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ProDeck Agent")]))
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(_now() - _DAY)
        .not_valid_after(_now() + 825 * _DAY)
        .add_extension(san, critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .sign(ca_key, hashes.SHA256())
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    _write_key(key_path, key)
    return cert_path, key_path, ca_path
