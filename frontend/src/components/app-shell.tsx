"use client";

import React from "react";

export function AppShell({ children }: { children: React.ReactNode }) {
    return (
        <div className="relative min-h-screen bg-slate-950 text-slate-100 overflow-x-hidden selection:bg-blue-500/30">
            {/* Background grid – Locked, does not affect layout */}
            <div className="pointer-events-none absolute inset-0 -z-10">
                <div className="h-full w-full bg-[linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.04)_1px,transparent_1px)] bg-[size:48px_48px]" />
                <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-blue-500 opacity-20 blur-[100px]" />
            </div>

            {/* Main Container - The Single Source of Truth for Width */}
            <main className="mx-auto max-w-7xl px-6 lg:px-8 pt-6">
                {children}
            </main>
        </div>
    );
}
