"""
Factory pour créer des entrées OTP à partir de différentes sources.
"""

from typing import Dict, Any
import urllib.parse

from .totp import TOTPEntry
from .hotp import HOTPEntry
from .base import OTPEntry
from .config import OTPConfig
from .exceptions import ParseError, OTPError


class OTPFactory:
    """
    Factory pour créer des entrées OTP à partir de différentes sources.
    
    Cette classe fournit des méthodes statiques pour créer des instances
    TOTPEntry ou HOTPEntry depuis différents formats d'entrée.
    
    Methods:
        create_from_dict: Crée une entrée depuis un dictionnaire
        parse_otpauth_url: Parse une URL otpauth://
        create_from_json: Crée depuis un JSON string
        create_from_2fas: Crée depuis le format 2FAS
    """
    
    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> OTPEntry:
        """
        Crée une entrée OTP à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les paramètres OTP
                  Doit contenir au minimum 'issuer' et 'secret'
                  'type' optionnel (défaut: 'totp')
        
        Returns:
            Instance de TOTPEntry ou HOTPEntry selon le type
            
        Raises:
            ParseError: Si le type n'est pas supporté
            KeyError: Si des champs requis sont manquants
            
        Example:
            >>> data = {
            ...     "issuer": "GitHub",
            ...     "secret": "JBSWY3DPEHPK3PXP",
            ...     "type": "totp"
            ... }
            >>> entry = OTPFactory.create_from_dict(data)
        """
        otp_type = data.get("type", "totp").lower()
        
        if otp_type == "totp":
            return TOTPEntry(
                issuer=data["issuer"],
                secret=data["secret"],
                account=data.get("account"),
                digits=data.get("digits", OTPConfig.DEFAULT_DIGITS),
                period=data.get("period", OTPConfig.DEFAULT_PERIOD),
                algorithm=data.get("algorithm", OTPConfig.DEFAULT_ALGORITHM)
            )

        elif otp_type == "hotp":
            return HOTPEntry(
                issuer=data["issuer"],
                secret=data["secret"],
                account=data.get("account"),
                digits=data.get("digits", OTPConfig.DEFAULT_DIGITS),
                counter=data.get("counter", 0),
                algorithm=data.get("algorithm", OTPConfig.DEFAULT_ALGORITHM)
            )

        else:
            raise ParseError(f"Type OTP non supporté: {otp_type}")