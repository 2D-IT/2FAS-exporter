# OTP Exporter — Contexte de Travail (Codex)

Ce fichier conserve une compréhension fonctionnelle du projet pour les prochaines sessions. Pour toute procédure (outils, commandes, dépendances, installation, exécution), se référer exclusivement à `AGENTS.md`.

Référence opérations et dépendances: voir `AGENTS.md`.

## Objectif
- Exporter des QR codes OTP (PNG) à partir d’une sauvegarde JSON de l’app 2FAS.

## Organisation du dépôt
- `main.py`: CLI principal. Prend `backup_file` (JSON) et `destination_folder`. Crée le dossier si besoin, gère erreurs basiques, appelle `generate_qr_codes`.
- `twofas_lib.py`: logique de génération; classes `TOTPEntry` et `HOTPEntry` importées de `otpcode`, `generate_qr_codes(file_path, output_dir)` crée automatiquement le dossier de sortie, itère `data["services"]` et écrit `{issuer}-{account}.png` via `with open()` pour éviter les warnings de type.
- `otpcode.py`: classes `TOTPEntry` et `HOTPEntry` pour construire les URLs `otpauth://...`.
- `pyproject.toml`: métadonnées projet (nom: `otp-exporter`), dépendances, script console `otp-export`.
- `requirements.txt`: versions figées pour la prod et fallback si `pyproject.toml` absent.
- `AGENTS.md`: règles et procédures opérationnelles (uv, installation, sync, offline, fallback, outils MCP).

## Flux haut niveau
- Entrée: fichier JSON de sauvegarde 2FAS.
- Traitement: construction d’URL otpauth pour chaque service, génération PNG via `qrcode`/Pillow.
- Sortie: fichiers PNG nommés `{issuer}-{account}.png` dans le dossier cible.

## Hypothèses sur le JSON 2FAS
- Clé racine: `services` (liste).
- Chaque service contient `secret` et un objet `otp` avec au minimum `tokenType`; champs optionnels: `issuer` (fallback `name`), `digits` (def 6), `period` (def 30), `algorithm` (def SHA1), `account` (def "").

## Points d’attention
- Nommage des fichiers: `issuer` et `account` peuvent contenir des caractères à assainir si besoin (amélioration future).
- Erreurs gérées sommairement; envisager logs plus détaillés et options CLI (ex: verbose, format alternative).

## Historique / Décisions
- Renommage: « 2FAS-exporter » → « OTP Exporter ».
- Adoption de `uv` pour l'outillage; centralisation des consignes dans `AGENTS.md`.
- Licence MIT ajoutée (`LICENSE`).
- Correction de `twofas_lib.py`: ajout de création automatique du répertoire de sortie et utilisation de `with open()` pour la sauvegarde des QR codes (correction des warnings de type VSCode/Pylance).
- Intégration des outils MCP pour diagnostics IDE et exécution de code.

## Où trouver les infos d’exécution
- Procédures d’installation, dépendances et commandes: `AGENTS.md`.
- Versions figées actuelles: `requirements.txt`.

