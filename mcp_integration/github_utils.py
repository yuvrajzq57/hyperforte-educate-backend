import logging
from typing import Optional, Dict, Any, List, Tuple
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import json
import re

logger = logging.getLogger(__name__)

def extract_github_intent_with_llm(message: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Use LLM to detect GitHub-related intent from user message.
    
    Args:
        message: User's message text
        
    Returns:
        Tuple of (intent_type, params) if GitHub intent is detected, else None
    """
    # First, quick check if it might be GitHub-related
    github_keywords = ['github', 'repo', 'repository', 'commit', 'issue', 'pull request', 'pr', 'branch', 'file', 'code']
    message_lower = message.lower()
    
    if not any(keyword in message_lower for keyword in github_keywords):
        return None
    
    # Use a simple pattern-based approach as fallback for now
    # This can be replaced with actual LLM call later
    patterns = {
        'list_repos': [
            r'list.*(?:my|the|all)?.*repositories?',
            r'show.*(?:my|the|all)?.*repositories?',
            r'my repositories?',
            r'list.*repos',
            r'show.*repos'
        ],
        'get_repo_info': [
            r'(?:get|show).*(?:repo|repository).*(?:info|information|details)',
            r'(?:tell me about|info about).*(?:repo|repository)',
            r'repository.*information'
        ],
        'list_issues': [
            r'list.*issues?',
            r'show.*issues?',
            r'issues? in',
            r'github.*issues?'
        ],
        'list_commits': [
            r'list.*commits?',
            r'show.*commits?',
            r'commits? in',
            r'github.*commits?'
        ],
        'list_pull_requests': [
            r'list.*pull requests?',
            r'show.*pull requests?',
            r'pr.? list',
            r'pulls? in'
        ],
        'list_branches': [
            r'list.*branches?',
            r'show.*branches?',
            r'branches? in'
        ],
        'get_file_content': [
            r'get.*file.*content',
            r'show.*file',
            r'read.*file',
            r'view.*file'
        ]
    }
    
    # Extract owner/repo patterns
    owner_repo_pattern = r'(\w[\w-]*)\/(\w[\w-]*)'
    owner_repo_match = re.search(owner_repo_pattern, message)
    
    # Extract file path pattern (owner/repo/path)
    file_path_pattern = r'(\w[\w-]*)\/(\w[\w-]*)\/(.+)'
    file_path_match = re.search(file_path_pattern, message)
    
    # Check each intent pattern
    for intent, regex_patterns in patterns.items():
        for pattern in regex_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                params = {}
                
                # Extract parameters based on intent
                if intent in ['list_issues', 'list_commits', 'list_pull_requests', 'list_branches', 'get_repo_info']:
                    if owner_repo_match:
                        params['owner'], params['repo'] = owner_repo_match.groups()
                
                elif intent == 'get_file_content':
                    if file_path_match:
                        params['owner'], params['repo'], params['path'] = file_path_match.groups()
                    elif owner_repo_match:
                        # If only owner/repo, ask for path
                        params['owner'], params['repo'] = owner_repo_match.groups()
                
                return intent, params
    
    # If no specific pattern matched but GitHub keywords exist, try to infer
    if owner_repo_match:
        owner, repo = owner_repo_match.groups()
        # Default to repo info if we have owner/repo but no specific intent
        return 'get_repo_info', {'owner': owner, 'repo': repo}
    
    return None

# Keep the old function as fallback
def extract_github_intent(message: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Extract GitHub-related intent from user message.
    
    Args:
        message: User's message text
        
    Returns:
        Tuple of (intent_type, params) if GitHub intent is detected, else None
    """
    # Try the LLM-based approach first
    result = extract_github_intent_with_llm(message)
    if result:
        return result
    
    # Fallback to basic patterns
    message_lower = message.lower()
    
    # Check for repository-related intents
    if any(keyword in message_lower for keyword in ['list my repos', 'my repositories', 'show my github repos', 'list all my repositories', 'list my repositories', 'show my repositories', 'list all the repositories']):
        return 'list_repos', {}
    
    return None

def format_github_response(intent_type: str, data: List[Dict[str, Any]], **kwargs) -> str:
    """
    Format GitHub API response into a user-friendly message.
    
    Args:
        intent_type: Type of GitHub intent
        data: List of response data from GitHub API
        **kwargs: Additional parameters (repo, owner, etc.)
    
    Returns:
        Formatted string response
    """
    if not data:
        return "No data found."
    
    if intent_type == 'list_repos':
        response = ["Here are your GitHub repositories:"]
        for repo in data[:10]:  # Limit to 10 repos
            response.append(f"• {repo.get('full_name')} - {repo.get('description', 'No description')}")
        if len(data) > 10:
            response.append(f"\n...and {len(data) - 10} more repositories.")
        return "\n".join(response)
        
    elif intent_type == 'list_issues':
        repo = kwargs.get('repo', 'this repository')
        response = [f"Open issues in {repo}:"]
        for issue in data[:10]:  # Limit to 10 issues
            response.append(f"• #{issue.get('number')} {issue.get('title')}")
        if len(data) > 10:
            response.append(f"\n...and {len(data) - 10} more issues.")
        return "\n".join(response)
        
    elif intent_type == 'list_commits':
        repo = kwargs.get('repo', 'this repository')
        response = [f"Recent commits in {repo}:"]
        for commit in data[:10]:  # Limit to 10 commits
            sha = commit.get('sha', '')[:7]
            message = commit.get('commit', {}).get('message', 'No message').split('\n')[0]
            author = commit.get('commit', {}).get('author', {}).get('name', 'Unknown')
            response.append(f"• {sha} - {message} (by {author})")
        if len(data) > 10:
            response.append(f"\n...and {len(data) - 10} more commits.")
        return "\n".join(response)
    
    elif intent_type == 'get_repo_info':
        if isinstance(data, dict):
            repo = data
            response = [
                f"Repository Information for {repo.get('full_name', 'Unknown')}:",
                f"• Description: {repo.get('description', 'No description')}",
                f"• Language: {repo.get('language', 'Not specified')}",
                f"• Stars: {repo.get('stargazers_count', 0)}",
                f"• Forks: {repo.get('forks_count', 0)}",
                f"• Open Issues: {repo.get('open_issues_count', 0)}",
                f"• Created: {repo.get('created_at', 'Unknown')}",
                f"• Updated: {repo.get('updated_at', 'Unknown')}",
                f"• Clone URL: {repo.get('clone_url', 'Not available')}",
            ]
            return "\n".join(response)
        else:
            return "Repository information not available."
    
    elif intent_type == 'list_pull_requests':
        repo = kwargs.get('repo', 'this repository')
        response = [f"Pull requests in {repo}:"]
        for pr in data[:10]:  # Limit to 10 PRs
            response.append(f"• #{pr.get('number')} {pr.get('title')} (by {pr.get('user', {}).get('login', 'Unknown')})")
        if len(data) > 10:
            response.append(f"\n...and {len(data) - 10} more pull requests.")
        return "\n".join(response)
    
    elif intent_type == 'list_branches':
        repo = kwargs.get('repo', 'this repository')
        response = [f"Branches in {repo}:"]
        for branch in data[:10]:  # Limit to 10 branches
            response.append(f"• {branch.get('name', 'Unknown')}")
        if len(data) > 10:
            response.append(f"\n...and {len(data) - 10} more branches.")
        return "\n".join(response)
    
    elif intent_type == 'get_file_content':
        if isinstance(data, dict):
            if data.get('encoding') == 'base64':
                import base64
                try:
                    content = base64.b64decode(data.get('content', '')).decode('utf-8')
                    # Truncate if too long
                    if len(content) > 1000:
                        content = content[:1000] + "\n... (truncated)"
                    return f"File content for {data.get('name', 'Unknown')}:\n\n{content}"
                except:
                    return "Unable to decode file content."
            else:
                return "File content is not in a readable format."
        else:
            return "File not found or not accessible."
    
    return "Here's the information you requested."

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
