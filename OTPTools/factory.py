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
        create_from_dict: Crée une entrée depuis un dictionnaire générique
        create_from_2fas: Crée une entrée depuis le format 2FAS spécifique
        parse_otpauth_url: Parse une URL otpauth:// et crée l'objet OTP
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

    @staticmethod
    def create_from_2fas(service: Dict[str, Any]) -> OTPEntry:
        """
        Crée une entrée OTP à partir d'un service 2FAS.

        Args:
            service: Dictionnaire contenant les données d'un service 2FAS
                     Format attendu:
                     {
                         "secret": "ABCD...",
                         "name": "Service Name",
                         "otp": {
                             "issuer": "Optional Issuer",
                             "account": "Optional Account",
                             "tokenType": "TOTP" ou "HOTP",
                             "digits": "6",
                             "period": "30",
                             "counter": "0",
                             "algorithm": "SHA1"
                         }
                     }

        Returns:
            Instance de TOTPEntry ou HOTPEntry selon le tokenType

        Raises:
            ParseError: Si les données 2FAS sont invalides
            OTPError: Si la création de l'objet OTP échoue

        Example:
            >>> service = {
            ...     "secret": "JBSWY3DPEHPK3PXP",
            ...     "name": "GitHub",
            ...     "otp": {"tokenType": "TOTP", "issuer": "GitHub"}
            ... }
            >>> entry = OTPFactory.create_from_2fas(service)
        """
        if not isinstance(service, dict):
            raise ParseError("Le service doit être un dictionnaire")

        # Extraction du secret (obligatoire à la racine)
        secret = service.get("secret", "")
        if not secret:
            raise ParseError("Le secret est obligatoire dans les données 2FAS")

        # Extraction du nom/issuer (obligatoire)
        name = service.get("name", "")
        if not name:
            raise ParseError("Le nom du service est obligatoire")

        # Extraction des paramètres OTP (dans l'objet "otp")
        otp_data = service.get("otp", {})
        if not isinstance(otp_data, dict):
            otp_data = {}

        # Issuer : priorité à otp.issuer, sinon name
        issuer = otp_data.get("issuer", name)

        # Account : depuis otp.account
        account = otp_data.get("account", "")

        # Type de token (TOTP par défaut)
        token_type = otp_data.get("tokenType", "TOTP").upper()

        # Paramètres avec valeurs par défaut
        digits = int(otp_data.get("digits", OTPConfig.DEFAULT_DIGITS))
        algorithm = otp_data.get("algorithm", OTPConfig.DEFAULT_ALGORITHM).upper()

        try:
            if token_type == "HOTP":
                counter = int(otp_data.get("counter", OTPConfig.DEFAULT_COUNTER))
                return HOTPEntry(
                    issuer=issuer,
                    secret=secret,
                    account=account if account else None,
                    digits=digits,
                    counter=counter,
                    algorithm=algorithm
                )
            else:  # TOTP par défaut
                period = int(otp_data.get("period", OTPConfig.DEFAULT_PERIOD))
                return TOTPEntry(
                    issuer=issuer,
                    secret=secret,
                    account=account if account else None,
                    digits=digits,
                    period=period,
                    algorithm=algorithm
                )
        except (ValueError, TypeError) as e:
            raise ParseError(f"Erreur de conversion des paramètres 2FAS: {e}")
        except OTPError as e:
            raise OTPError(f"Erreur de création OTP depuis 2FAS: {e}")

    @staticmethod
    def parse_otpauth_url(url: str) -> OTPEntry:
        """
        Parse une URL otpauth:// et crée l'objet OTP correspondant.

        Args:
            url: URL au format otpauth://totp/Label?secret=XXX&issuer=YYY
                 Format: otpauth://TYPE/LABEL?PARAMETERS

        Returns:
            Instance de TOTPEntry ou HOTPEntry selon le type

        Raises:
            ParseError: Si l'URL est malformée
            OTPError: Si la création de l'objet OTP échoue

        Example:
            >>> url = "otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub"
            >>> entry = OTPFactory.parse_otpauth_url(url)
        """
        if not url.startswith("otpauth://"):
            raise ParseError("L'URL doit commencer par 'otpauth://'")

        try:
            # Parse l'URL
            parsed = urllib.parse.urlparse(url)

            # Extraction du type (totp/hotp)
            otp_type = parsed.netloc.lower()
            if otp_type not in ["totp", "hotp"]:
                raise ParseError(f"Type OTP non supporté dans l'URL: {otp_type}")

            # Extraction du label (path sans le /)
            label = urllib.parse.unquote(parsed.path.lstrip('/'))
            if not label:
                raise ParseError("Le label est obligatoire dans l'URL otpauth")

            # Parse des paramètres
            params = urllib.parse.parse_qs(parsed.query)

            # Extraction du secret (obligatoire)
            secret = params.get("secret", [None])[0]
            if not secret:
                raise ParseError("Le paramètre 'secret' est obligatoire")

            # Extraction de l'issuer et account depuis le label et les paramètres
            issuer = params.get("issuer", [None])[0]
            account = None

            # Parse du label "issuer:account" ou juste "issuer"
            if ":" in label:
                label_issuer, account = label.split(":", 1)
                if not issuer:
                    issuer = label_issuer
            else:
                if not issuer:
                    issuer = label

            if not issuer:
                raise ParseError("L'issuer est obligatoire")

            # Paramètres optionnels avec valeurs par défaut
            digits = int(params.get("digits", [OTPConfig.DEFAULT_DIGITS])[0])
            algorithm = params.get("algorithm", [OTPConfig.DEFAULT_ALGORITHM])[0].upper()

            # Création selon le type
            if otp_type == "hotp":
                counter = int(params.get("counter", [OTPConfig.DEFAULT_COUNTER])[0])
                return HOTPEntry(
                    issuer=issuer,
                    secret=secret,
                    account=account,
                    digits=digits,
                    counter=counter,
                    algorithm=algorithm
                )
            else:  # totp
                period = int(params.get("period", [OTPConfig.DEFAULT_PERIOD])[0])
                return TOTPEntry(
                    issuer=issuer,
                    secret=secret,
                    account=account,
                    digits=digits,
                    period=period,
                    algorithm=algorithm
                )

        except (ValueError, TypeError) as e:
            raise ParseError(f"Erreur de parse des paramètres URL: {e}")
        except OTPError as e:
            raise OTPError(f"Erreur de création OTP depuis URL: {e}")