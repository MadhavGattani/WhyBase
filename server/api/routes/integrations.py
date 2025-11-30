# server/api/routes/integrations.py
import os
import secrets
from datetime import datetime
from flask import Blueprint, request, jsonify, redirect
from api.db import get_session
from api.models.integrations import Integration, Repository, Issue
from api.services.github import GitHubService, parse_github_datetime
from api.middleware import get_current_user, get_user_organization
from api.middleware.rate_limit import rate_limit

integrations_bp = Blueprint('integrations', __name__)
AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Store OAuth states temporarily (in production, use Redis)
oauth_states = {}


@integrations_bp.route("/integrations", methods=["GET"])
def get_integrations():
    """Get user's integrations"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"integrations": []})
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        integrations = session.query(Integration).filter(
            Integration.user_id == current_user.id,
            Integration.is_active == True
        ).all()
        
        result = [i.to_dict() for i in integrations]
        session.close()
        return jsonify({"integrations": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/integrations/github/connect", methods=["GET"])
def github_connect():
    """Initiate GitHub OAuth flow"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Generate state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        "user_id": current_user.id,
        "created_at": datetime.utcnow()
    }
    
    oauth_url = GitHubService.get_oauth_url(state)
    return jsonify({"oauth_url": oauth_url})


@integrations_bp.route("/integrations/github/callback", methods=["GET"])
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    
    if error:
        return redirect(f"{FRONTEND_URL}/settings/integrations?error={error}")
    
    if not code or not state:
        return redirect(f"{FRONTEND_URL}/settings/integrations?error=missing_params")
    
    # Validate state
    state_data = oauth_states.pop(state, None)
    if not state_data:
        return redirect(f"{FRONTEND_URL}/settings/integrations?error=invalid_state")
    
    user_id = state_data["user_id"]
    
    try:
        # Exchange code for token
        token_data = GitHubService.exchange_code_for_token(code)
        
        if "error" in token_data:
            return redirect(f"{FRONTEND_URL}/settings/integrations?error={token_data['error']}")
        
        access_token = token_data.get("access_token")
        scopes = token_data.get("scope", "")
        
        # Get GitHub user info
        gh = GitHubService(access_token)
        gh_user = gh.get_user()
        
        session = get_session()
        if not session:
            return redirect(f"{FRONTEND_URL}/settings/integrations?error=db_error")
        
        try:
            # Check for existing integration
            existing = session.query(Integration).filter(
                Integration.user_id == user_id,
                Integration.provider == "github"
            ).first()
            
            if existing:
                # Update existing integration
                existing.access_token = access_token
                existing.provider_user_id = str(gh_user["id"])
                existing.provider_username = gh_user["login"]
                existing.scopes = scopes
                existing.is_active = True
                existing.updated_at = datetime.utcnow()
            else:
                # Create new integration
                integration = Integration(
                    user_id=user_id,
                    provider="github",
                    provider_user_id=str(gh_user["id"]),
                    provider_username=gh_user["login"],
                    access_token=access_token,
                    scopes=scopes
                )
                session.add(integration)
            
            session.commit()
            session.close()
            
            return redirect(f"{FRONTEND_URL}/settings/integrations?success=github_connected")
            
        except Exception as e:
            session.rollback()
            session.close()
            return redirect(f"{FRONTEND_URL}/settings/integrations?error=save_failed")
        
    except Exception as e:
        print(f"GitHub OAuth error: {e}")
        return redirect(f"{FRONTEND_URL}/settings/integrations?error=oauth_failed")


@integrations_bp.route("/integrations/github/disconnect", methods=["POST"])
def github_disconnect():
    """Disconnect GitHub integration"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        integration = session.query(Integration).filter(
            Integration.user_id == current_user.id,
            Integration.provider == "github"
        ).first()
        
        if not integration:
            session.close()
            return jsonify({"error": "Integration not found"}), 404
        
        # Delete integration (cascade deletes repos and issues)
        session.delete(integration)
        session.commit()
        session.close()
        
        return jsonify({"message": "GitHub disconnected"})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/integrations/github/repositories", methods=["GET"])
def get_github_repositories():
    """Get synced repositories"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"repositories": []})
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        integration = session.query(Integration).filter(
            Integration.user_id == current_user.id,
            Integration.provider == "github",
            Integration.is_active == True
        ).first()
        
        if not integration:
            session.close()
            return jsonify({"repositories": []})
        
        repos = session.query(Repository).filter(
            Repository.integration_id == integration.id
        ).order_by(Repository.updated_at.desc()).all()
        
        result = [r.to_dict() for r in repos]
        session.close()
        return jsonify({"repositories": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/integrations/github/sync", methods=["POST"])
@rate_limit(max_requests=5, window_seconds=60)
def sync_github():
    """Sync repositories and issues from GitHub"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        integration = session.query(Integration).filter(
            Integration.user_id == current_user.id,
            Integration.provider == "github",
            Integration.is_active == True
        ).first()
        
        if not integration:
            session.close()
            return jsonify({"error": "GitHub not connected"}), 400
        
        gh = GitHubService(integration.access_token)
        
        # Fetch repositories
        gh_repos = gh.get_repositories(per_page=50)
        synced_repos = 0
        synced_issues = 0
        
        for gh_repo in gh_repos:
            # Skip forks optionally
            if gh_repo.get("fork"):
                continue
            
            # Find or create repository
            repo = session.query(Repository).filter(
                Repository.integration_id == integration.id,
                Repository.github_id == gh_repo["id"]
            ).first()
            
            if not repo:
                repo = Repository(integration_id=integration.id, github_id=gh_repo["id"])
                session.add(repo)
            
            # Update repository data
            repo.name = gh_repo["name"]
            repo.full_name = gh_repo["full_name"]
            repo.description = gh_repo.get("description")
            repo.url = gh_repo["html_url"]
            repo.is_private = gh_repo.get("private", False)
            repo.default_branch = gh_repo.get("default_branch", "main")
            repo.language = gh_repo.get("language")
            repo.stars_count = gh_repo.get("stargazers_count", 0)
            repo.forks_count = gh_repo.get("forks_count", 0)
            repo.open_issues_count = gh_repo.get("open_issues_count", 0)
            repo.updated_at = datetime.utcnow()
            
            synced_repos += 1
            
            # Sync issues for top repos (limit API calls)
            if synced_repos <= 10 and repo.is_synced:
                try:
                    owner, repo_name = gh_repo["full_name"].split("/")
                    gh_issues = gh.get_issues(owner, repo_name, state="all", per_page=20)
                    
                    for gh_issue in gh_issues:
                        # Skip pull requests
                        if "pull_request" in gh_issue:
                            continue
                        
                        issue = session.query(Issue).filter(
                            Issue.repository_id == repo.id,
                            Issue.github_id == gh_issue["id"]
                        ).first()
                        
                        if not issue:
                            issue = Issue(repository_id=repo.id, github_id=gh_issue["id"])
                            session.add(issue)
                        
                        issue.number = gh_issue["number"]
                        issue.title = gh_issue["title"]
                        issue.body = gh_issue.get("body")
                        issue.state = gh_issue["state"]
                        issue.url = gh_issue["html_url"]
                        issue.labels = [{"name": l["name"], "color": l["color"]} for l in gh_issue.get("labels", [])]
                        issue.assignees = [{"login": a["login"], "avatar_url": a["avatar_url"]} for a in gh_issue.get("assignees", [])]
                        issue.author_login = gh_issue["user"]["login"] if gh_issue.get("user") else None
                        issue.author_avatar = gh_issue["user"]["avatar_url"] if gh_issue.get("user") else None
                        issue.comments_count = gh_issue.get("comments", 0)
                        issue.github_created_at = parse_github_datetime(gh_issue.get("created_at"))
                        issue.github_updated_at = parse_github_datetime(gh_issue.get("updated_at"))
                        issue.github_closed_at = parse_github_datetime(gh_issue.get("closed_at"))
                        issue.updated_at = datetime.utcnow()
                        
                        synced_issues += 1
                        
                except Exception as e:
                    print(f"Error syncing issues for {gh_repo['full_name']}: {e}")
        
        integration.last_sync_at = datetime.utcnow()
        session.commit()
        session.close()
        
        return jsonify({
            "message": "Sync completed",
            "synced_repos": synced_repos,
            "synced_issues": synced_issues
        })
        
    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/integrations/github/repositories/<int:repo_id>/issues", methods=["GET"])
def get_repository_issues(repo_id):
    """Get issues for a repository"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"issues": []})
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Verify user owns this repo
        repo = session.query(Repository).join(Integration).filter(
            Repository.id == repo_id,
            Integration.user_id == current_user.id
        ).first()
        
        if not repo:
            session.close()
            return jsonify({"error": "Repository not found"}), 404
        
        state = request.args.get("state", "all")
        query = session.query(Issue).filter(Issue.repository_id == repo_id)
        
        if state != "all":
            query = query.filter(Issue.state == state)
        
        issues = query.order_by(Issue.github_updated_at.desc()).limit(50).all()
        
        result = [i.to_dict() for i in issues]
        session.close()
        return jsonify({"issues": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500


@integrations_bp.route("/integrations/github/repositories/<int:repo_id>/toggle-sync", methods=["POST"])
def toggle_repository_sync(repo_id):
    """Toggle sync for a repository"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        repo = session.query(Repository).join(Integration).filter(
            Repository.id == repo_id,
            Integration.user_id == current_user.id
        ).first()
        
        if not repo:
            session.close()
            return jsonify({"error": "Repository not found"}), 404
        
        repo.is_synced = not repo.is_synced
        session.commit()
        
        result = repo.to_dict()
        session.close()
        return jsonify({"repository": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500
    
    
@integrations_bp.route("/integrations/github/test", methods=["GET"])
def test_github_data():
    """Test if GitHub data exists"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    from api.models.integrations import Integration, Repository, Issue
    
    integration = session.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.provider == "github"
    ).first()
    
    if not integration:
        session.close()
        return jsonify({"error": "No GitHub integration found"})
    
    repos = session.query(Repository).filter(
        Repository.integration_id == integration.id
    ).count()
    
    issues = session.query(Issue).join(Repository).filter(
        Repository.integration_id == integration.id
    ).count()
    
    session.close()
    
    return jsonify({
        "integration": True,
        "repositories": repos,
        "issues": issues,
        "message": "GitHub data check"
    })