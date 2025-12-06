"""
MCP (Model Context Protocol) Integration for HyperForte Educate Platform.

This module provides integration with the Model Context Protocol server for
GitHub-related operations.
"""

# Import the main client for easy access
from .client import mcp_client, MCPClient, MCPClientError  # noqa

# Default app config
# This ensures that the app config is loaded when Django starts
default_app_config = 'mcp_integration.apps.MCPIntegrationConfig'
