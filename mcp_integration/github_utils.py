import logging
from typing import Optional, Dict, Any, List, Tuple
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)

def extract_github_intent(message: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Extract GitHub-related intent from user message.
    
    Args:
        message: User's message text
        
    Returns:
        Tuple of (intent_type, params) if GitHub intent is detected, else None
    """
    message_lower = message.lower()
    
    # Check for repository-related intents
    if any(keyword in message_lower for keyword in ['list my repos', 'my repositories', 'show my github repos', 'list all my repositories', 'list my repositories', 'show my repositories']):
        return 'list_repos', {}
    
    # Check for issue-related intents
    if any(keyword in message_lower for keyword in ['issues in', 'list issues', 'show issues', 'github issues']):
        # Try to extract owner/repo from message
        parts = message_lower.split()
        try:
            repo_idx = parts.index('in')
            if repo_idx + 1 < len(parts):
                repo_part = parts[repo_idx + 1]
                if '/' in repo_part:
                    owner, repo = repo_part.split('/')
                    return 'list_issues', {'owner': owner, 'repo': repo}
        except (ValueError, IndexError):
            pass
        return 'list_issues', {}
    
    # Check for commit-related intents
    if any(keyword in message_lower for keyword in ['commits in', 'list commits', 'show commits', 'github commits']):
        # Try to extract owner/repo from message
        parts = message_lower.split()
        try:
            repo_idx = parts.index('in')
            if repo_idx + 1 < len(parts):
                repo_part = parts[repo_idx + 1]
                if '/' in repo_part:
                    owner, repo = repo_part.split('/')
                    return 'list_commits', {'owner': owner, 'repo': repo}
        except (ValueError, IndexError):
            pass
        return 'list_commits', {}
    
    return None

def format_github_response(intent_type: str, data: List[Dict[str, Any]]) -> str:
    """
    Format GitHub API response into a user-friendly message.
    
    Args:
        intent_type: Type of GitHub intent
        data: Response data from GitHub API
        
    Returns:
        Formatted string response
    """
    if not data:
        return "No data found."
    
    if intent_type == 'list_repos':
        response = ["Here are your GitHub repositories:"]
        for i, repo in enumerate(data[:10], 1):  # Limit to 10 repos
            response.append(f"{i}. {repo['name']} - {repo.get('description', 'No description')}")
        if len(data) > 10:
            response.append(f"\nAnd {len(data) - 10} more repositories...")
        return "\n".join(response)
    
    elif intent_type == 'list_issues':
        repo_name = f"{data[0].get('repository', {}).get('full_name', '')}" if data else "this repository"
        response = [f"Issues in {repo_name}:"]
        for i, issue in enumerate(data[:10], 1):  # Limit to 10 issues
            response.append(f"{i}. #{issue['number']} {issue['title']} - {issue['state']}")
            if issue.get('assignee'):
                response[-1] += f" (Assigned to: {issue['assignee']['login']})"
        if len(data) > 10:
            response.append(f"\nAnd {len(data) - 10} more issues...")
        return "\n".join(response)
    
    elif intent_type == 'list_commits':
        repo_name = f"{data[0].get('repository', {}).get('full_name', '')}" if data else "this repository"
        response = [f"Recent commits in {repo_name}:"]
        for i, commit in enumerate(data[:10], 1):  # Limit to 10 commits
            commit_data = commit.get('commit', {})
            author = commit_data.get('author', {}).get('name', 'Unknown')
            message = commit_data.get('message', 'No message').split('\n')[0][:60]  # First line, max 60 chars
            response.append(f"{i}. {message} - {author}")
        if len(data) > 10:
            response.append(f"\nAnd {len(data) - 10} more commits...")
        return "\n".join(response)
    
    return "I found some GitHub data, but I'm not sure how to display it."

def get_github_token(user) -> Optional[str]:
    """
    Get the GitHub access token for the current user.
    
    Args:
        user: Django User instance
        
    Returns:
        GitHub access token if available, else None
    """
    if not user or not user.is_authenticated:
        logger.warning("User not authenticated")
        return None
    
    try:
        # The GitHubUser model is in the chatbot app
        from chatbot.models import GitHubUser
        github_user = GitHubUser.objects.filter(user=user).first()
        logger.info(f"GitHubUser found for user {user.username}: {github_user is not None}")
        
        if not github_user:
            logger.warning(f"No GitHubUser found for user {user.username}")
            return None
            
        if not github_user.access_token:
            logger.warning(f"GitHubUser exists but no access token for user {user.username}")
            return None
            
        # Check if token is expired
        if github_user.token_expires and github_user.token_expires <= timezone.now():
            logger.warning(f"Token expired for user {user.username}")
            # Token is expired, try to refresh it
            if github_user.refresh_token:
                from .refresh_token import refresh_github_token
                success = refresh_github_token(github_user)
                if not success:
                    logger.error(f"Failed to refresh token for user {user.username}")
                    return None
            else:
                logger.warning(f"No refresh token available for user {user.username}")
                return None
                
        logger.info(f"Returning valid token for user {user.username}")
        return github_user.access_token
    except ImportError:
        logger.error("GitHubUser model not found in chatbot.models")
        return None
    except Exception as e:
        logger.error(f"Error getting GitHub token: {str(e)}")
        return None
