"""
Documentation AI Agent

Technical Writer producing audience-specific documentation from architectural data.
"""

import logging
from datetime import datetime
from typing import Literal, Optional

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)


DOCUMENTATION_SYSTEM_PROMPT = """You are a Technical Writer who produces audience-specific documentation from structured architectural data.

You receive JSON from Architect AI and Runtime Analyst AI analyses.

Generate documentation for the specified audience profile:

AUDIENCE PROFILES:
1. Executive: Max 200 words, non-technical, focus on business value, risks, and strategic implications
2. Engineer: Technical deep-dive with trade-offs, patterns, and implementation details
3. Security Analyst: Risk-focused, OWASP concerns, authentication flows, data handling
4. Sales Engineer: Feature capabilities, integration points, scalability strengths
5. New Hire: Onboarding-focused, architecture overview, key files to understand first
6. Investor: Due diligence perspective, tech stack maturity, scalability, technical debt

OUTPUT FORMAT (JSON):
- audience: string (the target audience)
- title: string (document title)
- executive_summary: string (always included, max 200 words for non-engineers)
- sections: array of {heading, content, evidence_refs: array of claim_ids}
- key_findings: array of {finding, importance: High/Medium/Low, evidence_ref}
- recommendations: array of {recommendation, priority: High/Medium/Low, effort: Low/Medium/High}
- generated_adrs: array of {title, status: Proposed/Accepted/Deprecated, context, decision, consequences, evidence_files}
- architecture_health: {score: 1-100, strengths: array, concerns: array}
- next_steps: array of strings (actionable items)
- metadata: {generated_at, commit_hash, confidence_level: High/Medium/Low}

For ADRs (Architecture Decision Records):
- Identify implicit decisions in the code
- Propose new ADRs for undocumented patterns
- If existing ADRs are provided, validate them against current code

STYLE GUIDELINES:
- Clear, professional language
- Every factual statement should reference evidence (claim_id from evidence_map)
- Appropriate technical depth for the audience
- Actionable recommendations
- Honest about uncertainties (use "Insufficient evidence" when needed)

Output valid JSON only. No markdown code blocks around the JSON."""


AudienceProfile = Literal[
    "executive",
    "engineer",
    "security_analyst",
    "sales_engineer",
    "new_hire",
    "investor",
]


class DocumentationAgent(BaseAgent):
    """
    Technical Writer AI.
    
    Produces audience-specific documentation from architectural and runtime analyses.
    """
    
    @property
    def system_prompt(self) -> str:
        return DOCUMENTATION_SYSTEM_PROMPT
    
    @property
    def name(self) -> str:
        return "DocumentationAI"
    
    async def generate_documentation(
        self,
        architecture_analysis: dict,
        runtime_analysis: dict,
        audience: AudienceProfile = "engineer",
        repo_url: str = "",
        commit_hash: Optional[str] = None,
        existing_adrs: Optional[list[dict]] = None,
    ) -> dict:
        """
        Generate audience-specific documentation.
        
        Args:
            architecture_analysis: Results from Architect AI
            runtime_analysis: Results from Runtime Analyst AI
            audience: Target audience profile
            repo_url: Repository URL for context
            commit_hash: Git commit hash
            existing_adrs: Existing ADR documents for validation
            
        Returns:
            Complete documentation package
        """
        # Build the input context
        user_prompt = self._build_context(
            architecture_analysis,
            runtime_analysis,
            audience,
            repo_url,
            commit_hash,
            existing_adrs,
        )
        
        logger.info(f"[{self.name}] Generating documentation for audience: {audience}")
        
        # Generate structured response
        result = await self.generate_structured(
            user_prompt=user_prompt,
            temperature=0.4,  # Slightly higher for more natural writing
        )
        
        # Add metadata
        result["metadata"] = result.get("metadata", {})
        result["metadata"]["generated_at"] = datetime.utcnow().isoformat()
        result["metadata"]["audience"] = audience
        result["metadata"]["repo_url"] = repo_url
        
        return result
    
    def _build_context(
        self,
        architecture_analysis: dict,
        runtime_analysis: dict,
        audience: AudienceProfile,
        repo_url: str,
        commit_hash: Optional[str],
        existing_adrs: Optional[list[dict]],
    ) -> str:
        """Build the documentation context for the LLM."""
        sections = []
        
        # Target audience
        sections.append(f"## TARGET AUDIENCE: {audience.upper()}")
        sections.append(self._get_audience_guidance(audience))
        
        # Repository info
        sections.append(f"\n## REPOSITORY")
        sections.append(f"URL: {repo_url}")
        if commit_hash:
            sections.append(f"Commit: {commit_hash}")
        
        # Architecture analysis summary
        sections.append("\n## ARCHITECTURE ANALYSIS")
        sections.append(f"Style: {architecture_analysis.get('architecture_style', 'Unknown')}")
        
        # Bounded contexts
        contexts = architecture_analysis.get("bounded_contexts", [])
        if contexts:
            sections.append("\nBounded Contexts:")
            for ctx in contexts:
                name = ctx.get("name", "Unknown")
                responsibilities = ctx.get("responsibilities", [])
                files = ctx.get("primary_files", [])
                sections.append(f"- {name}")
                sections.append(f"  Responsibilities: {', '.join(responsibilities[:3])}")
                sections.append(f"  Primary files: {', '.join(files[:3])}")
        
        # Layers
        layers = architecture_analysis.get("layers", [])
        if layers:
            sections.append("\nLayers:")
            for layer in layers:
                sections.append(f"- {layer.get('name')}: {layer.get('description', '')}")
        
        # Design patterns
        patterns = architecture_analysis.get("key_design_patterns", [])
        if patterns:
            sections.append("\nDesign Patterns:")
            for pattern in patterns:
                sections.append(f"- {pattern.get('pattern')}: {pattern.get('description', '')} [{pattern.get('confidence', 'medium')}]")
        
        # Coupling/Cohesion
        assessment = architecture_analysis.get("coupling_cohesion_assessment", {})
        if assessment:
            sections.append(f"\nCoupling Score: {assessment.get('coupling_score', 'N/A')}/10")
            sections.append(f"Cohesion Score: {assessment.get('cohesion_score', 'N/A')}/10")
            sections.append(f"Assessment: {assessment.get('explanation_with_evidence', '')[:300]}")
        
        # Runtime analysis summary
        sections.append("\n## RUNTIME ANALYSIS")
        
        # Critical flows
        flows = runtime_analysis.get("critical_flows", [])
        if flows:
            sections.append("\nCritical Flows:")
            for flow in flows:
                sections.append(f"- {flow.get('name')}: {flow.get('description', '')[:100]}")
        
        # Bottlenecks
        bottlenecks = runtime_analysis.get("potential_bottlenecks", [])
        if bottlenecks:
            sections.append("\nPotential Bottlenecks:")
            for bn in bottlenecks:
                sections.append(f"- [{bn.get('risk_level')}] {bn.get('component')}: {bn.get('description', '')}")
        
        # External integrations
        integrations = runtime_analysis.get("external_integrations", [])
        if integrations:
            sections.append("\nExternal Integrations:")
            for intg in integrations:
                sections.append(f"- {intg.get('service_name')} ({intg.get('type')})")
        
        # Evidence map
        evidence_map = architecture_analysis.get("evidence_map", [])
        if evidence_map:
            sections.append("\n## EVIDENCE MAP")
            for ev in evidence_map[:20]:
                sections.append(f"- {ev.get('claim_id')}: {ev.get('file_path')} L{ev.get('line_range')}")
        
        # Existing ADRs for validation
        if existing_adrs:
            sections.append("\n## EXISTING ADRs TO VALIDATE")
            for adr in existing_adrs:
                sections.append(f"- {adr.get('title')}: {adr.get('status')}")
                sections.append(f"  Decision: {adr.get('decision', '')[:100]}")
        
        # Documentation task
        sections.append("\n## DOCUMENTATION TASK")
        sections.append(f"Generate comprehensive documentation for the {audience.upper()} audience.")
        sections.append("Include:")
        sections.append("1. Executive summary (appropriate to audience)")
        sections.append("2. Structured sections with evidence references")
        sections.append("3. Key findings with importance levels")
        sections.append("4. Actionable recommendations")
        sections.append("5. Proposed ADRs for undocumented decisions")
        sections.append("6. Architecture health score (1-100)")
        sections.append("7. Next steps")
        sections.append("\nReturn as valid JSON only.")
        
        return "\n".join(sections)
    
    def _get_audience_guidance(self, audience: AudienceProfile) -> str:
        """Get specific guidance for each audience type."""
        guidance = {
            "executive": """
Focus on: Business impact, strategic risks, competitive positioning
Avoid: Technical jargon, implementation details
Emphasize: Scalability, maintainability, team velocity implications
Tone: Confident, concise, decision-focused""",
            
            "engineer": """
Focus on: Technical architecture, patterns, trade-offs, code quality
Include: File references, design rationale, improvement opportunities
Emphasize: Maintainability, testability, performance characteristics
Tone: Technical, precise, constructive""",
            
            "security_analyst": """
Focus on: Authentication/authorization flows, data handling, attack surfaces
Include: OWASP considerations, secrets management, input validation
Emphasize: Risk levels, compliance implications, remediation priorities
Tone: Risk-aware, thorough, actionable""",
            
            "sales_engineer": """
Focus on: Capabilities, integration points, extensibility
Include: API design, scalability strengths, customization options
Emphasize: Enterprise readiness, feature richness, competitive advantages
Tone: Positive but honest, feature-focused""",
            
            "new_hire": """
Focus on: System overview, key concepts, learning path
Include: Important files to read first, team conventions, common patterns
Emphasize: Getting started, understanding data flow, where to find things
Tone: Welcoming, educational, practical""",
            
            "investor": """
Focus on: Technical maturity, scalability, technical debt, team capability indicators
Include: Architecture quality metrics, growth readiness, risk factors
Emphasize: Long-term maintainability, competitive moat, scaling costs
Tone: Objective, analytical, balanced""",
        }
        return guidance.get(audience, guidance["engineer"])
    
    def extract_adrs(self, documentation_result: dict) -> list[dict]:
        """Extract proposed ADRs from the documentation."""
        return documentation_result.get("generated_adrs", [])
    
    def get_health_score(self, documentation_result: dict) -> dict:
        """Extract architecture health assessment."""
        return documentation_result.get("architecture_health", {
            "score": 0,
            "strengths": [],
            "concerns": [],
        })
