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
    Code2,
    Wifi,
    WifiOff,
} from "lucide-react";
import { useAnalysisStore, ProgressEvent } from "@/stores/analysis";
import { useAnalysisWebSocket } from "@/hooks/use-analysis-websocket";
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

    const { connectionStatus, retryCount, reconnect } = useAnalysisWebSocket(analysisId);

    const [activeTab, setActiveTab] = useState<"diagrams" | "docs" | "evidence">("diagrams");
    const [selectedDiagram, setSelectedDiagram] = useState("c4_context");

    useEffect(() => {
        if (!analysisId || status === "completed" || status === "failed") return;

        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${API_BASE}/api/analyze/${analysisId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.status === "completed" || data.status === "failed") {
                        setProgress({
                            stage: data.status,
                            message: data.status === "completed" ? "Analyysi valmis!" : data.error,
                            progress_pct: data.status === "completed" ? 100 : 0,
                            timestamp: new Date().toISOString(),
                            result: data,
                        });
                    }
                }
            } catch (e) {
                console.error("Poll failed:", e);
            }
        }, 5000);

        return () => clearInterval(pollInterval);
    }, [analysisId, status, setProgress]);

    const isComplete = status === "completed";
    const isFailed = status === "failed";
    const isRunning = !isComplete && !isFailed && status !== "idle";

    const archData = architecture as ArchitectureResult | null;
    const docsData = documentation as DocumentationResult | null;

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

    const getConnectionStatusBadge = () => {
        switch (connectionStatus) {
            case "connected":
                return (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0">
                        <Wifi className="w-3.5 h-3.5" />
                        <span className="text-xs font-semibold tracking-wide uppercase">Yhdistetty</span>
                    </div>
                );
            case "connecting":
                return (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 shrink-0">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span className="text-xs font-semibold tracking-wide uppercase">Yhdistetään</span>
                    </div>
                );
            case "disconnected":
                return (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 shrink-0">
                        <WifiOff className="w-3.5 h-3.5" />
                        <span className="text-xs font-semibold tracking-wide uppercase">
                            Yhdistetään ({retryCount}/3)
                        </span>
                    </div>
                );
            case "error":
                return (
                    <button
                        onClick={reconnect}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 shrink-0 hover:bg-red-500/20 transition-colors"
                    >
                        <WifiOff className="w-3.5 h-3.5" />
                        <span className="text-xs font-semibold tracking-wide uppercase">Yhdistä uudelleen</span>
                    </button>
                );
            case "complete":
                return null;
            default:
                return null;
        }
    };

    return (
        <div className="min-h-screen w-full bg-[#020617] text-slate-300 font-sans selection:bg-indigo-500/30 flex flex-col relative overflow-x-hidden isolate">
            <div className="fixed inset-0 z-[-1] pointer-events-none overflow-hidden">
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[800px] bg-indigo-500/10 blur-[120px] rounded-[100%] mix-blend-screen" />
                <div className="absolute bottom-0 right-0 w-[600px] h-[600px] bg-blue-600/5 blur-[100px] rounded-full" />
            </div>

            <header className="fixed top-0 inset-x-0 z-50 border-b border-white/5 bg-[#020617]/70 backdrop-blur-xl supports-[backdrop-filter]:bg-[#020617]/40 h-16">
                <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
                    <button
                        onClick={() => router.push("/")}
                        className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors group shrink-0"
                    >
                        <div className="p-1.5 rounded-lg bg-white/5 group-hover:bg-white/10 transition-colors border border-white/5">
                            <ArrowLeft className="w-4 h-4" />
                        </div>
                        <span className="text-sm font-medium hidden sm:inline-block">Etusivulle</span>
                    </button>

                    <div className="flex items-center gap-4 sm:gap-6 overflow-hidden">
                        {getConnectionStatusBadge()}

                        {isRunning && (
                            <div className="flex items-center gap-3 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 shrink-0">
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                <span className="text-xs font-semibold tracking-wide uppercase whitespace-nowrap">Analysoidaan {Math.round(progress)}%</span>
                            </div>
                        )}
                        {isComplete && (
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span className="text-xs font-semibold tracking-wide uppercase">Valmis</span>
                            </div>
                        )}
                        {isFailed && (
                            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 shrink-0">
                                <AlertCircle className="w-3.5 h-3.5" />
                                <span className="text-xs font-semibold tracking-wide uppercase">Epäonnistui</span>
                            </div>
                        )}

                        <div className="h-4 w-[1px] bg-white/10 shrink-0" />

                        <div className="flex items-center gap-2 shrink-0">
                            <Code2 className="w-4 h-4 text-indigo-500" />
                            <span className="text-sm font-semibold text-white tracking-tight hidden sm:inline-block">RepoBlueprint</span>
                        </div>
                    </div>
                </div>
            </header>

            <main className="relative z-10 flex-grow pt-32 pb-24 px-6 w-full grid place-items-center">
                <div className="w-full max-w-3xl flex flex-col gap-8">
                    {isRunning && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="w-full"
                        >
                            <AnalysisProgress events={progressEvents} currentProgress={progress} />
                        </motion.div>
                    )}

                    {isFailed && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-red-950/20 border border-red-500/20 rounded-xl p-6 sm:p-8 w-full max-w-3xl"
                        >
                            <div className="flex items-start gap-6">
                                <div className="p-3 bg-red-500/10 rounded-lg shrink-0">
                                    <AlertCircle className="w-8 h-8 text-red-400" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-red-400 mb-2">Analyysi Epäonnistui</h3>
                                    <p className="text-red-200/60 leading-relaxed mb-6 break-words">{error || "Odottamaton virhe analyysin aikana."}</p>
                                    <button
                                        onClick={() => router.push("/")}
                                        className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-2 shadow-lg shadow-red-900/20"
                                    >
                                        <RefreshCw className="w-4 h-4" />
                                        Yritä Uudelleen
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    )}

                    {isComplete && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="w-full max-w-7xl"
                        >
                            <div className="flex items-center gap-2 mb-8 border-b border-white/5 pb-1 overflow-x-auto scrollbar-hide">
                                {[
                                    { id: "diagrams", label: "Arkkitehtuurikaaviot", icon: Network },
                                    { id: "docs", label: "Dokumentaatio", icon: FileText },
                                    { id: "evidence", label: "Lähdekooditodisteet", icon: FileCode2 },
                                ].map((tab) => (
                                    <button
                                        key={tab.id}
                                        onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                        className={`px-6 py-3 flex items-center gap-2.5 border-b-2 text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.id
                                            ? "border-indigo-500 text-indigo-400"
                                            : "border-transparent text-slate-400 hover:text-white"
                                            }`}
                                    >
                                        <tab.icon className="w-4 h-4" />
                                        {tab.label}
                                    </button>
                                ))}

                                <div className="ml-auto pl-4">
                                    <button className="px-5 py-2 text-sm bg-white/5 hover:bg-white/10 text-white rounded-lg border border-white/10 flex items-center gap-2 transition-colors whitespace-nowrap">
                                        <Download className="w-4 h-4 text-slate-400" />
                                        Vie Raportti
                                    </button>
                                </div>
                            </div>

                            <div className="grid lg:grid-cols-[1fr_320px] gap-10">
                                <div className="space-y-8 min-w-0">
                                    {activeTab === "diagrams" && (
                                        <div className="space-y-6">
                                            <div className="flex flex-wrap gap-2 bg-[#0B1121]/50 p-1.5 rounded-xl border border-white/5 w-fit">
                                                {[
                                                    { id: "c4_context", label: "Context" },
                                                    { id: "c4_container", label: "Container" },
                                                    { id: "c4_component", label: "Component" },
                                                    { id: "dependency_graph", label: "Dependencies" },
                                                ].map((diagram) => (
                                                    <button
                                                        key={diagram.id}
                                                        onClick={() => setSelectedDiagram(diagram.id)}
                                                        className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${selectedDiagram === diagram.id
                                                            ? "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20"
                                                            : "text-slate-400 hover:text-white hover:bg-white/5"
                                                            }`}
                                                    >
                                                        {diagram.label}
                                                    </button>
                                                ))}
                                            </div>

                                            <div className="bg-[#0B1121] border border-white/5 rounded-2xl overflow-hidden shadow-2xl shadow-black/50">
                                                <MermaidViewer
                                                    code={getDiagramCode()}
                                                    title={selectedDiagram.replace(/_/g, " ").replace(/c4/g, "C4")}
                                                />
                                            </div>

                                        </div>
                                    )}

                                    {activeTab === "docs" && docsData && (
                                        <DocumentationTabs documentation={docsData} />
                                    )}

                                    {activeTab === "evidence" && (
                                        <EvidencePanel evidenceMap={(archData?.evidence_map || []) as Evidence[]} />
                                    )}
                                </div>

                                <aside className="space-y-6 min-w-0">
                                    <div className="glass rounded-2xl p-6">
                                        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                                            <Network className="w-4 h-4 text-indigo-400" />
                                            Järjestelmän Yleiskatsaus
                                        </h3>

                                        <div className="space-y-5">
                                            <div className="flex flex-col gap-2 pb-4 border-b border-white/5">
                                                <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">Arkkitehtuurityyli</span>
                                                <span className="text-sm font-medium text-white bg-white/5 px-3 py-2 rounded-lg border border-white/5">
                                                    {archData?.architecture_style || "Analysoidaan..."}
                                                </span>
                                            </div>

                                            <div className="flex justify-between items-center py-2 border-b border-white/5">
                                                <span className="text-sm text-slate-400">Rajatut Kontekstit</span>
                                                <span className="text-sm font-mono font-medium text-white bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">
                                                    {archData?.bounded_contexts?.length || 0}
                                                </span>
                                            </div>

                                            <div className="flex justify-between items-center py-2">
                                                <span className="text-sm text-slate-400">Suunnittelumallit</span>
                                                <span className="text-sm font-mono font-medium text-white bg-purple-500/10 px-2.5 py-0.5 rounded border border-purple-500/20">
                                                    {archData?.key_design_patterns?.length || 0}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    {docsData?.architecture_health && (
                                        <div className="glass rounded-2xl p-8 flex flex-col items-center justify-center relative overflow-hidden group hover:border-indigo-500/30 transition-colors">
                                            <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent blur-2xl opacity-50 group-hover:opacity-100 transition-opacity" />
                                            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-2 relative z-10">Terveyspisteet</h3>

                                            <div className="relative z-10 text-center">
                                                <div className="text-6xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white via-indigo-200 to-indigo-400 tracking-tighter drop-shadow-sm">
                                                    {docsData.architecture_health.score}
                                                </div>
                                                <div className="px-3 py-1 mt-3 rounded-full bg-white/5 border border-white/10 text-[10px] font-medium text-slate-400 uppercase tracking-widest">
                                                    Korkea Laatu
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {archData?.coupling_cohesion_assessment && (
                                        <div className="glass rounded-2xl p-6">
                                            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-6">Laatumittarit</h3>

                                            <div className="space-y-6">
                                                <div>
                                                    <div className="flex justify-between text-xs font-medium mb-2">
                                                        <span className="text-slate-400">Kytkentä</span>
                                                        <span className="text-white font-mono">
                                                            {archData.coupling_cohesion_assessment.coupling_score}/10
                                                        </span>
                                                    </div>
                                                    <div className="h-1.5 bg-slate-800/50 rounded-full overflow-hidden border border-white/5">
                                                        <div
                                                            className="h-full bg-gradient-to-r from-indigo-500 to-indigo-400 rounded-full shadow-[0_0_10px_rgba(99,102,241,0.3)]"
                                                            style={{
                                                                width: `${(archData.coupling_cohesion_assessment.coupling_score || 0) * 10}%`,
                                                            }}
                                                        />
                                                    </div>
                                                </div>

                                                <div>
                                                    <div className="flex justify-between text-xs font-medium mb-2">
                                                        <span className="text-slate-400">Koheesio</span>
                                                        <span className="text-white font-mono">
                                                            {archData.coupling_cohesion_assessment.cohesion_score}/10
                                                        </span>
                                                    </div>
                                                    <div className="h-1.5 bg-slate-800/50 rounded-full overflow-hidden border border-white/5">
                                                        <div
                                                            className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full shadow-[0_0_10px_rgba(6,182,212,0.3)]"
                                                            style={{
                                                                width: `${(archData.coupling_cohesion_assessment.cohesion_score || 0) * 10}%`,
                                                            }}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </aside>
                            </div>
                        </motion.div>
                    )}

                    {!isRunning && !isComplete && !isFailed && (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="w-full max-w-xl mx-auto text-center py-20"
                        >
                            <div className="w-16 h-16 bg-indigo-500/10 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-indigo-500/20">
                                <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
                            </div>
                            <h3 className="text-xl font-bold text-white mb-2">Alustetaan Analyysiä</h3>
                            <p className="text-slate-400 text-sm leading-relaxed">
                                Yhdistetään palveluun ja valmistellaan dataa...
                            </p>
                        </motion.div>
                    )}
                </div>
            </main>
        </div>
    );
}
