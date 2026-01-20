"use client";

import {
    Briefcase,
    Code2,
    Shield,
    Presentation,
    GraduationCap,
    TrendingUp
} from "lucide-react";

interface AudienceSelectorProps {
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
}

const audiences = [
    { id: "executive", label: "Executive", icon: Briefcase, description: "Business-focused summary" },
    { id: "engineer", label: "Engineer", icon: Code2, description: "Technical deep-dive" },
    { id: "security_analyst", label: "Security", icon: Shield, description: "Risk & compliance focus" },
    { id: "sales_engineer", label: "Sales Engineer", icon: Presentation, description: "Capabilities overview" },
    { id: "new_hire", label: "New Hire", icon: GraduationCap, description: "Onboarding guide" },
    { id: "investor", label: "Investor", icon: TrendingUp, description: "Due diligence view" },
];

export function AudienceSelector({ value, onChange, disabled }: AudienceSelectorProps) {
    return (
        <div className="space-y-3">
            <label className="block text-sm font-medium text-slate-300">
                Target Audience
            </label>

            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {audiences.map((audience) => {
                    const isSelected = value === audience.id;
                    return (
                        <button
                            key={audience.id}
                            onClick={() => onChange(audience.id)}
                            disabled={disabled}
                            className={`p-3 rounded-xl border transition-all text-left ${isSelected
                                    ? "bg-blue-500/10 border-blue-500/50 text-blue-400"
                                    : "bg-slate-900/30 border-slate-700 text-slate-400 hover:bg-slate-800/50 hover:border-slate-600"
                                } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            <div className="flex items-center gap-2 mb-1">
                                <audience.icon className={`w-4 h-4 ${isSelected ? "text-blue-400" : "text-slate-500"}`} />
                                <span className={`font-medium ${isSelected ? "text-blue-300" : "text-slate-300"}`}>
                                    {audience.label}
                                </span>
                            </div>
                            <p className="text-xs text-slate-500">{audience.description}</p>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
