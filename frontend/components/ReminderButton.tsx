/**
 * ReminderButton — client component.
 * Allows authenticated users to set or cancel an in-app (+ optional email)
 * reminder for a specific event.
 */

"use client";

import { useState } from "react";

interface ReminderButtonProps {
  eventId: string;
  /** ISO string of the event start time — used to disable the button for past events */
  startAtUtc: string | null;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function ReminderButton({ eventId, startAtUtc }: ReminderButtonProps) {
  const [status, setStatus] = useState<"idle" | "loading" | "set" | "error">(
    "idle"
  );
  const [cancelling, setCancelling] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const isPast =
    startAtUtc !== null && new Date(startAtUtc) < new Date();

  function getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("techhunt_token");
  }

  async function handleSetReminder() {
    const token = getToken();
    if (!token) {
      setMessage("Sign in to set a reminder.");
      setStatus("error");
      return;
    }
    setStatus("loading");
    setMessage(null);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/events/${eventId}/reminders`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ lead_hours: 24, request_email: false }),
        }
      );
      if (res.ok) {
        setStatus("set");
        setMessage("Reminder set for 24 h before the event.");
      } else if (res.status === 401) {
        setStatus("error");
        setMessage("Sign in to set a reminder.");
      } else {
        const body = await res.json().catch(() => ({}));
        setStatus("error");
        setMessage(
          (body as { detail?: string }).detail ?? "Could not set reminder."
        );
      }
    } catch {
      setStatus("error");
      setMessage("Network error — try again.");
    }
  }

  async function handleCancelReminder() {
    const token = getToken();
    if (!token) return;
    setCancelling(true);
    setMessage(null);
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/events/${eventId}/reminders`,
        {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      if (res.ok) {
        setStatus("idle");
        setMessage("Reminder cancelled.");
      } else {
        setMessage("Could not cancel reminder.");
      }
    } catch {
      setMessage("Network error — try again.");
    } finally {
      setCancelling(false);
    }
  }

  if (isPast) return null;

  return (
    <div className="space-y-1">
      {status !== "set" ? (
        <button
          type="button"
          onClick={handleSetReminder}
          disabled={status === "loading"}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white px-6 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {status === "loading" ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-gray-400 border-t-transparent" />
          ) : (
            <svg
              className="h-4 w-4 text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
          )}
          Remind me
        </button>
      ) : (
        <button
          type="button"
          onClick={handleCancelReminder}
          disabled={cancelling}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-green-200 bg-green-50 px-6 py-2.5 text-sm font-medium text-green-700 hover:bg-green-100 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          Reminder set · Cancel
        </button>
      )}
      {message && (
        <p
          className={`text-xs text-center ${
            status === "error" ? "text-red-500" : "text-gray-500"
          }`}
        >
          {message}
        </p>
      )}
    </div>
  );
}
