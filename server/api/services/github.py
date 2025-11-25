# server/api/services/github.py
import os
import requests
from datetime import datetime
from typing import Optional, List, Dict

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:5000/api/integrations/github/callback")
GITHUB_API_BASE = "https://api.github.com"


class GitHubService:
    """Service for GitHub OAuth and API interactions"""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Loominal-App"
        }
        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"
    
    @staticmethod
    def get_oauth_url(state: str, scopes: List[str] = None) -> str:
        """Generate GitHub OAuth URL"""
        if scopes is None:
            scopes = ["repo", "read:user", "user:email"]
        
        scope_str = " ".join(scopes)
        return (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={GITHUB_CLIENT_ID}"
            f"&redirect_uri={GITHUB_REDIRECT_URI}"
            f"&scope={scope_str}"
            f"&state={state}"
        )
    
    @staticmethod
    def exchange_code_for_token(code: str) -> Dict:
        """Exchange OAuth code for access token"""
        response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI
            },
            headers={"Accept": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def get_user(self) -> Dict:
        """Get authenticated user info"""
        response = requests.get(
            f"{GITHUB_API_BASE}/user",
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def get_repositories(self, page: int = 1, per_page: int = 30) -> List[Dict]:
        """Get user's repositories"""
        response = requests.get(
            f"{GITHUB_API_BASE}/user/repos",
            headers=self.headers,
            params={
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc"
            },
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    
    def get_repository(self, owner: str, repo: str) -> Dict:
        """Get single repository details"""
        response = requests.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}",
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    
    def get_issues(self, owner: str, repo: str, state: str = "all", page: int = 1, per_page: int = 30) -> List[Dict]:
        """Get repository issues"""
        response = requests.get(
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues",
            headers=self.headers,
            params={
                "state": state,
                "page": page,
                "per_page": per_page,
                "sort": "updated",
                "direction": "desc"
            },
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    
    def get_rate_limit(self) -> Dict:
        """Get API rate limit status"""
        response = requests.get(
            f"{GITHUB_API_BASE}/rate_limit",
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()


def parse_github_datetime(dt_str: str) -> Optional[datetime]:
    """Parse GitHub datetime string"""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except:
        return None