"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Search,
    Send,
    Sparkles,
    ChevronRight,
    Code,
    GitBranch,
    Layers,
    Lightbulb,
    AlertCircle,
    Loader2,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

interface QueryResult {
    query: string;
    query_type: string;
    answer: string;
    nodes: { id: string; name: string; type: string; file?: string }[];
    edges: { source: string; target: string; relation: string }[];
    confidence: number;
    suggestions: string[];
}

interface QueryInterfaceProps {
    analysisId: string;
}

const exampleQueries = [
    { icon: Search, text: "Find class UserService", category: "search" },
    { icon: GitBranch, text: "What depends on Database?", category: "deps" },
    { icon: Code, text: "Show design patterns", category: "patterns" },
    { icon: Layers, text: "Analyze architectural layers", category: "layers" },
    { icon: AlertCircle, text: "Find coupling hotspots", category: "quality" },
];

export function QueryInterface({ analysisId }: QueryInterfaceProps) {
    const [query, setQuery] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [results, setResults] = useState<QueryResult[]>([]);
    const [error, setError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const resultsEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to latest result
    useEffect(() => {
        resultsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [results]);

    const handleSubmit = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!query.trim() || isLoading) return;

        setIsLoading(true);
        setError(null);

        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const response = await fetch(`${baseUrl}/api/query/ask`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    analysis_id: analysisId,
                    question: query,
                }),
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Query failed");
            }

            const result = await response.json();
            setResults((prev) => [...prev, result]);
            setQuery("");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Query failed");
        } finally {
            setIsLoading(false);
        }
    };

    const handleExampleClick = (text: string) => {
        setQuery(text);
        inputRef.current?.focus();
    };

    return (
        <div className="flex flex-col h-full">
            {/* Results Area */}
            <div className="flex-1 overflow-y-auto space-y-4 pb-4">
                {results.length === 0 ? (
                    <div className="text-center py-12">
                        <Sparkles className="w-12 h-12 mx-auto mb-4 text-blue-400 opacity-50" />
                        <h3 className="text-lg font-medium text-slate-300 mb-2">
                            Ask about the architecture
                        </h3>
                        <p className="text-sm text-slate-500 mb-6">
                            Query the knowledge graph with natural language
                        </p>

                        {/* Example Queries */}
                        <div className="flex flex-wrap justify-center gap-2 max-w-lg mx-auto">
                            {exampleQueries.map((example, i) => {
                                const Icon = example.icon;
                                return (
                                    <button
                                        key={i}
                                        onClick={() => handleExampleClick(example.text)}
                                        className="flex items-center gap-2 px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm text-slate-300 hover:bg-slate-700/50 hover:border-slate-600 transition-colors"
                                    >
                                        <Icon className="w-4 h-4 text-slate-400" />
                                        {example.text}
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <>
                        {results.map((result, i) => (
                            <QueryResultCard key={i} result={result} />
                        ))}
                        <div ref={resultsEndRef} />
                    </>
                )}
            </div>

            {/* Error */}
            <AnimatePresence>
                {error && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-sm text-red-400"
                    >
                        {error}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Input */}
            <form onSubmit={handleSubmit} className="relative">
                <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask about the architecture..."
                    className="w-full px-4 py-3 pr-12 bg-slate-900/80 border border-slate-700 rounded-xl text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50"
                />
                <button
                    type="submit"
                    disabled={!query.trim() || isLoading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-blue-500 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
                >
                    {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <Send className="w-4 h-4" />
                    )}
                </button>
            </form>
        </div>
    );
}

function QueryResultCard({ result }: { result: QueryResult }) {
    const [expanded, setExpanded] = useState(false);

    const confidenceColor =
        result.confidence >= 0.8
            ? "text-green-400"
            : result.confidence >= 0.6
                ? "text-yellow-400"
                : "text-orange-400";

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-xl overflow-hidden"
        >
            {/* Query */}
            <div className="px-4 py-3 border-b border-slate-700/50 bg-slate-800/30">
                <div className="flex items-center gap-2 text-sm">
                    <Search className="w-4 h-4 text-slate-500" />
                    <span className="text-slate-400">{result.query}</span>
                    <span className={`ml-auto text-xs ${confidenceColor}`}>
                        {Math.round(result.confidence * 100)}% confidence
                    </span>
                </div>
            </div>

            {/* Answer */}
            <div className="p-4">
                <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown
                        components={{
                            code: ({ children }) => (
                                <code className="px-1.5 py-0.5 bg-slate-700 rounded text-blue-300">
                                    {children}
                                </code>
                            ),
                            strong: ({ children }) => (
                                <strong className="text-slate-200 font-semibold">{children}</strong>
                            ),
                            ul: ({ children }) => (
                                <ul className="list-disc list-inside space-y-1">{children}</ul>
                            ),
                            h3: ({ children }) => (
                                <h3 className="text-base font-semibold text-slate-200 mt-3 mb-2">
                                    {children}
                                </h3>
                            ),
                        }}
                    >
                        {result.answer}
                    </ReactMarkdown>
                </div>

                {/* Nodes/Edges Summary */}
                {(result.nodes.length > 0 || result.edges.length > 0) && (
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="mt-3 flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
                    >
                        <ChevronRight
                            className={`w-3 h-3 transition-transform ${expanded ? "rotate-90" : ""}`}
                        />
                        {result.nodes.length > 0 && `${result.nodes.length} nodes`}
                        {result.nodes.length > 0 && result.edges.length > 0 && " • "}
                        {result.edges.length > 0 && `${result.edges.length} edges`}
                    </button>
                )}

                <AnimatePresence>
                    {expanded && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                        >
                            <div className="mt-3 pt-3 border-t border-slate-700/50 space-y-2">
                                {result.nodes.slice(0, 5).map((node, i) => (
                                    <div
                                        key={i}
                                        className="flex items-center gap-2 text-xs p-2 bg-slate-800/50 rounded"
                                    >
                                        <Code className="w-3 h-3 text-slate-500" />
                                        <span className="text-slate-300">{node.name}</span>
                                        <span className="text-slate-500">({node.type})</span>
                                        {node.file && (
                                            <span className="ml-auto text-slate-600 font-mono truncate max-w-[200px]">
                                                {node.file}
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Suggestions */}
                {result.suggestions.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-slate-700/50">
                        <div className="flex items-center gap-1 text-xs text-slate-500 mb-2">
                            <Lightbulb className="w-3 h-3" />
                            Try also:
                        </div>
                        <div className="flex flex-wrap gap-1">
                            {result.suggestions.slice(0, 3).map((suggestion, i) => (
                                <span
                                    key={i}
                                    className="px-2 py-1 bg-slate-800/50 rounded text-xs text-slate-400"
                                >
                                    {suggestion}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </motion.div>
    );
}

// Compact inline query input
export function InlineQueryInput({
    analysisId,
    onResult,
}: {
    analysisId: string;
    onResult?: (result: QueryResult) => void;
}) {
    const [query, setQuery] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || isLoading) return;

        setIsLoading(true);

        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const response = await fetch(`${baseUrl}/api/query/ask`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ analysis_id: analysisId, question: query }),
            });

            if (response.ok) {
                const result = await response.json();
                onResult?.(result);
                setQuery("");
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about architecture..."
                className="w-full pl-10 pr-10 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-sm placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30"
            />
            {isLoading && (
                <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-blue-400" />
            )}
        </form>
    );
}
