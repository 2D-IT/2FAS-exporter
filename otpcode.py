"""
Module de gestion des OTP (One-Time Password) pour TOTP et HOTP.
Supporte la génération d'URLs otpauth pour QR codes.
"""

import base64
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from urllib.parse import quote
from dataclasses import dataclass


@dataclass
class OTPConfig:
    """Configuration par défaut pour les OTP."""
    DEFAULT_DIGITS: int = 6
    DEFAULT_ALGORITHM: str = "SHA1"
    DEFAULT_PERIOD: int = 30
    DEFAULT_COUNTER: int = 0
    VALID_DIGITS: tuple = (6, 7, 8)
    VALID_ALGORITHMS: tuple = ("SHA1", "SHA256", "SHA512")
    MIN_PERIOD: int = 15
    MAX_PERIOD: int = 300


class OTPEntry(ABC):
    """
    Classe abstraite de base pour les entrées OTP.
    
    Attributes:
        issuer: L'émetteur du token (ex: "Google", "GitHub")
        secret: Le secret partagé encodé en base32
        account: Le compte utilisateur (email ou username)
        digits: Nombre de chiffres dans le code OTP (6, 7 ou 8)
        algorithm: Algorithme de hachage (SHA1, SHA256, SHA512)
    """
    
    def __init__(
        self,
        issuer: str,
        secret: str,
        account: Optional[str] = None,
        digits: int = OTPConfig.DEFAULT_DIGITS,
        algorithm: str = OTPConfig.DEFAULT_ALGORITHM
    ):
        self.issuer = self._sanitize_string(issuer)
        self.secret = self._normalize_secret(secret)
        self.account = self._sanitize_string(account) if account else None
        self.digits = int(digits)
        self.algorithm = algorithm.upper()
        
        self._validate_common_params()
        self._label = self._generate_label()
    
    @staticmethod
    def _sanitize_string(value: str) -> str:
        """Nettoie une chaîne pour l'utilisation dans otpauth."""
        if not value:
            return value
        # Supprime les caractères problématiques
        return value.strip().replace(":", "-")
    
    @staticmethod
    def _normalize_secret(secret: str) -> str:
        """Normalise le secret en supprimant les espaces et en majuscules."""
        if not secret:
            return secret
        # Supprime espaces et tirets, met en majuscules
        return secret.upper().replace(" ", "").replace("-", "")
    
    def _validate_common_params(self) -> None:
        """Valide les paramètres communs à tous les types OTP."""
        # Validation du secret
        if not self.secret:
            raise ValueError("Le secret ne peut pas être vide")
        
        if not self._is_valid_base32(self.secret):
            raise ValueError("Le secret doit être encodé en base32 valide")
        
        # Validation de l'issuer
        if not self.issuer:
            raise ValueError("L'émetteur (issuer) ne peut pas être vide")
        
        # Validation des digits
        if self.digits not in OTPConfig.VALID_DIGITS:
            raise ValueError(f"Le nombre de digits doit être dans {OTPConfig.VALID_DIGITS}")
        
        # Validation de l'algorithme
        if self.algorithm not in OTPConfig.VALID_ALGORITHMS:
            raise ValueError(f"L'algorithme doit être dans {OTPConfig.VALID_ALGORITHMS}")
    
    def _is_valid_base32(self, secret: str) -> bool:
        """Vérifie si le secret est un base32 valide."""
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
        """Génère le label pour l'URL otpauth."""
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
        
        Returns:
            URL au format otpauth://TYPE/LABEL?PARAMS
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


class TOTPEntry(OTPEntry):
    """
    Entrée TOTP (Time-based One-Time Password).
    
    Génère des codes OTP basés sur l'horloge système avec une période définie.
    
    Attributes:
        period: Période de renouvellement en secondes (défaut: 30)
    """
    
    def __init__(
        self,
        issuer: str,
        secret: str,
        account: Optional[str] = None,
        digits: int = OTPConfig.DEFAULT_DIGITS,
        period: int = OTPConfig.DEFAULT_PERIOD,
        algorithm: str = OTPConfig.DEFAULT_ALGORITHM
    ):
        self.period = int(period)
        super().__init__(issuer, secret, account, digits, algorithm)
        self._validate_totp_params()
    
    def _validate_totp_params(self) -> None:
        """Valide les paramètres spécifiques au TOTP."""
        if self.period < OTPConfig.MIN_PERIOD:
            raise ValueError(f"La période doit être au minimum {OTPConfig.MIN_PERIOD} secondes")
        
        if self.period > OTPConfig.MAX_PERIOD:
            raise ValueError(f"La période doit être au maximum {OTPConfig.MAX_PERIOD} secondes")
    
    @property
    def token_type(self) -> str:
        return "totp"
    
    def _get_specific_params(self) -> Dict[str, str]:
        """Retourne les paramètres spécifiques au TOTP."""
        # Ne pas inclure la période si c'est la valeur par défaut (30)
        if self.period != OTPConfig.DEFAULT_PERIOD:
            return {"period": str(self.period)}
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entrée TOTP en dictionnaire."""
        return {
            "issuer": self.issuer,
            "secret": self.secret,
            "account": self.account,
            "digits": self.digits,
            "period": self.period,
            "algorithm": self.algorithm,
            "type": "totp"
        }


class HOTPEntry(OTPEntry):
    """
    Entrée HOTP (HMAC-based One-Time Password).
    
    Génère des codes OTP basés sur un compteur incrémental.
    
    Attributes:
        counter: Valeur actuelle du compteur (défaut: 0)
    """
    
    def __init__(
        self,
        issuer: str,
        secret: str,
        account: Optional[str] = None,
        digits: int = OTPConfig.DEFAULT_DIGITS,
        counter: int = OTPConfig.DEFAULT_COUNTER,
        algorithm: str = OTPConfig.DEFAULT_ALGORITHM
    ):
        self.counter = int(counter)
        super().__init__(issuer, secret, account, digits, algorithm)
        self._validate_hotp_params()
    
    def _validate_hotp_params(self) -> None:
        """Valide les paramètres spécifiques au HOTP."""
        if self.counter < 0:
            raise ValueError("Le compteur doit être positif ou nul")
    
    @property
    def token_type(self) -> str:
        return "hotp"
    
    def _get_specific_params(self) -> Dict[str, str]:
        """Retourne les paramètres spécifiques au HOTP."""
        return {"counter": str(self.counter)}
    
    def increment_counter(self, steps: int = 1) -> int:
        """
        Incrémente le compteur HOTP.
        
        Args:
            steps: Nombre d'incrémentations (défaut: 1)
        
        Returns:
            La nouvelle valeur du compteur
        """
        if steps < 1:
            raise ValueError("Le nombre de pas doit être positif")
        
        self.counter += steps
        return self.counter
    
    def sync_counter(self, new_value: int) -> None:
        """
        Synchronise le compteur avec une nouvelle valeur.
        
        Args:
            new_value: Nouvelle valeur du compteur
        """
        if new_value < 0:
            raise ValueError("Le compteur doit être positif ou nul")
        
        self.counter = new_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entrée HOTP en dictionnaire."""
        return {
            "issuer": self.issuer,
            "secret": self.secret,
            "account": self.account,
            "digits": self.digits,
            "counter": self.counter,
            "algorithm": self.algorithm,
            "type": "hotp"
        }


class OTPFactory:
    """Factory pour créer des entrées OTP à partir de différentes sources."""
    
    @staticmethod
    def create_from_dict(data: Dict[str, Any]) -> OTPEntry:
        """
        Crée une entrée OTP à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les paramètres OTP
        
        Returns:
            Instance de TOTPEntry ou HOTPEntry selon le type
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
                counter=data.get("counter", OTPConfig.DEFAULT_COUNTER),
                algorithm=data.get("algorithm", OTPConfig.DEFAULT_ALGORITHM)
            )
        else:
            raise ValueError(f"Type OTP non supporté: {otp_type}")
    
    @staticmethod
    def parse_otpauth_url(url: str) -> OTPEntry:
        """
        Parse une URL otpauth et crée l'entrée OTP correspondante.
        
        Args:
            url: URL au format otpauth://TYPE/LABEL?PARAMS
        
        Returns:
            Instance de TOTPEntry ou HOTPEntry selon l'URL
        """
        # Parsing basique de l'URL otpauth
        if not url.startswith("otpauth://"):
            raise ValueError("L'URL doit commencer par 'otpauth://'")
        
        # Extraction des composants
        import urllib.parse
        
        parsed = urllib.parse.urlparse(url)
        otp_type = parsed.scheme.replace("otpauth", "").lower()
        
        if otp_type not in ["totp", "hotp"]:
            otp_type = parsed.netloc.lower()
        
        # Parse des paramètres
        params = urllib.parse.parse_qs(parsed.query)
        
        # Extraction du label
        path = parsed.path.lstrip("/")
        if ":" in path:
            issuer_from_label, account = path.split(":", 1)
        else:
            issuer_from_label = path
            account = None
        
        # Récupération des paramètres
        issuer = params.get("issuer", [issuer_from_label])[0]
        secret = params.get("secret", [""])[0]
        digits = int(params.get("digits", [OTPConfig.DEFAULT_DIGITS])[0])
        algorithm = params.get("algorithm", [OTPConfig.DEFAULT_ALGORITHM])[0]
        
        if otp_type == "totp":
            period = int(params.get("period", [OTPConfig.DEFAULT_PERIOD])[0])
            return TOTPEntry(issuer, secret, account, digits, period, algorithm)
        else:
            counter = int(params.get("counter", [OTPConfig.DEFAULT_COUNTER])[0])
            return HOTPEntry(issuer, secret, account, digits, counter, algorithm)

