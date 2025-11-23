"""
Encryption utilities for sensitive data protection
"""
import os
from cryptography.fernet import Fernet
from django.conf import settings


class EncryptionManager:
    """Manager for encrypting and decrypting sensitive data"""
    
    def __init__(self):
        # Get encryption key from settings or environment
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            key = os.environ.get('ENCRYPTION_KEY')
        
        if not key:
            raise ValueError(
                "ENCRYPTION_KEY not found in settings or environment. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
    
    def encrypt(self, value: str) -> str:
        """
        Encrypt a string value
        
        Args:
            value: Plain text to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not value:
            return ''
        
        encrypted = self.cipher.encrypt(value.encode())
        return encrypted.decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            encrypted_value: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted plain text
        """
        if not encrypted_value:
            return ''
        
        try:
            decrypted = self.cipher.decrypt(encrypted_value.encode())
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt value: {e}")
    
    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask email address for display
        
        Example: "user@example.com" -> "u***@e***.com"
        
        Args:
            email: Email address to mask
            
        Returns:
            Masked email address
        """
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        
        # Mask local part
        if len(local) <= 2:
            masked_local = local[0] + '*'
        else:
            masked_local = local[0] + '***'
        
        # Mask domain
        if '.' in domain:
            domain_parts = domain.split('.')
            masked_domain_parts = []
            for part in domain_parts[:-1]:  # All except TLD
                if len(part) <= 2:
                    masked_domain_parts.append(part[0] + '*')
                else:
                    masked_domain_parts.append(part[0] + '***')
            masked_domain_parts.append(domain_parts[-1])  # Keep TLD
            masked_domain = '.'.join(masked_domain_parts)
        else:
            masked_domain = domain[0] + '***'
        
        return f"{masked_local}@{masked_domain}"
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """
        Mask phone number for display
        
        Example: "+79991234567" -> "+7***67"
        
        Args:
            phone: Phone number to mask
            
        Returns:
            Masked phone number
        """
        if not phone:
            return phone
        
        # Remove all non-digit characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        if len(cleaned) < 4:
            return phone
        
        # Show first 2 and last 2 digits
        if cleaned.startswith('+'):
            return f"{cleaned[:2]}***{cleaned[-2:]}"
        else:
            return f"{cleaned[:1]}***{cleaned[-2:]}"
    
    @staticmethod
    def mask_text(text: str, show_chars: int = 2) -> str:
        """
        Mask arbitrary text for display
        
        Args:
            text: Text to mask
            show_chars: Number of characters to show at start and end
            
        Returns:
            Masked text
        """
        if not text or len(text) <= show_chars * 2:
            return '*' * len(text) if text else ''
        
        return f"{text[:show_chars]}***{text[-show_chars:]}"


# Global instance
encryption_manager = EncryptionManager()


# Convenience functions
def encrypt_field(value: str) -> str:
    """Encrypt a field value"""
    return encryption_manager.encrypt(value)


def decrypt_field(encrypted_value: str) -> str:
    """Decrypt a field value"""
    return encryption_manager.decrypt(encrypted_value)


def mask_email(email: str) -> str:
    """Mask email for display"""
    return EncryptionManager.mask_email(email)


def mask_phone(phone: str) -> str:
    """Mask phone for display"""
    return EncryptionManager.mask_phone(phone)


def mask_text(text: str, show_chars: int = 2) -> str:
    """Mask text for display"""
    return EncryptionManager.mask_text(text, show_chars)
