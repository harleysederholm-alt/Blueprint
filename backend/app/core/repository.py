"""
Repository Analyzer - Git Operations and File Tree Extraction
"""

import asyncio
import logging
import os
import shutil
import stat
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import git
from git import Repo

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class FileInfo:
    """Information about a single file."""
    path: str
    relative_path: str
    size_bytes: int
    extension: str
    language: Optional[str] = None
    is_critical: bool = False


@dataclass
class FileTree:
    """Complete file tree structure."""
    root: str
    total_files: int
    total_size_bytes: int
    files: list[FileInfo] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)  # language -> file count
    

@dataclass  
class CriticalFile:
    """A file identified as architecturally significant."""
    path: str
    category: str  # "entry_point", "config", "router", "model", "service", "test"
    reason: str
    content: Optional[str] = None


# Language detection by extension
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".scala": "scala",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
}

# Critical file patterns for architecture detection
CRITICAL_PATTERNS = {
    "entry_point": [
        "main.py", "app.py", "index.js", "index.ts", "main.go", "main.rs",
        "server.py", "server.js", "server.ts", "application.py",
        "__main__.py", "cli.py", "run.py",
    ],
    "config": [
        "config.py", "config.js", "config.ts", "settings.py", "settings.js",
        "package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml",
        ".env.example", "docker-compose.yml", "Dockerfile",
        "tsconfig.json", "vite.config.ts", "next.config.js", "next.config.mjs",
    ],
    "router": [
        "routes.py", "router.py", "urls.py", "routes.js", "routes.ts",
        "api.py", "endpoints.py", "handlers.go",
    ],
    "model": [
        "models.py", "model.py", "schema.py", "schemas.py", "types.ts",
        "entities.py", "domain.py",
    ],
    "service": [
        "service.py", "services.py", "controller.py", "controllers.py",
        "usecase.py", "interactor.py",
    ],
    "database": [
        "database.py", "db.py", "repository.py", "repositories.py",
        "migrations/", "alembic/",
    ],
}


def handle_readonly(func, path, exc_info):
    """Handle read-only files during cleanup on Windows."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


class RepositoryAnalyzer:
    """Analyzes Git repositories for architectural understanding."""
    
    def __init__(self):
        self.repos_path = settings.get_repos_path()
        self.repo: Optional[Repo] = None
        self.repo_path: Optional[Path] = None
        
    async def clone(self, url: str, branch: Optional[str] = None) -> Path:
        """
        Clone a repository and return the local path.
        
        Args:
            url: Git repository URL
            branch: Specific branch to clone (default: default branch)
            
        Returns:
            Path to cloned repository
        """
        # Generate unique folder name from URL
        repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")
        repo_hash = str(hash(url))[-8:]
        folder_name = f"{repo_name}_{repo_hash}"
        
        self.repo_path = self.repos_path / folder_name
        
        # Clean up if exists
        if self.repo_path.exists():
            logger.info(f"Cleaning up existing repo at {self.repo_path}")
            shutil.rmtree(self.repo_path, onerror=handle_readonly)
        
        logger.info(f"Cloning {url} to {self.repo_path}")
        
        # Clone in thread pool (git operations are blocking)
        loop = asyncio.get_event_loop()
        
        clone_kwargs = {
            "url": url,
            "to_path": str(self.repo_path),
            "depth": 1,  # Shallow clone for speed
        }
        if branch:
            clone_kwargs["branch"] = branch
            
        self.repo = await loop.run_in_executor(
            None,
            lambda: Repo.clone_from(**clone_kwargs)
        )
        
        logger.info(f"Cloned successfully: {self.repo_path}")
        return self.repo_path
    
    async def get_file_tree(self, max_files: int = None) -> FileTree:
        """
        Extract complete file tree with metadata.
        
        Args:
            max_files: Maximum files to include (for large repos)
            
        Returns:
            FileTree with all files and language statistics
        """
        if not self.repo_path:
            raise ValueError("Repository not cloned. Call clone() first.")
        
        max_files = max_files or settings.max_files_to_parse
        
        files: list[FileInfo] = []
        directories: set[str] = set()
        languages: dict[str, int] = {}
        total_size = 0
        
        # Directories to skip
        skip_dirs = {
            ".git", "node_modules", "__pycache__", ".venv", "venv",
            "dist", "build", ".next", ".nuxt", "target", ".idea",
            ".vscode", "coverage", ".pytest_cache", ".mypy_cache",
        }
        
        # Extensions to skip
        skip_extensions = {
            ".pyc", ".pyo", ".so", ".dll", ".exe", ".bin",
            ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg",
            ".woff", ".woff2", ".ttf", ".eot",
            ".mp3", ".mp4", ".avi", ".mov",
            ".zip", ".tar", ".gz", ".rar",
            ".lock", ".sum",
        }
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            rel_root = Path(root).relative_to(self.repo_path)
            if str(rel_root) != ".":
                directories.add(str(rel_root))
            
            for filename in filenames:
                if len(files) >= max_files:
                    break
                    
                filepath = Path(root) / filename
                ext = filepath.suffix.lower()
                
                # Skip binary and unwanted files
                if ext in skip_extensions:
                    continue
                    
                try:
                    size = filepath.stat().st_size
                    # Skip very large files (>1MB)
                    if size > 1_000_000:
                        continue
                        
                    rel_path = str(filepath.relative_to(self.repo_path))
                    language = EXTENSION_TO_LANGUAGE.get(ext)
                    
                    # Track language stats
                    if language:
                        languages[language] = languages.get(language, 0) + 1
                    
                    # Check if critical file
                    is_critical = self._is_critical_file(filename, rel_path)
                    
                    files.append(FileInfo(
                        path=str(filepath),
                        relative_path=rel_path,
                        size_bytes=size,
                        extension=ext,
                        language=language,
                        is_critical=is_critical,
                    ))
                    total_size += size
                    
                except (OSError, PermissionError):
                    continue
        
        return FileTree(
            root=str(self.repo_path),
            total_files=len(files),
            total_size_bytes=total_size,
            files=files,
            directories=list(directories),
            languages=languages,
        )
    
    def _is_critical_file(self, filename: str, rel_path: str) -> bool:
        """Check if a file is architecturally critical."""
        filename_lower = filename.lower()
        
        for category, patterns in CRITICAL_PATTERNS.items():
            for pattern in patterns:
                if pattern.endswith("/"):
                    # Directory pattern
                    if pattern.rstrip("/") in rel_path:
                        return True
                elif filename_lower == pattern.lower():
                    return True
                    
        return False
    
    async def get_critical_files(self, file_tree: FileTree) -> list[CriticalFile]:
        """
        Identify and return architecturally significant files.
        
        Args:
            file_tree: Previously extracted file tree
            
        Returns:
            List of critical files with categories and content
        """
        critical_files: list[CriticalFile] = []
        
        for file_info in file_tree.files:
            if not file_info.is_critical:
                continue
                
            # Determine category
            category = self._categorize_file(file_info.relative_path)
            reason = self._get_critical_reason(file_info.relative_path, category)
            
            # Read content (with size limit)
            content = None
            try:
                with open(file_info.path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(50_000)  # First 50KB
            except Exception:
                pass
            
            critical_files.append(CriticalFile(
                path=file_info.relative_path,
                category=category,
                reason=reason,
                content=content,
            ))
        
        return critical_files
    
    def _categorize_file(self, rel_path: str) -> str:
        """Determine the category of a critical file."""
        filename = Path(rel_path).name.lower()
        
        for category, patterns in CRITICAL_PATTERNS.items():
            for pattern in patterns:
                if pattern.endswith("/"):
                    if pattern.rstrip("/") in rel_path:
                        return category
                elif filename == pattern.lower():
                    return category
                    
        return "other"
    
    def _get_critical_reason(self, rel_path: str, category: str) -> str:
        """Explain why a file is critical."""
        reasons = {
            "entry_point": "Application entry point - defines startup behavior",
            "config": "Configuration file - defines settings and dependencies",
            "router": "Router/URL mapping - defines API structure",
            "model": "Data models - defines domain structure",
            "service": "Service layer - contains business logic",
            "database": "Database layer - defines data persistence",
        }
        return reasons.get(category, "Architecturally significant file")
    
    async def extract_dependency_info(self) -> dict:
        """
        Extract dependency information from package files.
        
        Returns:
            Dictionary with dependencies by ecosystem
        """
        if not self.repo_path:
            raise ValueError("Repository not cloned. Call clone() first.")
        
        dependencies = {
            "npm": None,
            "python": None,
            "go": None,
            "rust": None,
        }
        
        # package.json (Node.js)
        package_json = self.repo_path / "package.json"
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                dependencies["npm"] = {
                    "dependencies": data.get("dependencies", {}),
                    "devDependencies": data.get("devDependencies", {}),
                }
            except Exception:
                pass
        
        # pyproject.toml (Python)
        pyproject = self.repo_path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                deps = data.get("project", {}).get("dependencies", [])
                dependencies["python"] = {"dependencies": deps}
            except Exception:
                pass
        
        # requirements.txt fallback
        requirements = self.repo_path / "requirements.txt"
        if requirements.exists() and not dependencies["python"]:
            try:
                with open(requirements) as f:
                    deps = [l.strip() for l in f if l.strip() and not l.startswith("#")]
                dependencies["python"] = {"dependencies": deps}
            except Exception:
                pass
        
        # go.mod (Go)
        go_mod = self.repo_path / "go.mod"
        if go_mod.exists():
            try:
                with open(go_mod) as f:
                    content = f.read()
                dependencies["go"] = {"raw": content}
            except Exception:
                pass
        
        # Cargo.toml (Rust)
        cargo = self.repo_path / "Cargo.toml"
        if cargo.exists():
            try:
                import tomllib
                with open(cargo, "rb") as f:
                    data = tomllib.load(f)
                dependencies["rust"] = {
                    "dependencies": data.get("dependencies", {}),
                }
            except Exception:
                pass
        
        return {k: v for k, v in dependencies.items() if v is not None}
    
    def cleanup(self):
        """Remove cloned repository."""
        if self.repo_path and self.repo_path.exists():
            shutil.rmtree(self.repo_path, onerror=handle_readonly)
            logger.info(f"Cleaned up {self.repo_path}")
