"""
Runtime Analyst AI Agent

Senior Backend Engineer specializing in runtime behavior and performance.
Traces flows from actual code evidence.
"""

import logging
from typing import Optional

from app.agents.base import BaseAgent
from app.core.parser import ParsedFile

logger = logging.getLogger(__name__)


RUNTIME_ANALYST_SYSTEM_PROMPT = """You are a Senior Backend Engineer specializing in runtime behavior and performance.

Rules:
1. Trace flows ONLY from actual code evidence (routes, handlers, event emitters, job queues).
2. Identify exactly 3–5 most business-critical flows (prioritize auth, core CRUD, payment/external integration, background jobs).
3. Every arrow in diagram must correspond to real function calls or events.
4. Mark potential bottlenecks with evidence.

Output valid JSON with these fields:
- critical_flows: array of {name, description, entry_point, steps: array, sequence_diagram_mermaid}
  Each step should have: {component, action, file, line_range}
- data_lineage_diagram: Mermaid.js flowchart showing sources → transformations → sinks
- potential_bottlenecks: array of {component, description, evidence_file, evidence_line, risk_level: Low/Medium/High, mitigation}
- async_patterns: {queues: array, events: array, jobs: array, evidence_files: array}
- database_operations: array of {type: query/mutation, description, file, line}
- external_integrations: array of {service_name, type: REST/GraphQL/gRPC/WebSocket, file, line}

For sequence diagrams, use Mermaid sequenceDiagram syntax:
```
sequenceDiagram
    participant Client
    participant API
    participant Service
    participant Database
    Client->>API: Request
    API->>Service: Process
    Service->>Database: Query
    Database-->>Service: Result
    Service-->>API: Response
    API-->>Client: Result
```

Identify flows like:
1. Authentication/Authorization flow
2. Main CRUD operations
3. Payment/transaction flow (if present)
4. Background job processing
5. External API integrations

Output valid JSON only. No markdown code blocks around the JSON."""


class RuntimeAnalystAgent(BaseAgent):
    """
    Senior Backend Engineer AI.
    
    Analyzes runtime behavior, traces critical flows, identifies bottlenecks,
    and maps data lineage.
    """
    
    @property
    def system_prompt(self) -> str:
        return RUNTIME_ANALYST_SYSTEM_PROMPT
    
    @property
    def name(self) -> str:
        return "RuntimeAnalystAI"
    
    async def analyze(
        self,
        parsed_files: list[ParsedFile],
        architecture_context: dict,
    ) -> dict:
        """
        Perform runtime analysis.
        
        Args:
            parsed_files: Parsed source files with functions/classes
            architecture_context: Context from Architect AI analysis
            
        Returns:
            Runtime analysis with flows, bottlenecks, and diagrams
        """
        # Build the input context
        user_prompt = self._build_context(parsed_files, architecture_context)
        
        logger.info(f"[{self.name}] Starting runtime analysis with {len(parsed_files)} files")
        
        # Generate structured response
        result = await self.generate_structured(
            user_prompt=user_prompt,
            temperature=0.2,
        )
        
        return result
    
    def _build_context(
        self,
        parsed_files: list[ParsedFile],
        architecture_context: dict,
    ) -> str:
        """Build the analysis context for the LLM."""
        sections = []
        
        # Architecture context summary
        sections.append("## ARCHITECTURE CONTEXT")
        sections.append(f"Style: {architecture_context.get('architecture_style', 'Unknown')}")
        
        contexts = architecture_context.get("bounded_contexts", [])
        if contexts:
            sections.append("\nBounded Contexts:")
            for ctx in contexts[:5]:
                name = ctx.get("name", "Unknown")
                responsibilities = ctx.get("responsibilities", [])
                sections.append(f"- {name}: {', '.join(responsibilities[:3])}")
        
        # Function and class inventory
        sections.append("\n## CODE STRUCTURE")
        
        # Group by file type
        route_files = []
        service_files = []
        model_files = []
        other_files = []
        
        for pf in parsed_files:
            path_lower = pf.file_path.lower()
            if any(x in path_lower for x in ["route", "endpoint", "handler", "controller", "api"]):
                route_files.append(pf)
            elif any(x in path_lower for x in ["service", "usecase", "interactor"]):
                service_files.append(pf)
            elif any(x in path_lower for x in ["model", "schema", "entity", "domain"]):
                model_files.append(pf)
            else:
                other_files.append(pf)
        
        # Routes/Handlers
        if route_files:
            sections.append("\n### Routes/Handlers:")
            for pf in route_files[:10]:
                sections.append(f"\n#### {pf.file_path}")
                for func in pf.functions[:10]:
                    async_marker = "async " if func.is_async else ""
                    params = ", ".join(func.parameters[:3])
                    sections.append(f"  - {async_marker}{func.name}({params}) [L{func.line_start}]")
        
        # Services
        if service_files:
            sections.append("\n### Services:")
            for pf in service_files[:10]:
                sections.append(f"\n#### {pf.file_path}")
                for cls in pf.classes[:5]:
                    sections.append(f"  - class {cls.name} [L{cls.line_start}]")
                    for method in cls.methods[:5]:
                        sections.append(f"      - {method}()")
        
        # Models
        if model_files:
            sections.append("\n### Models/Schemas:")
            for pf in model_files[:10]:
                sections.append(f"\n#### {pf.file_path}")
                for cls in pf.classes[:5]:
                    bases = f"({', '.join(cls.bases[:2])})" if cls.bases else ""
                    sections.append(f"  - class {cls.name}{bases} [L{cls.line_start}]")
        
        # Imports for dependency tracing
        sections.append("\n### Key Imports/Dependencies:")
        all_imports = set()
        for pf in parsed_files:
            for imp in pf.imports:
                if not imp.is_relative:
                    all_imports.add(imp.module)
        
        external_imports = [i for i in all_imports if not i.startswith("app") and not i.startswith(".")]
        sections.append(", ".join(sorted(external_imports)[:30]))
        
        # Analysis task
        sections.append("\n## ANALYSIS TASK")
        sections.append("Analyze the runtime behavior and provide:")
        sections.append("1. 3-5 critical business flows with sequence diagrams")
        sections.append("2. Data lineage diagram (sources → transformations → sinks)")
        sections.append("3. Potential bottlenecks with risk levels")
        sections.append("4. Async patterns (queues, events, jobs)")
        sections.append("5. Database operations")
        sections.append("6. External integrations")
        sections.append("\nReturn as valid JSON only.")
        
        return "\n".join(sections)
    
    def get_critical_flows(self, analysis_result: dict) -> list[dict]:
        """Extract critical flows from the analysis."""
        return analysis_result.get("critical_flows", [])
    
    def get_bottlenecks(self, analysis_result: dict) -> list[dict]:
        """Extract potential bottlenecks."""
        return analysis_result.get("potential_bottlenecks", [])
    
    def get_diagrams(self, analysis_result: dict) -> dict:
        """Extract Mermaid diagrams from the analysis result."""
        diagrams = {
            "data_lineage_diagram": analysis_result.get("data_lineage_diagram", ""),
        }
        
        # Collect sequence diagrams from critical flows
        flows = analysis_result.get("critical_flows", [])
        for i, flow in enumerate(flows):
            diagram = flow.get("sequence_diagram_mermaid", "")
            if diagram:
                diagrams[f"sequence_{i}_{flow.get('name', 'flow')}"] = diagram
        
        return diagrams
