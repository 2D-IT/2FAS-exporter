# OTP Exporter — Contexte de Travail (Codex)

Ce fichier conserve une compréhension fonctionnelle du projet pour les prochaines sessions. Pour toute procédure (outils, commandes, dépendances, installation, exécution), se référer exclusivement à `AGENTS.md`.

Référence opérations et dépendances: voir `AGENTS.md`.

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
    └── BackupProcessors/          # Module BackupProcessors
        ├── __init__.py           # Factory et exports
        ├── base.py               # Interface BaseBackupProcessor
        ├── exceptions.py         # Exceptions spécialisées
        └── twofas.py             # Processor 2FAS
```

### Modules principaux

#### Script de base
- `main.py`: CLI principal. Prend `backup_file` (JSON) et `destination_folder`. Crée le dossier si besoin, gère erreurs basiques, appelle `generate_qr_codes`.
- `twofas_lib.py`: logique de génération; classes `TOTPEntry` et `HOTPEntry` importées depuis le module `OTPTools`, `generate_qr_codes(file_path, output_dir)` crée automatiquement le dossier de sortie, itère `data["services"]` et écrit des fichiers PNG avec noms assainis via `sanitize_filename()` et `generate_safe_filename()`.

#### OTPTools (~705 lignes)
Module core pour la gestion des tokens OTP avec classes standardisées et validation.

#### BackupProcessors (~472 lignes)
Module pour traiter différents formats de backup 2FA et les convertir vers des objets OTP standardisés.
- **Rôle**: Auto-détection et traitement de backups multi-applications
- **Patterns**: Strategy + Factory pour extensibilité
- **Applications supportées**: 2FAS (complet), Google Auth/Authy (à implémenter)
- **Formats**: .2fas, .zip, .json extensible

#### Configuration
- `pyproject.toml`: métadonnées projet (nom: `otp-exporter`), dépendances, script console `otp-export`.
- `requirements.txt`: versions figées pour la prod et fallback si `pyproject.toml` absent.
- `AGENTS.md`: règles et procédures opérationnelles (uv, installation, sync, offline, fallback, outils MCP).

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

### Statistiques globales
- **Total projet**: ~1177 lignes de code
- **Tests de cohérence**: ✅ Imports relatifs, Factory, instanciation, gestion d'erreurs
- **Applications**: 2FAS (complet), Google Auth/Authy (préparé)

## Où trouver les infos d’exécution
- Procédures d’installation, dépendances et commandes: `AGENTS.md`.
- Versions figées actuelles: `requirements.txt`.

