# Instructions Agent IA — uv (Astral)

Ce dépôt utilise exclusivement `uv` (Astral) pour gérer l’environnement Python, installer les dépendances et exécuter les scripts. En tant qu’agent, suis strictement les règles et commandes ci‑dessous.

## Règles
- Toujours utiliser `uv` pour tout: pas de `pip`, pas de `python -m venv`.
- Ne jamais installer de paquets globalement; utiliser l’environnement local `.venv`.
- Source de vérité des dépendances: `pyproject.toml` (`[project.dependencies]`).
- Pour la production, synchroniser un `requirements.txt` figé depuis l’environnement.
- En environnement sans réseau, utiliser le mode hors‑ligne de `uv`.

## Pré‑requis
- `uv` disponible dans le PATH (`uv --version`).
- Python installé (uv gère l’environnement; aucune activation manuelle n’est requise).

## Préparer l’environnement
Dans la racine du projet:

1) Créer (ou réutiliser) l’environnement local
```
uv venv .venv
```

2) Installer les dépendances depuis `pyproject.toml` (source de vérité)
```
uv pip install -e .
```
Si `pyproject.toml` est absent (ex: clone minimal), utiliser le fallback ci‑dessous.

Mode sans réseau (si nécessaire et si les artefacts sont déjà en cache):
```
uv pip install --offline -e .
```

Astuce: pour repartir propre, on peut régénérer l’environnement
```
rm -rf .venv && uv venv .venv && uv pip install -e .
```

### Alternative tout‑en‑un
`uv sync` crée `.venv` et installe depuis `pyproject.toml` (utilise `uv.lock` s’il existe):
```
uv sync
```
Mode hors‑ligne:
```
uv sync --offline
```

### Installation auto‑détectée (pyproject d’abord, sinon fallback)
Copier/coller cette commande pour une installation robuste:
```
uv venv .venv && \
([ -f pyproject.toml ] && uv pip install -e . || uv pip install -r requirements.txt)
```

## Fallback sans `pyproject.toml`
Utiliser cette section uniquement si le dépôt cloné ne contient pas `pyproject.toml`.

- Installation depuis `requirements.txt` (en ligne):
```
uv pip install -r requirements.txt
```

- Installation hors‑ligne (artefacts déjà en cache):
```
uv pip install --offline -r requirements.txt
```

## Exécuter les scripts
Script principal: `main.py`

Exécution standard (aucune activation d’environnement requise):
```
uv run python main.py <backup_2fas.json> <dossier_sortie>
```

Ou via le script console exposé par le projet:
```
uv run otp-export <backup_2fas.json> <dossier_sortie>
```

Exemples:
```
uv run python main.py ~/Downloads/2fas-backup.json ./qrcodes
uv run python main.py exemple/2fas-backup-20250915150420.2fas exports/
uv run otp-export exemple/2fas-backup-20250915150420.2fas exports/
```

## Utilitaires (maintenance)
- Nettoyer les dossiers `__pycache__` (et optionnellement les fichiers `.pyc`):
```
uv run clean-pycache [path] [--pyc] [--include-venv] [-n] [-v]
```
- Exemples:
```
# Nettoyer à la racine du dépôt (ignore .venv)
uv run clean-pycache .

# Simulation + verbose
uv run clean-pycache -n -v

# Inclure .pyc/.pyo et le dossier .venv
uv run clean-pycache --pyc --include-venv
```

## Gérer les dépendances
- Ajouter / modifier une dépendance: éditer `pyproject.toml` dans `[project.dependencies]`, puis réinstaller
```
uv pip install -e .
```

- Ne pas éditer `requirements.txt` à la main; il est généré depuis l’environnement résolu.

- Synchroniser `requirements.txt` (pour prod): figer les versions résolues
```
uv pip freeze --exclude-editable > requirements.txt
```

## Lockfile (optionnel)
- **But**: figer les versions exactes pour des installations reproductibles via `uv`.
- **Fichier**: `uv.lock` (à committer dans git).

Commandes utiles
```
# Créer/mettre à jour le lock
uv sync

# Forcer l'utilisation du lock (CI/production)
uv sync --frozen

# Idem, en mode hors-ligne
uv sync --frozen --offline
```
Notes
- Si `uv.lock` est manquant ou obsolète, `--frozen` échoue (c’est voulu).
- `requirements.txt` reste utilisé pour les environnements sans `uv` ou en fallback.

- Mettre à jour une version précise (ex: qrcode)
```
# 1) éditer pyproject.toml (ex: "qrcode==7.4.2")
# 2) réinstaller et figer
uv pip install -e .
uv pip freeze --exclude-editable > requirements.txt
```

- En contexte hors‑ligne (CI restreinte): ne pas modifier les deps; seulement exécuter
```
uv run --offline python main.py ...
```

## Option: exécution par shebang (facultatif)
Pour lancer directement un script avec `uv`, on peut ajouter en première ligne du fichier script:
```
#!/usr/bin/env -S uv run python
```
Puis rendre le fichier exécutable (`chmod +x`) et lancer `./main.py ...`.

## Outils MCP disponibles
Le projet dispose d'outils MCP (Model Context Protocol) pour l'intégration IDE:
- `mcp__ide__getDiagnostics`: obtenir les diagnostics/erreurs de l'IDE
- `mcp__ide__executeCode`: exécuter du code Python dans le kernel Jupyter

Ces outils permettent une meilleure intégration avec l'environnement de développement.

## Modules et architecture

### Structure du projet
```
└── 2FAS-exporter/
    ├── main.py                     # Point d'entrée CLI
    ├── twofas_lib.py              # Logique génération QR
    ├── OTPTools/                  # Module OTP core (~705 lignes)
    └── BackupProcessors/          # Module traitement backups (~472 lignes)
```

### Modules disponibles

#### OTPTools
Module core standardisé pour tokens OTP:
- Classes: `TOTPEntry`, `HOTPEntry`, `OTPFactory`
- Import: `from OTPTools import TOTPEntry, HOTPEntry`
- Usage: validation, génération otpauth URLs

#### BackupProcessors
Module traitement backups multi-applications:
- Classes: `TwoFASProcessor`, `BackupProcessorFactory`
- Import: `from BackupProcessors import BackupProcessorFactory`
- Usage: auto-détection et conversion formats → OTP
- Formats supportés: .2fas, .zip, .json (extensible)

### Scripts console exposés
- `otp-export`: lance l'export des QR codes (`main:main`).
- `clean-pycache`: nettoie les caches Python (`tools.clean_pycache:clean_pycache_main`).

#### Exemples d'utilisation modules
```python
# OTPTools - création directe
from OTPTools import TOTPEntry
totp = TOTPEntry(issuer="GitHub", secret="JBSWY3DPEHPK3PXP")

# BackupProcessors - auto-détection
from BackupProcessors import BackupProcessorFactory
factory = BackupProcessorFactory()
entries = factory.process_backup('backup.2fas')
```

## Références du dépôt
- Dépendances source: `pyproject.toml` (`[project.dependencies]`)
- Dépendances figées prod: `requirements.txt` (versions actuelles: Pillow 11.3.0, qrcode 8.2)
- Point d'entrée: `main.py` (script console: `otp-export`)
- Environnement local: `.venv`
- Modules: `OTPTools/` (core), `BackupProcessors/` (traitement)
- Exemples de test: `exemple/` (fichier sample `.2fas`)
- Sortie par défaut: `exports/` (QR codes générés)

Respecte ces conventions pour toutes les tâches futures: installation, exécution, tests, et maintenance des dépendances se font via `uv`.
