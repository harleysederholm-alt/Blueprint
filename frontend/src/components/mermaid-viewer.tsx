"use client";

import { useEffect, useRef, useState } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Download, Network } from "lucide-react";
import mermaid from "mermaid";

interface MermaidViewerProps {
    code: string;
    title?: string;
}

export function MermaidViewer({ code, title }: MermaidViewerProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const [zoom, setZoom] = useState(1);
    const [svgContent, setSvgContent] = useState<string>("");
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        mermaid.initialize({
            startOnLoad: false,
            theme: "base",
            themeVariables: {
                primaryColor: "#3b82f6",
                primaryTextColor: "#e2e8f0",
                primaryBorderColor: "#475569",
                lineColor: "#64748b",
                secondaryColor: "#1e293b",
                tertiaryColor: "#0f172a",
                background: "transparent",
                mainBkg: "transparent",
                nodeBkg: "#1e293b",
                nodeBorder: "#475569",
                clusterBkg: "rgba(30, 41, 59, 0.3)",
                clusterBorder: "#475569",
                titleColor: "#f1f5f9",
                edgeLabelBackground: "#1e293b",
                fontFamily: "var(--font-sans)",
            },
            fontFamily: "var(--font-sans)",
        });
    }, []);

    useEffect(() => {
        const renderDiagram = async () => {
            if (!code || !containerRef.current) {
                setSvgContent("");
                return;
            }

            try {
                setError(null);
                // Clear previous SVG to prevent flickering artifacts
                setSvgContent("");
                const id = `mermaid-${Date.now()}`;
                const { svg } = await mermaid.render(id, code);
                setSvgContent(svg);
            } catch (e) {
                console.error("Mermaid render error:", e);
                // Fallback for common errors
                setError(e instanceof Error ? e.message : "Failed to render diagram");
                setSvgContent("");
            }
        };

        renderDiagram();
    }, [code]);

    const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 3));
    const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.5));
    const handleReset = () => setZoom(1);

    const handleDownload = () => {
        if (!svgContent) return;

        const blob = new Blob([svgContent], { type: "image/svg+xml" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${title?.toLowerCase().replace(/\s+/g, '-') || "architecture-diagram"}.svg`;
        a.click();
        URL.revokeObjectURL(url);
    };

    if (!code) {
        return (
            <div className="glass rounded-2xl p-12 text-center border-dashed border-2 border-slate-800">
                <Network className="w-12 h-12 text-slate-700 mx-auto mb-4" />
                <div className="text-slate-500 font-medium">No diagram available for this view</div>
                <p className="text-slate-600 text-sm mt-2">Try selecting a different architectural view.</p>
            </div>
        );
    }

    return (
        <div className="glass rounded-2xl overflow-hidden flex flex-col h-full bg-[#0B1121]/50 backdrop-blur-xl border border-white/5">
            {/* Toolbar */}
            <div className="px-5 py-3 border-b border-white/5 bg-white/[0.02] flex items-center justify-between z-10">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 rounded-lg bg-indigo-500/10">
                        <Network className="w-4 h-4 text-indigo-400" />
                    </div>
                    <h3 className="font-medium text-slate-200 text-sm">{title || "Architecture Diagram"}</h3>
                </div>

                <div className="flex items-center bg-slate-900/50 rounded-lg p-1 border border-white/5">
                    <button
                        onClick={handleZoomOut}
                        className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-md transition-all active:scale-95"
                        title="Zoom out"
                    >
                        <ZoomOut className="w-4 h-4" />
                    </button>
                    <span className="text-xs font-mono text-slate-500 min-w-[3.5rem] text-center select-none border-l border-r border-white/5 mx-1">
                        {Math.round(zoom * 100)}%
                    </span>
                    <button
                        onClick={handleZoomIn}
                        className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-md transition-all active:scale-95"
                        title="Zoom in"
                    >
                        <ZoomIn className="w-4 h-4" />
                    </button>
                    <button
                        onClick={handleReset}
                        className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-md transition-all ml-1 border-l border-white/5 pl-2 active:scale-95"
                        title="Reset zoom"
                    >
                        <RotateCcw className="w-4 h-4" />
                    </button>
                    <button
                        onClick={handleDownload}
                        className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-md transition-all ml-1 active:scale-95"
                        title="Download SVG"
                    >
                        <Download className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Diagram Container */}
            <div className="relative flex-grow min-h-[500px] overflow-hidden bg-[url('/grid-pattern.svg')] bg-repeat opacity-100">
                {/* Subtle grid background if pattern is missing */}
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:24px_24px]"></div>

                <div
                    ref={containerRef}
                    className="absolute inset-0 overflow-auto flex items-center justify-center p-8 scrollbar-hide"
                >
                    {error ? (
                        <div className="text-center max-w-md p-8 rounded-2xl bg-red-500/5 border border-red-500/10">
                            <div className="text-red-400 font-medium mb-2">Render Error</div>
                            <div className="text-xs text-red-300/70 font-mono mb-4">{error}</div>
                            <div className="text-xs text-slate-500">
                                This usually happens when the generated syntax is invalid. Try regenerating the analysis.
                            </div>
                        </div>
                    ) : svgContent ? (
                        <div
                            className="transition-transform duration-300 ease-out origin-center"
                            style={{ transform: `scale(${zoom})` }}
                            dangerouslySetInnerHTML={{ __html: svgContent }}
                        />
                    ) : (
                        <div className="flex flex-col items-center justify-center gap-4 text-slate-500 animate-pulse">
                            <div className="w-12 h-12 rounded-full bg-slate-800/50"></div>
                            <div className="h-4 w-32 bg-slate-800/50 rounded"></div>
                        </div>
                    )}
                </div>
            </div>

            {/* Footer / Code Toggle */}
            <div className="border-t border-white/5 bg-slate-950/30">
                <details className="group">
                    <summary className="px-5 py-2 text-xs text-slate-500 cursor-pointer hover:text-slate-300 transition-colors flex items-center gap-2 select-none">
                        <span className="group-open:rotate-90 transition-transform">▸</span>
                        View Mermaid Syntax
                    </summary>
                    <div className="px-5 pb-4">
                        <div className="rounded-lg bg-black/40 border border-white/5 p-3 overflow-auto max-h-32">
                            <pre className="text-[10px] text-slate-400 font-mono leading-relaxed whitespace-pre-wrap">
                                {code}
                            </pre>
                        </div>
                    </div>
                </details>
            </div>
        </div>
    );
}
