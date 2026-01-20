"""
Git History Navigator - Checkout and analyze different versions

Enables:
- Listing commits and branches
- Checking out specific versions
- Building AKG for each version
- Managing temporary checkouts
"""

import asyncio
import logging
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import git
from git import Repo

from app.core.akg_builder import AKGBuilder
from app.core.akg import ArchitecturalKnowledgeGraph

logger = logging.getLogger(__name__)


@dataclass
class CommitInfo:
    """Information about a Git commit."""
    hash: str
    short_hash: str
    message: str
    author: str
    date: datetime
    
    def to_dict(self) -> dict:
        return {
            "hash": self.hash,
            "short_hash": self.short_hash,
            "message": self.message,
            "author": self.author,
            "date": self.date.isoformat(),
        }


@dataclass
class BranchInfo:
    """Information about a Git branch."""
    name: str
    is_remote: bool
    head_commit: str
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "is_remote": self.is_remote,
            "head_commit": self.head_commit,
        }


class GitHistoryNavigator:
    """
    Navigate Git history and build AKGs for different versions.
    
    Features:
    - List commits and branches
    - Checkout specific versions safely
    - Build AKG snapshots for each version
    - Manage temporary working directories
    """
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.repo: Optional[Repo] = None
        self._temp_dirs: List[Path] = []
    
    def open(self):
        """Open the repository."""
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")
        
        self.repo = Repo(self.repo_path)
    
    def close(self):
        """Clean up temporary directories."""
        for temp_dir in self._temp_dirs:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_dir}: {e}")
        self._temp_dirs.clear()
    
    def list_commits(self, max_count: int = 50, branch: Optional[str] = None) -> List[CommitInfo]:
        """
        List recent commits.
        
        Args:
            max_count: Maximum number of commits to return
            branch: Branch to list commits for (default: current branch)
            
        Returns:
            List of CommitInfo objects
        """
        if not self.repo:
            self.open()
        
        commits = []
        try:
            ref = branch if branch else self.repo.active_branch.name
            for commit in self.repo.iter_commits(ref, max_count=max_count):
                commits.append(CommitInfo(
                    hash=commit.hexsha,
                    short_hash=commit.hexsha[:8],
                    message=commit.message.strip().split('\n')[0][:100],
                    author=str(commit.author),
                    date=datetime.fromtimestamp(commit.committed_date),
                ))
        except Exception as e:
            logger.warning(f"Failed to list commits: {e}")
        
        return commits
    
    def list_branches(self, include_remote: bool = True) -> List[BranchInfo]:
        """
        List all branches.
        
        Args:
            include_remote: Include remote tracking branches
            
        Returns:
            List of BranchInfo objects
        """
        if not self.repo:
            self.open()
        
        branches = []
        
        # Local branches
        for branch in self.repo.branches:
            branches.append(BranchInfo(
                name=branch.name,
                is_remote=False,
                head_commit=branch.commit.hexsha[:8],
            ))
        
        # Remote branches
        if include_remote:
            for ref in self.repo.remote().refs:
                if ref.name != 'origin/HEAD':
                    branches.append(BranchInfo(
                        name=ref.name,
                        is_remote=True,
                        head_commit=ref.commit.hexsha[:8],
                    ))
        
        return branches
    
    def get_commit_info(self, ref: str) -> Optional[CommitInfo]:
        """Get info for a specific commit or ref."""
        if not self.repo:
            self.open()
        
        try:
            commit = self.repo.commit(ref)
            return CommitInfo(
                hash=commit.hexsha,
                short_hash=commit.hexsha[:8],
                message=commit.message.strip().split('\n')[0][:100],
                author=str(commit.author),
                date=datetime.fromtimestamp(commit.committed_date),
            )
        except Exception as e:
            logger.warning(f"Failed to get commit info for {ref}: {e}")
            return None
    
    async def checkout_to_temp(self, ref: str) -> Path:
        """
        Checkout a specific ref to a temporary directory.
        
        This allows analyzing old versions without affecting the current checkout.
        
        Args:
            ref: Commit hash or branch name
            
        Returns:
            Path to temporary directory with the checkout
        """
        if not self.repo:
            self.open()
        
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"blueprint_diff_{ref[:8]}_"))
        self._temp_dirs.append(temp_dir)
        
        try:
            # Clone to temp dir
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: git.Repo.clone_from(
                    str(self.repo_path),
                    str(temp_dir),
                    no_checkout=True,
                )
            )
            
            # Checkout specific ref
            temp_repo = Repo(temp_dir)
            await loop.run_in_executor(
                None,
                lambda: temp_repo.git.checkout(ref)
            )
            
            logger.info(f"Checked out {ref} to {temp_dir}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"Failed to checkout {ref}: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            self._temp_dirs.remove(temp_dir)
            raise
    
    async def build_akg_for_ref(self, ref: str) -> ArchitecturalKnowledgeGraph:
        """
        Build an AKG for a specific commit or branch.
        
        Args:
            ref: Commit hash or branch name
            
        Returns:
            AKG for that version of the codebase
        """
        # Checkout to temp directory
        temp_path = await self.checkout_to_temp(ref)
        
        try:
            # Build AKG
            builder = AKGBuilder(temp_path)
            
            # Collect source files
            source_files = []
            for ext in ['.py', '.ts', '.tsx', '.js', '.jsx', '.go']:
                source_files.extend(temp_path.rglob(f'*{ext}'))
            
            # Filter out common non-source directories
            source_files = [
                f for f in source_files
                if not any(skip in str(f) for skip in [
                    'node_modules', '__pycache__', '.git', 'venv', 
                    'dist', 'build', '.next', 'coverage'
                ])
            ]
            
            # Parse files
            builder.parse_directory(source_files)
            
            # Get commit info for naming
            commit_info = self.get_commit_info(ref)
            repo_name = f"{self.repo_path.name}@{ref[:8]}"
            
            # Build AKG
            akg = builder.build_akg(repo_name=repo_name)
            
            return akg
            
        finally:
            # Cleanup is handled by close()
            pass
    
    def get_diff_refs(self, base_ref: str, target_ref: str) -> tuple:
        """
        Resolve and validate refs for diffing.
        
        Returns:
            Tuple of (base_commit_hash, target_commit_hash)
        """
        if not self.repo:
            self.open()
        
        try:
            base_commit = self.repo.commit(base_ref)
            target_commit = self.repo.commit(target_ref)
            
            return (base_commit.hexsha, target_commit.hexsha)
        except Exception as e:
            logger.error(f"Failed to resolve refs: {e}")
            raise ValueError(f"Invalid refs: {base_ref} or {target_ref}")
    
    def get_changed_files(self, base_ref: str, target_ref: str) -> dict:
        """
        Get list of files changed between two refs.
        
        Returns:
            Dict with 'added', 'modified', 'deleted' file lists
        """
        if not self.repo:
            self.open()
        
        base_commit = self.repo.commit(base_ref)
        target_commit = self.repo.commit(target_ref)
        
        diff = base_commit.diff(target_commit)
        
        return {
            "added": [d.b_path for d in diff.iter_change_type('A')],
            "modified": [d.a_path for d in diff.iter_change_type('M')],
            "deleted": [d.a_path for d in diff.iter_change_type('D')],
            "renamed": [(d.a_path, d.b_path) for d in diff.iter_change_type('R')],
        }
