"use client";

import { useEffect, useRef, useState } from "react";
import { ZoomIn, ZoomOut, RotateCcw, Download, Maximize2 } from "lucide-react";
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
            theme: "dark",
            themeVariables: {
                primaryColor: "#3b82f6",
                primaryTextColor: "#f1f5f9",
                primaryBorderColor: "#334155",
                lineColor: "#64748b",
                secondaryColor: "#1e293b",
                tertiaryColor: "#0f172a",
                background: "#020617",
                mainBkg: "#0f172a",
                nodeBkg: "#1e293b",
                nodeBorder: "#334155",
                clusterBkg: "#1e293b",
                clusterBorder: "#334155",
                titleColor: "#f1f5f9",
                edgeLabelBackground: "#1e293b",
            },
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
                const id = `mermaid-${Date.now()}`;
                const { svg } = await mermaid.render(id, code);
                setSvgContent(svg);
            } catch (e) {
                console.error("Mermaid render error:", e);
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
        a.download = `${title || "diagram"}.svg`;
        a.click();
        URL.revokeObjectURL(url);
    };

    if (!code) {
        return (
            <div className="glass rounded-xl p-8 text-center">
                <div className="text-slate-500">No diagram available for this view</div>
            </div>
        );
    }

    return (
        <div className="glass rounded-xl overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-medium text-slate-300 capitalize">{title}</h3>

                <div className="flex items-center gap-2">
                    <button
                        onClick={handleZoomOut}
                        className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                        title="Zoom out"
                    >
                        <ZoomOut className="w-4 h-4" />
                    </button>
                    <span className="text-sm text-slate-500 min-w-[3rem] text-center">
                        {Math.round(zoom * 100)}%
                    </span>
                    <button
                        onClick={handleZoomIn}
                        className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                        title="Zoom in"
                    >
                        <ZoomIn className="w-4 h-4" />
                    </button>
                    <button
                        onClick={handleReset}
                        className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                        title="Reset zoom"
                    >
                        <RotateCcw className="w-4 h-4" />
                    </button>
                    <div className="w-px h-4 bg-slate-700 mx-1" />
                    <button
                        onClick={handleDownload}
                        className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                        title="Download SVG"
                    >
                        <Download className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Diagram Container */}
            <div
                ref={containerRef}
                className="p-4 overflow-auto bg-slate-950/50"
                style={{ minHeight: "400px", maxHeight: "600px" }}
            >
                {error ? (
                    <div className="text-center py-8">
                        <div className="text-red-400 mb-2">Failed to render diagram</div>
                        <div className="text-sm text-slate-500">{error}</div>
                        <pre className="mt-4 p-4 bg-slate-900 rounded-lg text-left text-xs text-slate-400 overflow-auto max-h-48">
                            {code}
                        </pre>
                    </div>
                ) : svgContent ? (
                    <div
                        className="flex items-center justify-center transition-transform duration-200"
                        style={{ transform: `scale(${zoom})`, transformOrigin: "top center" }}
                        dangerouslySetInnerHTML={{ __html: svgContent }}
                    />
                ) : (
                    <div className="flex items-center justify-center h-64 text-slate-500">
                        Loading diagram...
                    </div>
                )}
            </div>

            {/* Raw Code Toggle */}
            <details className="border-t border-slate-800">
                <summary className="px-4 py-2 text-sm text-slate-500 cursor-pointer hover:text-slate-300">
                    View Mermaid Code
                </summary>
                <pre className="px-4 py-3 bg-slate-900/50 text-xs text-slate-400 overflow-auto max-h-48">
                    {code}
                </pre>
            </details>
        </div>
    );
}
