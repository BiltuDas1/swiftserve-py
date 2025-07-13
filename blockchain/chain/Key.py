import os
import re
import base64
import httpx
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.backends import default_backend
from typing import Optional
from environments import Env


class Key:
  """
  Handles loading, saving, and fetching Ed25519 public/private keys
  for blockchain node identification and verification.
  """

  _key_pattern = re.compile(r"^-{5}(END|BEGIN) (PUBLIC|PRIVATE) KEY-{5}$")

  def __init__(self, private_key: Optional[Ed25519PrivateKey] = None):
    self._private_key = private_key
    if self._private_key is not None:
      self._public_key = self._private_key.public_key()
    else:
      self._public_key = None

  def load_key(self, filepath: str) -> bool:
    """
    Load Ed25519 private/public key from a PEM file.

    Args:
      filepath: Path to the PEM file.

    Returns:
      bool: True if key loaded successfully, else False.
    """
    if not Path(filepath).exists():
      return False

    try:
      with open(filepath, "r") as f:
        lines = f.read().strip().splitlines()

      # Check if the header and footer matched with PEM format
      if not (
          self._key_pattern.match(
              lines[0]) and self._key_pattern.match(lines[-1])
      ):
        return False

      if (k := self._key_pattern.match(lines[0])) is not None:
        key_type = k.group(2)

      key_data = base64.b64decode(lines[1])

      if key_type == "PRIVATE":
        loaded_key_priv = serialization.load_der_private_key(
            key_data, password=None, backend=default_backend()
        )

        if not isinstance(loaded_key_priv, Ed25519PrivateKey):
          raise TypeError(
              "Expected Ed25519 private key, got a different type"
          )
        self._private_key = loaded_key_priv
        self._public_key = self._private_key.public_key()
      elif key_type == "PUBLIC":
        loaded_key_pub = serialization.load_der_public_key(
            key_data, backend=default_backend()
        )

        if not isinstance(loaded_key_pub, Ed25519PublicKey):
          raise TypeError(
              "Expected Ed25519 public key, got a different type")
        self._public_key = loaded_key_pub
      else:
        return False

      return True
    except Exception:
      return False

  def save_key(self, filepath: str) -> bool:
    """
    Save private keys to a PEM file.

    Args:
      filepath: Path to save the PEM file.

    Returns:
      bool: True if saved successfully, else False.
    """
    try:
      pem_content = ""

      if self._private_key:
        priv_bytes = self._private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pem_content += "-----BEGIN PRIVATE KEY-----\n"
        pem_content += base64.b64encode(priv_bytes).decode() + "\n"
        pem_content += "-----END PRIVATE KEY-----\n"
      else:
        return False

      with open(filepath, "w") as f:
        f.write(pem_content)

      return True
    except Exception:
      return False

  def save_public_key(self, filepath: str) -> bool:
    """
    Save public keys to a PEM file.

    Args:
      filepath: Path to save the PEM file.

    Returns:
      bool: True if saved successfully, else False.
    """
    try:
      pem_content = ""

      if self._public_key:
        pub_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        pem_content += "-----BEGIN PUBLIC KEY-----\n"
        pem_content += base64.b64encode(pub_bytes).decode() + "\n"
        pem_content += "-----END PUBLIC KEY-----\n"
      else:
        return False

      with open(filepath, "w") as f:
        f.write(pem_content)

      return True
    except Exception:
      return False

  def get_key(self, ip_address: str, port: int):
    """
    Ensure the key for a given IP exists locally; download if missing.

    Args:
      ip_address: Target node IP address.
      port: Port of remote key server.

    Raises:
      Exception: If unable to create directory or download key.
    """
    downloads = Env.get("DOWNLOADS")
    key_dir = os.path.join(downloads, "keys")
    os.makedirs(key_dir, exist_ok=True)
    key_path = os.path.join(key_dir, f"{ip_address}.pem")

    if not self.load_key(key_path):
      try:
        url = f"http://{ip_address}:{port}/key"
        response = httpx.get(url, timeout=5)
        response.raise_for_status()

        with open(key_path, "wb") as f:
          f.write(response.content)

        self.load_key(key_path)
      except Exception as e:
        raise RuntimeError(f"Failed to fetch key: {e}")

  def get_public_key(self) -> Optional[str]:
    """
    Get public key as Base64 string.

    Returns:
      Optional[str]: Public key as Base64 string if exists.
    """
    if not self._public_key:
      return None
    pub_bytes = self._public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return base64.b64encode(pub_bytes).decode()

  def get_public_key_raw(self) -> Optional[Ed25519PublicKey]:
    """
    Get public key object.

    Returns:
      Optional[Ed25519PublicKey]: Public key if exists.
    """
    return self._public_key

  def get_private_key_raw(self) -> Optional[Ed25519PrivateKey]:
    """
    Get private key object.

    Returns:
      Optional[Ed25519PrivateKey]: Private key if exists.
    """
    return self._private_key
