"""
Architect AI Agent

Principal Software Architect with 20+ years of experience.
Infers architecture from evidence in file tree, dependency graph, and code excerpts.
"""

import logging
from typing import Optional

from app.agents.base import BaseAgent
from app.core.akg import (
    ArchitecturalKnowledgeGraph,
    AKGNode,
    AKGEdge,
    BoundedContext,
    ArchitecturalLayer,
    DesignPattern,
    Evidence,
)
from app.core.repository import FileTree, CriticalFile

logger = logging.getLogger(__name__)


ARCHITECT_SYSTEM_PROMPT = """You are a Principal Software Architect with 20+ years of experience. Your task is to infer the architecture of the provided repository STRICTLY from evidence in the supplied file tree, dependency graph, and code excerpts.

Rules (non-negotiable):
1. Every claim MUST be backed by explicit evidence: file path + line numbers or clear pattern.
2. If evidence is missing or ambiguous, state: "Insufficient evidence to determine X."
3. Distinguish clearly: [Fact] vs [Interpretation] vs [Assumption].
4. Never hallucinate components, patterns, or technologies that are not visible.
5. Use precise terminology (e.g., "hexagonal architecture" only if ports/adapters pattern is evident).
6. Output in structured JSON format only.

Required output fields:
- architecture_style: string (e.g., "Layered monolith with modular boundaries")
- bounded_contexts: array of objects {name, primary_files, responsibilities, evidence_files}
- layers: array of objects {name, modules, description}
- key_design_patterns: array of objects {pattern, description, evidence_files, confidence}
- coupling_cohesion_assessment: {coupling_score: 1-10, cohesion_score: 1-10, explanation_with_evidence}
- c4_context_diagram: Mermaid.js C4Context code (strict syntax)
- c4_container_diagram: Mermaid.js C4Container code
- c4_component_diagram: Mermaid.js C4Component code (main containers only)
- dependency_graph: Mermaid.js flowchart showing module dependencies
- evidence_map: array of {claim_id, file_path, line_range, quote, claim_type}

For bounded contexts, identify:
- Clear domain boundaries
- Modules that change together
- Shared vs isolated data

For patterns, look for:
- Repository pattern (data access abstraction)
- Factory pattern (object creation)
- Strategy pattern (interchangeable algorithms)
- Observer/Event pattern (pub/sub)
- Dependency Injection (constructor injection)
- MVC/MVP/MVVM (UI patterns)
- CQRS (command/query separation)
- Microservices indicators (separate APIs, message queues)

Output valid JSON only. No markdown code blocks around the JSON."""


class ArchitectAgent(BaseAgent):
    """
    Principal Software Architect AI.
    
    Analyzes repository structure and code to infer architectural patterns,
    bounded contexts, layers, and generates C4 diagrams.
    """
    
    @property
    def system_prompt(self) -> str:
        return ARCHITECT_SYSTEM_PROMPT
    
    @property
    def name(self) -> str:
        return "ArchitectAI"
    
    async def analyze(
        self,
        file_tree: FileTree,
        critical_files: list[CriticalFile],
        dependencies: dict,
    ) -> dict:
        """
        Perform architectural analysis.
        
        Args:
            file_tree: Complete file tree with metadata
            critical_files: List of architecturally significant files with content
            dependencies: Extracted dependency information
            
        Returns:
            Complete architectural analysis with diagrams and evidence
        """
        # Build the input context
        user_prompt = self._build_context(file_tree, critical_files, dependencies)
        
        logger.info(f"[{self.name}] Starting analysis with {len(critical_files)} critical files")
        
        # Generate structured response
        result = await self.generate_structured(
            user_prompt=user_prompt,
            temperature=0.2,  # Lower temperature for more deterministic output
        )
        
        return result
    
    def _build_context(
        self,
        file_tree: FileTree,
        critical_files: list[CriticalFile],
        dependencies: dict,
    ) -> str:
        """Build the analysis context for the LLM."""
        sections = []
        
        # File tree summary
        sections.append("## FILE TREE SUMMARY")
        sections.append(f"Total files: {file_tree.total_files}")
        sections.append(f"Total size: {file_tree.total_size_bytes / 1024:.1f} KB")
        sections.append("\n### Languages detected:")
        for lang, count in sorted(file_tree.languages.items(), key=lambda x: -x[1]):
            sections.append(f"- {lang}: {count} files")
        
        # Directory structure
        sections.append("\n### Directory structure:")
        for dir_path in sorted(file_tree.directories)[:50]:
            sections.append(f"  {dir_path}/")
        
        # Dependency information
        if dependencies:
            sections.append("\n## DEPENDENCIES")
            for ecosystem, deps in dependencies.items():
                sections.append(f"\n### {ecosystem.upper()}")
                if isinstance(deps, dict):
                    for dep_type, dep_list in deps.items():
                        if isinstance(dep_list, list):
                            sections.append(f"{dep_type}: {', '.join(str(d) for d in dep_list[:20])}")
                        elif isinstance(dep_list, dict):
                            sections.append(f"{dep_type}: {', '.join(list(dep_list.keys())[:20])}")
        
        # Critical files with content
        sections.append("\n## CRITICAL CODE EXCERPTS")
        for cf in critical_files[:15]:  # Limit to avoid token overflow
            sections.append(f"\n### [{cf.category.upper()}] {cf.path}")
            sections.append(f"Reason: {cf.reason}")
            if cf.content:
                # Truncate very long files
                content = cf.content[:3000] if len(cf.content) > 3000 else cf.content
                sections.append(f"```\n{content}\n```")
        
        # Analysis instructions
        sections.append("\n## ANALYSIS TASK")
        sections.append("Analyze this repository and provide:")
        sections.append("1. Architecture style identification with evidence")
        sections.append("2. Bounded contexts (domain boundaries)")
        sections.append("3. Architectural layers")
        sections.append("4. Design patterns with evidence")
        sections.append("5. Coupling/cohesion assessment")
        sections.append("6. C4 diagrams (Context, Container, Component)")
        sections.append("7. Module dependency graph")
        sections.append("\nReturn as valid JSON only.")
        
        return "\n".join(sections)
    
    def populate_akg(self, analysis_result: dict, akg: ArchitecturalKnowledgeGraph):
        """
        Populate an AKG from the analysis result.
        
        Args:
            analysis_result: The JSON result from analyze()
            akg: The AKG to populate
        """
        # Set architecture style
        akg.architecture_style = analysis_result.get("architecture_style", "Unknown")
        
        # Add bounded contexts
        for ctx_data in analysis_result.get("bounded_contexts", []):
            ctx = BoundedContext(
                name=ctx_data.get("name", "Unknown"),
                description=ctx_data.get("description", ""),
                primary_files=ctx_data.get("primary_files", []),
                responsibilities=ctx_data.get("responsibilities", []),
            )
            akg.bounded_contexts.append(ctx)
            
            # Create nodes for bounded context modules
            for file_path in ctx.primary_files[:5]:
                node = AKGNode(
                    id=f"ctx_{ctx.name}_{len(ctx.node_ids)}",
                    type="module",
                    name=file_path.split("/")[-1],
                    file_path=file_path,
                )
                node_id = akg.add_node(node)
                ctx.node_ids.append(node_id)
        
        # Add layers
        for layer_data in analysis_result.get("layers", []):
            layer = ArchitecturalLayer(
                name=layer_data.get("name", "Unknown"),
                modules=layer_data.get("modules", []),
                description=layer_data.get("description", ""),
            )
            akg.layers.append(layer)
        
        # Add design patterns
        for pattern_data in analysis_result.get("key_design_patterns", []):
            pattern = DesignPattern(
                pattern=pattern_data.get("pattern", "Unknown"),
                description=pattern_data.get("description", ""),
                evidence_files=pattern_data.get("evidence_files", []),
                confidence=pattern_data.get("confidence", "medium"),
            )
            akg.design_patterns.append(pattern)
        
        # Set coupling/cohesion scores
        assessment = analysis_result.get("coupling_cohesion_assessment", {})
        akg.coupling_score = assessment.get("coupling_score")
        akg.cohesion_score = assessment.get("cohesion_score")
        akg.assessment_explanation = assessment.get("explanation_with_evidence")
        
        # Add evidence from evidence_map
        for evidence_data in analysis_result.get("evidence_map", []):
            evidence = Evidence(
                claim_id=evidence_data.get("claim_id", akg.generate_claim_id()),
                file_path=evidence_data.get("file_path", ""),
                line_start=evidence_data.get("line_range", "1-1").split("-")[0] if isinstance(evidence_data.get("line_range"), str) else 1,
                line_end=evidence_data.get("line_range", "1-1").split("-")[-1] if isinstance(evidence_data.get("line_range"), str) else 1,
                quote=evidence_data.get("quote", ""),
            )
            try:
                evidence.line_start = int(evidence.line_start)
                evidence.line_end = int(evidence.line_end)
            except (ValueError, TypeError):
                evidence.line_start = 1
                evidence.line_end = 1
            akg.add_evidence(evidence)
    
    def get_diagrams(self, analysis_result: dict) -> dict:
        """
        Extract Mermaid diagrams from the analysis result.
        
        Returns:
            Dictionary of diagram_type -> mermaid_code
        """
        return {
            "c4_context_diagram": analysis_result.get("c4_context_diagram", ""),
            "c4_container_diagram": analysis_result.get("c4_container_diagram", ""),
            "c4_component_diagram": analysis_result.get("c4_component_diagram", ""),
            "dependency_graph": analysis_result.get("dependency_graph", ""),
        }
