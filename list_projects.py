"""
Script to list all Overleaf projects to find the correct project name.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from automation import OverleafAutomation
from automation.config import AutomationConfig
from automation.utils import get_logger


async def list_overleaf_projects():
    """List all projects in the user's Overleaf account."""
    logger = get_logger("list_projects")
    
    logger.info("=" * 60)
    logger.info("LISTING OVERLEAF PROJECTS")
    logger.info("=" * 60)
    
    try:
        # Create automation instance with visual mode to see what's happening
        automation = OverleafAutomation(visual_mode=True)
        
        # List all projects
        projects = await automation.list_projects()
        
        print("\n" + "=" * 60)
        print("AVAILABLE PROJECTS")
        print("=" * 60)
        
        for i, project in enumerate(projects, 1):
            print(f"{i}. {project}")
        
        print("\n" + "=" * 60)
        print("Copy the exact project name and update your .env file:")
        print("OVERLEAF_DEFAULT_PROJECT=<exact_project_name>")
        print("=" * 60)
        
        await automation.cleanup()
        
        return projects
        
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    asyncio.run(list_overleaf_projects())
