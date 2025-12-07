import requests
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

class MCPClientError(Exception):
    """Base exception for MCP client errors."""
    pass

class MCPClient:
    """Client for interacting with the Model Context Protocol (MCP) server."""
    
    def __init__(self, base_url: str = None, timeout: int = 10):
        """Initialize the MCP client.
        
        Args:
            base_url: Base URL of the MCP server (default: settings.MCP_SERVER_URL)
            timeout: Request timeout in seconds (default: 10)
        """
        self.base_url = base_url or getattr(settings, 'MCP_SERVER_URL', 'http://localhost:3333')
        self.timeout = timeout
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        access_token: str, 
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the MCP server."""
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            error_msg = f"MCP server returned {e.response.status_code}: {e.response.text}"
            logger.error(error_msg)
            raise MCPClientError(error_msg) from e
        except requests.RequestError as e:
            error_msg = f"Failed to connect to MCP server: {str(e)}"
            logger.error(error_msg)
            raise MCPClientError("Service temporarily unavailable. Please try again later.") from e
        except Exception as e:
            error_msg = f"Unexpected error communicating with MCP server: {str(e)}"
            logger.error(error_msg)
            raise MCPClientError("An unexpected error occurred. Please try again later.") from e
    
    def list_repos(
        self, 
        access_token: str, 
        per_page: int = 10, 
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """List GitHub repositories for the authenticated user."""
        return self._make_request(
            method="GET",
            endpoint="/tools/github/list_repos",
            access_token=access_token,
            params={"per_page": per_page, "page": page},
        )
    
    def list_issues(
        self, 
        access_token: str, 
        owner: str, 
        repo: str, 
        state: str = "open",
        per_page: int = 10, 
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """List issues for a GitHub repository."""
        return self._make_request(
            method="GET",
            endpoint="/tools/github/list_issues",
            access_token=access_token,
            params={
                "owner": owner,
                "repo": repo,
                "state": state,
                "per_page": per_page,
                "page": page,
            },
        )
    
    def list_commits(
        self, 
        access_token: str, 
        owner: str, 
        repo: str, 
        sha: Optional[str] = None,
        path: Optional[str] = None,
        per_page: int = 10, 
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """List commits for a GitHub repository."""
        params = {
            "owner": owner,
            "repo": repo,
            "per_page": per_page,
            "page": page,
        }
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
            
        return self._make_request(
            method="GET",
            endpoint="/tools/github/list_commits",
            access_token=access_token,
            params=params,
        )
    
    def get_file_content(self, access_token: str, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Dict[str, Any]:
        """Get the contents of a file in a repository."""
        params = {
            "owner": owner,
            "repo": repo,
            "path": path,
        }
        if ref:
            params["ref"] = ref
        
        return self._make_request("GET", "/tools/github/get_file_content", access_token, params=params)

    def list_pull_requests(self, access_token: str, owner: str, repo: str, state: str = "open", per_page: int = 10, page: int = 1) -> List[Dict[str, Any]]:
        """List pull requests for a repository."""
        return self._make_request("GET", "/tools/github/list_pull_requests", access_token, params={
            "owner": owner,
            "repo": repo,
            "state": state,
            "per_page": per_page,
            "page": page,
        })

    def create_pull_request(self, access_token: str, owner: str, repo: str, title: str, head: str, base: str, body: Optional[str] = None) -> Dict[str, Any]:
        """Create a new pull request."""
        params = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "head": head,
            "base": base,
        }
        if body:
            params["body"] = body
        
        return self._make_request("POST", "/tools/github/create_pull_request", access_token, params=params)

    def list_branches(self, access_token: str, owner: str, repo: str, per_page: int = 10, page: int = 1) -> List[Dict[str, Any]]:
        """List branches in a repository."""
        return self._make_request("GET", "/tools/github/list_branches", access_token, params={
            "owner": owner,
            "repo": repo,
            "per_page": per_page,
            "page": page,
        })

    def get_repo_info(self, access_token: str, owner: str, repo: str) -> Dict[str, Any]:
        """Get detailed information about a repository."""
        return self._make_request("GET", "/tools/github/get_repo_info", access_token, params={
            "owner": owner,
            "repo": repo,
        })

    def search_repositories(self, access_token: str, query: str, sort: Optional[str] = None, order: str = "desc", per_page: int = 10, page: int = 1) -> Dict[str, Any]:
        """Search for repositories."""
        params = {
            "q": query,
            "order": order,
            "per_page": per_page,
            "page": page,
        }
        if sort:
            params["sort"] = sort
        
        return self._make_request("GET", "/tools/github/search_repositories", access_token, params=params)

    def list_collaborators(self, access_token: str, owner: str, repo: str, per_page: int = 10, page: int = 1) -> List[Dict[str, Any]]:
        """List collaborators on a repository."""
        return self._make_request("GET", "/tools/github/list_collaborators", access_token, params={
            "owner": owner,
            "repo": repo,
            "per_page": per_page,
            "page": page,
        })

    def get_repo_languages(self, access_token: str, owner: str, repo: str) -> Dict[str, int]:
        """Get languages used in a repository."""
        return self._make_request("GET", "/tools/github/get_repo_languages", access_token, params={
            "owner": owner,
            "repo": repo,
        })

    def health_check(self) -> Dict[str, Any]:
        """Check if the MCP server is healthy."""
        try:
            response = requests.get(
                f"{self.base_url.rstrip('/')}/health",
                timeout=5,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"MCP health check failed: {str(e)}")
            return {"status": "error", "error": str(e)}

# Global client instance
mcp_client = MCPClient()
