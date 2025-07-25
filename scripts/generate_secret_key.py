#!/usr/bin/env python3
"""
Generate a secure secret key for JWT authentication.
This script generates a cryptographically secure random key suitable for use as SECRET_KEY.
"""

import secrets
import string
import base64
import os

def generate_secret_key(length=64):
    """
    Generate a cryptographically secure secret key.
    
    Args:
        length (int): Length of the secret key in bytes (default: 64)
    
    Returns:
        str: Base64 encoded secret key
    """
    # Generate random bytes
    random_bytes = secrets.token_bytes(length)
    
    # Encode to base64 for easy copying
    secret_key = base64.b64encode(random_bytes).decode('utf-8')
    
    return secret_key

def generate_alternative_key(length=50):
    """
    Generate an alternative secret key using alphanumeric characters.
    
    Args:
        length (int): Length of the secret key (default: 50)
    
    Returns:
        str: Random alphanumeric secret key
    """
    # Define character set (alphanumeric + special characters)
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Generate random string
    secret_key = ''.join(secrets.choice(characters) for _ in range(length))
    
    return secret_key

def main():
    """Main function to generate and display secret keys."""
    print("🔐 FIFA Rivalry Tracker - Secret Key Generator")
    print("=" * 50)
    
    # Generate base64 encoded key (recommended)
    print("\n1️⃣ Base64 Encoded Secret Key (Recommended):")
    print("-" * 40)
    base64_key = generate_secret_key(64)
    print(f"SECRET_KEY={base64_key}")
    
    # Generate alternative key
    print("\n2️⃣ Alternative Secret Key (Alphanumeric):")
    print("-" * 40)
    alt_key = generate_alternative_key(50)
    print(f"SECRET_KEY={alt_key}")
    
    # Generate shorter key for testing
    print("\n3️⃣ Short Secret Key (for testing):")
    print("-" * 40)
    short_key = generate_secret_key(32)
    print(f"SECRET_KEY={short_key}")
    
    print("\n" + "=" * 50)
    print("📝 Instructions:")
    print("1. Copy one of the generated keys above")
    print("2. Add it to your .env file as SECRET_KEY=your-key-here")
    print("3. For production, use the Base64 encoded key (option 1)")
    print("4. Keep this key secret and never commit it to version control")
    print("5. Use different keys for development, staging, and production")
    
    print("\n🔒 Security Notes:")
    print("- The Base64 key is 64 bytes (512 bits) of entropy")
    print("- The alternative key uses 50 random characters")
    print("- Both are cryptographically secure for JWT signing")
    print("- Rotate your keys periodically in production")

if __name__ == "__main__":
    main() 