# server/api/utils/helpers.py
import os
from functools import wraps
from flask import request, jsonify
from api.auth import requires_auth

AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"

def requires_auth_conditional(f):
    """Conditionally require authentication based on AUTH0_ENABLED"""
    if AUTH0_ENABLED:
        return requires_auth(f)
    else:
        @wraps(f)
        def decorated(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated