import os
import base64
from .path import EntityPath
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

class Crypt:
  def __init__(self, *args, **kwargs):
    """
    Initialize Crypt with SSH keys.

    Args:
      key_name (str): Name of the SSH key files (e.g., 'id_rsa'). Default: 'id_rsa'
      ssh_dir (str): SSH directory path. If None, uses ~/.ssh
      key_path (str): Full path to the key files (without extension). If provided, overrides key_name and ssh_dir.
        Example: '/path/to/mykey' will look for '/path/to/mykey' (private) and '/path/to/mykey.pub' (public)
    """

    self.key_name     = kwargs.pop('key_name', 'id_rsa')
    self.ssh_dir      = EntityPath(kwargs.pop('ssh_dir', '~/.ssh')).expanduser()
    key_path          = kwargs.pop('key_path', None)
    self.key_path     = EntityPath(key_path).expanduser() if key_path else None

    self.private_key  = None
    self.public_key   = None
    self._load_keys()

  def _load_keys(self):
    # Load private key
    if EntityPath(self.private_key_path).exists():
      with open(self.private_key_path, 'rb') as f:
        key_data = f.read()
        try:
          # Try OpenSSH format first
          self.private_key = serialization.load_ssh_private_key(
            key_data, password=None, backend=default_backend()
          )
        except Exception:
          # Fallback to PEM format
          self.private_key = serialization.load_pem_private_key(
            key_data, password=None, backend=default_backend()
          )
    # Load public key
    if EntityPath(self.public_key_path).exists():
      with open(self.public_key_path, 'rb') as f:
        pub_data = f.read()
        try:
          self.public_key = serialization.load_ssh_public_key(pub_data, backend=default_backend())
        except Exception:
          self.public_key = serialization.load_pem_public_key(pub_data, backend=default_backend())

  def encrypt(self, *args, **kwargs):
    data      = kwargs.pop('data', args[0] if len(args) > 0 else None)
    as_string = kwargs.pop('as_string', args[1] if len(args) > 1 else True)
    out_file  = kwargs.pop('out_file', args[2] if len(args) > 2 else None)

    if not self.public_key:
      raise ValueError('Public key not loaded')
    if isinstance(data, str):
      data = data.encode('utf-8')
    encrypted = self.public_key.encrypt(
      data,
      padding.OAEP(
        mgf       = padding.MGF1(algorithm=hashes.SHA256()),
        algorithm = hashes.SHA256(),
        label     = None
      )
    )
    if as_string:
      # Encode as URL-safe base64 and add SSK prefix (SSH Key encryption)
      encoded = base64.urlsafe_b64encode(encrypted).decode('utf-8').rstrip('=')
      result = f'SSK{encoded}'
    else:
      result = encrypted

    # Write to file if out_file is specified
    if out_file:
      out_path = EntityPath(out_file)
      if as_string:
        out_path.write_text(result, mode='w')
      else:
        out_path.write_bytes(result)
      return out_path

    return result

  enc = encrypt

  def decrypt(self, *args, **kwargs):
    encrypted_data = kwargs.pop('encrypted_data', args[0] if len(args) > 0 else None)
    out_file       = kwargs.pop('out_file', args[1] if len(args) > 1 else None)

    if not self.private_key:
      raise ValueError('Private key not loaded')

    # Check if it's a string with SSK prefix
    if isinstance(encrypted_data, str):
      if encrypted_data.startswith('SSK'):
        encrypted_data = encrypted_data[3:]  # Remove prefix
        # Add back padding if needed
        padding_needed = (4 - len(encrypted_data) % 4) % 4
        encrypted_data += '=' * padding_needed
        encrypted_data = base64.urlsafe_b64decode(encrypted_data)
      else:
        raise ValueError('Invalid encrypted string format')

    decrypted = self.private_key.decrypt(
      encrypted_data,
      padding.OAEP(
        mgf       = padding.MGF1(algorithm=hashes.SHA256()),
        algorithm = hashes.SHA256(),
        label     = None
      )
    )
    result = decrypted.decode('utf-8')

    # Write to file if out_file is specified
    if out_file:
      out_path = EntityPath(out_file)
      out_path.write_text(result, mode='w')
      return out_path

    return result

  dec = decrypt

  def crypt(self, data):
    """Auto encrypt/decrypt based on SSK prefix. Encrypts if no prefix, decrypts if prefix present."""
    if isinstance(data, str) and data.startswith('SSK'):
      # Already encrypted, decrypt it
      return self.decrypt(data)
    else:
      # Not encrypted, encrypt it
      return self.encrypt(data)


class CryptData:
  """Static class for quick encryption/decryption of strings or files."""

  @staticmethod
  def encrypt(*args, **kwargs):
    """Crypt.encrypt Wrapper Method"""
    return Crypt(*args, **kwargs).encrypt(**kwargs)

  enc = encrypt

  @staticmethod
  def decrypt(*args, **kwargs):
    """Crypt.decrypt Wrapper Method"""
    return Crypt(*args, **kwargs).decrypt(**kwargs)

  dec = decrypt


class CryptGPG:
  """GPG-based encryption for encrypting data to specific recipients."""

  def __init__(self, *args, **kwargs):
    """
    Initialize CryptGPG.

    Args:
      gpg_home (str): GPG home directory. If None, uses default (~/.gnupg)
      **kwargs: Additional parameters for future extensibility
    """
    import gnupg

    gpg_home = kwargs.pop('gpg_home', None)

    if gpg_home:
      self.gpg = gnupg.GPG(gnupghome=str(EntityPath(gpg_home).expanduser()))
    else:
      self.gpg = gnupg.GPG()

  def encrypt(self, *args, **kwargs):
    """
    Encrypt data for specific recipient(s).

    Args:
      data: String or bytes to encrypt (first positional arg or 'data' kwarg)
      recipient: Email/Key ID of recipient (second positional arg or 'recipient' kwarg)
                 Can be a single string or list of recipients for multiple recipients
      as_string (bool): Return as string (default: True)
      out_file (str): Output file path (optional)
      armor (bool): ASCII-armored output (default: True)
      sign (str): Sign with this key ID (optional)
      **kwargs: Additional GPG options

    Returns:
      Encrypted string (GPG format) or file path
    """
    data      = kwargs.pop('data', args[0] if len(args) > 0 else None)
    recipient = kwargs.pop('recipient', args[1] if len(args) > 1 else None)
    as_string = kwargs.pop('as_string', args[2] if len(args) > 2 else True)
    out_file  = kwargs.pop('out_file', args[3] if len(args) > 3 else None)
    armor     = kwargs.pop('armor', True)
    sign      = kwargs.pop('sign', None)

    if not recipient:
      raise ValueError('Recipient required for GPG encryption')

    if isinstance(data, bytes):
      data = data.decode('utf-8')

    # Encrypt
    encrypted = self.gpg.encrypt(
      data,
      recipients=recipient if isinstance(recipient, list) else [recipient],
      armor=armor,
      sign=sign,
      **kwargs
    )

    if not encrypted.ok:
      raise ValueError(f'GPG encryption failed: {encrypted.status}')

    result = str(encrypted) if as_string else bytes(str(encrypted), 'utf-8')

    # Write to file if out_file is specified
    if out_file:
      out_path = EntityPath(out_file)
      if as_string:
        out_path.write_text(result, mode='w')
      else:
        out_path.write_bytes(result)
      return out_path

    return result

  enc = encrypt

  def decrypt(self, *args, **kwargs):
    """
    Decrypt GPG-encrypted data.

    Args:
      encrypted_data: GPG-encrypted string (first positional arg or 'encrypted_data' kwarg)
      passphrase (str): Passphrase for private key (if needed)
      out_file (str): Output file path (optional)
      **kwargs: Additional GPG options

    Returns:
      Decrypted string or file path
    """
    encrypted_data = kwargs.pop('encrypted_data', args[0] if len(args) > 0 else None)
    passphrase = kwargs.pop('passphrase', args[1] if len(args) > 1 else None)
    out_file = kwargs.pop('out_file', args[2] if len(args) > 2 else None)

    if isinstance(encrypted_data, bytes):
      encrypted_data = encrypted_data.decode('utf-8')

    # Decrypt
    decrypted = self.gpg.decrypt(encrypted_data, passphrase=passphrase, **kwargs)

    if not decrypted.ok:
      raise ValueError(f'GPG decryption failed: {decrypted.status}')

    result = str(decrypted)

    # Write to file if out_file is specified
    if out_file:
      out_path = EntityPath(out_file)
      out_path.write_text(result, mode='w')
      return out_path

    return result

  dec = decrypt

  def list_keys(self, secret=False):
    """
    List available GPG keys.

    Args:
      secret (bool): If True, list private keys. If False, list public keys.

    Returns:
      List of key dictionaries
    """
    return self.gpg.list_keys(secret=secret)

  def import_key(self, key_data):
    """
    Import a GPG public key.

    Args:
      key_data (str): Armor-encoded public key or file path

    Returns:
      Import result
    """
    # Check if it's a file path
    key_path = EntityPath(key_data)
    if key_path.exists():
      key_data = key_path.read_text()

    result = self.gpg.import_keys(key_data)
    return result

  def export_key(self, keyid, secret=False):
    """
    Export a GPG key.

    Args:
      keyid (str): Key ID or email to export
      secret (bool): Export private key (default: False, exports public key)

    Returns:
      Armor-encoded key string
    """
    return self.gpg.export_keys(keyid, secret=secret)


class CryptGPGData:
  """Static class for quick GPG encryption/decryption."""

  @staticmethod
  def encrypt(*args, **kwargs):
    """
    Encrypt data for specific recipient(s) using GPG.

    Args:
      data: String or bytes to encrypt
      recipient: Email/Key ID of recipient (required)
      *args, **kwargs: Additional arguments passed to CryptGPG

    Returns:
      GPG-encrypted string or file path
    """
    data = kwargs.pop('data', args[0] if len(args) > 0 else None)
    recipient = kwargs.pop('recipient', args[1] if len(args) > 1 else None)
    return CryptGPG(**kwargs).encrypt(data, recipient=recipient, **kwargs)

  enc = encrypt

  @staticmethod
  def decrypt(*args, **kwargs):
    """
    Decrypt GPG-encrypted data.

    Args:
      encrypted_data: GPG-encrypted string
      *args, **kwargs: Additional arguments passed to CryptGPG

    Returns:
      Decrypted string or file path
    """
    encrypted_data = kwargs.pop('encrypted_data', args[0] if len(args) > 0 else None)
    return CryptGPG(**kwargs).decrypt(encrypted_data, **kwargs)

  dec = decrypt


class CryptPass:
  """Password-based symmetric encryption using AES-256."""

  def __init__(self, *args, **kwargs):
    """
    Initialize CryptPass.

    Args:
      password (str): Password for encryption/decryption
      **kwargs: Additional parameters for future extensibility
    """
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    self.password = kwargs.pop('password', args[0] if len(args) > 0 else None)
    self.extra_kwargs = kwargs

    if not self.password:
      raise ValueError('Password required for encryption/decryption')

  def _derive_key(self, salt):
    """Derive a key from password using PBKDF2."""
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    kdf = PBKDF2HMAC(
      algorithm=hashes.SHA256(),
      length=32,  # 256 bits for AES-256
      salt=salt,
      iterations=100000,
      backend=default_backend()
    )
    return kdf.derive(self.password.encode('utf-8') if isinstance(self.password, str) else self.password)

  def encrypt(self, *args, **kwargs):
    """
    Encrypt data using password.

    Args:
      data: String or bytes to encrypt (first positional arg or 'data' kwarg)
      as_string (bool): Return as string (default: True)
      out_file (str): Output file path (optional)
      **kwargs: Additional parameters

    Returns:
      Encrypted string with SPS prefix (Symmetric Password) or file path
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    data = kwargs.pop('data', args[0] if len(args) > 0 else None)
    as_string = kwargs.pop('as_string', args[1] if len(args) > 1 else True)
    out_file = kwargs.pop('out_file', args[2] if len(args) > 2 else None)

    if isinstance(data, str):
      data = data.encode('utf-8')

    # Generate random salt and IV
    salt = os.urandom(16)
    iv = os.urandom(16)

    # Derive key from password
    key = self._derive_key(salt)

    # Encrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Add PKCS7 padding
    pad_length = 16 - (len(data) % 16)
    padded_data = data + bytes([pad_length] * pad_length)

    encrypted = encryptor.update(padded_data) + encryptor.finalize()

    # Combine salt + iv + encrypted data
    combined = salt + iv + encrypted

    if as_string:
      # Encode as URL-safe base64 and add SPS prefix (Symmetric Password encryption)
      encoded = base64.urlsafe_b64encode(combined).decode('utf-8').rstrip('=')
      result = f'SPS{encoded}'
    else:
      result = combined

    # Write to file if out_file is specified
    if out_file:
      out_path = EntityPath(out_file)
      if as_string:
        out_path.write_text(result, mode='w')
      else:
        out_path.write_bytes(result)
      return out_path

    return result

  enc = encrypt

  def decrypt(self, *args, **kwargs):
    """
    Decrypt password-encrypted data.

    Args:
      encrypted_data: SPS-prefixed encrypted string (first positional arg or 'encrypted_data' kwarg)
      out_file (str): Output file path (optional)
      **kwargs: Additional parameters

    Returns:
      Decrypted string or file path
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    encrypted_data = kwargs.pop('encrypted_data', args[0] if len(args) > 0 else None)
    out_file = kwargs.pop('out_file', args[1] if len(args) > 1 else None)

    # Handle SPS prefix
    if isinstance(encrypted_data, str):
      if encrypted_data.startswith('SPS'):
        encrypted_data = encrypted_data[3:]  # Remove prefix
        # Add back padding if needed
        padding_needed = (4 - len(encrypted_data) % 4) % 4
        encrypted_data += '=' * padding_needed
        encrypted_data = base64.urlsafe_b64decode(encrypted_data)
      else:
        raise ValueError('Invalid encrypted string format (expected SPS prefix)')

    # Extract salt, IV, and encrypted data
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    encrypted = encrypted_data[32:]

    # Derive key from password
    key = self._derive_key(salt)

    # Decrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()

    # Remove PKCS7 padding
    pad_length = decrypted_padded[-1]
    decrypted = decrypted_padded[:-pad_length]

    result = decrypted.decode('utf-8')

    # Write to file if out_file is specified
    if out_file:
      out_path = EntityPath(out_file)
      out_path.write_text(result, mode='w')
      return out_path

    return result

  dec = decrypt


class CryptPassData:
  """Static class for quick password-based encryption/decryption."""

  @staticmethod
  def encrypt(*args, **kwargs):
    """
    Encrypt data using password.

    Args:
      data: String or bytes to encrypt
      password: Password for encryption (required)
      *args, **kwargs: Additional arguments passed to CryptPass

    Returns:
      SPS-prefixed encrypted string or file path
    """
    data = kwargs.pop('data', args[0] if len(args) > 0 else None)
    password = kwargs.pop('password', args[1] if len(args) > 1 else None)
    return CryptPass(password=password, **kwargs).encrypt(data, **kwargs)

  enc = encrypt

  @staticmethod
  def decrypt(*args, **kwargs):
    """
    Decrypt password-encrypted data.

    Args:
      encrypted_data: SPS-prefixed encrypted string
      password: Password for decryption (required)
      *args, **kwargs: Additional arguments passed to CryptPass

    Returns:
      Decrypted string or file path
    """
    encrypted_data = kwargs.pop('encrypted_data', args[0] if len(args) > 0 else None)
    password = kwargs.pop('password', args[1] if len(args) > 1 else None)
    return CryptPass(password=password, **kwargs).decrypt(encrypted_data, **kwargs)

  dec = decrypt
