"""
Run this script once to generate VAPID keys for push notifications.
Put the printed values in server environment variables, never in frontend files.
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
print("VAPID_PRIVATE_KEY = <<contents of vapid_private.pem>>")
print(priv.decode().strip())
print()
print("Set VAPID_PUBLIC_KEY and VAPID_PRIVATE_KEY in .env or Render environment variables.")
