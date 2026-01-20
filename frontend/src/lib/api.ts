const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AnalysisRequest {
    repo_url: string;
    branch?: string;
    audience: string;
}

export interface AnalysisResponse {
    analysis_id: string;
    status: string;
    message: string;
    stream_url: string;
}

export interface AnalysisResult {
    analysis_id: string;
    status: string;
    repo_url: string;
    started_at: string;
    completed_at?: string;
    architecture?: Record<string, unknown>;
    runtime?: Record<string, unknown>;
    documentation?: Record<string, unknown>;
    error?: string;
}

export interface DiagramResponse {
    type: string;
    mermaid?: string;
    diagrams?: Array<{
        name: string;
        description: string;
        mermaid: string;
    }>;
}

export interface HealthResponse {
    status: string;
    version: string;
}

export interface OllamaHealthResponse {
    status: string;
    ollama_url: string;
    configured_model: string;
    model_available: boolean;
    available_models: string[];
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE) {
        this.baseUrl = baseUrl;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Request failed: ${response.status}`);
        }

        return response.json();
    }

    // Health endpoints
    async getHealth(): Promise<HealthResponse> {
        return this.request<HealthResponse>("/health");
    }

    async getOllamaHealth(): Promise<OllamaHealthResponse> {
        return this.request<OllamaHealthResponse>("/health/ollama");
    }

    // Analysis endpoints
    async startAnalysis(request: AnalysisRequest): Promise<AnalysisResponse> {
        return this.request<AnalysisResponse>("/api/analyze", {
            method: "POST",
            body: JSON.stringify(request),
        });
    }

    async getAnalysis(analysisId: string): Promise<AnalysisResult> {
        return this.request<AnalysisResult>(`/api/analyze/${analysisId}`);
    }

    async deleteAnalysis(analysisId: string): Promise<void> {
        await this.request(`/api/analyze/${analysisId}`, {
            method: "DELETE",
        });
    }

    // Diagram endpoints
    async getDiagram(
        analysisId: string,
        diagramType: string
    ): Promise<DiagramResponse> {
        return this.request<DiagramResponse>(
            `/api/diagrams/${analysisId}/${diagramType}`
        );
    }

    async listDiagrams(
        analysisId: string
    ): Promise<{ analysis_id: string; available_diagrams: Array<{ type: string; name: string }> }> {
        return this.request(`/api/diagrams/${analysisId}`);
    }

    // WebSocket connection for live updates
    createAnalysisStream(analysisId: string): WebSocket {
        const wsUrl = `ws://localhost:8000/api/analyze/${analysisId}/stream`;
        return new WebSocket(wsUrl);
    }
}

export const api = new ApiClient();
export default api;
