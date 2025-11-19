import time
import jwt
from cryptography.hazmat.primitives import serialization
import time
import secrets
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY_ID = os.getenv("COINBASE_API_KEY")
API_SECRET = os.getenv("COINBASE_API_SECRET_KEY")


def build_jwt(uri):
    private_key_bytes = API_SECRET.encode('utf-8')
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
    jwt_payload = {
        'sub': API_KEY_ID,
        'iss': "cdp",
        'nbf': int(time.time()),
        'exp': int(time.time()) + 120,
        'uri': uri,
    }
    jwt_token = jwt.encode(
        jwt_payload,
        private_key,
        algorithm='ES256',
        headers={'kid': API_KEY_ID, 'nonce': secrets.token_hex()},
    )
    return jwt_token

