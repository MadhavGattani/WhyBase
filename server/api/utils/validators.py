# server/api/utils/validators.py
import re
from typing import Tuple

def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format
    Returns: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    if len(email) > 255:
        return False, "Email is too long"
    
    # Check for common typos
    common_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    domain = email.split('@')[-1].lower()
    
    # Check for suspicious patterns
    if '..' in email:
        return False, "Email contains invalid characters"
    
    if email.startswith('.') or email.endswith('.'):
        return False, "Email cannot start or end with a dot"
    
    return True, ""

def validate_url(url: str) -> Tuple[bool, str]:
    """
    Validate URL format
    Returns: (is_valid, error_message)
    """
    if not url:
        return True, ""  # URL is optional
    
    url_pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    
    if not re.match(url_pattern, url):
        return False, "Invalid URL format"
    
    if len(url) > 2048:
        return False, "URL is too long"
    
    # Block localhost and private IPs for security
    blocked_patterns = [
        r'localhost',
        r'127\.0\.0\.1',
        r'192\.168\.',
        r'10\.',
        r'172\.(1[6-9]|2[0-9]|3[0-1])\.'
    ]
    
    for pattern in blocked_patterns:
        if re.search(pattern, url.lower()):
            return False, "URLs pointing to local/private networks are not allowed"
    
    return True, ""

def sanitize_html(text: str) -> str:
    """
    Remove HTML tags from text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    
    # Remove HTML entities
    clean = re.sub(r'&[a-zA-Z]+;', '', clean)
    
    return clean.strip()

def validate_slug_format(slug: str) -> Tuple[bool, str]:
    """
    Validate slug format (used in organizations.py)
    Returns: (is_valid, error_message)
    """
    if not slug:
        return False, "Slug is required"
    
    if len(slug) < 3:
        return False, "Slug must be at least 3 characters"
    
    if len(slug) > 50:
        return False, "Slug must be less than 50 characters"
    
    # Only lowercase letters, numbers, and hyphens
    if not re.match(r'^[a-z0-9-]+$', slug):
        return False, "Slug can only contain lowercase letters, numbers, and hyphens"
    
    # Cannot start or end with hyphen
    if slug.startswith('-') or slug.endswith('-'):
        return False, "Slug cannot start or end with a hyphen"
    
    # Cannot have consecutive hyphens
    if '--' in slug:
        return False, "Slug cannot contain consecutive hyphens"
    
    return True, ""