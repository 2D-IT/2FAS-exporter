"""
Exceptions personnalisées pour le module OTP.
"""


class OTPError(Exception):
    """Exception de base pour toutes les erreurs OTP."""
    pass


class InvalidSecretError(OTPError):
    """Exception levée quand le secret OTP est invalide."""
    
    def __init__(self, secret: str, message: str = None):
        self.secret = secret
        if message is None:
            message = f"Secret invalide: '{secret}' n'est pas un base32 valide"
        super().__init__(message)


class InvalidParameterError(OTPError):
    """Exception levée quand un paramètre OTP est invalide."""
    
    def __init__(self, param_name: str, param_value, message: str = None):
        self.param_name = param_name
        self.param_value = param_value
        if message is None:
            message = f"Paramètre invalide: {param_name}='{param_value}'"
        super().__init__(message)


class ParseError(OTPError):
    """Exception levée lors d'erreurs de parsing."""
    
    def __init__(self, source: str, message: str = None):
        self.source = source
        if message is None:
            message = f"Impossible de parser: '{source}'"
        super().__init__(message)


class ExportError(OTPError):
    """Exception levée lors d'erreurs d'export."""
    pass
