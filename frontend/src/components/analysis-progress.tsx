"use client";

import { motion } from "framer-motion";
import {
    GitBranch,
    FileSearch,
    Brain,
    FileCode2,
    Workflow,
    FileText,
    CheckCircle2,
    Loader2,
} from "lucide-react";
import { ProgressEvent } from "@/stores/analysis";

interface AnalysisProgressProps {
    events: ProgressEvent[];
    currentProgress: number;
}

const stages = [
    { id: "cloning", label: "Cloning Repository", icon: GitBranch },
    { id: "parsing", label: "Parsing Files", icon: FileSearch },
    { id: "building_akg", label: "Building Knowledge Graph", icon: Brain },
    { id: "architect_analysis", label: "Architect AI Analysis", icon: FileCode2 },
    { id: "runtime_analysis", label: "Runtime Analysis", icon: Workflow },
    { id: "documentation", label: "Generating Documentation", icon: FileText },
];

export function AnalysisProgress({ events, currentProgress }: AnalysisProgressProps) {
    const currentStage = events[events.length - 1]?.stage || "queued";
    const currentStageIndex = stages.findIndex((s) => s.id === currentStage);

    return (
        <div className="glass rounded-2xl p-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <h2 className="text-xl font-semibold text-white">Analysis Progress</h2>
                <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">
                        {Math.round(currentProgress)}%
                    </span>
                </div>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-slate-800/80 rounded-full overflow-hidden mb-10">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${currentProgress}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-500 rounded-full"
                    style={{ boxShadow: "0 0 20px rgba(99, 102, 241, 0.5)" }}
                />
            </div>

            {/* Stage Steps */}
            <div className="space-y-3">
                {stages.map((stage, index) => {
                    const isComplete = currentStageIndex > index;
                    const isCurrent = currentStage === stage.id || currentStage.includes(stage.id.split("_")[0]);

                    return (
                        <motion.div
                            key={stage.id}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05, duration: 0.3 }}
                            className={`flex items-center gap-4 p-4 rounded-xl transition-all duration-300 ${isCurrent
                                    ? "bg-indigo-500/10 border border-indigo-500/20"
                                    : isComplete
                                        ? "bg-emerald-500/5 border border-transparent"
                                        : "opacity-40 border border-transparent"
                                }`}
                        >
                            <div
                                className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all duration-300 ${isComplete
                                        ? "bg-emerald-500/15 text-emerald-400"
                                        : isCurrent
                                            ? "bg-indigo-500/15 text-indigo-400"
                                            : "bg-slate-800/50 text-slate-500"
                                    }`}
                            >
                                {isComplete ? (
                                    <CheckCircle2 className="w-5 h-5" />
                                ) : isCurrent ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <stage.icon className="w-5 h-5" />
                                )}
                            </div>

                            <div className="flex-1 min-w-0">
                                <div className={`text-sm font-medium ${isCurrent ? "text-indigo-300" : isComplete ? "text-emerald-300" : "text-slate-400"
                                    }`}>
                                    {stage.label}
                                </div>
                                {isCurrent && events.length > 0 && (
                                    <div className="text-xs text-slate-500 mt-1 truncate">
                                        {events[events.length - 1]?.message}
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    );
                })}
            </div>

            {/* Recent Events Log */}
            {events.length > 0 && (
                <div className="mt-8 pt-6 border-t border-white/5">
                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-4">
                        Recent Activity
                    </div>
                    <div className="space-y-2 max-h-36 overflow-y-auto scrollbar-hide">
                        {events.slice(-5).reverse().map((event, i) => (
                            <div key={i} className="text-sm text-slate-400 flex items-start gap-3">
                                <span className="text-slate-600 text-xs font-mono flex-shrink-0 pt-0.5">
                                    {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </span>
                                <span className="leading-relaxed">{event.message}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
