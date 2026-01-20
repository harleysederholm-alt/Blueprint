"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useAnalysisStore, ProgressEvent } from "@/stores/analysis";

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
const MAX_RETRIES = 5;
const RETRY_DELAY_MS = 1000;

type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error" | "complete";

interface UseAnalysisWebSocketResult {
    connectionStatus: ConnectionStatus;
    retryCount: number;
    reconnect: () => void;
}

export function useAnalysisWebSocket(analysisId: string | null): UseAnalysisWebSocketResult {
    const wsRef = useRef<WebSocket | null>(null);
    const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const retryCountRef = useRef(0);
    const isMountedRef = useRef(true);
    const hasCompletedRef = useRef(false);
    const analysisIdRef = useRef(analysisId);

    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("connecting");
    const [retryCount, setRetryCount] = useState(0);

    const setProgress = useAnalysisStore((state) => state.setProgress);

    // Keep analysisId ref updated
    useEffect(() => {
        analysisIdRef.current = analysisId;
    }, [analysisId]);

    const connect = useCallback(() => {
        const currentAnalysisId = analysisIdRef.current;
        if (!currentAnalysisId) return;
        if (!isMountedRef.current) return;
        if (hasCompletedRef.current) return;

        const currentStatus = useAnalysisStore.getState().status;
        if (currentStatus === "completed" || currentStatus === "failed") {
            hasCompletedRef.current = true;
            setConnectionStatus("complete");
            return;
        }

        // Close existing connection if any
        if (wsRef.current) {
            try {
                if (wsRef.current.readyState === WebSocket.OPEN ||
                    wsRef.current.readyState === WebSocket.CONNECTING) {
                    wsRef.current.close();
                }
            } catch {
                // Ignore close errors
            }
        }

        setConnectionStatus("connecting");
        const wsUrl = `${WS_BASE}/api/analyze/${currentAnalysisId}/stream`;

        try {
            console.log("[WebSocket] Connecting to:", wsUrl);
            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                if (!isMountedRef.current || hasCompletedRef.current) return;
                console.log("[WebSocket] Connected");
                setConnectionStatus("connected");
                retryCountRef.current = 0;
                setRetryCount(0);
            };

            ws.onmessage = (event) => {
                if (!isMountedRef.current) return;

                try {
                    const data: ProgressEvent = JSON.parse(event.data);

                    // Skip keepalive pings for UI update
                    if (!data.keepalive) {
                        setProgress(data);
                    }

                    if (data.stage === "completed" || data.stage === "failed") {
                        hasCompletedRef.current = true;
                        setConnectionStatus("complete");
                        // Don't close here - let server close
                    }
                } catch (e) {
                    console.error("[WebSocket] Parse error:", e);
                }
            };

            ws.onerror = (error) => {
                if (hasCompletedRef.current) return;
                console.error("[WebSocket] Error:", error);
            };

            ws.onclose = (event) => {
                if (!isMountedRef.current) return;

                console.log("[WebSocket] Closed:", event.code);

                // Normal close (1000) or closed without status (1005) after complete
                if (hasCompletedRef.current || event.code === 1000) {
                    setConnectionStatus("complete");
                    return;
                }

                const status = useAnalysisStore.getState().status;
                if (status === "completed" || status === "failed") {
                    hasCompletedRef.current = true;
                    setConnectionStatus("complete");
                    return;
                }

                // Only retry if not completed and not at max retries
                if (retryCountRef.current < MAX_RETRIES) {
                    setConnectionStatus("disconnected");
                    const delay = RETRY_DELAY_MS * Math.pow(1.5, retryCountRef.current);
                    console.log(`[WebSocket] Retry ${retryCountRef.current + 1}/${MAX_RETRIES} in ${delay}ms`);

                    retryCountRef.current += 1;
                    setRetryCount(retryCountRef.current);

                    retryTimeoutRef.current = setTimeout(() => {
                        if (isMountedRef.current && !hasCompletedRef.current) {
                            connect();
                        }
                    }, delay);
                } else {
                    setConnectionStatus("error");
                    console.error("[WebSocket] Max retries reached");
                }
            };
        } catch (error) {
            console.error("[WebSocket] Connection error:", error);
            setConnectionStatus("error");
        }
    }, [setProgress]);

    const reconnect = useCallback(() => {
        hasCompletedRef.current = false;
        retryCountRef.current = 0;
        setRetryCount(0);
        connect();
    }, [connect]);

    // Connect on mount and when analysisId changes
    useEffect(() => {
        isMountedRef.current = true;
        hasCompletedRef.current = false;

        if (analysisId) {
            // Small delay to prevent immediate connection during SSR
            const timeoutId = setTimeout(() => {
                if (isMountedRef.current) {
                    connect();
                }
            }, 100);

            return () => {
                clearTimeout(timeoutId);
                isMountedRef.current = false;

                if (retryTimeoutRef.current) {
                    clearTimeout(retryTimeoutRef.current);
                    retryTimeoutRef.current = null;
                }

                if (wsRef.current) {
                    try {
                        wsRef.current.close();
                    } catch {
                        // Ignore
                    }
                    wsRef.current = null;
                }
            };
        }

        return () => {
            isMountedRef.current = false;
        };
    }, [analysisId, connect]);

    return {
        connectionStatus,
        retryCount,
        reconnect,
    };
}
