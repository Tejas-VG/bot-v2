import sys
import argparse
import os

# Insert parent dir to import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import send_email

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--age", required=True)
    parser.add_argument("--vaccine", required=True)
    parser.add_argument("--dose", required=True)
    parser.add_argument("--slot", required=True)
    parser.add_argument("--ref", required=True)
    parser.add_argument("--hospital", required=True)
    parser.add_argument("--address", required=True)
    args = parser.parse_args()

    import urllib.parse
    qr_info = f"MAYDEN SMARTHEALTH PVT LTD\n\nReference ID: {args.ref}\nPatient Name: {args.name}\nAge: {args.age}\nVaccine: {args.vaccine} - {args.dose}\nTime Slot: {args.slot}\nHospital: {args.hospital}"
    qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=" + urllib.parse.quote(qr_info)

    message = f"""
Vaccine Appointment Confirmed!
Reference ID: {args.ref}

Appointment Details:
----------------------------------------------
Facility:      {args.hospital}
Address:       {args.address}
Beneficiary:   {args.name} ({args.age} years)
Vaccine:       {args.vaccine} - {args.dose}
Time Slot:     {args.slot}
----------------------------------------------
QR Verification Link: {qr_url}

Please bring your registered Govt photo ID card to the clinic counter for verification.

Thank you for choosing MAYDEN SMARTHEALTH PVT LTD.
"""
    status = send_email(args.email, message)
    print(status)

if __name__ == "__main__":
    main()
