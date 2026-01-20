"""
Agent Orchestrator - Pipeline coordinator for full repository analysis

Runs the three AI agents in sequence:
1. Architect AI → AKG + C4 diagrams
2. Runtime Analyst AI → Sequence diagrams + data lineage
3. Documentation AI → Audience-specific docs + ADRs
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, Literal, Optional
from pathlib import Path

from pydantic import BaseModel

from app.config import get_settings
from app.core.repository import RepositoryAnalyzer, FileTree, CriticalFile
from app.core.tree_sitter_parser import TreeSitterParser, ParsedFile, get_parser
from app.core.akg_builder import AKGBuilder
from app.core.akg import ArchitecturalKnowledgeGraph
from app.agents.architect import ArchitectAgent
from app.agents.runtime import RuntimeAnalystAgent
from app.agents.documentation import DocumentationAgent, AudienceProfile

logger = logging.getLogger(__name__)
settings = get_settings()


AnalysisStage = Literal[
    "queued",
    "cloning",
    "parsing",
    "building_akg",
    "architect_analysis",
    "architect_complete",
    "runtime_analysis",
    "runtime_complete",
    "documentation",
    "documentation_complete",
    "completed",
    "failed",
]


class AnalysisProgress(BaseModel):
    """Progress update during analysis."""
    stage: AnalysisStage
    message: str
    progress_pct: float = 0.0
    timestamp: str = ""
    result: Optional[dict] = None
    
    def __init__(self, **data):
        if "timestamp" not in data or not data["timestamp"]:
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)


@dataclass
class AnalysisResult:
    """Complete analysis result from all agents."""
    repo_url: str
    branch: Optional[str]
    audience: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Intermediate data
    file_tree: Optional[FileTree] = None
    critical_files: list[CriticalFile] = field(default_factory=list)
    parsed_files: list[ParsedFile] = field(default_factory=list)
    dependencies: dict = field(default_factory=dict)
    
    # AKG
    akg: Optional[ArchitecturalKnowledgeGraph] = None
    
    # Agent outputs
    architecture_analysis: dict = field(default_factory=dict)
    runtime_analysis: dict = field(default_factory=dict)
    documentation: dict = field(default_factory=dict)
    
    # Diagrams
    diagrams: dict = field(default_factory=dict)
    
    # Error
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "repo_url": self.repo_url,
            "branch": self.branch,
            "audience": self.audience,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "architecture": self.architecture_analysis,
            "runtime": self.runtime_analysis,
            "documentation": self.documentation,
            "diagrams": self.diagrams,
            "akg": self.akg.to_dict() if self.akg else None,
            "stats": {
                "total_files": self.file_tree.total_files if self.file_tree else 0,
                "critical_files": len(self.critical_files),
                "parsed_files": len(self.parsed_files),
            },
            "error": self.error,
        }


class AgentOrchestrator:
    """
    Orchestrates the full analysis pipeline.
    
    Coordinates:
    1. Repository cloning and file extraction
    2. Code parsing and AKG building
    3. Architect AI analysis
    4. Runtime Analyst AI analysis
    5. Documentation AI generation
    """
    
    def __init__(self):
        self.repo_analyzer = RepositoryAnalyzer()
        self.tree_sitter_parser = get_parser()
        self.architect_agent = ArchitectAgent()
        self.runtime_agent = RuntimeAnalystAgent()
        self.documentation_agent = DocumentationAgent()
        self.akg_builder: Optional[AKGBuilder] = None
    
    async def run_full_analysis(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        audience: AudienceProfile = "engineer",
    ) -> AsyncGenerator[AnalysisProgress, None]:
        """
        Run the complete analysis pipeline.
        
        Yields progress updates at each stage.
        
        Args:
            repo_url: Git repository URL
            branch: Branch to analyze (default: main/master)
            audience: Target audience for documentation
            
        Yields:
            AnalysisProgress objects with stage updates and results
        """
        result = AnalysisResult(
            repo_url=repo_url,
            branch=branch,
            audience=audience,
            started_at=datetime.utcnow(),
        )
        
        try:
            # Stage 1: Clone repository
            yield AnalysisProgress(
                stage="cloning",
                message=f"Cloning repository: {repo_url}",
                progress_pct=5.0,
            )
            
            repo_path = await self.repo_analyzer.clone(repo_url, branch)
            
            # Stage 2: Extract file tree
            yield AnalysisProgress(
                stage="parsing",
                message="Extracting file tree and identifying critical files",
                progress_pct=10.0,
            )
            
            result.file_tree = await self.repo_analyzer.get_file_tree()
            result.critical_files = await self.repo_analyzer.get_critical_files(result.file_tree)
            result.dependencies = await self.repo_analyzer.extract_dependency_info()
            
            logger.info(f"Found {result.file_tree.total_files} files, {len(result.critical_files)} critical")
            
            # Stage 3: Parse source files with Tree-sitter
            yield AnalysisProgress(
                stage="building_akg",
                message=f"Parsing {result.file_tree.total_files} source files with Tree-sitter",
                progress_pct=20.0,
            )
            
            # Initialize AKG Builder
            self.akg_builder = AKGBuilder(Path(self.repo_analyzer.repo_path))
            
            # Collect all parseable files
            source_files = []
            for file_info in result.file_tree.files:
                file_path = Path(file_info.path)
                if self.tree_sitter_parser.get_language_for_file(str(file_path)):
                    source_files.append(file_path)
            
            # Parse all files using Tree-sitter
            self.akg_builder.parse_directory(source_files)
            parsing_stats = self.akg_builder.get_parsing_stats()
            
            logger.info(
                f"Tree-sitter parsed {parsing_stats['files_parsed']} files: "
                f"{parsing_stats['classes_found']} classes, "
                f"{parsing_stats['functions_found']} functions, "
                f"{parsing_stats['imports_found']} imports. "
                f"(Tree-sitter available: {parsing_stats['tree_sitter_available']})"
            )
            
            # Build AKG from parsed files
            commit_hash = None
            if self.repo_analyzer.repo:
                try:
                    commit_hash = self.repo_analyzer.repo.head.commit.hexsha[:8]
                except Exception:
                    pass
            
            result.akg = self.akg_builder.build_akg(
                repo_name=repo_url.split('/')[-1].replace('.git', ''),
            )
            
            # Stage 4: Architect AI analysis
            yield AnalysisProgress(
                stage="architect_analysis",
                message="Running Architect AI analysis (this may take a few minutes)",
                progress_pct=30.0,
            )
            
            result.architecture_analysis = await self.architect_agent.analyze(
                file_tree=result.file_tree,
                critical_files=result.critical_files,
                dependencies=result.dependencies,
            )
            
            # Populate AKG from analysis
            self.architect_agent.populate_akg(result.architecture_analysis, result.akg)
            
            # Extract diagrams
            arch_diagrams = self.architect_agent.get_diagrams(result.architecture_analysis)
            result.diagrams.update(arch_diagrams)
            
            yield AnalysisProgress(
                stage="architect_complete",
                message="Architect AI analysis complete",
                progress_pct=50.0,
                result=result.architecture_analysis,
            )
            
            # Stage 5: Runtime Analyst AI
            yield AnalysisProgress(
                stage="runtime_analysis",
                message="Running Runtime Analyst AI (tracing flows, identifying bottlenecks)",
                progress_pct=55.0,
            )
            
            result.runtime_analysis = await self.runtime_agent.analyze(
                parsed_files=result.parsed_files,
                architecture_context=result.architecture_analysis,
            )
            
            # Extract runtime diagrams
            runtime_diagrams = self.runtime_agent.get_diagrams(result.runtime_analysis)
            result.diagrams.update(runtime_diagrams)
            
            yield AnalysisProgress(
                stage="runtime_complete",
                message="Runtime Analyst AI complete",
                progress_pct=75.0,
                result=result.runtime_analysis,
            )
            
            # Stage 6: Documentation AI
            yield AnalysisProgress(
                stage="documentation",
                message=f"Generating {audience} documentation",
                progress_pct=80.0,
            )
            
            result.documentation = await self.documentation_agent.generate_documentation(
                architecture_analysis=result.architecture_analysis,
                runtime_analysis=result.runtime_analysis,
                audience=audience,
                repo_url=repo_url,
                commit_hash=commit_hash,
            )
            
            yield AnalysisProgress(
                stage="documentation_complete",
                message="Documentation AI complete",
                progress_pct=95.0,
                result=result.documentation,
            )
            
            # Complete
            result.completed_at = datetime.utcnow()
            
            yield AnalysisProgress(
                stage="completed",
                message="Analysis complete!",
                progress_pct=100.0,
                result=result.to_dict(),
            )
            
        except Exception as e:
            logger.exception(f"Analysis failed: {e}")
            result.error = str(e)
            result.completed_at = datetime.utcnow()
            
            yield AnalysisProgress(
                stage="failed",
                message=f"Analysis failed: {str(e)}",
                progress_pct=0.0,
            )
        
        finally:
            # Cleanup cloned repository
            try:
                self.repo_analyzer.cleanup()
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")
    
    async def run_quick_analysis(
        self,
        repo_url: str,
        branch: Optional[str] = None,
    ) -> dict:
        """
        Run a quick architecture-only analysis.
        
        Skips runtime and documentation for faster results.
        
        Returns:
            Architecture analysis result
        """
        try:
            repo_path = await self.repo_analyzer.clone(repo_url, branch)
            file_tree = await self.repo_analyzer.get_file_tree()
            critical_files = await self.repo_analyzer.get_critical_files(file_tree)
            dependencies = await self.repo_analyzer.extract_dependency_info()
            
            result = await self.architect_agent.analyze(
                file_tree=file_tree,
                critical_files=critical_files,
                dependencies=dependencies,
            )
            
            return result
            
        finally:
            self.repo_analyzer.cleanup()
