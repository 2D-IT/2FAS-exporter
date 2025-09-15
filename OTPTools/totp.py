"""
Implémentation de TOTP (Time-based One-Time Password).
"""

from typing import Optional, Dict, Any

from .base import OTPEntry
from .config import OTPConfig
from .exceptions import InvalidParameterError


class TOTPEntry(OTPEntry):
    """
    Entrée TOTP (Time-based One-Time Password).
    
    Génère des codes OTP basés sur l'horloge système avec une période définie.
    Les codes changent automatiquement toutes les X secondes (par défaut 30).
    
    Attributes:
        period: Période de renouvellement en secondes (défaut: 30)
        
    Example:
        >>> totp = TOTPEntry(
        ...     issuer="GitHub",
        ...     secret="JBSWY3DPEHPK3PXP",
        ...     account="user@example.com",
        ...     period=30
        ... )
        >>> print(totp.otpauth)
        otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&...
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
        """
        Initialise une entrée TOTP.
        
        Args:
            issuer: Nom du service émetteur
            secret: Secret base32
            account: Identifiant du compte (optionnel)
            digits: Nombre de chiffres du code (6, 7 ou 8)
            period: Période de renouvellement en secondes
            algorithm: Algorithme de hachage (SHA1, SHA256, SHA512)
            
        Raises:
            InvalidParameterError: Si la période est hors limites
        """
        self.period = int(period)
        super().__init__(issuer, secret, account, digits, algorithm)
        self._validate_totp_params()
    
    def _validate_totp_params(self) -> None:
        """
        Valide les paramètres spécifiques au TOTP.
        
        Raises:
            InvalidParameterError: Si la période est invalide
        """
        if self.period < OTPConfig.MIN_PERIOD:
            raise InvalidParameterError(
                "period", self.period,
                f"La période doit être au minimum {OTPConfig.MIN_PERIOD} secondes"
            )
        
        if self.period > OTPConfig.MAX_PERIOD:
            raise InvalidParameterError(
                "period", self.period,
                f"La période doit être au maximum {OTPConfig.MAX_PERIOD} secondes"
            )
    
    @property
    def token_type(self) -> str:
        """Retourne le type de token: 'totp'."""
        return "totp"
    
    def _get_specific_params(self) -> Dict[str, str]:
        """
        Retourne les paramètres spécifiques au TOTP.

        Returns:
            Dictionnaire avec la période si différente de 30
        """
        # Ne pas inclure la période si c'est la valeur par défaut (30)
        if self.period != OTPConfig.DEFAULT_PERIOD:
            return {"period": str(self.period)}
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entrée TOTP en dictionnaire.
        
        Returns:
            Dictionnaire contenant tous les paramètres TOTP
        """
        return {
            "issuer": self.issuer,
            "secret": self.secret,
            "account": self.account,
            "digits": self.digits,
            "period": self.period,
            "algorithm": self.algorithm,
            "type": "totp"
        }
    
    def is_default_period(self) -> bool:
        """
        Vérifie si la période est celle par défaut.
        
        Returns:
            True si période = 30 secondes
        """
        return self.period == OTPConfig.DEFAULT_PERIOD
