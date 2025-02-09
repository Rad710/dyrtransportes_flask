import os
import hashlib

def hash_password(password: str) -> str:
    """Hash password with SHA-256 and random salt"""
    salt = os.urandom(32)
    
    # Hash password with salt
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    
    # Combine salt and hash with $ separator
    return f"{salt.hex()}${hashed.hex()}"



def verify_password(password: str, stored_password: str) -> bool:
    """Verify password against stored salt$hash"""
    try:
        # Split stored value into salt and hash
        salt_str, hash_str = stored_password.split('$')
        salt = bytes.fromhex(salt_str)
        
        # Hash the provided password with stored salt
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        return hashed.hex() == hash_str
    except:
        return False