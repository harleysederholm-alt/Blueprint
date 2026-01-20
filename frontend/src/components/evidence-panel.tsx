"use client";

import { useState } from "react";
import { Search, FileCode2, ChevronRight, FileText } from "lucide-react";
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
        <div className="glass rounded-2xl overflow-hidden flex flex-col h-full max-h-[800px]">
            {/* Header */}
            <div className="px-6 py-5 border-b border-white/5 bg-white/[0.02]">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                        <FileText className="w-5 h-5 text-indigo-400" />
                        Todistekartta
                    </h3>
                    <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                        {filteredEvidence.length} kohdetta
                    </span>
                </div>

                {/* Search */}
                <div className="relative group">
                    <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 group-focus-within:text-indigo-400 transition-colors" />
                    <input
                        type="text"
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        placeholder="Etsi todisteita tiedoston, sisällön tai ID:n perusteella..."
                        className="w-full pl-10 pr-4 py-2.5 bg-slate-900/50 border border-slate-700/50 rounded-xl text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500/30 transition-all"
                    />
                </div>
            </div>

            {/* Evidence List */}
            <div className="overflow-y-auto scrollbar-hide p-2 flex-grow">
                {filteredEvidence.length > 0 ? (
                    <div className="space-y-1">
                        {filteredEvidence.map((evidence, i) => {
                            const claimId = evidence.claim_id;
                            const isExpanded = expandedClaim === claimId;

                            return (
                                <div
                                    key={i}
                                    className={`rounded-xl transition-all duration-200 ${isExpanded
                                        ? "bg-white/[0.04] shadow-lg"
                                        : "hover:bg-white/[0.02]"
                                        }`}
                                >
                                    <button
                                        onClick={() => setExpandedClaim(isExpanded ? null : claimId)}
                                        className="w-full text-left p-3"
                                    >
                                        <div className="flex items-start gap-3">
                                            <div className={`mt-1 transition-transform duration-200 ${isExpanded ? "rotate-90" : ""}`}>
                                                <ChevronRight className="w-4 h-4 text-slate-500" />
                                            </div>

                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                                    <span className="text-[10px] uppercase tracking-wider font-mono px-1.5 py-0.5 bg-indigo-500/10 text-indigo-300 rounded border border-indigo-500/20">
                                                        {claimId}
                                                    </span>
                                                    <span
                                                        className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${evidence.confidence === "high"
                                                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                                                            : evidence.confidence === "medium"
                                                                ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                                                                : "bg-slate-700/50 text-slate-400 border-slate-600/30"
                                                            }`}
                                                    >
                                                        {evidence.confidence === "high" ? "korkea" : evidence.confidence === "medium" ? "keskitaso" : "matala"} luottamus
                                                    </span>
                                                </div>

                                                <div className="flex items-center gap-2 text-sm text-slate-300 group">
                                                    <FileCode2 className="w-3.5 h-3.5 text-slate-500 group-hover:text-slate-400 transition-colors" />
                                                    <span className="truncate font-mono text-xs opacity-80">{evidence.file_path}</span>
                                                    {evidence.line_range && (
                                                        <span className="text-slate-600 text-xs font-mono shrink-0">
                                                            L{evidence.line_range}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </button>

                                    {/* Expanded Quote */}
                                    {isExpanded && evidence.quote && (
                                        <div className="px-4 pb-4 pl-10">
                                            <div className="relative">
                                                <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-indigo-500/30 rounded-full"></div>
                                                <pre className="pl-4 py-2 text-xs text-slate-400 font-mono leading-relaxed whitespace-pre-wrap break-words max-h-60 overflow-y-auto scrollbar-hide">
                                                    {evidence.quote}
                                                </pre>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-64 text-slate-500">
                        <Search className="w-8 h-8 mb-3 opacity-20" />
                        <p className="text-sm">Hakuehdoilla ei löytynyt todisteita</p>
                    </div>
                )}
            </div>
        </div>
    );
}
