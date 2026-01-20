"""
Evidence Linker - Links claims to source code with line numbers
"""

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from app.core.akg import Evidence

logger = logging.getLogger(__name__)


@dataclass
class EvidenceMatch:
    """A matched piece of evidence."""
    claim_id: str
    file_path: str
    line_start: int
    line_end: int
    content: str
    context_before: list[str]
    context_after: list[str]


class EvidenceLinker:
    """
    Links architectural claims to specific source code locations.
    
    Provides:
    - File content retrieval with line numbers
    - Context extraction around evidence
    - Quote matching
    """
    
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self._file_cache: dict[str, list[str]] = {}
    
    def _get_file_lines(self, file_path: str) -> list[str]:
        """Get file contents as list of lines."""
        if file_path in self._file_cache:
            return self._file_cache[file_path]
        
        full_path = self.repo_path / file_path
        if not full_path.exists():
            return []
        
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            self._file_cache[file_path] = lines
            return lines
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return []
    
    def get_evidence_content(
        self,
        evidence: Evidence,
        context_lines: int = 3,
    ) -> EvidenceMatch:
        """
        Get the full content for a piece of evidence with context.
        
        Args:
            evidence: The evidence to get content for
            context_lines: Number of context lines before/after
            
        Returns:
            EvidenceMatch with content and context
        """
        lines = self._get_file_lines(evidence.file_path)
        
        if not lines:
            return EvidenceMatch(
                claim_id=evidence.claim_id,
                file_path=evidence.file_path,
                line_start=evidence.line_start,
                line_end=evidence.line_end,
                content="[File not found]",
                context_before=[],
                context_after=[],
            )
        
        # Adjust for 0-indexed
        start = max(0, evidence.line_start - 1)
        end = min(len(lines), evidence.line_end)
        
        content_lines = lines[start:end]
        content = "".join(content_lines)
        
        # Get context
        context_start = max(0, start - context_lines)
        context_end = min(len(lines), end + context_lines)
        
        context_before = lines[context_start:start]
        context_after = lines[end:context_end]
        
        return EvidenceMatch(
            claim_id=evidence.claim_id,
            file_path=evidence.file_path,
            line_start=evidence.line_start,
            line_end=evidence.line_end,
            content=content,
            context_before=[l.rstrip() for l in context_before],
            context_after=[l.rstrip() for l in context_after],
        )
    
    def find_quote_location(
        self,
        file_path: str,
        quote: str,
    ) -> Optional[tuple[int, int]]:
        """
        Find the line range where a quote appears.
        
        Args:
            file_path: Path to the file
            quote: Code snippet to find
            
        Returns:
            Tuple of (start_line, end_line) or None if not found
        """
        lines = self._get_file_lines(file_path)
        if not lines:
            return None
        
        full_content = "".join(lines)
        
        # Try exact match
        if quote in full_content:
            # Find starting line
            before_quote = full_content[:full_content.find(quote)]
            start_line = before_quote.count("\n") + 1
            
            # Find ending line
            end_line = start_line + quote.count("\n")
            
            return (start_line, end_line)
        
        # Try normalized match (strip whitespace)
        quote_normalized = " ".join(quote.split())
        for i, line in enumerate(lines):
            line_normalized = " ".join(line.split())
            if quote_normalized in line_normalized:
                return (i + 1, i + 1)
        
        return None
    
    def create_evidence(
        self,
        file_path: str,
        line_start: int,
        line_end: int,
        claim_id: str,
    ) -> Evidence:
        """
        Create an evidence object with the actual code quote.
        
        Args:
            file_path: Path to the file
            line_start: Starting line number
            line_end: Ending line number
            claim_id: Unique claim identifier
            
        Returns:
            Evidence with populated quote
        """
        lines = self._get_file_lines(file_path)
        
        if lines:
            start = max(0, line_start - 1)
            end = min(len(lines), line_end)
            quote = "".join(lines[start:end]).strip()
        else:
            quote = "[Content unavailable]"
        
        return Evidence(
            claim_id=claim_id,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            quote=quote[:500],  # Limit quote length
        )
    
    def get_file_snippet(
        self,
        file_path: str,
        line: int,
        context: int = 5,
    ) -> str:
        """
        Get a snippet of a file around a specific line.
        
        Args:
            file_path: Path to the file
            line: Center line number
            context: Lines of context on each side
            
        Returns:
            Formatted code snippet with line numbers
        """
        lines = self._get_file_lines(file_path)
        if not lines:
            return f"[File not found: {file_path}]"
        
        start = max(0, line - context - 1)
        end = min(len(lines), line + context)
        
        result = []
        for i, content in enumerate(lines[start:end], start=start + 1):
            marker = "→ " if i == line else "  "
            result.append(f"{marker}{i:4d} │ {content.rstrip()}")
        
        return "\n".join(result)
