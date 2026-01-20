"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
    Download,
    FileText,
    FileCode,
    FileJson,
    Loader2,
    Check,
    ChevronDown,
} from "lucide-react";

interface ExportButtonsProps {
    analysisId: string;
    type?: "analysis" | "diff";
}

const exportFormats = [
    {
        id: "markdown",
        name: "Markdown",
        icon: FileText,
        extension: ".md",
        description: "With Mermaid diagrams",
    },
    {
        id: "html",
        name: "HTML",
        icon: FileCode,
        extension: ".html",
        description: "Standalone document",
    },
    {
        id: "json",
        name: "JSON",
        icon: FileJson,
        extension: ".json",
        description: "Raw data",
    },
];

export function ExportButtons({ analysisId, type = "analysis" }: ExportButtonsProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [downloading, setDownloading] = useState<string | null>(null);
    const [downloaded, setDownloaded] = useState<string | null>(null);

    const handleExport = async (formatId: string) => {
        setDownloading(formatId);

        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const endpoint = type === "analysis"
                ? `${baseUrl}/api/export/analysis/${analysisId}/${formatId}`
                : `${baseUrl}/api/export/diff/${analysisId}/${formatId}`;

            const response = await fetch(endpoint);

            if (!response.ok) {
                throw new Error("Export failed");
            }

            // Get filename from content-disposition header
            const contentDisposition = response.headers.get("content-disposition");
            let filename = `${type}_${analysisId}.${formatId === "markdown" ? "md" : formatId}`;

            if (contentDisposition) {
                const match = contentDisposition.match(/filename="(.+)"/);
                if (match) {
                    filename = match[1];
                }
            }

            // Download the file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            setDownloaded(formatId);
            setTimeout(() => setDownloaded(null), 2000);

        } catch (error) {
            console.error("Export failed:", error);
        } finally {
            setDownloading(null);
        }
    };

    return (
        <div className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/30 rounded-lg text-sm font-medium hover:bg-blue-500/30 transition-colors"
            >
                <Download className="w-4 h-4" />
                Export
                <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`} />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        {/* Backdrop */}
                        <div
                            className="fixed inset-0 z-10"
                            onClick={() => setIsOpen(false)}
                        />

                        {/* Dropdown */}
                        <motion.div
                            initial={{ opacity: 0, y: -10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -10, scale: 0.95 }}
                            transition={{ duration: 0.15 }}
                            className="absolute right-0 top-full mt-2 z-20 w-56 glass rounded-xl border border-slate-700 shadow-xl overflow-hidden"
                        >
                            <div className="p-2">
                                <div className="text-xs text-slate-500 px-2 py-1 mb-1">
                                    Export Format
                                </div>

                                {exportFormats.map((format) => {
                                    const Icon = format.icon;
                                    const isDownloading = downloading === format.id;
                                    const isDownloaded = downloaded === format.id;

                                    return (
                                        <button
                                            key={format.id}
                                            onClick={() => handleExport(format.id)}
                                            disabled={isDownloading}
                                            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-700/50 transition-colors text-left group"
                                        >
                                            <div className="w-8 h-8 rounded-lg bg-slate-700/50 flex items-center justify-center group-hover:bg-slate-700">
                                                {isDownloading ? (
                                                    <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
                                                ) : isDownloaded ? (
                                                    <Check className="w-4 h-4 text-green-400" />
                                                ) : (
                                                    <Icon className="w-4 h-4 text-slate-400" />
                                                )}
                                            </div>

                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-medium text-slate-200">
                                                    {format.name}
                                                </div>
                                                <div className="text-xs text-slate-500">
                                                    {format.description}
                                                </div>
                                            </div>

                                            <span className="text-xs text-slate-500 font-mono">
                                                {format.extension}
                                            </span>
                                        </button>
                                    );
                                })}
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}

// Quick single-format export button
interface QuickExportButtonProps {
    analysisId: string;
    format: "markdown" | "html" | "json";
    type?: "analysis" | "diff";
}

export function QuickExportButton({
    analysisId,
    format,
    type = "analysis"
}: QuickExportButtonProps) {
    const [downloading, setDownloading] = useState(false);
    const [downloaded, setDownloaded] = useState(false);

    const formatConfig = exportFormats.find((f) => f.id === format);
    const Icon = formatConfig?.icon || FileText;

    const handleExport = async () => {
        setDownloading(true);

        try {
            const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
            const endpoint = type === "analysis"
                ? `${baseUrl}/api/export/analysis/${analysisId}/${format}`
                : `${baseUrl}/api/export/diff/${analysisId}/markdown`;

            const response = await fetch(endpoint);

            if (!response.ok) throw new Error("Export failed");

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `${type}_${analysisId}.${format === "markdown" ? "md" : format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            setDownloaded(true);
            setTimeout(() => setDownloaded(false), 2000);

        } catch (error) {
            console.error("Export failed:", error);
        } finally {
            setDownloading(false);
        }
    };

    return (
        <button
            onClick={handleExport}
            disabled={downloading}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-xs font-medium hover:bg-slate-700 transition-colors disabled:opacity-50"
        >
            {downloading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : downloaded ? (
                <Check className="w-3.5 h-3.5 text-green-400" />
            ) : (
                <Icon className="w-3.5 h-3.5" />
            )}
            {formatConfig?.extension}
        </button>
    );
}
