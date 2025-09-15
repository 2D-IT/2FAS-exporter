# OTP Exporter — Contexte de Travail (uv)

Ce document résume l’architecture, les conventions d’exécution et les points
importants du projet. Pour les procédures détaillées (installation, offline,
lockfile), voir `AGENTS.md`. Les commandes ci‑dessous utilisent exclusivement `uv`.

## Objectif
- Exporter des QR codes OTP (PNG) à partir d’une sauvegarde JSON de l’app 2FAS.

## Architecture du dépôt

### Structure globale
```
└── 2FAS-exporter/
    ├── main.py                     # CLI principal
    ├── twofas_lib.py              # Logique de génération QR
    ├── pyproject.toml             # Configuration projet
    ├── requirements.txt           # Dépendances figées
    ├── AGENTS.md                  # Procédures opérationnelles
    │
    ├── OTPTools/                  # Module OTP core
    │   ├── __init__.py           # Exports principaux
    │   ├── base.py               # Classe abstraite OTPEntry
    │   ├── config.py             # Configuration par défaut
    │   ├── exceptions.py         # Exceptions OTP
    │   ├── factory.py            # Factory pour créer des OTP
    │   ├── hotp.py               # Implémentation HOTP
    │   └── totp.py               # Implémentation TOTP
    │
    ├── BackupProcessors/         # Module traitement de backups
    │   ├── __init__.py          # Factory + exports
    │   ├── base.py              # Interface BaseBackupProcessor
    │   ├── exceptions.py        # Exceptions spécialisées
    │   └── twofas.py            # Processor 2FAS
    │
    ├── tools/                    # Utilitaires dev
    │   ├── __init__.py
    │   └── clean_pycache.py     # CLI clean des __pycache__
    │
    ├── [exemple/]                # Dossier de test (utilisateur)
    │   └── *.2fas               # Fichiers backup sample
    │
    └── [exports/]               # QR codes générés (utilisateur)
        └── *.png                # Fichiers de sortie
```

### Modules principaux

#### Script de base
- `main.py`: CLI principale. Prend `backup_file` (JSON 2FAS) et `destination_folder`.
  Crée le dossier si besoin, gère quelques erreurs, et appelle `generate_qr_codes`.
- `twofas_lib.py`: logique de génération; utilise `OTPTools` (`TOTPEntry`/`HOTPEntry`).
  `generate_qr_codes(file_path, output_dir)` crée le dossier de sortie, itère
  `data["services"]` et écrit des PNG avec noms sûrs via `sanitize_filename()`
  et `generate_safe_filename()`.

#### Utilitaires dev
- `tools/clean_pycache.py`: CLI `clean-pycache` pour supprimer les dossiers `__pycache__` (et optionnellement `.pyc/.pyo`).

#### OTPTools (~705 lignes)
Module core pour la gestion des tokens OTP avec classes standardisées et validation.

#### BackupProcessors (~472 lignes)
Base pour traiter différents formats de backup 2FA et les convertir vers des
objets OTP standardisés.
- Rôle: auto‑détection et traitement multi‑applications
- Patterns: Strategy + Factory pour extensibilité
- Applications: 2FAS (complet), Google Auth/Authy (stubs à implémenter)
- Formats: `.2fas`, `.zip`, `.json` (extensible)
Note: la CLI actuelle lit un JSON 2FAS; l’intégration d’autres formats passera
par ce module ultérieurement.

#### Configuration
- `pyproject.toml`: métadonnées projet (nom: `otp-exporter`), dépendances, scripts console `otp-export` et `clean-pycache`. Packaging via `setuptools` incluant `OTPTools`, `BackupProcessors` et `tools`.
- `requirements.txt`: versions figées pour la prod (Pillow 11.3.0, qrcode 8.2) et fallback si `pyproject.toml` absent.
- `AGENTS.md`: règles et procédures opérationnelles (uv, installation, sync, offline, fallback, outils MCP).
- Dossiers utilisateur: l'utilisateur définit ses propres dossiers pour les backups et la sortie.

## Flux haut niveau
- Entrée: fichier JSON de sauvegarde 2FAS.
- Traitement: construction d'URL otpauth pour chaque service, génération PNG via `qrcode`/Pillow.
- Sortie: fichiers PNG avec noms assainis (format `{issuer_safe}_{account_safe}.png`) dans le dossier cible.

## Hypothèses sur le JSON 2FAS
- Clé racine: `services` (liste).
- Chaque service contient `secret` et un objet `otp` avec au minimum `tokenType`; champs optionnels: `issuer` (fallback `name`), `digits` (def 6), `period` (def 30), `algorithm` (def SHA1), `account` (def "").

## Points d'attention
- Nommage des fichiers: RÉSOLU - implémentation complète de sanitization avec `sanitize_filename()` pour gérer caractères interdits, noms réservés Windows, accents, espaces, et limitations de longueur.
- Erreurs gérées sommairement; envisager logs plus détaillés et options CLI (ex: verbose, format alternative).

## Évolution architecturale

### Refactoring modulaire (Sept 2024)
- **Extraction OTPTools**: Création du module core OTP standardisé (~705 lignes)
  - Classes `TOTPEntry`/`HOTPEntry` avec validation robuste
  - Factory pattern pour création d'entrées depuis diverses sources
  - Gestion d'exceptions spécialisées

- **Nouveau module BackupProcessors** (~472 lignes)
  - Architecture Strategy + Factory pour traitement multi-applications
  - `TwoFASProcessor` complet (.2fas, .zip, .json)
  - Interface `BaseBackupProcessor` pour extensibilité
  - Auto-détection automatique via `BackupProcessorFactory`

### Historique technique
- Renommage: « 2FAS-exporter » → « OTP Exporter »
- Adoption de `uv` pour l'outillage; centralisation des consignes dans `AGENTS.md`
- Licence MIT ajoutée (`LICENSE`)
- Correction de `twofas_lib.py`: ajout de création automatique du répertoire de sortie et utilisation de `with open()` pour la sauvegarde des QR codes (correction des warnings de type VSCode/Pylance)
- Intégration des outils MCP pour diagnostics IDE et exécution de code
- Implémentation robuste de sanitization des noms de fichiers: `sanitize_filename()` et `generate_safe_filename()` pour gérer caractères interdits, noms réservés Windows, normalisation Unicode, et limitations de longueur. Correction critique pour éviter les erreurs `FileNotFoundError` sur noms problématiques

- Ajout d'un utilitaire de nettoyage: `clean-pycache` (module `tools/`) exposé via `uv run clean-pycache`.
- Correction des imports de `BackupProcessors` pour référencer `OTPTools` et publication des packages via `pyproject.toml` (`[tool.setuptools.packages.find]`).

### Statistiques globales
- **Total projet**: ~1177 lignes de code
- **Tests de cohérence**: ✅ Imports relatifs, Factory, instanciation, gestion d'erreurs
- **Applications**: 2FAS (complet), Google Auth/Authy (préparé)

## Où trouver les infos d’exécution
- Procédures d’installation, dépendances et commandes: `AGENTS.md` (uv only).
- Versions figées actuelles: `requirements.txt`.

## Conventions d’exécution (uv)

- Installation locale:
  - `uv venv .venv && uv pip install -e .`
  - Alternative: `uv sync` (offline: `uv sync --offline`).
- Exécution CLI:
  - `uv run otp-export <backup_2fas.json> <dossier_sortie>`
  - ou `uv run python main.py <backup_2fas.json> <dossier_sortie>`
  - Exemple: `uv run otp-export backup.2fas ./exports`
- Maintenance:
  - `uv run clean-pycache [path] [--pyc] [--include-venv] [-n] [-v]`
- Lock/CI:
  - `uv sync --frozen` (et `--offline` si nécessaire)

### Scripts console exposés
- `otp-export`: lance l’export des QR (`main:main`).
- `clean-pycache`: nettoyage des caches Python.
