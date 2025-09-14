"""
Interface de base abstraite pour les processors de backup.

Ce module définit l'interface commune que doivent implémenter
tous les processors spécialisés pour assurer une utilisation uniforme.
"""

from abc import ABC, abstractmethod
from typing import List, Union, Dict, Any
from ..totp import TOTPEntry
from ..hotp import HOTPEntry


class BaseBackupProcessor(ABC):
    """
    Interface commune pour tous les processors de backup.

    Chaque processor spécialisé doit implémenter cette interface
    pour assurer une utilisation uniforme.
    """

    @property
    @abstractmethod
    def supported_formats(self) -> List[str]:
        """Liste des extensions de fichier supportées (ex: ['.2fas', '.zip'])."""
        pass

    @property
    @abstractmethod
    def app_name(self) -> str:
        """Nom de l'application source (ex: '2FAS', 'Google Authenticator')."""
        pass

    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """
        Vérifie si ce processor peut traiter le fichier donné.

        Args:
            file_path: Chemin vers le fichier de backup

        Returns:
            True si le fichier peut être traité
        """
        pass

    @abstractmethod
    def process_backup(self, file_path: str) -> List[Union[TOTPEntry, HOTPEntry]]:
        """
        Traite un fichier de backup et retourne une liste d'entrées OTP.

        Args:
            file_path: Chemin vers le fichier de backup

        Returns:
            Liste d'objets TOTPEntry ou HOTPEntry

        Raises:
            BackupProcessorError: Si le traitement échoue
        """
        pass

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extrait les métadonnées du backup (optionnel).

        Args:
            file_path: Chemin vers le fichier de backup

        Returns:
            Dictionnaire avec les métadonnées (nombre d'entrées, version, etc.)
        """
        return {}