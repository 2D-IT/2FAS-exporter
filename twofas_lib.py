import json
import qrcode
import os
import re
import unicodedata

from otpcode import TOTPEntry, HOTPEntry


def sanitize_filename(filename):
    """
    Assainit un nom de fichier en supprimant/remplaçant les caractères problématiques.
    
    Args:
        filename (str): Nom de fichier à assainir
        
    Returns:
        str: Nom de fichier assaini et sécurisé
    """
    if not filename:
        return "unknown"
    
    # Normalise les caractères Unicode (ex: é -> e)
    filename = unicodedata.normalize('NFKD', filename)
    filename = filename.encode('ascii', 'ignore').decode('ascii')
    
    # Remplace les caractères interdits par des tirets
    # Windows: < > : " | ? * \ /
    # Unix: /
    filename = re.sub(r'[<>:"/\\|?*]', '-', filename)
    
    # Supprime les espaces en début/fin et remplace les espaces multiples
    filename = re.sub(r'\s+', '_', filename.strip())
    
    # Supprime les points en début/fin (problématique sur Windows)
    filename = filename.strip('.')
    
    # Limite la longueur (255 caractères max sur la plupart des systèmes)
    if len(filename) > 200:  # Garde de la marge pour l'extension
        filename = filename[:200]
    
    # Évite les noms réservés Windows
    reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                     'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                     'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    
    if filename.upper() in reserved_names:
        filename = f"_{filename}"
    
    # Si le nom est vide après nettoyage
    if not filename:
        filename = "sanitized"
        
    return filename


def generate_safe_filename(issuer, account):
    """
    Génère un nom de fichier sécurisé pour un QR code OTP.
    
    Args:
        issuer (str): Émetteur du service
        account (str): Compte utilisateur (peut être None/vide)
        
    Returns:
        str: Nom de fichier sécurisé sans extension
    """
    # Assainit l'issuer
    safe_issuer = sanitize_filename(issuer)
    
    # Gère le compte (None, vide, ou valide)
    if account and account.strip():
        safe_account = sanitize_filename(account)
        return f"{safe_issuer}_{safe_account}"
    else:
        return safe_issuer

def generate_qr_codes(file_path,output_dir):
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load json file
    with open(file_path, "r") as file:
        data = json.load(file)

    # Parse json file and generate QR codes for each service
    # Count number of services
    print(f"Generating QR codes for {len(data['services'])} services")
    for service in data["services"]:
        # Generate TOTPCode object
        try:
            token_type = service["otp"]["tokenType"]
            if token_type.lower() == "totp":
                qr_code = TOTPEntry(
                    issuer=service["otp"].get("issuer", service["name"]),
                    secret=service["secret"],
                    account=service["otp"].get("account", ""),
                    digits=int(service["otp"].get("digits", "6")),
                    period=int(service["otp"].get("period", "30")),
                    algorithm=service["otp"].get("algorithm", "SHA1")
                )
            else:  # HOTP
                qr_code = HOTPEntry(
                    issuer=service["otp"].get("issuer", service["name"]),
                    secret=service["secret"],
                    account=service["otp"].get("account", ""),
                    digits=int(service["otp"].get("digits", "6")),
                    counter=int(service["otp"].get("counter", "0")),
                    algorithm=service["otp"].get("algorithm", "SHA1")
                )
            
            # Generate QR code based on TOTPCode/HOTPCode OTPAuth URL
            qr_img = qrcode.make(qr_code.otpauth)
            
            # Generate safe filename
            safe_filename = generate_safe_filename(qr_code.issuer, qr_code.account)
            output_file = os.path.join(output_dir, f"{safe_filename}.png")
            
            with open(output_file, "wb") as f:
                qr_img.save(f)

            print(f"TOTPCode {qr_code.label} saved as {output_file}")
            
        except KeyError:
            print(f"JSON file for {service['otp']['label']} is not properly formatted or a value is missing")
                 
# Test commit