# TODO

- [x] Mettre à jour `pyproject.toml` pour retirer `twofas_lib` de `[tool.setuptools] py-modules` et déclarer uniquement les modules réellement présents (`pyproject.toml:23`).
- [x] Remplacer toutes les utilisations de `exit()` par `sys.exit()` pour éviter la dépendance au shell interactif (`main.py:134`, `main.py:144`, `main.py:163`, `main.py:187`).
- Éviter la double lecture des backups dans `TwoFASProcessor.can_process` en introduisant un cache léger ou une détection plus heuristique (`BackupProcessors/twofas.py:57`, `BackupProcessors/twofas.py:118`).
- Nettoyer l'import `os` devenu inutile dans `src/utils.py` et appliquer un linting léger pour détecter d'autres résidus (`src/utils.py:8`).
- Compléter la suite de tests pour couvrir les backups ZIP/chiffrés et les scénarios d'erreur de déchiffrement, idéalement via `pytest` et des fixtures simulées (`tests/test_refactoring.py`).
