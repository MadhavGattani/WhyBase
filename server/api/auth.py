# server/api/auth.py
import os
import json
import requests
from functools import wraps
from flask import request, jsonify, abort, current_app
import jwt  # PyJWT

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ISSUER = f"https://{AUTH0_DOMAIN}/"

_jwks = None

def _get_jwks():
    global _jwks
    if _jwks is None:
        jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
        resp = requests.get(jwks_url, timeout=5)
        resp.raise_for_status()
        _jwks = resp.json()
    return _jwks

def _get_rsa_key(token_kid):
    jwks = _get_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == token_kid:
            jwk_json = json.dumps(key)
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk_json)
            return public_key
    return None

def verify_jwt(token: str):
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception as e:
        raise ValueError("Invalid token header") from e

    kid = unverified_header.get("kid")
    if not kid:
        raise ValueError("Token missing kid")

    rsa_key = _get_rsa_key(kid)
    if not rsa_key:
        raise ValueError("Unable to find matching JWK")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=AUTH0_AUDIENCE,
            issuer=ISSUER,
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidAudienceError:
        raise ValueError("Invalid audience")
    except jwt.InvalidIssuerError:
        raise ValueError("Invalid issuer")
    except Exception as e:
        raise ValueError("Failed to verify token: " + str(e)) from e

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", None)
        if not auth:
            return jsonify({"error": "Authorization header is expected"}), 401
        parts = auth.split()
        if parts[0].lower() != "bearer":
            return jsonify({"error": "Authorization header must start with Bearer"}), 401
        elif len(parts) == 1:
            return jsonify({"error": "Token not found"}), 401
        elif len(parts) > 2:
            return jsonify({"error": "Authorization header must be Bearer token"}), 401
        token = parts[1]
        try:
            payload = verify_jwt(token)
            request.user = payload
        except Exception as e:
            current_app.logger.warning("JWT verify failed: %s", e)
            return jsonify({"error": "Unauthorized", "message": str(e)}), 401
        return f(*args, **kwargs)
    return decorated