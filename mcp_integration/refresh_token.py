import logging
import httpx
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

def refresh_github_token(github_user) -> bool:
    """
    Refresh an expired GitHub OAuth token.
    
    Args:
        github_user: GitHubUser instance with refresh_token
        
    Returns:
        bool: True if token was refreshed successfully, False otherwise
    """
    if not github_user or not github_user.refresh_token:
        return False
    
    client_id = getattr(settings, 'GITHUB_CLIENT_ID', '')
    client_secret = getattr(settings, 'GITHUB_CLIENT_SECRET', '')
    
    if not client_id or not client_secret:
        logger.error("GitHub OAuth client ID or secret not configured")
        return False
    
    token_url = "https://github.com/login/oauth/access_token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": github_user.refresh_token,
        "grant_type": "refresh_token",
    }
    
    try:
        with httpx.Client() as client:
            response = client.post(
                token_url,
                headers=headers,
                json=data,
                timeout=10,
            )
            response.raise_for_status()
            token_data = response.json()
            
            if 'access_token' in token_data:
                github_user.access_token = token_data['access_token']
                
                # Update refresh token if a new one was provided
                if 'refresh_token' in token_data:
                    github_user.refresh_token = token_data['refresh_token']
                
                # Set token expiration (default to 1 hour if not provided)
                expires_in = token_data.get('expires_in', 3600)
                github_user.token_expires = timezone.now() + timedelta(seconds=expires_in)
                
                github_user.save()
                return True
            
            logger.error(f"Failed to refresh token: {token_data.get('error', 'Unknown error')}")
            return False
            
    except httpx.HTTPStatusError as e:
        logger.error(f"GitHub token refresh failed with status {e.response.status_code}: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Failed to connect to GitHub for token refresh: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}")
    
    return False
