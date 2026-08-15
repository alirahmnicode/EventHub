from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt

private_key = Path("keys/dev_private.pem").read_text()
public_key = Path("keys/dev_public.pem").read_text()

payload = {
    "sub": "user-123",
    "role": "admin",
    "exp": datetime.now(UTC) + timedelta(minutes=15),
    "iat": datetime.now(UTC),
}

token = jwt.encode(payload, private_key, algorithm="RS256")
print("TOKEN:", token)

decoded = jwt.decode(token, public_key, algorithms=["RS256"])
print("DECODED:", decoded)
