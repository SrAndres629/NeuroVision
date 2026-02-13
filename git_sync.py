import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# --- Configuration & Styling ---
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger("git_sync")

class GitSync:
    """
    Silicon Valley Genius Edition: Git Automation Script.
    Designed for production environments with high reliability.
    """

    def __init__(self, commit_message: Optional[str] = None):
        self.project_path = Path(__file__).parent.absolute()
        self.commit_message = commit_message or f"auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    def run_command(self, command: List[str]) -> bool:
        """Executes a shell command and logs output/errors."""
        try:
            logger.info(f"Executing: {' '.join(command)}")
            result = subprocess.run(
                command, 
                cwd=self.project_path, 
                capture_output=True, 
                text=True, 
                check=True
            )
            if result.stdout:
                logger.debug(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error output: {e.stderr}")
            return False

    def sync(self):
        """Main synchronization workflow."""
        logger.info("🚀 Starting Git synchronization...")

        # 1. Add changes
        if not self.run_command(["git", "add", "."]):
            sys.exit(1)

        # 2. Check if there are changes to commit
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"], 
            cwd=self.project_path, 
            capture_output=True, 
            text=True
        )
        if not status_proc.stdout.strip():
            logger.info("✨ No changes to commit. Everything is up to date.")
            return

        # 3. Commit
        if not self.run_command(["git", "commit", "-m", self.commit_message]):
            sys.exit(1)

        # 4. Pull latest (rebase recommended for clean history)
        logger.info("📥 Pulling latest changes from remote...")
        if not self.run_command(["git", "pull", "--rebase", "origin", "main"]):
            logger.warning("Pull failed. Attempting to resolve...")
            # If rebase fails, you might need manual intervention, but we'll try a basic pull as fallback
            if not self.run_command(["git", "pull", "origin", "main"]):
               logger.error("Critical: Could not pull from remote. Resolve conflicts manually.")
               sys.exit(1)

        # 5. Push
        logger.info("📤 Pushing changes to GitHub...")
        if not self.run_command(["git", "push", "origin", "main"]):
            logger.error("❌ Failed to push changes. Check your connection or permissions.")
            sys.exit(1)

        logger.info("✅ Synchronization complete! Project is safe on GitHub.")

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else None
    bot = GitSync(msg)
    bot.sync()
