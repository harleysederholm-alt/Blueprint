"use client";

import { GitBranch, Github, ExternalLink } from "lucide-react";

interface RepoInputProps {
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
}

const exampleRepos = [
    { name: "Express.js", url: "https://github.com/expressjs/express" },
    { name: "FastAPI", url: "https://github.com/tiangolo/fastapi" },
    { name: "Next.js", url: "https://github.com/vercel/next.js" },
];

export function RepoInput({ value, onChange, disabled }: RepoInputProps) {
    return (
        <div className="space-y-4">
            <label className="block text-sm font-semibold text-slate-300 tracking-wide">
                Repository URL
            </label>

            <div className="relative group">
                <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-blue-400 transition-colors duration-300">
                    <GitBranch className="w-5 h-5" />
                </div>
                <input
                    type="url"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    placeholder="https://github.com/owner/repository"
                    className="w-full pl-12 pr-4 py-4 bg-slate-900/40 border border-slate-700/50 rounded-xl text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 focus:bg-slate-900/60 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed font-mono text-sm shadow-inner"
                />

                {/* Subtle glow effect on focus */}
                <div className="absolute inset-0 rounded-xl bg-blue-500/5 opacity-0 group-focus-within:opacity-100 transition-opacity duration-500 pointer-events-none" />
            </div>

            {/* Quick Examples */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-500 font-medium px-1">TRY:</span>
                {exampleRepos.map((repo) => (
                    <button
                        key={repo.url}
                        onClick={() => onChange(repo.url)}
                        disabled={disabled}
                        className="group flex items-center gap-1.5 px-3 py-1.5 bg-slate-800/30 hover:bg-blue-500/10 border border-slate-700/50 hover:border-blue-500/30 rounded-lg text-slate-400 hover:text-blue-300 transition-all duration-300 disabled:opacity-50"
                    >
                        <Github className="w-3.5 h-3.5 opacity-70 group-hover:opacity-100" />
                        {repo.name}
                    </button>
                ))}
            </div>
        </div>
    );
}
