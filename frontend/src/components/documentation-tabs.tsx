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

export function DocumentationTabs({ documentation }: DocumentationTabsProps) {
    const [activeTab, setActiveTab] = useState("executive");

    const executiveSummary = documentation?.executive_summary || "";
    const sections = documentation?.sections || [];
    const keyFindings = documentation?.key_findings || [];
    const recommendations = documentation?.recommendations || [];
    const adrs = documentation?.generated_adrs || [];
    const nextSteps = documentation?.next_steps || [];

    return (
        <div className="glass rounded-xl overflow-hidden">
            {/* Tab Navigation */}
            <div className="flex border-b border-slate-800">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors ${activeTab === tab.id
                                ? "text-blue-400 border-b-2 border-blue-500 bg-blue-500/5"
                                : "text-slate-400 hover:text-slate-200"
                            }`}
                    >
                        <tab.icon className="w-4 h-4" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="p-6">
                <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                >
                    {activeTab === "executive" && (
                        <div className="space-y-6">
                            {/* Executive Summary */}
                            {executiveSummary && (
                                <div>
                                    <h3 className="text-lg font-semibold text-slate-200 mb-3">Executive Summary</h3>
                                    <p className="text-slate-300 leading-relaxed">{executiveSummary}</p>
                                </div>
                            )}

                            {/* Key Findings */}
                            {keyFindings.length > 0 && (
                                <div>
                                    <h3 className="text-lg font-semibold text-slate-200 mb-3">Key Findings</h3>
                                    <div className="space-y-3">
                                        {keyFindings.map((finding: KeyFinding, i: number) => (
                                            <div
                                                key={i}
                                                className={`p-4 rounded-lg border ${finding.importance === "High"
                                                        ? "bg-red-500/5 border-red-500/30"
                                                        : finding.importance === "Medium"
                                                            ? "bg-yellow-500/5 border-yellow-500/30"
                                                            : "bg-blue-500/5 border-blue-500/30"
                                                    }`}
                                            >
                                                <div className="flex items-start gap-3">
                                                    {finding.importance === "High" ? (
                                                        <AlertTriangle className="w-5 h-5 text-red-400 mt-0.5" />
                                                    ) : (
                                                        <Lightbulb className="w-5 h-5 text-yellow-400 mt-0.5" />
                                                    )}
                                                    <div>
                                                        <div className="text-slate-200">{finding.finding}</div>
                                                        <div className="text-xs text-slate-500 mt-1">
                                                            Importance: {finding.importance}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Next Steps */}
                            {nextSteps.length > 0 && (
                                <div>
                                    <h3 className="text-lg font-semibold text-slate-200 mb-3">Next Steps</h3>
                                    <ul className="space-y-2">
                                        {nextSteps.map((step: string, i: number) => (
                                            <li key={i} className="flex items-start gap-3 text-slate-300">
                                                <CheckCircle className="w-4 h-4 text-green-400 mt-1" />
                                                {step}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === "technical" && (
                        <div className="space-y-6">
                            {/* Sections */}
                            {sections.map((section: DocumentSection, i: number) => (
                                <div key={i}>
                                    <h3 className="text-lg font-semibold text-slate-200 mb-3">
                                        {section.heading}
                                    </h3>
                                    <div className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                                        {section.content}
                                    </div>
                                </div>
                            ))}

                            {sections.length === 0 && (
                                <div className="text-slate-500 text-center py-8">
                                    Technical documentation not available
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === "security" && (
                        <div className="space-y-6">
                            {/* Recommendations */}
                            {recommendations.length > 0 && (
                                <div>
                                    <h3 className="text-lg font-semibold text-slate-200 mb-3">
                                        Security Recommendations
                                    </h3>
                                    <div className="space-y-3">
                                        {recommendations.map((rec: Recommendation, i: number) => (
                                            <div
                                                key={i}
                                                className="p-4 rounded-lg bg-slate-800/50 border border-slate-700"
                                            >
                                                <div className="flex items-start justify-between gap-4">
                                                    <div className="text-slate-200">{rec.recommendation}</div>
                                                    <div className="flex gap-2 shrink-0">
                                                        <span
                                                            className={`text-xs px-2 py-1 rounded ${rec.priority === "High"
                                                                    ? "bg-red-500/20 text-red-400"
                                                                    : rec.priority === "Medium"
                                                                        ? "bg-yellow-500/20 text-yellow-400"
                                                                        : "bg-blue-500/20 text-blue-400"
                                                                }`}
                                                        >
                                                            {rec.priority}
                                                        </span>
                                                        <span className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-400">
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
                                <div className="text-slate-500 text-center py-8">
                                    Security recommendations not available
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
                                        className="p-5 rounded-lg bg-slate-800/50 border border-slate-700"
                                    >
                                        <div className="flex items-center justify-between mb-3">
                                            <h4 className="font-semibold text-slate-200">{adr.title}</h4>
                                            <span
                                                className={`text-xs px-2 py-1 rounded ${adr.status === "Accepted"
                                                        ? "bg-green-500/20 text-green-400"
                                                        : adr.status === "Proposed"
                                                            ? "bg-blue-500/20 text-blue-400"
                                                            : "bg-slate-700 text-slate-400"
                                                    }`}
                                            >
                                                {adr.status}
                                            </span>
                                        </div>

                                        <div className="space-y-3 text-sm">
                                            {adr.context && (
                                                <div>
                                                    <div className="text-slate-500 mb-1">Context</div>
                                                    <div className="text-slate-300">{adr.context}</div>
                                                </div>
                                            )}
                                            {adr.decision && (
                                                <div>
                                                    <div className="text-slate-500 mb-1">Decision</div>
                                                    <div className="text-slate-300">{adr.decision}</div>
                                                </div>
                                            )}
                                            {adr.consequences && (
                                                <div>
                                                    <div className="text-slate-500 mb-1">Consequences</div>
                                                    <div className="text-slate-300">{adr.consequences}</div>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className="text-slate-500 text-center py-8">
                                    No Architecture Decision Records generated
                                </div>
                            )}
                        </div>
                    )}
                </motion.div>
            </div>
        </div>
    );
}
