"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
    ArrowLeft,
    CheckCircle2,
    Loader2,
    AlertCircle,
    FileCode2,
    Network,
    FileText,
    Download,
    RefreshCw,
} from "lucide-react";
import { useAnalysisStore, ProgressEvent } from "@/stores/analysis";
import { AnalysisProgress } from "@/components/analysis-progress";
import { MermaidViewer } from "@/components/mermaid-viewer";
import { DocumentationTabs } from "@/components/documentation-tabs";
import { EvidencePanel } from "@/components/evidence-panel";
import type { ArchitectureResult, DocumentationResult, Evidence } from "@/types/analysis";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AnalyzePage() {
    const params = useParams();
    const router = useRouter();
    const analysisId = params.id as string;

    const {
        status,
        progress,
        progressEvents,
        architecture,
        runtime,
        documentation,
        error,
        setProgress,
    } = useAnalysisStore();

    const [activeTab, setActiveTab] = useState<"diagrams" | "docs" | "evidence">("diagrams");
    const [selectedDiagram, setSelectedDiagram] = useState("c4_context");

    // Connect to WebSocket for live updates
    useEffect(() => {
        if (!analysisId) return;

        const wsUrl = `ws://localhost:8000/api/analyze/${analysisId}/stream`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log("WebSocket connected");
        };

        ws.onmessage = (event) => {
            try {
                const data: ProgressEvent = JSON.parse(event.data);
                setProgress(data);
            } catch (e) {
                console.error("Failed to parse WebSocket message:", e);
            }
        };

        ws.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        ws.onclose = () => {
            console.log("WebSocket closed");
        };

        return () => {
            ws.close();
        };
    }, [analysisId, setProgress]);

    // Poll for status as fallback
    useEffect(() => {
        if (!analysisId || status === "completed" || status === "failed") return;

        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/api/analyze/${analysisId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.status === "completed" || data.status === "failed") {
                        // Final update
                        setProgress({
                            stage: data.status,
                            message: data.status === "completed" ? "Analysis complete!" : data.error,
                            progress_pct: data.status === "completed" ? 100 : 0,
                            timestamp: new Date().toISOString(),
                            result: data,
                        });
                    }
                }
            } catch (e) {
                console.error("Poll failed:", e);
            }
        }, 3000);

        return () => clearInterval(pollInterval);
    }, [analysisId, status, setProgress]);

    const isComplete = status === "completed";
    const isFailed = status === "failed";
    const isRunning = !isComplete && !isFailed && status !== "idle";

    // Cast to proper types
    const archData = architecture as ArchitectureResult | null;
    const docsData = documentation as DocumentationResult | null;

    // Get diagram code based on selection
    const getDiagramCode = (): string => {
        if (!archData) return "";
        switch (selectedDiagram) {
            case "c4_context":
                return archData.c4_context_diagram || "";
            case "c4_container":
                return archData.c4_container_diagram || "";
            case "c4_component":
                return archData.c4_component_diagram || "";
            case "dependency_graph":
                return archData.dependency_graph || "";
            default:
                return "";
        }
    };

    return (
        <main className="min-h-screen">
            {/* Header */}
            <header className="sticky top-0 z-50 glass-strong border-b border-slate-800/50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <button
                        onClick={() => router.push("/")}
                        className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors"
                    >
                        <ArrowLeft className="w-5 h-5" />
                        <span>New Analysis</span>
                    </button>

                    <div className="flex items-center gap-4">
                        {isRunning && (
                            <div className="flex items-center gap-2 text-blue-400">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                <span className="text-sm">{Math.round(progress)}%</span>
                            </div>
                        )}
                        {isComplete && (
                            <div className="flex items-center gap-2 text-green-400">
                                <CheckCircle2 className="w-4 h-4" />
                                <span className="text-sm">Complete</span>
                            </div>
                        )}
                        {isFailed && (
                            <div className="flex items-center gap-2 text-red-400">
                                <AlertCircle className="w-4 h-4" />
                                <span className="text-sm">Failed</span>
                            </div>
                        )}
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Progress Section */}
                {isRunning && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="mb-8"
                    >
                        <AnalysisProgress events={progressEvents} currentProgress={progress} />
                    </motion.div>
                )}

                {/* Error Display */}
                {isFailed && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="glass rounded-xl p-6 border-red-500/30 mb-8"
                    >
                        <div className="flex items-start gap-4">
                            <AlertCircle className="w-6 h-6 text-red-400 mt-0.5" />
                            <div>
                                <h3 className="font-semibold text-red-400 mb-2">Analysis Failed</h3>
                                <p className="text-slate-400">{error || "An unexpected error occurred"}</p>
                                <button
                                    onClick={() => router.push("/")}
                                    className="mt-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors flex items-center gap-2"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    Try Again
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Results Section */}
                {isComplete && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                    >
                        {/* Tab Navigation */}
                        <div className="flex items-center gap-2 mb-6 border-b border-slate-800">
                            {[
                                { id: "diagrams", label: "Diagrams", icon: Network },
                                { id: "docs", label: "Documentation", icon: FileText },
                                { id: "evidence", label: "Evidence", icon: FileCode2 },
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                    className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-colors ${activeTab === tab.id
                                            ? "border-blue-500 text-blue-400"
                                            : "border-transparent text-slate-400 hover:text-slate-200"
                                        }`}
                                >
                                    <tab.icon className="w-4 h-4" />
                                    {tab.label}
                                </button>
                            ))}

                            <div className="ml-auto">
                                <button className="px-4 py-2 text-sm text-slate-400 hover:text-slate-200 flex items-center gap-2">
                                    <Download className="w-4 h-4" />
                                    Export
                                </button>
                            </div>
                        </div>

                        {/* Tab Content */}
                        <div className="grid lg:grid-cols-3 gap-6">
                            {/* Main Content */}
                            <div className="lg:col-span-2">
                                {activeTab === "diagrams" && (
                                    <div className="space-y-4">
                                        {/* Diagram Type Selector */}
                                        <div className="flex flex-wrap gap-2">
                                            {[
                                                { id: "c4_context", label: "C4 Context" },
                                                { id: "c4_container", label: "C4 Container" },
                                                { id: "c4_component", label: "C4 Component" },
                                                { id: "dependency_graph", label: "Dependencies" },
                                            ].map((diagram) => (
                                                <button
                                                    key={diagram.id}
                                                    onClick={() => setSelectedDiagram(diagram.id)}
                                                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${selectedDiagram === diagram.id
                                                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                                                            : "bg-slate-800/50 text-slate-400 border border-slate-700 hover:bg-slate-700/50"
                                                        }`}
                                                >
                                                    {diagram.label}
                                                </button>
                                            ))}
                                        </div>

                                        {/* Mermaid Diagram */}
                                        <MermaidViewer
                                            code={getDiagramCode()}
                                            title={selectedDiagram.replace(/_/g, " ").replace(/c4/g, "C4")}
                                        />
                                    </div>
                                )}

                                {activeTab === "docs" && docsData && (
                                    <DocumentationTabs documentation={docsData} />
                                )}

                                {activeTab === "evidence" && (
                                    <EvidencePanel evidenceMap={(archData?.evidence_map || []) as Evidence[]} />
                                )}
                            </div>

                            {/* Sidebar - Quick Stats */}
                            <div className="space-y-4">
                                {/* Architecture Overview */}
                                <div className="glass rounded-xl p-5">
                                    <h3 className="font-semibold text-slate-200 mb-4">Architecture Overview</h3>

                                    <div className="space-y-3 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-slate-400">Style</span>
                                            <span className="text-slate-200">
                                                {archData?.architecture_style || "Analyzing..."}
                                            </span>
                                        </div>

                                        <div className="flex justify-between">
                                            <span className="text-slate-400">Bounded Contexts</span>
                                            <span className="text-slate-200">
                                                {archData?.bounded_contexts?.length || 0}
                                            </span>
                                        </div>

                                        <div className="flex justify-between">
                                            <span className="text-slate-400">Design Patterns</span>
                                            <span className="text-slate-200">
                                                {archData?.key_design_patterns?.length || 0}
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Health Score */}
                                {docsData?.architecture_health && (
                                    <div className="glass rounded-xl p-5">
                                        <h3 className="font-semibold text-slate-200 mb-4">Health Score</h3>

                                        <div className="text-center mb-4">
                                            <div className="text-4xl font-bold gradient-text">
                                                {docsData.architecture_health.score}
                                            </div>
                                            <div className="text-sm text-slate-400">out of 100</div>
                                        </div>
                                    </div>
                                )}

                                {/* Coupling/Cohesion */}
                                {archData?.coupling_cohesion_assessment && (
                                    <div className="glass rounded-xl p-5">
                                        <h3 className="font-semibold text-slate-200 mb-4">Quality Metrics</h3>

                                        <div className="space-y-3">
                                            <div>
                                                <div className="flex justify-between text-sm mb-1">
                                                    <span className="text-slate-400">Coupling</span>
                                                    <span className="text-slate-200">
                                                        {archData.coupling_cohesion_assessment.coupling_score}/10
                                                    </span>
                                                </div>
                                                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-green-500 to-yellow-500"
                                                        style={{
                                                            width: `${(archData.coupling_cohesion_assessment.coupling_score || 0) * 10}%`,
                                                        }}
                                                    />
                                                </div>
                                            </div>

                                            <div>
                                                <div className="flex justify-between text-sm mb-1">
                                                    <span className="text-slate-400">Cohesion</span>
                                                    <span className="text-slate-200">
                                                        {archData.coupling_cohesion_assessment.cohesion_score}/10
                                                    </span>
                                                </div>
                                                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                                                        style={{
                                                            width: `${(archData.coupling_cohesion_assessment.cohesion_score || 0) * 10}%`,
                                                        }}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                )}
            </div>
        </main>
    );
}
