import json
import qrcode
import os

from otpcode import TOTPEntry, HOTPEntry

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
            output_file = os.path.join(output_dir, f"{qr_code.issuer}-{qr_code.account}.png")
            with open(output_file, "wb") as f:
                qr_img.save(f)

            print(f"TOTPCode {qr_code.label} saved as {output_file}")
            
        except KeyError:
            print(f"JSON file for {service['otp']['label']} is not properly formatted or a value is missing")
                 
# Test commit