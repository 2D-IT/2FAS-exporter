"""
Module BackupProcessors pour traiter différents formats de backup 2FA.

Ce module fournit des processors spécialisés pour chaque application 2FA,
permettant de convertir leurs formats de backup vers des objets OTP standardisés.

Architecture:
    BackupProcessors/
    ├── __init__.py
    ├── base.py           # Interface commune
    ├── twofas.py         # Processor 2FAS
    ├── google_auth.py    # Processor Google Authenticator (à implémenter)
    ├── authy.py          # Processor Authy (à implémenter)
    └── exceptions.py     # Exceptions spécialisées

Usage:
    >>> from BackupProcessors import TwoFASProcessor
    >>> processor = TwoFASProcessor()
    >>> entries = processor.process_backup('backup.2fas')
    >>> for entry in entries:
    ...     print(entry.otpauth)

    >>> # Ou avec auto-détection
    >>> from BackupProcessors import BackupProcessorFactory
    >>> factory = BackupProcessorFactory()
    >>> entries = factory.process_backup('unknown_backup.zip')
"""

from pathlib import Path
from typing import List, Union, Optional

from .exceptions import (
    BackupProcessorError,
    UnsupportedFormatError,
    CorruptedBackupError
)
from .base import BaseBackupProcessor
from .twofas import TwoFASProcessor

# Import des classes OTP du module parent
from ..totp import TOTPEntry
from ..hotp import HOTPEntry


class BackupProcessorFactory:
    """
    Factory pour détecter automatiquement le type de backup et utiliser
    le bon processor.
    """

    def __init__(self):
        # Enregistrement des processors disponibles
        self._processors = [
            TwoFASProcessor(),
            # GoogleAuthProcessor(),  # À implémenter
            # AuthyProcessor(),       # À implémenter
        ]

    def get_processor(self, file_path: str) -> Optional[BaseBackupProcessor]:
        """
        Trouve le processor approprié pour un fichier de backup.

        Args:
            file_path: Chemin vers le fichier de backup

        Returns:
            Processor compatible ou None si aucun trouvé
        """
        for processor in self._processors:
            if processor.can_process(file_path):
                return processor
        return None

    def process_backup(self, file_path: str) -> List[Union[TOTPEntry, HOTPEntry]]:
        """
        Traite automatiquement un backup en détectant son format.

        Args:
            file_path: Chemin vers le fichier de backup

        Returns:
            Liste d'entrées OTP

        Raises:
            UnsupportedFormatError: Si aucun processor ne peut traiter le fichier
        """
        processor = self.get_processor(file_path)

        if processor is None:
            raise UnsupportedFormatError("Format non reconnu", file_path)

        return processor.process_backup(file_path)

    def get_supported_apps(self) -> List[str]:
        """Retourne la liste des applications supportées."""
        return [p.app_name for p in self._processors]


# Exports principaux
__version__ = "1.0.0"
__author__ = "BackupProcessors Team"

__all__ = [
    # Exceptions
    "BackupProcessorError",
    "UnsupportedFormatError",
    "CorruptedBackupError",

    # Interface de base
    "BaseBackupProcessor",

    # Processors spécialisés
    "TwoFASProcessor",

    # Factory
    "BackupProcessorFactory",

    # Classes OTP réexportées pour commodité
    "TOTPEntry",
    "HOTPEntry",
]


# Exemple d'usage intégré au module
def example_usage():
    """Exemple d'utilisation du module BackupProcessors."""
    print("=== BackupProcessors - Exemple d'usage ===")

    # Usage direct avec un processor spécifique
    print("\n1. Usage direct avec TwoFASProcessor:")
    processor = TwoFASProcessor()
    print(f"   Processor: {processor.app_name}")
    print(f"   Formats supportés: {processor.supported_formats}")

    # Usage avec auto-détection
    print("\n2. Usage avec auto-détection:")
    factory = BackupProcessorFactory()
    print(f"   Applications supportées: {factory.get_supported_apps()}")

    print("\n3. Code d'exemple:")
    print("""
    # Pour traiter un backup spécifique
    processor = TwoFASProcessor()
    if processor.can_process("backup.2fas"):
        entries = processor.process_backup("backup.2fas")
        print(f"Trouvé {len(entries)} entrées")

    # Pour auto-détection du format
    factory = BackupProcessorFactory()
    try:
        entries = factory.process_backup("unknown_backup.zip")
        print(f"Auto-détection réussie: {len(entries)} entrées")
    except UnsupportedFormatError:
        print("Format de backup non supporté")
    """)


if __name__ == "__main__":
    example_usage()