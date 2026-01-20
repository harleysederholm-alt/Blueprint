"use client";

import { useState } from "react";
import { Search, FileCode2, ChevronRight } from "lucide-react";
import type { Evidence } from "@/types/analysis";

interface EvidencePanelProps {
    evidenceMap: Evidence[];
}

export function EvidencePanel({ evidenceMap }: EvidencePanelProps) {
    const [search, setSearch] = useState("");
    const [expandedClaim, setExpandedClaim] = useState<string | null>(null);

    const filteredEvidence = evidenceMap.filter((ev) => {
        if (!search) return true;
        const searchLower = search.toLowerCase();
        return (
            ev.file_path?.toLowerCase().includes(searchLower) ||
            ev.quote?.toLowerCase().includes(searchLower) ||
            ev.claim_id?.toLowerCase().includes(searchLower)
        );
    });

    return (
        <div className="glass rounded-xl overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-800">
                <h3 className="font-semibold text-slate-200 mb-3">Evidence Map</h3>

                {/* Search */}
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Search evidence..."
                        className="w-full pl-9 pr-4 py-2 bg-slate-900/50 border border-slate-700 rounded-lg text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    />
                </div>
            </div>

            {/* Evidence List */}
            <div className="max-h-[500px] overflow-y-auto">
                {filteredEvidence.length > 0 ? (
                    <div className="divide-y divide-slate-800">
                        {filteredEvidence.map((evidence, i) => {
                            const claimId = evidence.claim_id;
                            const isExpanded = expandedClaim === claimId;

                            return (
                                <div
                                    key={i}
                                    className="p-4 hover:bg-slate-800/30 transition-colors"
                                >
                                    <button
                                        onClick={() => setExpandedClaim(isExpanded ? null : claimId)}
                                        className="w-full text-left"
                                    >
                                        <div className="flex items-start gap-3">
                                            <ChevronRight
                                                className={`w-4 h-4 text-slate-500 mt-1 transition-transform ${isExpanded ? "rotate-90" : ""
                                                    }`}
                                            />
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded">
                                                        {claimId}
                                                    </span>
                                                    <span
                                                        className={`text-xs px-2 py-0.5 rounded ${evidence.confidence === "high"
                                                                ? "bg-green-500/20 text-green-400"
                                                                : evidence.confidence === "medium"
                                                                    ? "bg-yellow-500/20 text-yellow-400"
                                                                    : "bg-slate-700 text-slate-400"
                                                            }`}
                                                    >
                                                        {evidence.confidence || "medium"}
                                                    </span>
                                                </div>

                                                <div className="flex items-center gap-2 text-sm text-slate-300">
                                                    <FileCode2 className="w-4 h-4 text-slate-500" />
                                                    <span className="truncate">{evidence.file_path}</span>
                                                    {evidence.line_range && (
                                                        <span className="text-slate-500 shrink-0">
                                                            :{evidence.line_range}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </button>

                                    {/* Expanded Quote */}
                                    {isExpanded && evidence.quote && (
                                        <div className="mt-3 ml-7">
                                            <pre className="p-3 bg-slate-900/50 rounded-lg text-xs text-slate-300 overflow-x-auto">
                                                {evidence.quote}
                                            </pre>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="p-8 text-center text-slate-500">
                        {search ? "No evidence matches your search" : "No evidence available"}
                    </div>
                )}
            </div>

            {/* Footer Stats */}
            <div className="px-4 py-3 border-t border-slate-800 text-sm text-slate-500">
                {filteredEvidence.length} evidence item{filteredEvidence.length !== 1 ? "s" : ""}
                {search && ` matching "${search}"`}
            </div>
        </div>
    );
}
