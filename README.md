# OTP Exporter — 2FAS → QR codes

Exporte des QR codes OTP (PNG) à partir de sauvegardes 2FA (2FAS, etc.).

## Aperçu

- **Auto-détection de format** : Support 2FAS (.2fas, .json, .zip) avec extensibilité pour d'autres apps
- **Génération QR codes** : Un fichier PNG par service avec noms sécurisés
- **CLI enrichie** : Options verbose, liste des entrées, choix de format
- **Architecture modulaire** : Séparation claire entre extraction de données et création d'objets OTP
- **Script console** : `otp-export` (équivalent à `python main.py`)

## Prérequis

- `uv` (Astral) installé et disponible dans le PATH (`uv --version`).
- Python installé. Aucune activation manuelle de l’environnement n’est requise.

## Installation (avec uv)

Dans la racine du projet:

```bash
uv venv .venv
uv pip install -e .
```

Alternative tout‑en‑un (crée `.venv` et installe d’après `pyproject.toml`):

```bash
uv sync
```

Mode hors‑ligne (artefacts déjà en cache):

```bash
uv pip install --offline -e .
# ou
uv sync --offline
```

Générer un `requirements.txt` figé (prod/fallback):

```bash
uv pip freeze --exclude-editable > requirements.txt
```

## Utilisation

### CLI de base

Exécuter via le script console:

```bash
uv run otp-export <backup_file> <dossier_sortie>
```

Ou directement avec Python via uv:

```bash
uv run python main.py <backup_file> <dossier_sortie>
```

### Options avancées

```bash
# Lister les entrées sans générer de QR codes
uv run otp-export backup.2fas --list-only

# Mode verbeux avec détails
uv run otp-export backup.2fas ./qrcodes --verbose

# Forcer le format 2FAS (bypass auto-détection)
uv run otp-export backup.zip ./qrcodes --format 2fas

# Aide complète
uv run python main.py --help
```

### Exemples complets

```bash
# Export standard
uv run otp-export ~/Downloads/2fas-backup.json ./qrcodes

# Vérifier le contenu avant export
uv run otp-export backup.2fas --list-only

# Export verbeux d'une archive ZIP
uv run otp-export backup.zip ./exports --verbose
```

### Exemple fourni

Un backup de démonstration est disponible dans `exemple/2fas-backup-20250915150420.2fas`.
Vous pouvez inspecter son contenu sans générer de QR codes:

```bash
uv run otp-export exemple/2fas-backup-20250915150420.2fas --list-only
```

La commande affiche le nombre total d’entrées TOTP/HOTP détectées avec leurs labels.

## Maintenance

Nettoyer les dossiers `__pycache__` (et optionnellement `.pyc/.pyo`):

```bash
uv run clean-pycache [path] [--pyc] [--include-venv] [-n] [-v]
```

Exemples:

```bash
uv run clean-pycache .          # Nettoie à la racine (ignore .venv)
uv run clean-pycache -n -v      # Simulation + verbose
uv run clean-pycache --pyc --include-venv
```

## Dépendances et lock

- Source de vérité: `pyproject.toml` (`[project.dependencies]`).
- `requirements.txt` est généré; ne pas l’éditer à la main.
- Lockfile optionnel `uv.lock` pour installations reproductibles:

```bash
uv sync            # crée/maj le lock
uv sync --frozen   # CI/prod — échoue si lock absent/obsolète
```

## Structure du projet

```
├── main.py                    # Point d'entrée CLI principal
├── src/                       # Modules utilitaires
│   ├── __init__.py
│   └── utils.py              # Fonctions sanitisation noms fichiers
├── tests/                     # Tests unitaires
│   ├── __init__.py
│   └── test_refactoring.py   # Tests de validation
├── OTPTools/                  # Module core OTP (TOTP/HOTP, factory)
│   ├── __init__.py
│   ├── base.py               # Classe abstraite OTPEntry
│   ├── config.py             # Configuration par défaut
│   ├── exceptions.py         # Exceptions OTP
│   ├── factory.py            # Factory pour créer des OTP
│   ├── hotp.py               # Implémentation HOTP
│   └── totp.py               # Implémentation TOTP
├── BackupProcessors/          # Traitement de backups multi-formats
│   ├── __init__.py           # Factory + exports
│   ├── base.py               # Interface BaseBackupProcessor
│   ├── exceptions.py         # Exceptions spécialisées
│   └── twofas.py             # Processor 2FAS complet
└── tools/                     # Utilitaires de développement
    ├── __init__.py
    └── clean_pycache.py      # CLI de nettoyage
```

## Architecture après refactoring

Le flux de données suit maintenant une séparation claire des responsabilités :

```
Fichier backup → BackupProcessorFactory → OTPFactory → QR codes
                        ↓                      ↓
                 TwoFASProcessor      create_from_2fas()
                 (extraction)         (création objets)
```

- **BackupProcessors** : Extrait les données brutes depuis différents formats
- **OTPFactory** : Crée les objets OTP standardisés (TOTP/HOTP)
- **main.py** : Gère la CLI et génère les QR codes
- **src/utils** : Fonctions utilitaires partagées
- Les backups JSON/ZIP invalides sont signalés proprement avec des messages de log
- Les modules utilitaires (`src`) sont empaquetés avec l'installation editable pour éviter les erreurs d'import

## Licence

MIT — voir `LICENSE`.
