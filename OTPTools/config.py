"""
Configuration par défaut pour le module OTP.
"""

from dataclasses import dataclass


@dataclass
class OTPConfig:
    """
    Configuration et constantes par défaut pour les OTP.
    
    Cette classe contient toutes les valeurs par défaut et les contraintes
    de validation pour les tokens OTP (TOTP et HOTP).
    
    Attributes:
        DEFAULT_DIGITS: Nombre de chiffres par défaut (6)
        DEFAULT_ALGORITHM: Algorithme de hachage par défaut (SHA1)
        DEFAULT_PERIOD: Période par défaut pour TOTP en secondes (30)
        DEFAULT_COUNTER: Compteur initial par défaut pour HOTP (0)
        VALID_DIGITS: Tuple des nombres de chiffres valides
        VALID_ALGORITHMS: Tuple des algorithmes supportés
        MIN_PERIOD: Période minimale pour TOTP en secondes
        MAX_PERIOD: Période maximale pour TOTP en secondes
    """
    
    # Valeurs par défaut
    DEFAULT_DIGITS: int = 6
    DEFAULT_ALGORITHM: str = "SHA1"
    DEFAULT_PERIOD: int = 30
    DEFAULT_COUNTER: int = 0
    
    # Contraintes de validation
    VALID_DIGITS: tuple = (6, 7, 8)
    VALID_ALGORITHMS: tuple = ("SHA1", "SHA256", "SHA512")
    MIN_PERIOD: int = 15
    MAX_PERIOD: int = 300
    
    # Options d'export
    DEFAULT_QR_SIZE: int = 10  # Taille du QR code
    DEFAULT_QR_BORDER: int = 4  # Bordure du QR code
    
    # Formats d'export supportés
    EXPORT_FORMATS: tuple = ("qr", "url", "json", "csv")
