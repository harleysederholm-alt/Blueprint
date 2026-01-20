"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  GitBranch,
  Sparkles,
  FileCode2,
  Network,
  Shield,
  Users,
  ArrowRight,
  Loader2
} from "lucide-react";
import { RepoInput } from "@/components/repo-input";
import { AudienceSelector } from "@/components/audience-selector";
import { useAnalysisStore } from "@/stores/analysis";
import { useRouter } from "next/navigation";

const features = [
  {
    icon: FileCode2,
    title: "Evidence-Anchored",
    description: "Every claim links to file:line numbers"
  },
  {
    icon: Network,
    title: "C4 Diagrams",
    description: "Auto-generated Context, Container, Component"
  },
  {
    icon: Users,
    title: "Multi-Audience",
    description: "Executive, Engineer, Security, Investor views"
  },
  {
    icon: Shield,
    title: "Local LLM",
    description: "Powered by Ollama - no data leaves your machine"
  }
];

export default function HomePage() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState("");
  const [audience, setAudience] = useState("engineer");
  const [isLoading, setIsLoading] = useState(false);
  const { startAnalysis } = useAnalysisStore();

  const handleAnalyze = async () => {
    if (!repoUrl.trim()) return;

    setIsLoading(true);
    try {
      const analysisId = await startAnalysis(repoUrl, audience);
      router.push(`/analyze/${analysisId}`);
    } catch (error) {
      console.error("Failed to start analysis:", error);
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <section className="relative px-6 py-24 lg:py-32">
        {/* Background glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse-slow" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: "1.5s" }} />
        </div>

        <div className="relative max-w-6xl mx-auto">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="flex justify-center mb-8"
          >
            <div className="glass px-4 py-2 rounded-full flex items-center gap-2 text-sm">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span className="text-slate-300">Powered by Local AI • v3.0</span>
            </div>
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-4xl md:text-6xl lg:text-7xl font-bold text-center mb-6"
          >
            <span className="gradient-text">RepoBlueprint</span>
            <span className="text-slate-200"> AI</span>
          </motion.h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg md:text-xl text-slate-400 text-center max-w-3xl mx-auto mb-12"
          >
            Instant, evidence-based, executable architecture understanding —
            <br className="hidden md:block" />
            from any repository, for any stakeholder.
          </motion.p>

          {/* Input Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="max-w-3xl mx-auto"
          >
            <div className="glass-strong rounded-2xl p-6 md:p-8">
              <div className="space-y-6">
                {/* Repository URL Input */}
                <RepoInput
                  value={repoUrl}
                  onChange={setRepoUrl}
                  disabled={isLoading}
                />

                {/* Audience Selector */}
                <AudienceSelector
                  value={audience}
                  onChange={setAudience}
                  disabled={isLoading}
                />

                {/* Analyze Button */}
                <button
                  onClick={handleAnalyze}
                  disabled={!repoUrl.trim() || isLoading}
                  className="w-full py-4 px-8 bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 disabled:from-slate-600 disabled:to-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all duration-300 flex items-center justify-center gap-3 glow-blue hover:scale-[1.02] active:scale-[0.98]"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Starting Analysis...</span>
                    </>
                  ) : (
                    <>
                      <span>Analyze Repository</span>
                      <ArrowRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>

          {/* Features Grid */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16"
          >
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.5 + index * 0.1 }}
                className="glass rounded-xl p-5 text-center hover:border-blue-500/30 transition-colors"
              >
                <feature.icon className="w-8 h-8 mx-auto mb-3 text-blue-400" />
                <h3 className="font-semibold text-slate-200 mb-1">{feature.title}</h3>
                <p className="text-sm text-slate-400">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="px-6 py-16 border-t border-slate-800/50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-12">
            How It Works
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Paste Repository URL",
                description: "Enter any public GitHub, GitLab, or Bitbucket repository URL"
              },
              {
                step: "02",
                title: "AI Analysis Pipeline",
                description: "Three specialized AI agents analyze architecture, runtime, and documentation"
              },
              {
                step: "03",
                title: "Explore Results",
                description: "Interactive C4 diagrams, evidence-linked docs, and actionable insights"
              }
            ].map((item, i) => (
              <div key={item.step} className="relative">
                <div className="text-6xl font-bold text-slate-800/50 mb-4">{item.step}</div>
                <h3 className="text-xl font-semibold text-slate-200 mb-2">{item.title}</h3>
                <p className="text-slate-400">{item.description}</p>
                {i < 2 && (
                  <div className="hidden md:block absolute top-8 right-0 translate-x-1/2">
                    <ArrowRight className="w-6 h-6 text-slate-600" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-8 border-t border-slate-800/50">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-blue-400" />
            <span className="font-semibold">RepoBlueprint AI</span>
            <span className="text-slate-500">v3.0</span>
          </div>
          <p className="text-sm text-slate-500">
            Powered by Ollama • Local LLM • No data leaves your machine
          </p>
        </div>
      </footer>
    </main>
  );
}
