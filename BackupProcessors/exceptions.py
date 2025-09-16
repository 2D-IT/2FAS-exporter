"""
Exceptions spécialisées pour les BackupProcessors.

Ce module définit toutes les exceptions utilisées par les processors
de backup pour une gestion d'erreur cohérente et spécialisée.
"""


class BackupProcessorError(Exception):
    """Exception de base pour les erreurs de traitement de backup."""

    pass


class UnsupportedFormatError(BackupProcessorError):
    """Format de backup non supporté."""

    def __init__(self, format_name: str, file_path: str = None):
        self.format_name = format_name
        self.file_path = file_path
        message = f"Format non supporté: {format_name}"
        if file_path:
            message += f" dans {file_path}"
        super().__init__(message)


class CorruptedBackupError(BackupProcessorError):
    """Backup corrompu ou illisible."""

    def __init__(self, file_path: str, reason: str = None):
        self.file_path = file_path
        self.reason = reason
        message = f"Backup corrompu: {file_path}"
        if reason:
            message += f" - {reason}"
        super().__init__(message)
