// Analysis data types

export interface Evidence {
    claim_id: string;
    file_path: string;
    line_range?: string;
    quote?: string;
    confidence?: "high" | "medium" | "low";
}

export interface BoundedContext {
    name: string;
    purpose: string;
    files: string[];
}

export interface DesignPattern {
    name: string;
    location: string;
    description: string;
}

export interface CouplingCohesionAssessment {
    coupling_score: number;
    cohesion_score: number;
    explanation: string;
}

export interface ArchitectureResult {
    architecture_style?: string;
    architectural_layers?: Array<{ name: string; purpose: string }>;
    bounded_contexts?: BoundedContext[];
    key_design_patterns?: DesignPattern[];
    coupling_cohesion_assessment?: CouplingCohesionAssessment;
    c4_context_diagram?: string;
    c4_container_diagram?: string;
    c4_component_diagram?: string;
    dependency_graph?: string;
    evidence_map?: Evidence[];
}

export interface KeyFinding {
    finding: string;
    importance: "High" | "Medium" | "Low";
    evidence?: Evidence[];
}

export interface Recommendation {
    recommendation: string;
    priority: "High" | "Medium" | "Low";
    effort: "Low" | "Medium" | "High";
}

export interface DocumentSection {
    heading: string;
    content: string;
}

export interface ADR {
    title: string;
    status: "Accepted" | "Proposed" | "Deprecated";
    context?: string;
    decision?: string;
    consequences?: string;
}

export interface ArchitectureHealth {
    score: number;
    issues: string[];
}

export interface DocumentationResult {
    executive_summary?: string;
    sections?: DocumentSection[];
    key_findings?: KeyFinding[];
    recommendations?: Recommendation[];
    generated_adrs?: ADR[];
    next_steps?: string[];
    architecture_health?: ArchitectureHealth;
}

export interface RuntimeResult {
    critical_flows?: Array<{
        name: string;
        description: string;
        sequence_diagram?: string;
    }>;
    potential_bottlenecks?: Array<{
        location: string;
        issue: string;
        severity: string;
    }>;
    data_lineage?: string;
}
