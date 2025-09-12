import json
import qrcode
import os

from otpcode import QRCode

def generate_qr_codes(file_path,output_dir):

    # Load json file
    with open(file_path, "r") as file:
        data = json.load(file)

    # Parse json file and generate QR codes for each service
    # Count number of services
    print(f"Generating QR codes for {len(data['services'])} services")
    for service in data["services"]:
        # Generate QrCode object
        try:
            qr_code = QRCode(
                secret=service["secret"],
                issuer=service["otp"].get("issuer", service["name"]),
                tokenType=service["otp"]["tokenType"],
                digits=service["otp"].get("digits", "6"),
                period=service["otp"].get("period", "30"),
                algorithm=service["otp"].get("algorithm", "SHA1"),
                account=service["otp"].get("account", "")
            )
            
            # Generate QR code based on QrCode OTPAuth URL
            qr_img = qrcode.make(qr_code.otpauth)
            output_file = os.path.join(output_dir, f"{qr_code.issuer}-{qr_code.account}.png")
            qr_img.save(output_file)

            print(f"QRCode {qr_code.label} saved as {output_file}")
            
        except KeyError:
            print(f"JSON file for {service['otp']['label']} is not properly formatted or a value is missing")
                 
# Test commit