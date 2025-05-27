"""
Encryption utilities for Gradit
Handles encryption and decryption of sensitive data
"""

import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get encryption key from environment or generate one
def get_encryption_key():
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # Generate a key if not provided
        salt = b'gradit_salt'  # In production, this should be randomly generated and stored
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b'default-key'))  # In production, use a strong password
    
    return key

# Initialize Fernet cipher with the key
cipher = Fernet(get_encryption_key())

def encrypt_data(data):
    """
    Encrypt data using Fernet symmetric encryption
    
    Args:
        data (str): Data to encrypt
        
    Returns:
        str: Encrypted data as a base64 string
    """
    if not data:
        return ""
    
    # Convert data to bytes if it's a string
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    # Encrypt the data
    encrypted_data = cipher.encrypt(data)
    
    # Return as base64 string
    return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')

def decrypt_data(encrypted_data):
    """
    Decrypt data using Fernet symmetric encryption
    
    Args:
        encrypted_data (str): Encrypted data as a base64 string
        
    Returns:
        str: Decrypted data
    """
    if not encrypted_data:
        return ""
    
    # Convert from base64 string to bytes
    encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
    
    # Decrypt the data
    decrypted_data = cipher.decrypt(encrypted_bytes)
    
    # Return as string
    return decrypted_data.decode('utf-8')
