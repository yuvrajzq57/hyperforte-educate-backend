from django.core.management.base import BaseCommand
from django.utils import timezone
from mcp_integration.client import mcp_client
import asyncio
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check the health of the MCP server'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Checking MCP Server Health...'))
        
        async def check_health():
            try:
                health = await mcp_client.health_check()
                if health.get('status') == 'ok':
                    self.stdout.write(self.style.SUCCESS('✅ MCP Server is healthy!'))
                    self.stdout.write(f"• Status: {health.get('status')}")
                    self.stdout.write(f"• Timestamp: {health.get('timestamp')}")
                    return True
                else:
                    self.stdout.write(self.style.ERROR('❌ MCP Server is not healthy!'))
                    self.stdout.write(f"• Status: {health.get('status', 'unknown')}")
                    self.stdout.write(f"• Error: {health.get('error', 'No error details')}")
                    return False
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to connect to MCP Server: {str(e)}'))
                return False
        
        # Run the async function
        return asyncio.run(check_health())
