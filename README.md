# 2FAS-exporter

## Overview

Use this tool to export individual 2FA QRCode from 2FAS app backup

## Features

Export individual QRcode image from 2FAS Json backup file.

## Installation

To create a virtual environment, follow these steps:

1. Ensure you have Python installed. You can download it from [python.org](https://www.python.org/).

2. Open a terminal or command prompt.

3. Navigate to your project directory:
    ```bash
    cd path/to/2FAS-exporter
    ```

4. Create a virtual environment:
    ```bash
    python -m venv .venv
    ```

5. Activate the virtual environment:
    - On Windows:
        ```bash
        .\.venv\Scripts\activate
        ```
    - On macOS and Linux:
        ```bash
        source .venv/bin/activate
        ```

6. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

Your virtual environment is now set up and ready to use.

## Usage

To use the tool, run:
```bash
python main.py backup_file destination_folder
```
For help, use 

```bash
python main.py -h
```

## License

This project is licensed under the MIT License.
