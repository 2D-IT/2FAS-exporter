# OTP Exporter

## Overview

Export individual OTP QR codes from a 2FAS JSON backup file.

## Features

- Generate a PNG QR code per service from a 2FAS backup.

## Installation (uv recommended)

1. Ensure you have `uv` installed.
2. From the project root:
   ```bash
   uv venv .venv
   uv pip install -e .
   ```
3. Generate a frozen `requirements.txt` for production if needed:
   ```bash
   uv pip freeze --exclude-editable > requirements.txt
   ```

## Usage

Run with uv:
```bash
uv run python main.py backup_file destination_folder
```

Help:
```bash
uv run python main.py -h
```

## License

This project is licensed under the MIT License.

