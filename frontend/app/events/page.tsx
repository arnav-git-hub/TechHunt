/**
 * Events list page — /events
 *
 * Server component that fetches the first page of published events.
 * Client-side filtering and pagination are handled by EventsClient.
 */

import { Suspense } from "react";
import type { Metadata } from "next";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { EventsClient } from "@/components/EventsClient";

export const metadata: Metadata = {
  title: "Explore Opportunities",
  description:
    "Browse hackathons, contests, workshops, meetups, fellowships, and more.",
};

export default function EventsPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar />
      <main className="flex-1">
        {/* Page header */}
        <section className="border-b border-gray-100 bg-gray-50 px-4 py-10 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl">
              Explore opportunities
            </h1>
            <p className="mt-1 text-gray-500">
              Hackathons, contests, workshops, meetups, fellowships, and more.
            </p>
          </div>
        </section>

        {/* Events list + filters — client component */}
        <Suspense fallback={<EventsLoadingSkeleton />}>
          <EventsClient />
        </Suspense>
      </main>
      <Footer />
    </div>
  );
}

function EventsLoadingSkeleton() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-48 animate-pulse rounded-xl bg-gray-100"
          />
        ))}
      </div>
    </div>
  );
}
