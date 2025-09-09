import os
import argparse
from twofas_lib import generate_qr_codes


def main():
    parser = argparse.ArgumentParser(
        description="Export QR codes from a 2FAS JSON backup file."
    )
    parser.add_argument(
        "backup_file", type=str, help="Path to the 2FAS backup JSON file"
    )
    parser.add_argument(
        "destination_folder",
        type=str,
        help="Directory where the QR code images will be saved",
    )

    args = parser.parse_args()

    # Vérification de l'existence du fichier source
    if not os.path.isfile(args.backup_file):
        print(f"❌ Error: Source file '{args.backup_file}' does not exist.")
        exit(1)

    # Création du répertoire de destination s'il n'existe pas
    if not os.path.exists(args.destination_folder):
        try:
            os.makedirs(args.destination_folder)
        except Exception as e:
            print(f"❌ Failed to create destination directory: {e}")
            exit(1)

    try:
        generate_qr_codes(args.backup_file, args.destination_folder)
    except Exception as e:
        print(f"❌ An unexpected error occurred during QR code generation: {e}")
        exit(1)


if __name__ == "__main__":
    main()
