"""
Processor spécialisé pour les backups 2FAS Android.

Ce module implémente le traitement des fichiers de backup 2FAS,
supportant différents formats (JSON, ZIP) et structures de données.
"""

import json
import logging
import zipfile
from pathlib import Path
from typing import List, Union, Dict, Any, Optional

from .base import BaseBackupProcessor
from .exceptions import UnsupportedFormatError, CorruptedBackupError
from OTPTools import TOTPEntry, HOTPEntry
from OTPTools.factory import OTPFactory
from OTPTools.exceptions import OTPError, ParseError


logger = logging.getLogger(__name__)


class TwoFASProcessor(BaseBackupProcessor):
    """
    Processor pour les backups 2FAS Android.

    Formats supportés:
    - Fichiers .2fas (JSON)
    - Archives ZIP contenant des fichiers JSON
    - Export direct JSON depuis 2FAS
    """

    @property
    def supported_formats(self) -> List[str]:
        return ['.2fas', '.zip', '.json']

    @property
    def app_name(self) -> str:
        return '2FAS'

    def can_process(self, file_path: str) -> bool:
        """Vérifie si le fichier est un backup 2FAS valide."""
        path = Path(file_path)

        if not path.exists():
            return False

        # Vérification par extension
        if path.suffix.lower() not in self.supported_formats:
            return False

        try:
            # Vérification du contenu pour les JSON
            if path.suffix.lower() in ['.2fas', '.json']:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return self._is_valid_2fas_format(data)

            # Vérification pour les ZIP
            elif path.suffix.lower() == '.zip':
                return self._is_valid_2fas_zip(path)

        except Exception:
            return False

        return False

    def _is_valid_2fas_format(self, data: Dict) -> bool:
        """Vérifie si les données JSON correspondent au format 2FAS."""
        # Vérification basique de la structure
        if isinstance(data, dict):
            if 'services' in data or 'entries' in data:
                return True
            # Peut-être que le dictionnaire représente directement un service
            if 'secret' in data:
                return True

        if isinstance(data, list) and data:
            first_item = data[0]
            if isinstance(first_item, dict) and 'secret' in first_item:
                return True

        return False

    def _is_valid_2fas_zip(self, zip_path: Path) -> bool:
        """Vérifie si l'archive ZIP contient un backup 2FAS."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                # Recherche de fichiers JSON dans l'archive
                json_files = [f for f in zip_file.namelist() if f.endswith('.json')]

                for json_file in json_files:
                    with zip_file.open(json_file) as f:
                        data = json.load(f)
                        if self._is_valid_2fas_format(data):
                            return True
        except Exception:
            return False

        return False

    def process_backup(self, file_path: str) -> List[Union[TOTPEntry, HOTPEntry]]:
        """Traite un backup 2FAS et retourne les entrées OTP."""
        path = Path(file_path)

        if not path.exists() or path.suffix.lower() not in self.supported_formats:
            raise UnsupportedFormatError(self.app_name, file_path)

        try:
            if path.suffix.lower() == '.zip':
                return self._process_zip_backup(path)
            return self._process_json_backup(path)
        except UnsupportedFormatError:
            raise
        except CorruptedBackupError:
            raise
        except Exception as e:
            raise CorruptedBackupError(file_path, str(e))

    def _process_json_backup(self, json_path: Path) -> List[Union[TOTPEntry, HOTPEntry]]:
        """Traite un fichier JSON 2FAS."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not self._is_valid_2fas_format(data):
            raise UnsupportedFormatError(self.app_name, str(json_path))

        return self._extract_entries_from_data(data)

    def _process_zip_backup(self, zip_path: Path) -> List[Union[TOTPEntry, HOTPEntry]]:
        """Traite une archive ZIP 2FAS."""
        entries = []
        found_valid_data = False

        with zipfile.ZipFile(zip_path, 'r') as zip_file:
            json_files = [f for f in zip_file.namelist() if f.endswith('.json')]

            for json_file in json_files:
                with zip_file.open(json_file) as f:
                    data = json.load(f)
                    if self._is_valid_2fas_format(data):
                        found_valid_data = True
                        entries.extend(self._extract_entries_from_data(data))

        if not found_valid_data:
            raise UnsupportedFormatError(self.app_name, str(zip_path))

        return entries

    def _extract_entries_from_data(self, data: Dict) -> List[Union[TOTPEntry, HOTPEntry]]:
        """Extrait les entrées OTP des données JSON 2FAS."""
        entries = []

        # Gestion des différents formats 2FAS
        services = []

        if isinstance(data, dict):
            if 'services' in data:
                services = data['services']
            elif 'entries' in data:
                services = data['entries']
            else:
                # Peut-être que data contient directement les services
                services = [data]
        elif isinstance(data, list):
            services = data

        for service in services:
            entry = self._create_otp_entry_from_service(service)
            if entry:
                entries.append(entry)

        return entries

    def _create_otp_entry_from_service(self, service: Dict) -> Optional[Union[TOTPEntry, HOTPEntry]]:
        """Crée une entrée OTP à partir d'un service 2FAS en utilisant OTPFactory."""
        if not isinstance(service, dict):
            return None

        try:
            # Délègue entièrement la création à OTPFactory
            return OTPFactory.create_from_2fas(service)
        except (OTPError, ParseError) as e:
            service_name = service.get('name', 'service inconnu')
            logger.warning("Erreur lors de la création OTP pour %s: %s", service_name, e)
            return None
        except Exception as e:
            service_name = service.get('name', 'service inconnu')
            logger.exception("Erreur inattendue pour %s: %s", service_name, e)
            return None

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrait les métadonnées du backup 2FAS."""
        try:
            entries = self.process_backup(file_path)

            totp_count = sum(1 for e in entries if isinstance(e, TOTPEntry))
            hotp_count = sum(1 for e in entries if isinstance(e, HOTPEntry))

            return {
                'app_name': self.app_name,
                'total_entries': len(entries),
                'totp_count': totp_count,
                'hotp_count': hotp_count,
                'file_path': file_path,
                'supported_formats': self.supported_formats
            }
        except Exception:
            return {'error': 'Impossible de lire les métadonnées'}
