"""
Run this script ONCE to generate your VAPID keys for push notifications.
Then paste the output into app.py.
"""
from py_vapid import Vapid

vapid = Vapid()
vapid.generate_keys()
vapid.save_key("vapid_private.pem")

public_key = vapid.public_key
private_key = vapid.private_key

print("=== VAPID Keys Generated ===")
print("Private Key PEM file saved to: vapid_private.pem")
print()
# Export Base64 URL-safe encoded versions
from py_vapid import b64urlencode
import binascii

pub = vapid.public_key.public_bytes(
    encoding=__import__('cryptography').hazmat.primitives.serialization.Encoding.X962,
    format=__import__('cryptography').hazmat.primitives.serialization.PublicFormat.UncompressedPoint
)
priv = vapid.private_key.private_bytes(
    encoding=__import__('cryptography').hazmat.primitives.serialization.Encoding.PEM,
    format=__import__('cryptography').hazmat.primitives.serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=__import__('cryptography').hazmat.primitives.serialization.NoEncryption()
)

import base64
pub_b64 = base64.urlsafe_b64encode(pub).rstrip(b'=').decode()
print(f"VAPID_PUBLIC_KEY = '{pub_b64}'")
print()
print("Copy those lines above and put in app.py where VAPID_PUBLIC_KEY is defined.")
