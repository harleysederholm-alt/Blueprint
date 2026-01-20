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
        <div className="space-y-3">
            <label className="block text-sm font-medium text-slate-300">
                Repository URL
            </label>

            <div className="relative">
                <div className="absolute left-4 top-1/2 -translate-y-1/2">
                    <GitBranch className="w-5 h-5 text-slate-500" />
                </div>
                <input
                    type="url"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={disabled}
                    placeholder="https://github.com/owner/repository"
                    className="w-full pl-12 pr-4 py-3.5 bg-slate-900/50 border border-slate-700 rounded-xl text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                />
            </div>

            {/* Quick Examples */}
            <div className="flex flex-wrap items-center gap-2 text-sm">
                <span className="text-slate-500">Try:</span>
                {exampleRepos.map((repo) => (
                    <button
                        key={repo.url}
                        onClick={() => onChange(repo.url)}
                        disabled={disabled}
                        className="px-3 py-1 bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700 rounded-lg text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                    >
                        <Github className="w-3.5 h-3.5" />
                        {repo.name}
                    </button>
                ))}
            </div>
        </div>
    );
}
