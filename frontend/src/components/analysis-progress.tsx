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
        <div className="glass rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-slate-200">Analysis Progress</h2>
                <span className="text-sm text-slate-400">{Math.round(currentProgress)}%</span>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden mb-8">
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${currentProgress}%` }}
                    transition={{ duration: 0.5 }}
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                />
            </div>

            {/* Stage Steps */}
            <div className="space-y-4">
                {stages.map((stage, index) => {
                    const isComplete = currentStageIndex > index;
                    const isCurrent = currentStage === stage.id || currentStage.includes(stage.id.split("_")[0]);
                    const isPending = !isComplete && !isCurrent;

                    return (
                        <motion.div
                            key={stage.id}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.1 }}
                            className={`flex items-center gap-4 p-3 rounded-lg transition-colors ${isCurrent
                                    ? "bg-blue-500/10 border border-blue-500/30"
                                    : isComplete
                                        ? "bg-green-500/5"
                                        : "opacity-50"
                                }`}
                        >
                            <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center ${isComplete
                                        ? "bg-green-500/20 text-green-400"
                                        : isCurrent
                                            ? "bg-blue-500/20 text-blue-400"
                                            : "bg-slate-800 text-slate-500"
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

                            <div className="flex-1">
                                <div className={`font-medium ${isCurrent ? "text-blue-300" : isComplete ? "text-green-300" : "text-slate-400"}`}>
                                    {stage.label}
                                </div>
                                {isCurrent && events.length > 0 && (
                                    <div className="text-sm text-slate-500">
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
                <div className="mt-6 pt-6 border-t border-slate-800">
                    <div className="text-sm text-slate-500 mb-2">Recent Activity</div>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                        {events.slice(-5).reverse().map((event, i) => (
                            <div key={i} className="text-xs text-slate-400 flex items-center gap-2">
                                <span className="text-slate-600">
                                    {new Date(event.timestamp).toLocaleTimeString()}
                                </span>
                                <span>{event.message}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
