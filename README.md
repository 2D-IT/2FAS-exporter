# OTP Exporter — 2FAS → QR codes

Exporte des QR codes OTP (PNG) à partir d’une sauvegarde JSON 2FAS.

## Aperçu

- Génère un fichier PNG par service présent dans le backup 2FAS.
- Noms de fichiers sûrs (normalisation Unicode, caractères interdits, longueur).
- Script console exposé: `otp-export` (équivalent à `python main.py`).

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

Exécuter via le script console:

```bash
uv run otp-export <backup_2fas.json> <dossier_sortie>
```

Ou directement avec Python via uv:

```bash
uv run python main.py <backup_2fas.json> <dossier_sortie>
```

Exemples:

```bash
uv run otp-export ~/Downloads/2fas-backup.json ./qrcodes
uv run python main.py data/backup.json export/
```

Aide:

```bash
uv run python main.py -h
```

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

## Structure (résumé)

```
├── main.py            # Entrée CLI (script console: otp-export)
├── twofas_lib.py      # Génération des QR à partir du JSON 2FAS
├── OTPTools/          # Module core OTP (TOTP/HOTP, factory, validations)
└── BackupProcessors/  # Base pour traitements de backups (extensible)
```

Note: la CLI actuelle consomme un JSON 2FAS; d’autres formats pourront être
supportés via `BackupProcessors` dans de futures évolutions.

## Licence

MIT — voir `LICENSE`.
