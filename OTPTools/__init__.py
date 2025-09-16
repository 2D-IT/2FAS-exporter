"""
Module OTP (One-Time Password) pour la gestion TOTP et HOTP.

Ce module fournit des classes et utilitaires pour travailler avec des tokens OTP,
incluant la génération d'URLs otpauth pour QR codes et la validation des paramètres.

Classes principales:
    - TOTPEntry: Gestion des tokens basés sur le temps (Time-based OTP)
    - HOTPEntry: Gestion des tokens basés sur compteur (HMAC-based OTP)
    - OTPFactory: Factory pour créer des entrées OTP depuis diverses sources
    - OTPConfig: Configuration et constantes par défaut

Usage typique:
    >>> from otp_module import TOTPEntry
    >>> totp = TOTPEntry(issuer="GitHub", secret="JBSWY3DPEHPK3PXP")
    >>> print(totp.otpauth)
    otpauth://totp/GitHub?secret=JBSWY3DPEHPK3PXP&issuer=GitHub&digits=6&algorithm=SHA1
"""

from .config import OTPConfig
from .base import OTPEntry
from .totp import TOTPEntry
from .hotp import HOTPEntry
from .factory import OTPFactory
from .exceptions import OTPError, InvalidSecretError, InvalidParameterError, ParseError

__version__ = "1.0.0"
__author__ = "Your Name"
__all__ = [
    "OTPConfig",
    "OTPEntry",
    "TOTPEntry",
    "HOTPEntry",
    "OTPFactory",
    "OTPError",
    "InvalidSecretError",
    "InvalidParameterError",
    "ParseError",
]
