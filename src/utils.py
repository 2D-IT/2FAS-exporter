"""
Utilitaires pour l'export de QR codes 2FAS.

Ce module contient les fonctions utilitaires communes utilisées
pour la génération et la sauvegarde des QR codes.
"""

import os
import re
import unicodedata


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