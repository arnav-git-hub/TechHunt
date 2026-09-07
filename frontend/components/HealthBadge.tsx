/**
 * HealthBadge client component.
 *
 * Fetches the backend health status and displays a subtle badge.
 * This proves frontend ↔ backend communication on the landing page.
 * Rendered client-side so it shows live status without a server reload.
 */

"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";
import type { HealthResponse } from "@/types";

type BadgeState = "loading" | "ok" | "degraded" | "unreachable";

function getBadgeState(
  health: HealthResponse | null,
  error: boolean
): BadgeState {
  if (error) return "unreachable";
  if (!health) return "loading";
  if (health.status === "ok" && health.database === "ok") return "ok";
  return "degraded";
}

const BADGE_CONFIG: Record<
  BadgeState,
  { dot: string; text: string; label: string }
> = {
  loading: {
    dot: "bg-gray-400 animate-pulse",
    text: "text-gray-500",
    label: "Checking API…",
  },
  ok: {
    dot: "bg-green-500",
    text: "text-gray-500",
    label: "API connected",
  },
  degraded: {
    dot: "bg-yellow-500",
    text: "text-gray-500",
    label: "API degraded",
  },
  unreachable: {
    dot: "bg-red-500",
    text: "text-gray-500",
    label: "API unreachable",
  },
};

export function HealthBadge() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [hasError, setHasError] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function check() {
      const result = await fetchHealth();
      if (cancelled) return;
      if (result.error) {
        setHasError(true);
      } else {
        setHealth(result.data);
        setHasError(false);
      }
    }

    void check();
    // Re-check every 30 seconds
    const interval = setInterval(() => void check(), 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const state = getBadgeState(health, hasError);
  const config = BADGE_CONFIG[state];

  if (!isVisible) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={`Backend status: ${config.label}`}
      title={
        health
          ? `TechHunt API v${health.version} · ${health.environment} · DB: ${health.database} · uptime: ${Math.round(health.uptime_seconds)}s`
          : config.label
      }
      className="group flex items-center gap-2 rounded-full border border-gray-200 bg-white/95 px-3 py-1.5 text-xs shadow-sm backdrop-blur-sm cursor-default"
    >
      <span
        className={`h-1.5 w-1.5 flex-shrink-0 rounded-full ${config.dot}`}
        aria-hidden="true"
      />
      <span className={`font-medium ${config.text}`}>{config.label}</span>
      {health && (
        <span className="text-gray-300 group-hover:text-gray-400 transition-colors">
          v{health.version}
        </span>
      )}
      {/* Dismiss button */}
      <button
        type="button"
        onClick={() => setIsVisible(false)}
        className="ml-1 text-gray-300 hover:text-gray-500 transition-colors"
        aria-label="Dismiss backend status badge"
      >
        <svg
          className="h-3 w-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2.5}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  );
}
