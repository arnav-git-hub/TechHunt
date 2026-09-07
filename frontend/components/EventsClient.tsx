/**
 * EventsClient — client component for the events list page.
 * Handles search, filters, pagination, and live data fetching.
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchEvents } from "@/lib/api";
import type { Event, PaginatedEvents } from "@/types";

const OPPORTUNITY_TYPE_LABELS: Record<string, string> = {
  hackathon: "Hackathon",
  coding_competition: "Coding Competition",
  technical_competition: "Technical Competition",
  meetup: "Meetup",
  workshop: "Workshop",
  conference: "Conference",
  ai_ml_event: "AI / ML Event",
  open_source_program: "Open Source",
  fellowship: "Fellowship",
  scholarship: "Scholarship",
  startup_event: "Startup Event",
  startup_competition: "Startup Competition",
  accelerator: "Accelerator",
  grant: "Grant",
  student_opportunity: "Student Opportunity",
  other: "Other",
};

const FILTER_TYPES = [
  { value: "", label: "All types" },
  { value: "hackathon", label: "Hackathons" },
  { value: "coding_competition", label: "Coding Competitions" },
  { value: "workshop", label: "Workshops" },
  { value: "conference", label: "Conferences" },
  { value: "meetup", label: "Meetups" },
  { value: "ai_ml_event", label: "AI / ML Events" },
  { value: "open_source_program", label: "Open Source" },
  { value: "fellowship", label: "Fellowships" },
  { value: "startup_event", label: "Startup Events" },
];

export function EventsClient() {
  const [data, setData] = useState<PaginatedEvents | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [opportunityType, setOpportunityType] = useState("");
  const [isOnline, setIsOnline] = useState<boolean | undefined>(undefined);
  const [page, setPage] = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    const result = await fetchEvents({
      q: query || undefined,
      opportunity_type: opportunityType || undefined,
      is_online: isOnline,
      page,
      page_size: 12,
    });
    setLoading(false);
    if (result.error) {
      setError(result.error.message);
    } else {
      setData(result.data);
    }
  }, [query, opportunityType, isOnline, page]);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => {
      void load();
    }, 300);
    return () => clearTimeout(t);
  }, [load]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setPage(1);
  };

  const handleTypeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setOpportunityType(e.target.value);
    setPage(1);
  };

  const handleOnlineChange = (val: boolean | undefined) => {
    setIsOnline(val);
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Filter bar */}
      <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        {/* Search */}
        <div className="flex flex-1 items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-400">
          <svg
            className="h-4 w-4 flex-shrink-0 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"
            />
          </svg>
          <input
            type="search"
            value={query}
            onChange={handleSearch}
            placeholder="Search opportunities…"
            className="flex-1 bg-transparent text-sm text-gray-700 placeholder-gray-400 focus:outline-none"
            aria-label="Search opportunities"
          />
        </div>

        {/* Type filter */}
        <select
          value={opportunityType}
          onChange={handleTypeChange}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 focus:border-blue-400 focus:outline-none focus:ring-1 focus:ring-blue-400"
          aria-label="Filter by opportunity type"
        >
          {FILTER_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>

        {/* Online/in-person filter */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <button
            onClick={() => handleOnlineChange(undefined)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              isOnline === undefined
                ? "bg-blue-600 text-white"
                : "border border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            All
          </button>
          <button
            onClick={() => handleOnlineChange(true)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              isOnline === true
                ? "bg-blue-600 text-white"
                : "border border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            Online
          </button>
          <button
            onClick={() => handleOnlineChange(false)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              isOnline === false
                ? "bg-blue-600 text-white"
                : "border border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
            }`}
          >
            In-person
          </button>
        </div>
      </div>

      {/* Results count */}
      {data && !loading && (
        <p className="mb-4 text-sm text-gray-500">
          {data.total === 0
            ? "No opportunities found"
            : `${data.total} opportunit${data.total === 1 ? "y" : "ies"}`}
        </p>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-48 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="rounded-xl border border-red-100 bg-red-50 px-6 py-8 text-center">
          <p className="text-sm font-medium text-red-700">
            Failed to load opportunities
          </p>
          <p className="mt-1 text-xs text-red-500">{error}</p>
          <button
            onClick={() => void load()}
            className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
          >
            Try again
          </button>
        </div>
      )}

      {/* Empty state */}
      {data && data.total === 0 && !loading && (
        <div className="rounded-xl border border-gray-100 bg-gray-50 px-6 py-16 text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100">
            <svg
              className="h-6 w-6 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z"
              />
            </svg>
          </div>
          <p className="text-sm font-medium text-gray-700">
            No opportunities found
          </p>
          <p className="mt-1 text-xs text-gray-400">
            Try adjusting your filters or search term.
          </p>
        </div>
      )}

      {/* Events grid */}
      {data && data.items.length > 0 && !loading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((event) => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.pages > 1 && !loading && (
        <div className="mt-8 flex items-center justify-center gap-3">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">
            Page {page} of {data.pages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
            disabled={page === data.pages}
            className="rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// EventCard
// ---------------------------------------------------------------------------

function EventCard({ event }: { event: Event }) {
  const typeLabel =
    OPPORTUNITY_TYPE_LABELS[event.opportunity_type] ?? event.opportunity_type;

  const dateStr = event.start_at_utc
    ? new Intl.DateTimeFormat("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        timeZone: "UTC",
      }).format(new Date(event.start_at_utc))
    : null;

  return (
    <Link
      href={`/events/${event.slug}`}
      className="group flex flex-col rounded-xl border border-gray-100 bg-white p-5 shadow-sm transition-shadow hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
    >
      {/* Type badge + price badge */}
      <div className="mb-3 flex items-center justify-between gap-2">
        <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
          {typeLabel}
        </span>
        {event.price_type === "free" && (
          <span className="rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
            Free
          </span>
        )}
        {event.is_online && (
          <span className="rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-medium text-purple-700">
            Online
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="mb-2 text-sm font-semibold text-gray-900 leading-snug group-hover:text-blue-600 transition-colors line-clamp-2">
        {event.title}
      </h3>

      {/* Organizer */}
      {event.organizer && (
        <p className="mb-2 text-xs text-gray-500 truncate">
          by {event.organizer}
        </p>
      )}

      {/* Description snippet */}
      {event.description && (
        <p className="mb-3 text-xs text-gray-400 line-clamp-2 flex-1">
          {event.description}
        </p>
      )}

      <div className="mt-auto pt-3 border-t border-gray-50 flex items-center justify-between gap-2">
        {/* Date */}
        {dateStr && (
          <span className="text-xs text-gray-400 flex items-center gap-1">
            <svg
              className="h-3.5 w-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            {dateStr}
          </span>
        )}
        {/* Location */}
        {!event.is_online && event.city && (
          <span className="text-xs text-gray-400 truncate">
            {event.city}
            {event.country ? `, ${event.country}` : ""}
          </span>
        )}
        {/* Tags */}
        {event.tags.length > 0 && (
          <div className="flex gap-1 flex-wrap justify-end">
            {event.tags.slice(0, 2).map((tag) => (
              <span
                key={tag}
                className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
