"""
Repository Processor Module

Handles cloning, filtering, and extracting code from GitHub repositories.
"""

import os
import re
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from git import Repo, InvalidGitRepositoryError, GitCommandError

# Directories to ignore
IGNORE_DIRS = {
    '.git', 'node_modules', 'venv', '.venv', '__pycache__',
    'dist', 'build', 'coverage', '.idea', '.vscode',
    '.pytest_cache', '.mypy_cache', '.ruff_cache'
}

# File extensions to ignore (binary/generated)
IGNORE_EXTENSIONS = {
    '.pyc', '.pyo', '.so', '.dll', '.exe', '.bin',
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg',
    '.mp3', '.mp4', '.avi', '.mov', '.zip', '.tar', '.gz'
}

# High-priority files (documentation and config)
HIGH_PRIORITY_FILES = {
    'README.md', 'README', 'readme.md', 'readme',
    'LICENSE', 'license', 'COPYING', 'copyright',
    'package.json', 'requirements.txt', 'pyproject.toml',
    'setup.py', 'setup.cfg', 'Cargo.toml', 'go.mod',
    'Gemfile.lock', 'pom.xml', 'build.gradle'
}

# Medium-priority files (entry points)
MEDIUM_PRIORITY_FILES = {
    'main.py', 'app.py', 'server.py', 'index.py',
    'index.js', 'index.ts', 'wsgi.py', 'asgi.py',
    'Dockerfile', 'docker-compose.yml'
}

# File extensions to process
SUPPORTED_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h',
    '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala',
    '.html', '.css', '.scss', '.sql', '.sh', '.yaml', '.yml', '.json',
    '.md', '.txt', '.toml'
}


class RepositoryProcessor:
    """
    Processes GitHub repositories by cloning, filtering, and extracting code.
    """

    def __init__(self, clone_dir: str = None):
        """
        Initialize the repository processor.

        Args:
            clone_dir: Directory to clone the repository into.
                       If None, uses a temporary directory.
        """
        self.clone_dir = Path(clone_dir) if clone_dir else Path(temp_repo_dir())
        self.repo: Optional[Repo] = None
        self.files_context: List[Dict[str, str]] = []

    def clone_repository(self, url: str) -> bool:
        """
        Clone a GitHub repository.

        Args:
            url: The GitHub repository URL.

        Returns:
            True if cloning succeeded, False otherwise.
        """
        try:
            # Validate URL format
            if not self._validate_url(url):
                return False

            # Always ensure the directory is clean before cloning
            import shutil
            if self.clone_dir.exists():
                print(f"Cleaning up existing clone: {self.clone_dir}")
                shutil.rmtree(self.clone_dir, ignore_errors=True)

            # Create fresh temp directory for this clone
            self.clone_dir = Path(tempfile.mkdtemp(prefix='gh_explainer_'))

            # Do not assume the repository uses "main". Git resolves the
            # remote's default branch while keeping the clone shallow.
            self.repo = Repo.clone_from(url, str(self.clone_dir), depth=1)
            return True

        except InvalidGitRepositoryError:
            print(f"Error: '{url}' is not a valid Git repository.")
            return False
        except GitCommandError as e:
            print(f"Error cloning repository: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error cloning repository: {e}")
            return False

    def _validate_url(self, url: str) -> bool:
        """
        Validate the GitHub repository URL.

        Args:
            url: The URL to validate.

        Returns:
            True if valid, False otherwise.
        """
        # Basic URL validation
        pattern = r'^https://github\.com/([^/]+)/([^/?#]+?)/?$'
        return bool(re.match(pattern, url, re.IGNORECASE))

    def process_repository(self) -> List[Dict[str, str]]:
        """
        Process the cloned repository and extract relevant files.

        Returns:
            List of file contexts with path and content.
        """
        if not self.repo or not self.repo.bare:
            # Not a bare repo, need to walk the working tree
            repo_path = self.repo.working_tree_dir
        else:
            repo_path = self.clone_dir

        if not repo_path or not os.path.exists(repo_path):
            print("Repository path is invalid or does not exist.")
            return []

        # Walk through repository files
        file_contexts = []
        for root, dirs, files in os.walk(repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            for file in files:
                file_path = Path(root) / file

                # Never follow or read symlinked files from a cloned repo.
                if file_path.is_symlink():
                    continue

                # Skip ignored extensions
                if file_path.suffix.lower() in IGNORE_EXTENSIONS:
                    continue

                # Get relative path from repo root
                rel_path = os.path.relpath(file_path, repo_path)

                # Calculate priority score
                priority = self._calculate_priority(rel_path)

                # Only include files with sufficient priority
                if priority >= 1:
                    try:
                        content = self._read_file(file_path)
                        if content:
                            file_contexts.append({
                                'path': rel_path,
                                'content': content,
                                'priority': priority
                            })
                    except Exception as e:
                        print(f"Error reading {rel_path}: {e}")
                        continue

        # Sort by priority (descending) then by path
        file_contexts.sort(key=lambda x: (-x['priority'], x['path']))

        self.files_context = file_contexts
        return file_contexts

    def _calculate_priority(self, rel_path: str) -> int:
        """
        Calculate the priority score for a file.

        Args:
            rel_path: Relative path of the file in the repository.

        Returns:
            Priority score (higher = more important).
        """
        filename = os.path.basename(rel_path)
        ext = Path(rel_path).suffix.lower()

        # High priority files
        if filename in HIGH_PRIORITY_FILES:
            return 10

        # Medium priority files
        if filename in MEDIUM_PRIORITY_FILES:
            return 8

        # Source code files
        if ext in {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs'}:
            return 6

        # Documentation and config files
        if ext in {'.md', '.txt', '.json', '.yaml', '.yml', '.toml'}:
            return 5

        # Web assets (lower priority but still relevant)
        if ext in {'.html', '.css', '.scss'}:
            return 3

        # Default: ignore
        return 0

    def _read_file(self, file_path: Path) -> Optional[str]:
        """
        Read a file and return its content as text.

        Args:
            file_path: Path to the file.

        Returns:
            File content as string, or None if unreadable.
        """
        try:
            # Try UTF-8 first, then fallback to latin-1 for some formats
            # A NUL byte is a reliable indication that this is not text.
            raw_sample = file_path.read_bytes()[:4096]
            if b'\x00' in raw_sample:
                return None
            content = file_path.read_text(encoding='utf-8', errors='ignore')

            # Skip files that are too large (limit to ~50KB per file)
            if len(content) > 50000:
                return None

            return content

        except Exception:
            return None

    def get_files_context(self) -> List[Dict[str, str]]:
        """
        Get the extracted files context.

        Returns:
            List of file contexts.
        """
        return self.files_context

    def cleanup(self):
        """
        Clean up the cloned repository.
        """
        if self.clone_dir and self.clone_dir.exists():
            import shutil
            try:
                # Use force=True to handle locked files on Windows
                shutil.rmtree(self.clone_dir, ignore_errors=True)
                print(f"Cleaned up repository clone: {self.clone_dir}")
            except Exception as e:
                print(f"Warning: Could not cleanup {self.clone_dir}: {e}")


def temp_repo_dir() -> str:
    """
    Get the temporary directory for cloning repositories.

    Returns:
        Path to the temporary directory.
    """
    import tempfile
    return tempfile.mkdtemp(prefix='gh_explainer_')
