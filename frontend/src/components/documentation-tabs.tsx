"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
    Briefcase,
    Code2,
    Shield,
    AlertTriangle,
    CheckCircle,
    Lightbulb,
    FileText,
    ChevronRight,
} from "lucide-react";
import type { DocumentationResult, KeyFinding, Recommendation, DocumentSection, ADR } from "@/types/analysis";

interface DocumentationTabsProps {
    documentation: DocumentationResult;
}

const tabs = [
    { id: "executive", label: "Executive", icon: Briefcase },
    { id: "technical", label: "Technical", icon: Code2 },
    { id: "security", label: "Security", icon: Shield },
    { id: "adrs", label: "ADRs", icon: FileText },
];

const ImportanceBadge = ({ importance }: { importance: string }) => {
    const styles = {
        High: "bg-red-500/10 text-red-400 border-red-500/20",
        Medium: "bg-amber-500/10 text-amber-400 border-amber-500/20",
        Low: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    };
    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 text-xs font-medium rounded-full border ${styles[importance as keyof typeof styles] || styles.Low}`}>
            {importance}
        </span>
    );
};

export function DocumentationTabs({ documentation }: DocumentationTabsProps) {
    const [activeTab, setActiveTab] = useState("executive");

    const executiveSummary = documentation?.executive_summary || "";
    const sections = documentation?.sections || [];
    const keyFindings = documentation?.key_findings || [];
    const recommendations = documentation?.recommendations || [];
    const adrs = documentation?.generated_adrs || [];
    const nextSteps = documentation?.next_steps || [];

    return (
        <div className="glass rounded-2xl overflow-hidden">
            {/* Tab Navigation */}
            <div className="flex gap-1 p-1.5 border-b border-white/5 bg-white/[0.02]">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`relative flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200 ${activeTab === tab.id
                                ? "text-white bg-white/10"
                                : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        <span>{tab.label}</span>
                        {activeTab === tab.id && (
                            <motion.div
                                layoutId="activeTab"
                                className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 to-purple-500/10 rounded-lg border border-indigo-500/20"
                                transition={{ type: "spring", duration: 0.4 }}
                            />
                        )}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="p-8">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25, ease: "easeOut" }}
                >
                    {activeTab === "executive" && (
                        <div className="space-y-8">
                            {/* Executive Summary */}
                            {executiveSummary && (
                                <section>
                                    <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                        <Briefcase className="w-5 h-5 text-indigo-400" />
                                        Executive Summary
                                    </h3>
                                    <p className="text-slate-300 text-base leading-[1.75] max-w-prose">
                                        {executiveSummary}
                                    </p>
                                </section>
                            )}

                            {/* Key Findings */}
                            {keyFindings.length > 0 && (
                                <section>
                                    <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                        <Lightbulb className="w-5 h-5 text-amber-400" />
                                        Key Findings
                                    </h3>
                                    <div className="space-y-4">
                                        {keyFindings.map((finding: KeyFinding, i: number) => (
                                            <div
                                                key={i}
                                                className={`p-5 rounded-xl border transition-colors ${finding.importance === "High"
                                                        ? "bg-red-500/5 border-red-500/20 hover:border-red-500/30"
                                                        : finding.importance === "Medium"
                                                            ? "bg-amber-500/5 border-amber-500/20 hover:border-amber-500/30"
                                                            : "bg-blue-500/5 border-blue-500/20 hover:border-blue-500/30"
                                                    }`}
                                            >
                                                <div className="flex items-start gap-4">
                                                    {finding.importance === "High" ? (
                                                        <div className="p-2 rounded-lg bg-red-500/10 flex-shrink-0">
                                                            <AlertTriangle className="w-4 h-4 text-red-400" />
                                                        </div>
                                                    ) : (
                                                        <div className="p-2 rounded-lg bg-amber-500/10 flex-shrink-0">
                                                            <Lightbulb className="w-4 h-4 text-amber-400" />
                                                        </div>
                                                    )}
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-slate-200 text-base leading-relaxed mb-2">
                                                            {finding.finding}
                                                        </p>
                                                        <ImportanceBadge importance={finding.importance} />
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            {/* Next Steps */}
                            {nextSteps.length > 0 && (
                                <section>
                                    <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                                        <ChevronRight className="w-5 h-5 text-emerald-400" />
                                        Next Steps
                                    </h3>
                                    <ul className="space-y-3">
                                        {nextSteps.map((step: string, i: number) => (
                                            <li key={i} className="flex items-start gap-3 group">
                                                <div className="p-1 rounded-full bg-emerald-500/10 mt-0.5 flex-shrink-0">
                                                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                                                </div>
                                                <span className="text-slate-300 text-base leading-relaxed group-hover:text-slate-200 transition-colors">
                                                    {step}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </section>
                            )}
                        </div>
                    )}

                    {activeTab === "technical" && (
                        <div className="space-y-8">
                            {sections.map((section: DocumentSection, i: number) => (
                                <section key={i} className="border-b border-white/5 pb-8 last:border-0 last:pb-0">
                                    <h3 className="text-xl font-semibold text-white mb-4">
                                        {section.heading}
                                    </h3>
                                    <div className="text-slate-300 text-base leading-[1.75] whitespace-pre-wrap max-w-prose">
                                        {section.content}
                                    </div>
                                </section>
                            ))}

                            {sections.length === 0 && (
                                <div className="flex flex-col items-center justify-center py-16 text-center">
                                    <div className="p-4 rounded-2xl bg-slate-800/50 mb-4">
                                        <Code2 className="w-8 h-8 text-slate-500" />
                                    </div>
                                    <p className="text-slate-400 text-base">
                                        Technical documentation not available
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === "security" && (
                        <div className="space-y-6">
                            {recommendations.length > 0 && (
                                <div>
                                    <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                                        <Shield className="w-5 h-5 text-cyan-400" />
                                        Security Recommendations
                                    </h3>
                                    <div className="space-y-4">
                                        {recommendations.map((rec: Recommendation, i: number) => (
                                            <div
                                                key={i}
                                                className="p-5 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:border-slate-600/50 transition-colors"
                                            >
                                                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                                                    <p className="text-slate-200 text-base leading-relaxed flex-1">
                                                        {rec.recommendation}
                                                    </p>
                                                    <div className="flex gap-2 flex-shrink-0">
                                                        <span
                                                            className={`text-xs font-medium px-3 py-1.5 rounded-full ${rec.priority === "High"
                                                                    ? "bg-red-500/15 text-red-400 border border-red-500/20"
                                                                    : rec.priority === "Medium"
                                                                        ? "bg-amber-500/15 text-amber-400 border border-amber-500/20"
                                                                        : "bg-blue-500/15 text-blue-400 border border-blue-500/20"
                                                                }`}
                                                        >
                                                            {rec.priority}
                                                        </span>
                                                        <span className="text-xs font-medium px-3 py-1.5 rounded-full bg-slate-700/50 text-slate-400 border border-slate-600/30">
                                                            {rec.effort} effort
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {recommendations.length === 0 && (
                                <div className="flex flex-col items-center justify-center py-16 text-center">
                                    <div className="p-4 rounded-2xl bg-slate-800/50 mb-4">
                                        <Shield className="w-8 h-8 text-slate-500" />
                                    </div>
                                    <p className="text-slate-400 text-base">
                                        Security recommendations not available
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === "adrs" && (
                        <div className="space-y-6">
                            {adrs.length > 0 ? (
                                adrs.map((adr: ADR, i: number) => (
                                    <div
                                        key={i}
                                        className="p-6 rounded-xl bg-slate-800/40 border border-slate-700/50 hover:border-slate-600/50 transition-colors"
                                    >
                                        <div className="flex items-center justify-between mb-5">
                                            <h4 className="text-lg font-semibold text-white">{adr.title}</h4>
                                            <span
                                                className={`text-xs font-medium px-3 py-1.5 rounded-full ${adr.status === "Accepted"
                                                        ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20"
                                                        : adr.status === "Proposed"
                                                            ? "bg-blue-500/15 text-blue-400 border border-blue-500/20"
                                                            : "bg-slate-700/50 text-slate-400 border border-slate-600/30"
                                                    }`}
                                            >
                                                {adr.status}
                                            </span>
                                        </div>

                                        <div className="space-y-5">
                                            {adr.context && (
                                                <div>
                                                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                                                        Context
                                                    </div>
                                                    <p className="text-slate-300 text-base leading-relaxed">
                                                        {adr.context}
                                                    </p>
                                                </div>
                                            )}
                                            {adr.decision && (
                                                <div>
                                                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                                                        Decision
                                                    </div>
                                                    <p className="text-slate-300 text-base leading-relaxed">
                                                        {adr.decision}
                                                    </p>
                                                </div>
                                            )}
                                            {adr.consequences && (
                                                <div>
                                                    <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                                                        Consequences
                                                    </div>
                                                    <p className="text-slate-300 text-base leading-relaxed">
                                                        {adr.consequences}
                                                    </p>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="flex flex-col items-center justify-center py-16 text-center">
                                    <div className="p-4 rounded-2xl bg-slate-800/50 mb-4">
                                        <FileText className="w-8 h-8 text-slate-500" />
                                    </div>
                                    <p className="text-slate-400 text-base">
                                        No Architecture Decision Records generated
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </motion.div>
            </div>
        </div>
    );
}
