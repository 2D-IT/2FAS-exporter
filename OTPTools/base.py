"""
Classe de base abstraite pour les entrées OTP.
"""

import base64
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from urllib.parse import quote

from .config import OTPConfig
from .exceptions import InvalidSecretError, InvalidParameterError


class OTPEntry(ABC):
    """
    Classe abstraite de base pour les entrées OTP.
    
    Cette classe définit l'interface commune et les méthodes partagées
    pour tous les types de tokens OTP (TOTP et HOTP).
    
    Attributes:
        issuer: L'émetteur du token (ex: "Google", "GitHub")
        secret: Le secret partagé encodé en base32
        account: Le compte utilisateur (email ou username)
        digits: Nombre de chiffres dans le code OTP (6, 7 ou 8)
        algorithm: Algorithme de hachage (SHA1, SHA256, SHA512)
    
    Raises:
        InvalidSecretError: Si le secret n'est pas un base32 valide
        InvalidParameterError: Si un paramètre est invalide
    """
    
    def __init__(
        self,
        issuer: str,
        secret: str,
        account: Optional[str] = None,
        digits: int = OTPConfig.DEFAULT_DIGITS,
        algorithm: str = OTPConfig.DEFAULT_ALGORITHM
    ):
        """
        Initialise une entrée OTP.
        
        Args:
            issuer: Nom du service émetteur
            secret: Secret base32
            account: Identifiant du compte (optionnel)
            digits: Nombre de chiffres du code
            algorithm: Algorithme de hachage
        """
        self.issuer = self._sanitize_string(issuer)
        self.secret = self._normalize_secret(secret)
        self.account = self._sanitize_string(account) if account else None
        self.digits = int(digits)
        self.algorithm = algorithm.upper()
        
        self._validate_common_params()
        self._label = self._generate_label()
    
    @staticmethod
    def _sanitize_string(value: str) -> str:
        """
        Nettoie une chaîne pour l'utilisation dans otpauth.
        
        Args:
            value: Chaîne à nettoyer
            
        Returns:
            Chaîne nettoyée sans caractères problématiques
        """
        if not value:
            return value
        # Supprime les caractères problématiques
        return value.strip().replace(":", "-")
    
    @staticmethod
    def _normalize_secret(secret: str) -> str:
        """
        Normalise le secret en supprimant les espaces et en majuscules.
        
        Args:
            secret: Secret à normaliser
            
        Returns:
            Secret normalisé en base32
        """
        if not secret:
            return secret
        # Supprime espaces et tirets, met en majuscules
        return secret.upper().replace(" ", "").replace("-", "")
    
    def _validate_common_params(self) -> None:
        """
        Valide les paramètres communs à tous les types OTP.
        
        Raises:
            InvalidSecretError: Si le secret est invalide
            InvalidParameterError: Si un paramètre est invalide
        """
        # Validation du secret
        if not self.secret:
            raise InvalidSecretError("", "Le secret ne peut pas être vide")
        
        if not self._is_valid_base32(self.secret):
            raise InvalidSecretError(self.secret)
        
        # Validation de l'issuer
        if not self.issuer:
            raise InvalidParameterError("issuer", self.issuer, 
                                       "L'émetteur (issuer) ne peut pas être vide")
        
        # Validation des digits
        if self.digits not in OTPConfig.VALID_DIGITS:
            raise InvalidParameterError(
                "digits", self.digits,
                f"Le nombre de digits doit être dans {OTPConfig.VALID_DIGITS}"
            )
        
        # Validation de l'algorithme
        if self.algorithm not in OTPConfig.VALID_ALGORITHMS:
            raise InvalidParameterError(
                "algorithm", self.algorithm,                f"L'algorithme doit être dans {OTPConfig.VALID_ALGORITHMS}"
            )
    
    def _is_valid_base32(self, secret: str) -> bool:
        """
        Vérifie si le secret est un base32 valide.
        
        Args:
            secret: Secret à vérifier
            
        Returns:
            True si le secret est valide, False sinon
        """
        # Base32 alphabet (RFC 4648)
        base32_pattern = re.compile(r'^[A-Z2-7]+=*$')
        
        if not base32_pattern.match(secret):
            return False
        
        # Vérification du padding
        try:
            # Ajoute le padding si nécessaire
            padding = (8 - len(secret) % 8) % 8
            padded_secret = secret + '=' * padding
            base64.b32decode(padded_secret)
            return True
        except Exception:
            return False    
    def _generate_label(self) -> str:
        """
        Génère le label pour l'URL otpauth.
        
        Returns:
            Label formaté "issuer:account" ou juste "issuer"
        """
        if self.account:
            return f"{self.issuer}:{self.account}"
        return self.issuer
    
    @property
    def label(self) -> str:
        """Retourne le label formaté."""
        return self._label
    
    @property
    @abstractmethod
    def token_type(self) -> str:
        """Type de token (totp ou hotp)."""
        pass
    
    @abstractmethod
    def _get_specific_params(self) -> Dict[str, str]:
        """Retourne les paramètres spécifiques au type d'OTP."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entrée OTP en dictionnaire."""
        pass    
    @property
    def otpauth(self) -> str:
        """
        Génère l'URL otpauth complète pour créer un QR code.
        
        Format: otpauth://TYPE/LABEL?PARAMS
        
        Returns:
            URL formatée pour génération de QR code
        """
        base_params = {
            "secret": self.secret,
            "issuer": self.issuer,
            "digits": str(self.digits),
            "algorithm": self.algorithm
        }
        
        # Ajouter les paramètres spécifiques au type
        base_params.update(self._get_specific_params())
        
        # Filtrer les paramètres None
        params = {k: v for k, v in base_params.items() if v is not None}
        
        # Construire l'URL avec encodage approprié
        params_str = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
        encoded_label = quote(self.label)
        
        return f"otpauth://{self.token_type}/{encoded_label}?{params_str}"    
    def __str__(self) -> str:
        """Représentation textuelle de l'entrée OTP."""
        return f"{self.__class__.__name__}(issuer='{self.issuer}', account='{self.account}')"
    
    def __repr__(self) -> str:
        """Représentation technique de l'entrée OTP."""
        params = self.to_dict()
        params_str = ", ".join([f"{k}={repr(v)}" for k, v in params.items()])
        return f"{self.__class__.__name__}({params_str})"
    
    def __eq__(self, other) -> bool:
        """Vérifie l'égalité entre deux entrées OTP."""
        if not isinstance(other, OTPEntry):
            return False
        return self.to_dict() == other.to_dict()
