import { create } from "zustand";

/**
 * Base URL for the API. Defaults to localhost:8000 if not set in environment.
 */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Represents a progress event received from the backend during analysis.
 */
export interface ProgressEvent {
    /** The current stage of analysis (e.g., 'cloning', 'parsing'). */
    stage: string;
    /** A descriptive message about the current progress. */
    message: string;
    /** The percentage of completion (0-100). */
    progress_pct: number;
    /** timestamp of the event. */
    timestamp: string;
    /** Optional result data associated with the event (e.g., intermediate analysis artifacts). */
    result?: Record<string, unknown>;
    /** Optional keepalive flag for heartbeat messages. */
    keepalive?: boolean;
}

/**
 * State definition for the analysis store.
 */
export interface AnalysisState {
    /** The ID of the current analysis session. */
    currentAnalysisId: string | null;
    /** The current status of the analysis (e.g., 'idle', 'starting', 'queued', 'completed', 'failed'). */
    status: string;
    /** The overall progress percentage (0-100). */
    progress: number;
    /** A list of progress events received. */
    progressEvents: ProgressEvent[];
    /** The architectural analysis result. */
    architecture: Record<string, unknown> | null;
    /** The runtime analysis result. */
    runtime: Record<string, unknown> | null;
    /** The documentation generation result. */
    documentation: Record<string, unknown> | null;
    /** Generated diagrams given ID -> Content mapping. */
    diagrams: Record<string, string>;
    /** Error message if the analysis failed. */
    error: string | null;

    // Actions
    /**
     * Starts a new analysis for the given repository.
     * @param repoUrl The URL of the repository to analyze.
     * @param audience The target audience for the analysis.
     * @returns A promise that resolves to the analysis ID.
     */
    startAnalysis: (repoUrl: string, audience: string) => Promise<string>;
    /**
     * Updates the store state based on a received progress event.
     * @param event The progress event to process.
     */
    setProgress: (event: ProgressEvent) => void;
    /**
     * Resets the store to its initial state.
     */
    reset: () => void;
}

/**
 * Zustand store for managing analysis state.
 */
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
