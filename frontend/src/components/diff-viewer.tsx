"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    GitBranch,
    GitCommit,
    ArrowRight,
    Plus,
    Minus,
    Edit3,
    AlertTriangle,
    Shield,
    CheckCircle2,
    Clock,
    Loader2,
} from "lucide-react";
import { MermaidViewer } from "./mermaid-viewer";

interface NodeChange {
    change_type: "added" | "removed" | "modified";
    node_id: string;
    node_name: string;
    node_type: string;
    file_path?: string;
    old_line_range?: string;
    new_line_range?: string;
    details: string;
    impact: "low" | "medium" | "high";
}

interface DiffStats {
    total_changes: number;
    added: number;
    removed: number;
    modified: number;
}

interface BlueprintDiffResult {
    base_ref: string;
    target_ref: string;
    base_timestamp?: string;
    target_timestamp?: string;
    summary: string;
    risk_level: "low" | "medium" | "high" | "critical";
    breaking_changes: string[];
    stats: DiffStats;
    node_changes: NodeChange[];
    edge_changes: { change_type: string; source: string; target: string; relation: string }[];
    layer_changes: { layer_name: string; added_components: string[]; removed_components: string[] }[];
}

interface DiffViewerProps {
    diff: BlueprintDiffResult;
    mermaidDiff?: string;
}

const riskColors = {
    low: "text-green-400 bg-green-500/10 border-green-500/30",
    medium: "text-yellow-400 bg-yellow-500/10 border-yellow-500/30",
    high: "text-orange-400 bg-orange-500/10 border-orange-500/30",
    critical: "text-red-400 bg-red-500/10 border-red-500/30",
};

const changeTypeIcons = {
    added: <Plus className="w-4 h-4 text-green-400" />,
    removed: <Minus className="w-4 h-4 text-red-400" />,
    modified: <Edit3 className="w-4 h-4 text-yellow-400" />,
};

const changeTypeColors = {
    added: "border-green-500/30 bg-green-500/5",
    removed: "border-red-500/30 bg-red-500/5",
    modified: "border-yellow-500/30 bg-yellow-500/5",
};

export function DiffViewer({ diff, mermaidDiff }: DiffViewerProps) {
    const [activeView, setActiveView] = useState<"summary" | "changes" | "diagram">("summary");
    const [filterType, setFilterType] = useState<"all" | "added" | "removed" | "modified">("all");

    const filteredChanges =
        filterType === "all"
            ? diff.node_changes
            : diff.node_changes.filter((c) => c.change_type === filterType);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="glass rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 rounded-lg">
                            <GitCommit className="w-4 h-4 text-slate-400" />
                            <span className="text-sm font-mono">{diff.base_ref.slice(0, 8)}</span>
                        </div>
                        <ArrowRight className="w-5 h-5 text-slate-500" />
                        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 border border-blue-500/30 rounded-lg">
                            <GitBranch className="w-4 h-4 text-blue-400" />
                            <span className="text-sm font-mono">{diff.target_ref.slice(0, 8)}</span>
                        </div>
                    </div>

                    {/* Risk Badge */}
                    <div
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${riskColors[diff.risk_level]}`}
                    >
                        {diff.risk_level === "critical" || diff.risk_level === "high" ? (
                            <AlertTriangle className="w-4 h-4" />
                        ) : diff.risk_level === "medium" ? (
                            <Shield className="w-4 h-4" />
                        ) : (
                            <CheckCircle2 className="w-4 h-4" />
                        )}
                        <span className="text-sm font-medium capitalize">{diff.risk_level} Risk</span>
                    </div>
                </div>

                {/* Summary */}
                <p className="text-slate-300">{diff.summary}</p>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 mt-4">
                    <div className="text-center p-3 bg-slate-800/50 rounded-lg">
                        <div className="text-2xl font-bold text-slate-200">{diff.stats.total_changes}</div>
                        <div className="text-xs text-slate-500">Total Changes</div>
                    </div>
                    <div className="text-center p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                        <div className="text-2xl font-bold text-green-400">+{diff.stats.added}</div>
                        <div className="text-xs text-slate-500">Added</div>
                    </div>
                    <div className="text-center p-3 bg-red-500/10 rounded-lg border border-red-500/20">
                        <div className="text-2xl font-bold text-red-400">-{diff.stats.removed}</div>
                        <div className="text-xs text-slate-500">Removed</div>
                    </div>
                    <div className="text-center p-3 bg-yellow-500/10 rounded-lg border border-yellow-500/20">
                        <div className="text-2xl font-bold text-yellow-400">~{diff.stats.modified}</div>
                        <div className="text-xs text-slate-500">Modified</div>
                    </div>
                </div>
            </div>

            {/* Breaking Changes Warning */}
            {diff.breaking_changes.length > 0 && (
                <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass rounded-xl p-4 border border-red-500/30 bg-red-500/5"
                >
                    <div className="flex items-start gap-3">
                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5" />
                        <div>
                            <h4 className="font-semibold text-red-400 mb-2">
                                ⚠️ Potential Breaking Changes ({diff.breaking_changes.length})
                            </h4>
                            <ul className="space-y-1 text-sm text-slate-300">
                                {diff.breaking_changes.map((change, i) => (
                                    <li key={i} className="flex items-start gap-2">
                                        <span className="text-red-400">•</span>
                                        {change}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </motion.div>
            )}

            {/* View Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-800">
                {(["summary", "changes", "diagram"] as const).map((view) => (
                    <button
                        key={view}
                        onClick={() => setActiveView(view)}
                        className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${activeView === view
                                ? "border-blue-500 text-blue-400"
                                : "border-transparent text-slate-400 hover:text-slate-200"
                            }`}
                    >
                        {view.charAt(0).toUpperCase() + view.slice(1)}
                    </button>
                ))}
            </div>

            {/* View Content */}
            <AnimatePresence mode="wait">
                {activeView === "summary" && (
                    <motion.div
                        key="summary"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="space-y-4"
                    >
                        {/* Layer Changes */}
                        {diff.layer_changes.length > 0 && (
                            <div className="glass rounded-xl p-5">
                                <h4 className="font-semibold text-slate-200 mb-3">Layer Changes</h4>
                                <div className="space-y-2">
                                    {diff.layer_changes.map((layer, i) => (
                                        <div key={i} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg">
                                            <span className="font-medium text-slate-300">{layer.layer_name}</span>
                                            <div className="flex gap-4 text-sm">
                                                {layer.added_components.length > 0 && (
                                                    <span className="text-green-400">
                                                        +{layer.added_components.length} added
                                                    </span>
                                                )}
                                                {layer.removed_components.length > 0 && (
                                                    <span className="text-red-400">
                                                        -{layer.removed_components.length} removed
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Edge Changes */}
                        {diff.edge_changes.length > 0 && (
                            <div className="glass rounded-xl p-5">
                                <h4 className="font-semibold text-slate-200 mb-3">
                                    Dependency Changes ({diff.edge_changes.length})
                                </h4>
                                <div className="space-y-2 max-h-48 overflow-y-auto">
                                    {diff.edge_changes.slice(0, 10).map((edge, i) => (
                                        <div
                                            key={i}
                                            className={`p-2 rounded border ${edge.change_type === "added"
                                                    ? "border-green-500/30 bg-green-500/5"
                                                    : "border-red-500/30 bg-red-500/5"
                                                }`}
                                        >
                                            <span className="text-xs font-mono text-slate-400">
                                                {edge.source.split(":").pop()} → {edge.target.split(":").pop()}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                )}

                {activeView === "changes" && (
                    <motion.div
                        key="changes"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="space-y-4"
                    >
                        {/* Filter */}
                        <div className="flex gap-2">
                            {(["all", "added", "removed", "modified"] as const).map((type) => (
                                <button
                                    key={type}
                                    onClick={() => setFilterType(type)}
                                    className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${filterType === type
                                            ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                                            : "bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700"
                                        }`}
                                >
                                    {type.charAt(0).toUpperCase() + type.slice(1)}
                                </button>
                            ))}
                        </div>

                        {/* Changes List */}
                        <div className="space-y-2">
                            {filteredChanges.map((change, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: -10 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.02 }}
                                    className={`p-4 rounded-lg border ${changeTypeColors[change.change_type]}`}
                                >
                                    <div className="flex items-start gap-3">
                                        {changeTypeIcons[change.change_type]}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-medium text-slate-200">{change.node_name}</span>
                                                <span className="text-xs px-2 py-0.5 bg-slate-700 rounded text-slate-400">
                                                    {change.node_type}
                                                </span>
                                                {change.impact === "high" && (
                                                    <span className="text-xs px-2 py-0.5 bg-red-500/20 text-red-400 rounded">
                                                        High Impact
                                                    </span>
                                                )}
                                            </div>
                                            {change.file_path && (
                                                <div className="text-xs text-slate-500 font-mono truncate">
                                                    {change.file_path}
                                                </div>
                                            )}
                                            {change.details && (
                                                <div className="text-sm text-slate-400 mt-1">{change.details}</div>
                                            )}
                                        </div>
                                    </div>
                                </motion.div>
                            ))}

                            {filteredChanges.length === 0 && (
                                <div className="text-center py-8 text-slate-500">
                                    No {filterType === "all" ? "" : filterType} changes
                                </div>
                            )}
                        </div>
                    </motion.div>
                )}

                {activeView === "diagram" && (
                    <motion.div
                        key="diagram"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        {mermaidDiff ? (
                            <MermaidViewer code={mermaidDiff} title="Architecture Diff" />
                        ) : (
                            <div className="text-center py-8 text-slate-500">
                                Diff diagram not available
                            </div>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// Loading skeleton
export function DiffViewerSkeleton() {
    return (
        <div className="space-y-6 animate-pulse">
            <div className="glass rounded-xl p-6">
                <div className="flex items-center gap-4 mb-4">
                    <div className="w-24 h-8 bg-slate-700 rounded" />
                    <div className="w-8 h-8 bg-slate-700 rounded-full" />
                    <div className="w-24 h-8 bg-slate-700 rounded" />
                </div>
                <div className="h-4 bg-slate-700 rounded w-3/4" />
                <div className="grid grid-cols-4 gap-4 mt-4">
                    {[1, 2, 3, 4].map((i) => (
                        <div key={i} className="h-16 bg-slate-700 rounded" />
                    ))}
                </div>
            </div>
        </div>
    );
}

// Diff request form
interface DiffFormProps {
    onSubmit: (baseRef: string, targetRef: string) => void;
    isLoading?: boolean;
    commits?: { hash: string; short_hash: string; message: string }[];
}

export function DiffForm({ onSubmit, isLoading, commits = [] }: DiffFormProps) {
    const [baseRef, setBaseRef] = useState("");
    const [targetRef, setTargetRef] = useState("");

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (baseRef && targetRef) {
            onSubmit(baseRef, targetRef);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="glass rounded-xl p-6 space-y-4">
            <h3 className="font-semibold text-slate-200 flex items-center gap-2">
                <GitBranch className="w-5 h-5" />
                Compare Architecture
            </h3>

            <div className="grid md:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm text-slate-400 mb-2">Base (from)</label>
                    <input
                        type="text"
                        value={baseRef}
                        onChange={(e) => setBaseRef(e.target.value)}
                        placeholder="main, HEAD~5, abc1234..."
                        list="commits-base"
                        className="w-full px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    />
                    <datalist id="commits-base">
                        {commits.map((c) => (
                            <option key={c.hash} value={c.short_hash}>
                                {c.message}
                            </option>
                        ))}
                    </datalist>
                </div>

                <div>
                    <label className="block text-sm text-slate-400 mb-2">Target (to)</label>
                    <input
                        type="text"
                        value={targetRef}
                        onChange={(e) => setTargetRef(e.target.value)}
                        placeholder="feature-branch, HEAD, def5678..."
                        list="commits-target"
                        className="w-full px-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    />
                    <datalist id="commits-target">
                        {commits.map((c) => (
                            <option key={c.hash} value={c.short_hash}>
                                {c.message}
                            </option>
                        ))}
                    </datalist>
                </div>
            </div>

            <button
                type="submit"
                disabled={!baseRef || !targetRef || isLoading}
                className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg font-medium text-white flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity"
            >
                {isLoading ? (
                    <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Comparing...
                    </>
                ) : (
                    <>
                        <GitCommit className="w-4 h-4" />
                        Compare Architecture
                    </>
                )}
            </button>
        </form>
    );
}
