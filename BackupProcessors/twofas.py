"""
Processor spécialisé pour les backups 2FAS Android.

Ce module implémente le traitement des fichiers de backup 2FAS,
supportant différents formats (JSON, ZIP) et structures de données.
"""

import json
import logging
import sys
import zipfile
from pathlib import Path
from typing import List, Union, Dict, Any, Optional, Tuple

from base64 import b64decode
from binascii import Error as BinasciiError
from getpass import getpass
import hashlib

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .base import BaseBackupProcessor
from .exceptions import UnsupportedFormatError, CorruptedBackupError
from OTPTools import TOTPEntry, HOTPEntry
from OTPTools.factory import OTPFactory
from OTPTools.exceptions import OTPError, ParseError


logger = logging.getLogger(__name__)


class TwoFASProcessor(BaseBackupProcessor):
    """Processor pour les backups 2FAS Android.

    Formats supportés:
    - Fichiers .2fas (JSON)
    - Archives ZIP contenant des fichiers JSON
    - Export direct JSON depuis 2FAS
    """

    _PBKDF2_ITERATIONS = 10_000
    _PBKDF2_KEY_LENGTH = 32
    _MAX_PASSWORD_ATTEMPTS = 3

    def __init__(self) -> None:
        self._cached_password: Optional[str] = None

    @property
    def supported_formats(self) -> List[str]:
        return [".2fas", ".zip", ".json"]

    @property
    def app_name(self) -> str:
        return "2FAS"

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
            if path.suffix.lower() in [".2fas", ".json"]:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return self._is_valid_2fas_format(data)

            # Vérification pour les ZIP
            elif path.suffix.lower() == ".zip":
                return self._is_valid_2fas_zip(path)

        except Exception:
            return False

        return False

    def _is_valid_2fas_format(self, data: Dict) -> bool:
        """Vérifie si les données JSON correspondent au format 2FAS."""
        # Vérification basique de la structure
        if isinstance(data, dict):
            if "services" in data or "entries" in data:
                return True
            # Peut-être que le dictionnaire représente directement un service
            if "secret" in data:
                return True

        if isinstance(data, list) and data:
            first_item = data[0]
            if isinstance(first_item, dict) and "secret" in first_item:
                return True

        return False

    def _is_valid_2fas_zip(self, zip_path: Path) -> bool:
        """Vérifie si l'archive ZIP contient un backup 2FAS."""
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                # Recherche de fichiers JSON dans l'archive
                json_files = [f for f in zip_file.namelist() if f.endswith(".json")]

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
            if path.suffix.lower() == ".zip":
                return self._process_zip_backup(path)
            return self._process_json_backup(path)
        except UnsupportedFormatError:
            raise
        except CorruptedBackupError:
            raise
        except Exception as e:
            raise CorruptedBackupError(file_path, str(e))

    def _process_json_backup(
        self, json_path: Path
    ) -> List[Union[TOTPEntry, HOTPEntry]]:
        """Traite un fichier JSON 2FAS."""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not self._is_valid_2fas_format(data):
            raise UnsupportedFormatError(self.app_name, str(json_path))

        data = self._decrypt_backup_if_needed(data, str(json_path))

        return self._extract_entries_from_data(data)

    def _process_zip_backup(self, zip_path: Path) -> List[Union[TOTPEntry, HOTPEntry]]:
        """Traite une archive ZIP 2FAS."""
        entries = []
        found_valid_data = False

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            json_files = [f for f in zip_file.namelist() if f.endswith(".json")]

            for json_file in json_files:
                with zip_file.open(json_file) as f:
                    data = json.load(f)
                    if self._is_valid_2fas_format(data):
                        found_valid_data = True
                        source = f"{zip_path}!/{json_file}"
                        data = self._decrypt_backup_if_needed(data, source)
                        entries.extend(self._extract_entries_from_data(data))

        if not found_valid_data:
            raise UnsupportedFormatError(self.app_name, str(zip_path))

        return entries

    def _extract_entries_from_data(
        self, data: Dict
    ) -> List[Union[TOTPEntry, HOTPEntry]]:
        """Extrait les entrées OTP des données JSON 2FAS."""
        entries = []

        # Gestion des différents formats 2FAS
        services = []

        if isinstance(data, dict):
            if "services" in data:
                services = data["services"]
            elif "entries" in data:
                services = data["entries"]
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

    def _is_encrypted_backup(self, data: Dict[str, Any]) -> bool:
        """Détecte si le backup contient des données chiffrées."""
        if not isinstance(data, dict):
            return False
        encrypted = data.get("servicesEncrypted")
        return isinstance(encrypted, str) and encrypted.strip() != ""

    def _decrypt_backup_if_needed(self, data: Any, source: str) -> Any:
        """Déchiffre un backup 2FAS si nécessaire."""
        if not isinstance(data, dict) or not self._is_encrypted_backup(data):
            return data

        services_encrypted = data.get("servicesEncrypted")
        reference_encrypted = data.get("reference")
        key_encoded = data.get("keyEncoded") or data.get("key")

        password: Optional[str] = self._cached_password
        attempts = 0

        if key_encoded is None and password is None:
            password = self._prompt_for_password(attempts, source)

        while True:
            try:
                decrypted_services = self._decrypt_encrypted_blob(
                    services_encrypted,
                    password=password,
                    key_encoded=key_encoded,
                    source=source,
                    field_name="servicesEncrypted",
                )
                services_payload = json.loads(decrypted_services)

                data_copy = dict(data)
                data_copy["services"] = services_payload
                data_copy.pop("servicesEncrypted", None)

                if reference_encrypted:
                    try:
                        self._decrypt_encrypted_blob(
                            reference_encrypted,
                            password=password,
                            key_encoded=key_encoded,
                            source=source,
                            field_name="reference",
                        )
                    except InvalidTag:
                        logger.debug(
                            "Mot de passe valide pour les services mais échec pour la référence dans %s",
                            source,
                        )

                if key_encoded is None and password is not None:
                    self._cached_password = password

                return data_copy

            except InvalidTag:
                if key_encoded is not None:
                    raise CorruptedBackupError(
                        source, "Clé de déchiffrement invalide ou données corrompues"
                    )

                attempts += 1

                if attempts >= self._MAX_PASSWORD_ATTEMPTS:
                    raise CorruptedBackupError(
                        source, "Mot de passe invalide pour le backup 2FAS"
                    )

                password = self._prompt_for_password(attempts, source)

            except json.JSONDecodeError as exc:
                raise CorruptedBackupError(
                    source, f"Données JSON invalides après déchiffrement: {exc}"
                )

    def _prompt_for_password(self, attempt: int, source: str) -> str:
        """Demande le mot de passe à l'utilisateur en gérant les annulations."""
        if not sys.stdin.isatty():
            raise CorruptedBackupError(
                source,
                "Mot de passe requis pour ce backup chiffré (exécution interactive uniquement).",
            )

        prompt = (
            "Mot de passe du backup 2FAS: "
            if attempt == 0
            else "Mot de passe incorrect, réessayez: "
        )

        try:
            return getpass(prompt)
        except (EOFError, KeyboardInterrupt):
            raise CorruptedBackupError(
                source, "Saisie du mot de passe annulée par l'utilisateur"
            )

    def _decrypt_encrypted_blob(
        self,
        blob: str,
        password: Optional[str],
        key_encoded: Optional[str],
        source: str,
        field_name: str,
    ) -> str:
        """Décrypte une structure `data:salt:iv` du backup 2FAS."""

        data_bytes, salt, iv = self._split_encrypted_blob(blob, source, field_name)
        key = self._resolve_key(password, key_encoded, salt, source)

        try:
            plaintext = AESGCM(key).decrypt(iv, data_bytes, None)
            return plaintext.decode("utf-8")
        except InvalidTag:
            raise
        except Exception as exc:
            raise CorruptedBackupError(
                source, f"Échec du déchiffrement de {field_name}: {exc}"
            )

    def _split_encrypted_blob(
        self,
        blob: str,
        source: str,
        field_name: str,
    ) -> Tuple[bytes, bytes, bytes]:
        """Convertit la structure encodée en base64 en triplet (data, salt, iv)."""

        parts = blob.strip().split(":") if isinstance(blob, str) else []

        if len(parts) != 3:
            raise CorruptedBackupError(
                source, f"Structure de champ chiffré invalide pour '{field_name}'"
            )

        try:
            data_bytes = b64decode(parts[0], validate=True)
            salt = b64decode(parts[1], validate=True)
            iv = b64decode(parts[2], validate=True)
        except (BinasciiError, ValueError) as exc:
            raise CorruptedBackupError(
                source, f"Encodage base64 invalide pour '{field_name}'"
            ) from exc

        if not data_bytes or not iv:
            raise CorruptedBackupError(
                source, f"Données ou IV manquants pour '{field_name}'"
            )

        return data_bytes, salt, iv

    def _resolve_key(
        self,
        password: Optional[str],
        key_encoded: Optional[str],
        salt: bytes,
        source: str,
    ) -> bytes:
        """Construit la clé AES en utilisant le mot de passe ou la clé encodée."""

        if key_encoded:
            try:
                key_bytes = b64decode(key_encoded, validate=True)
            except (BinasciiError, ValueError) as exc:
                raise CorruptedBackupError(
                    source, "Clé encodée invalide dans le backup"
                ) from exc

            if len(key_bytes) not in (16, 24, 32):
                raise CorruptedBackupError(source, "Longueur de clé AES inattendue")

            return key_bytes

        if password is None:
            raise CorruptedBackupError(
                source, "Mot de passe requis pour déchiffrer le backup 2FAS"
            )

        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self._PBKDF2_ITERATIONS,
            dklen=self._PBKDF2_KEY_LENGTH,
        )

    def _create_otp_entry_from_service(
        self, service: Dict
    ) -> Optional[Union[TOTPEntry, HOTPEntry]]:
        """Crée une entrée OTP à partir d'un service 2FAS en utilisant OTPFactory."""
        if not isinstance(service, dict):
            return None

        try:
            # Délègue entièrement la création à OTPFactory
            return OTPFactory.create_from_2fas(service)
        except (OTPError, ParseError) as e:
            service_name = service.get("name", "service inconnu")
            logger.warning(
                "Erreur lors de la création OTP pour %s: %s", service_name, e
            )
            return None
        except Exception as e:
            service_name = service.get("name", "service inconnu")
            logger.exception("Erreur inattendue pour %s: %s", service_name, e)
            return None

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extrait les métadonnées du backup 2FAS."""
        try:
            entries = self.process_backup(file_path)

            totp_count = sum(1 for e in entries if isinstance(e, TOTPEntry))
            hotp_count = sum(1 for e in entries if isinstance(e, HOTPEntry))

            return {
                "app_name": self.app_name,
                "total_entries": len(entries),
                "totp_count": totp_count,
                "hotp_count": hotp_count,
                "file_path": file_path,
                "supported_formats": self.supported_formats,
            }
        except Exception:
            return {"error": "Impossible de lire les métadonnées"}
