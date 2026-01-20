import { create } from "zustand";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ProgressEvent {
    stage: string;
    message: string;
    progress_pct: number;
    timestamp: string;
    result?: Record<string, unknown>;
}

export interface AnalysisState {
    currentAnalysisId: string | null;
    status: string;
    progress: number;
    progressEvents: ProgressEvent[];
    architecture: Record<string, unknown> | null;
    runtime: Record<string, unknown> | null;
    documentation: Record<string, unknown> | null;
    diagrams: Record<string, string>;
    error: string | null;

    // Actions
    startAnalysis: (repoUrl: string, audience: string) => Promise<string>;
    setProgress: (event: ProgressEvent) => void;
    reset: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
    currentAnalysisId: null,
    status: "idle",
    progress: 0,
    progressEvents: [],
    architecture: null,
    runtime: null,
    documentation: null,
    diagrams: {},
    error: null,

    startAnalysis: async (repoUrl: string, audience: string) => {
        try {
            set({
                status: "starting",
                progress: 0,
                progressEvents: [],
                architecture: null,
                runtime: null,
                documentation: null,
                diagrams: {},
                error: null,
            });

            const response = await fetch(`${API_BASE}/api/analyze`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    repo_url: repoUrl,
                    audience: audience,
                }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Failed to start analysis");
            }

            const data = await response.json();
            const analysisId = data.analysis_id;

            set({
                currentAnalysisId: analysisId,
                status: "queued",
            });

            return analysisId;
        } catch (error) {
            const message = error instanceof Error ? error.message : "Unknown error";
            set({ status: "error", error: message });
            throw error;
        }
    },

    setProgress: (event: ProgressEvent) => {
        set((state) => {
            const newState: Partial<AnalysisState> = {
                progressEvents: [...state.progressEvents, event],
                progress: event.progress_pct,
                status: event.stage,
            };

            // Update results based on stage
            if (event.stage === "architect_complete" && event.result) {
                newState.architecture = event.result;
            } else if (event.stage === "runtime_complete" && event.result) {
                newState.runtime = event.result;
            } else if (event.stage === "documentation_complete" && event.result) {
                newState.documentation = event.result;
            } else if (event.stage === "completed" && event.result) {
                // When analysis is fully complete, populate all data if available
                if (event.result.architecture) newState.architecture = event.result.architecture as Record<string, unknown>;
                if (event.result.runtime) newState.runtime = event.result.runtime as Record<string, unknown>;
                if (event.result.documentation) newState.documentation = event.result.documentation as Record<string, unknown>;
            } else if (event.stage === "failed") {
                newState.error = event.message;
            }

            return newState;
        });
    },

    reset: () => {
        set({
            currentAnalysisId: null,
            status: "idle",
            progress: 0,
            progressEvents: [],
            architecture: null,
            runtime: null,
            documentation: null,
            diagrams: {},
            error: null,
        });
    },
}));
