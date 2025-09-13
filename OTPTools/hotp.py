"""
Implémentation de HOTP (HMAC-based One-Time Password).
"""

from typing import Optional, Dict, Any

from .base import OTPEntry
from .config import OTPConfig
from .exceptions import InvalidParameterError


class HOTPEntry(OTPEntry):
    """
    Entrée HOTP (HMAC-based One-Time Password).
    
    Génère des codes OTP basés sur un compteur incrémental.
    Le code change uniquement quand le compteur est incrémenté.
    
    Attributes:
        counter: Valeur actuelle du compteur (défaut: 0)
        
    Example:
        >>> hotp = HOTPEntry(
        ...     issuer="Bank",
        ...     secret="JBSWY3DPEHPK3PXP",
        ...     account="12345678",
        ...     counter=42
        ... )
        >>> hotp.increment_counter()
        43
        >>> print(hotp.otpauth)
        otpauth://hotp/Bank:12345678?secret=JBSWY3DPEHPK3PXP&counter=43...
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
        """
        Initialise une entrée HOTP.
        
        Args:
            issuer: Nom du service émetteur
            secret: Secret base32
            account: Identifiant du compte (optionnel)
            digits: Nombre de chiffres du code (6, 7 ou 8)
            counter: Valeur initiale du compteur
            algorithm: Algorithme de hachage (SHA1, SHA256, SHA512)
            
        Raises:
            InvalidParameterError: Si le compteur est négatif
        """
        self.counter = int(counter)
        super().__init__(issuer, secret, account, digits, algorithm)
        self._validate_hotp_params()
    
    def _validate_hotp_params(self) -> None:
        """
        Valide les paramètres spécifiques au HOTP.
        
        Raises:
            InvalidParameterError: Si le compteur est négatif
        """
        if self.counter < 0:
            raise InvalidParameterError(
                "counter", self.counter,
                "Le compteur doit être positif ou nul"
            )
    
    @property
    def token_type(self) -> str:
        """Retourne le type de token: 'hotp'."""
        return "hotp"
    
    def _get_specific_params(self) -> Dict[str, str]:
        """
        Retourne les paramètres spécifiques au HOTP.
        
        Returns:
            Dictionnaire avec le compteur actuel
        """
        return {"counter": str(self.counter)}
    
    def increment_counter(self, steps: int = 1) -> int:
        """
        Incrémente le compteur HOTP.

        Args:
            steps: Nombre d'incrémentations (défaut: 1)
        
        Returns:
            La nouvelle valeur du compteur
            
        Raises:
            InvalidParameterError: Si steps < 1
        """
        if steps < 1:
            raise InvalidParameterError(
                "steps", steps,
                "Le nombre de pas doit être positif"
            )
        
        self.counter += steps
        return self.counter
    
    def sync_counter(self, new_value: int) -> None:
        """
        Synchronise le compteur avec une nouvelle valeur.
        
        Utile pour resynchroniser avec un serveur.
        
        Args:
            new_value: Nouvelle valeur du compteur
            
        Raises:
            InvalidParameterError: Si new_value < 0
        """
        if new_value < 0:
            raise InvalidParameterError(
                "counter", new_value,
                "Le compteur doit être positif ou nul"
            )
        
        self.counter = new_value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convertit l'entrée HOTP en dictionnaire.
        
        Returns:
            Dictionnaire contenant tous les paramètres HOTP
        """
        return {
            "issuer": self.issuer,
            "secret": self.secret,
            "account": self.account,
            "digits": self.digits,
            "counter": self.counter,
            "algorithm": self.algorithm,
            "type": "hotp"
        }
    
    def reset_counter(self) -> None:
        """Réinitialise le compteur à 0."""
        self.counter = 0
