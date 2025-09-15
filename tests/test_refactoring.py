#!/usr/bin/env python3
"""
Test de validation du refactoring 2FAS Exporter.

Ce script teste les fonctionnalités principales après le refactoring
pour s'assurer qu'il n'y a pas de régression.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Ajouter le répertoire racine au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from OTPTools.factory import OTPFactory
from OTPTools import TOTPEntry, HOTPEntry
from OTPTools.exceptions import OTPError, ParseError
from BackupProcessors import BackupProcessorFactory, TwoFASProcessor
from src.utils import sanitize_filename, generate_safe_filename


def test_otpfactory_create_from_2fas():
    """Test de création d'objet OTP via OTPFactory.create_from_2fas()."""
    print("🧪 Test OTPFactory.create_from_2fas()...")

    # Test TOTP basique
    service_totp = {
        "secret": "JBSWY3DPEHPK3PXP",
        "name": "GitHub",
        "otp": {
            "issuer": "GitHub",
            "account": "user@example.com",
            "tokenType": "TOTP",
            "digits": "6",
            "period": "30",
            "algorithm": "SHA1"
        }
    }

    try:
        entry = OTPFactory.create_from_2fas(service_totp)
        assert isinstance(entry, TOTPEntry)
        assert entry.issuer == "GitHub"
        assert entry.account == "user@example.com"
        assert entry.secret == "JBSWY3DPEHPK3PXP"
        assert entry.digits == 6
        assert entry.period == 30
        print("  ✅ TOTP créé avec succès")
    except Exception as e:
        print(f"  ❌ Erreur TOTP: {e}")
        return False

    # Test HOTP
    service_hotp = {
        "secret": "JBSWY3DPEHPK3PXP",
        "name": "Service HOTP",
        "otp": {
            "tokenType": "HOTP",
            "counter": "5"
        }
    }

    try:
        entry = OTPFactory.create_from_2fas(service_hotp)
        assert isinstance(entry, HOTPEntry)
        assert entry.issuer == "Service HOTP"
        assert entry.counter == 5
        print("  ✅ HOTP créé avec succès")
    except Exception as e:
        print(f"  ❌ Erreur HOTP: {e}")
        return False

    # Test avec données minimales
    service_minimal = {
        "secret": "JBSWY3DPEHPK3PXP",
        "name": "Minimal Service"
    }

    try:
        entry = OTPFactory.create_from_2fas(service_minimal)
        assert isinstance(entry, TOTPEntry)  # TOTP par défaut
        assert entry.issuer == "Minimal Service"
        print("  ✅ Service minimal créé avec succès")
    except Exception as e:
        print(f"  ❌ Erreur service minimal: {e}")
        return False

    return True


def test_otpfactory_parse_otpauth_url():
    """Test de parsing d'URL otpauth via OTPFactory.parse_otpauth_url()."""
    print("🧪 Test OTPFactory.parse_otpauth_url()...")

    # Test URL TOTP
    totp_url = "otpauth://totp/GitHub:user@example.com?secret=JBSWY3DPEHPK3PXP&issuer=GitHub&digits=6&period=30"

    try:
        entry = OTPFactory.parse_otpauth_url(totp_url)
        assert isinstance(entry, TOTPEntry)
        assert entry.issuer == "GitHub"
        assert entry.account == "user@example.com"
        assert entry.secret == "JBSWY3DPEHPK3PXP"
        print("  ✅ URL TOTP parsée avec succès")
    except Exception as e:
        print(f"  ❌ Erreur URL TOTP: {e}")
        return False

    # Test URL HOTP
    hotp_url = "otpauth://hotp/Service:account?secret=JBSWY3DPEHPK3PXP&issuer=Service&counter=0"

    try:
        entry = OTPFactory.parse_otpauth_url(hotp_url)
        assert isinstance(entry, HOTPEntry)
        assert entry.issuer == "Service"
        assert entry.account == "account"
        print("  ✅ URL HOTP parsée avec succès")
    except Exception as e:
        print(f"  ❌ Erreur URL HOTP: {e}")
        return False

    return True


def test_backup_processor_factory():
    """Test de BackupProcessorFactory sur un fichier de backup réel."""
    print("🧪 Test BackupProcessorFactory...")

    # Créer un fichier de test 2FAS temporaire
    test_data = {
        "services": [
            {
                "secret": "JBSWY3DPEHPK3PXP",
                "name": "Test Service 1",
                "otp": {
                    "issuer": "Test Issuer 1",
                    "account": "test1@example.com",
                    "tokenType": "TOTP",
                    "digits": "6",
                    "period": "30"
                }
            },
            {
                "secret": "ABCDEFGHIJKLMNOP",
                "name": "Test Service 2",
                "otp": {
                    "tokenType": "HOTP",
                    "counter": "0"
                }
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.2fas', delete=False) as f:
        json.dump(test_data, f)
        temp_file = f.name

    try:
        # Test avec TwoFASProcessor direct
        processor = TwoFASProcessor()
        if not processor.can_process(temp_file):
            print("  ❌ TwoFASProcessor ne peut pas traiter le fichier de test")
            return False

        entries = processor.process_backup(temp_file)
        assert len(entries) == 2
        assert isinstance(entries[0], TOTPEntry)
        assert isinstance(entries[1], HOTPEntry)
        print("  ✅ TwoFASProcessor fonctionne correctement")

        # Test avec BackupProcessorFactory
        factory = BackupProcessorFactory()
        entries = factory.process_backup(temp_file)
        assert len(entries) == 2
        print("  ✅ BackupProcessorFactory fonctionne correctement")

    except Exception as e:
        print(f"  ❌ Erreur BackupProcessor: {e}")
        return False
    finally:
        # Nettoyer le fichier temporaire
        os.unlink(temp_file)

    return True


def test_utils_functions():
    """Test des fonctions utilitaires."""
    print("🧪 Test des fonctions utilitaires...")

    # Test sanitize_filename
    test_cases = [
        ("Normal Name", "Normal_Name"),
        ("Name with/slashes", "Name_with-slashes"),
        ("Name:with|special*chars", "Name-with-special-chars"),
        ("", "unknown"),
        ("CON", "_CON"),  # Nom réservé Windows
    ]

    for input_name, expected in test_cases:
        result = sanitize_filename(input_name)
        if result != expected:
            print(f"  ❌ sanitize_filename('{input_name}') = '{result}', attendu '{expected}'")
            return False

    print("  ✅ sanitize_filename fonctionne correctement")

    # Test generate_safe_filename
    result = generate_safe_filename("GitHub", "user@example.com")
    expected = "GitHub_user@example.com"
    if result != expected:
        print(f"  ❌ generate_safe_filename résultat inattendu: '{result}'")
        return False

    result = generate_safe_filename("GitHub", "")
    expected = "GitHub"
    if result != expected:
        print(f"  ❌ generate_safe_filename sans account résultat inattendu: '{result}'")
        return False

    print("  ✅ generate_safe_filename fonctionne correctement")

    return True


def test_qr_code_generation():
    """Test de génération d'URLs otpauth et comparaison."""
    print("🧪 Test de génération d'URLs otpauth...")

    # Créer un objet TOTP via OTPFactory
    service_data = {
        "secret": "JBSWY3DPEHPK3PXP",
        "name": "GitHub",
        "otp": {
            "issuer": "GitHub",
            "account": "user@example.com",
            "tokenType": "TOTP"
        }
    }

    try:
        entry = OTPFactory.create_from_2fas(service_data)
        otpauth_url = entry.otpauth

        # Vérifier que l'URL contient les bonnes parties
        assert otpauth_url.startswith("otpauth://totp/")
        assert "secret=JBSWY3DPEHPK3PXP" in otpauth_url
        assert "issuer=GitHub" in otpauth_url
        print("  ✅ URL otpauth générée correctement")
        print(f"    URL: {otpauth_url}")

        # Test de round-trip: créer depuis l'URL
        parsed_entry = OTPFactory.parse_otpauth_url(otpauth_url)
        assert parsed_entry.secret == entry.secret
        assert parsed_entry.issuer == entry.issuer
        assert parsed_entry.account == entry.account
        print("  ✅ Round-trip URL->OTP->URL réussi")

    except Exception as e:
        print(f"  ❌ Erreur génération QR: {e}")
        return False

    return True


def main():
    """Lance tous les tests de validation."""
    print("🚀 Début des tests de validation du refactoring...")
    print("=" * 60)

    tests = [
        test_otpfactory_create_from_2fas,
        test_otpfactory_parse_otpauth_url,
        test_backup_processor_factory,
        test_utils_functions,
        test_qr_code_generation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
                print()
            else:
                failed += 1
                print()
        except Exception as e:
            print(f"❌ Erreur inattendue dans {test.__name__}: {e}")
            failed += 1
            print()

    print("=" * 60)
    print(f"📊 Résultats: {passed} tests réussis, {failed} tests échoués")

    if failed == 0:
        print("🎉 Tous les tests sont passés! Le refactoring est validé.")
        return 0
    else:
        print("⚠️  Des tests ont échoué. Vérifiez les erreurs ci-dessus.")
        return 1


if __name__ == "__main__":
    sys.exit(main())