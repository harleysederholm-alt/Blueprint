"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Github,
  Search,
  Layout,
  Shield,
  Zap,
  CheckCircle2,
  Code2,
  Menu,
  Database,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { useAnalysisStore } from "@/stores/analysis";

const FeatureCard = ({
  icon,
  title,
  desc,
  delay,
  order,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
  delay: number;
  order: number;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.5, delay }}
    className="glass-card group relative !p-8 rounded-2xl overflow-hidden flex flex-col h-full"
    style={{ order }}
  >
    <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/[0.03] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
    <div className="relative z-10 w-12 h-12 bg-indigo-500/10 rounded-xl flex items-center justify-center mb-6 border border-indigo-500/20 group-hover:scale-105 transition-transform duration-300">
      {icon}
    </div>
    <h3 className="relative z-10 text-lg font-semibold text-white mb-3 group-hover:text-indigo-300 transition-colors">
      {title}
    </h3>
    <p className="relative z-10 text-slate-400 text-sm leading-relaxed line-clamp-3">
      {desc}
    </p>
  </motion.div>
);

const PipelineStep = ({
  number,
  title,
  desc,
  delay,
}: {
  number: string;
  title: string;
  desc: string;
  delay: number;
}) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ duration: 0.5, delay }}
    className="glass-card relative !p-8 rounded-2xl w-full group hover:border-indigo-500/30 transition-all flex flex-col h-full"
  >
    <div className="absolute top-4 right-6 opacity-[0.06] group-hover:opacity-10 transition-opacity">
      <span className="text-6xl font-black text-white">{number}</span>
    </div>
    <div className="relative z-10 flex flex-col h-full">
      <div className="text-[10px] font-mono text-indigo-400 mb-4 tracking-widest uppercase bg-indigo-500/10 w-fit px-2 py-1 rounded border border-indigo-500/10">
        Step {number}
      </div>
      <h4 className="text-xl font-bold text-white mb-3">{title}</h4>
      <p className="text-slate-400 text-sm leading-relaxed flex-grow">{desc}</p>
    </div>
  </motion.div>
);

export default function LandingPage() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState("");
  const [audience] = useState("engineer");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { startAnalysis } = useAnalysisStore();

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) return;

    setIsLoading(true);
    setErrorMessage(null);

    try {
      const analysisId = await startAnalysis(repoUrl, audience);
      router.push(`/analyze/${analysisId}`);
    } catch (error) {
      console.error("Failed to start analysis:", error);
      setErrorMessage(error instanceof Error ? error.message : "Failed to start analysis");
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && repoUrl.trim() && !isLoading) {
      handleAnalyze();
    }
  };

  return (
    <main
      className="relative isolate flex min-h-screen w-full flex-col items-center justify-start pb-40 px-6 overflow-x-hidden bg-[#020617] text-slate-300"
      style={{ paddingTop: '280px' }}
    >
      <div className="fixed inset-0 z-[-1] pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[5%] w-[1200px] h-[1200px] bg-indigo-500/10 blur-[150px] rounded-full mix-blend-screen opacity-40" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[1000px] h-[1000px] bg-blue-600/8 blur-[120px] rounded-full mix-blend-screen opacity-30" />
        <div className="absolute top-[50%] left-[70%] w-[500px] h-[500px] bg-purple-500/5 blur-[100px] rounded-full mix-blend-screen opacity-30" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808008_1px,transparent_1px),linear-gradient(to_bottom,#80808008_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_0%,#000_70%,transparent_100%)]" />
      </div>

      <header className="fixed top-0 left-0 right-0 z-50 h-20 border-b border-white/5 bg-[#020617]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          <div
            className="flex items-center gap-3 cursor-pointer"
            onClick={() => router.push("/")}
          >
            <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-blue-600 shadow-lg shadow-indigo-500/20 ring-1 ring-white/10">
              <Code2 className="text-white w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-white tracking-tight text-lg leading-none">
                RepoBlueprint
              </span>
              <span className="text-[10px] font-mono text-indigo-400 font-medium tracking-wider uppercase mt-0.5">
                Engine v3.0
              </span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 hover:text-white transition-colors pointer-events-auto"
            >
              <Github className="w-4 h-4" />
              GitHub
            </a>
            <div className="h-4 w-px bg-white/10" />
            <button
              onClick={() => document.getElementById('repo-input')?.focus()}
              className="bg-white text-slate-950 px-6 py-2.5 rounded-full font-bold hover:bg-indigo-50 transition-all shadow-[0_0_20px_-5px_rgba(255,255,255,0.3)] active:scale-95 pointer-events-auto"
            >
              Get Started
            </button>
          </nav>

          <div className="md:hidden text-slate-400 p-2 hover:bg-white/5 rounded-lg pointer-events-auto">
            <Menu className="w-6 h-6" />
          </div>
        </div>
      </header>

      <div className="flex flex-col items-center text-center max-w-7xl w-full mb-40 z-10 relative">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <div className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-indigo-500/20 bg-indigo-500/5 text-indigo-300 text-xs font-mono font-medium tracking-wide shadow-lg shadow-indigo-500/10">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            System Operational
            <span className="mx-2 text-indigo-500/30">|</span>
            <span className="text-indigo-400/80">Local Inference Ready</span>
          </div>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold tracking-tight text-white leading-[1.05] mb-10 drop-shadow-2xl break-words w-full"
        >
          Architectural Intelligence
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-cyan-400">
            For GitHub.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-base sm:text-lg md:text-xl text-slate-400 max-w-3xl mx-auto leading-relaxed font-light mb-14"
        >
          Transform complex GitHub repositories into evidence-anchored C4 diagrams, context maps, and audit reports.
          <span className="block sm:inline text-slate-200 font-medium">
            {" "}Zero cloud data egress. 100% Local.
          </span>
        </motion.p>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="w-full max-w-3xl relative group shrink-0 z-30"
        >
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 rounded-2xl blur opacity-30 group-hover:opacity-60 group-focus-within:opacity-60 transition duration-500 pointer-events-none" />

          <div className="relative flex flex-col sm:flex-row items-center bg-[#0B1121] border border-white/10 rounded-xl p-3 shadow-2xl gap-3 sm:gap-0 backdrop-blur-xl pointer-events-auto">
            <div className="hidden sm:flex items-center justify-center w-14 h-14 rounded-lg bg-white/5 ml-1 flex-shrink-0 border border-white/5">
              <Github className="w-6 h-6 text-slate-400" />
            </div>

            <input
              id="repo-input"
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="https://github.com/organization/repository"
              className="w-full sm:flex-grow bg-transparent border-none outline-none text-white placeholder-slate-600 font-mono text-sm sm:text-base px-5 h-14 min-w-0 focus:ring-0 pointer-events-auto disabled:opacity-50"
              autoComplete="off"
              spellCheck="false"
            />

            <button
              onClick={handleAnalyze}
              disabled={!repoUrl.trim() || isLoading}
              className="w-full sm:w-auto shrink-0 bg-indigo-600 hover:bg-indigo-500 text-white px-10 h-14 rounded-lg font-bold text-base transition-all flex items-center justify-center gap-3 shadow-lg hover:shadow-indigo-500/30 hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed pointer-events-auto relative z-40 active:scale-95"
            >
              {isLoading ? (
                <>
                  <Zap className="w-5 h-5 animate-spin fill-white" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 fill-white" />
                  <span>Generate</span>
                </>
              )}
            </button>
          </div>

          {errorMessage && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 flex items-center justify-center gap-2 text-red-400 text-sm"
            >
              <AlertCircle className="w-4 h-4" />
              <span>{errorMessage}</span>
            </motion.div>
          )}

          <div className="flex flex-wrap justify-center gap-6 sm:gap-8 mt-10 text-[11px] uppercase tracking-wider font-bold text-slate-500 select-none">
            <span className="flex items-center gap-2 hover:text-emerald-400 transition-colors">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> SOC2 Compliant
            </span>
            <span className="flex items-center gap-2 hover:text-emerald-400 transition-colors">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Local Enclave
            </span>
            <span className="flex items-center gap-2 hover:text-emerald-400 transition-colors">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" /> Mermaid.js Ready
            </span>
          </div>
        </motion.div>
      </div>

      <div className="w-full max-w-7xl mb-40 z-10">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-8">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">How It Works</h2>
            <p className="text-slate-400 max-w-md text-base leading-relaxed">
              From raw code to executive intelligence in three automated steps.
            </p>
          </div>
          <div className="h-px flex-grow bg-gradient-to-r from-transparent via-white/10 to-transparent hidden md:block mb-4 mx-8" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <PipelineStep
            delay={0}
            number="01"
            title="Ingest & Parse"
            desc="Clones the repository locally and builds an Abstract Syntax Tree to map code structure and dependencies."
          />
          <PipelineStep
            delay={0.1}
            number="02"
            title="Reason & Infer"
            desc="Uses local LLMs to identify design patterns, bounded contexts, and data flows without cloud egress."
          />
          <PipelineStep
            delay={0.2}
            number="03"
            title="Visualize"
            desc="Generates instant C4 diagrams (Context, Container, Component) and comprehensive audit reports."
          />
        </div>
      </div>

      <div className="w-full max-w-7xl pb-20 pt-20 border-t border-white/5 z-10">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          <FeatureCard
            order={1}
            delay={0}
            icon={<Search className="w-7 h-7 text-indigo-400" />}
            title="Deep Analysis"
            desc="AST parsing meets local LLMs to understand code logic, not just syntax. Identifies patterns and anti-patterns automatically."
          />
          <FeatureCard
            order={2}
            delay={0.1}
            icon={<Layout className="w-7 h-7 text-blue-400" />}
            title="Auto C4 Models"
            desc="Generate Context, Container, and Component diagrams instantly. Export to Mermaid, PlantUML, or Structurizr."
          />
          <FeatureCard
            order={3}
            delay={0.2}
            icon={<Shield className="w-7 h-7 text-cyan-400" />}
            title="Local Executive"
            desc="Runs entirely on Ollama. Your source code never leaves your machine. Perfect for sensitive enterprise projects."
          />
          <FeatureCard
            order={4}
            delay={0.3}
            icon={<Database className="w-7 h-7 text-purple-400" />}
            title="Graph Database"
            desc="Maps dependencies and call graphs into a queryable knowledge graph. Ask natural language questions about architecture."
          />
        </div>
      </div>
    </main>
  );
}
