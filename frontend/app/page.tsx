/**
 * TechHunt landing page.
 *
 * Server component — fetches initial health status server-side.
 * The HealthBadge client component re-fetches on the client to
 * show live status without a full page reload.
 */

import { Suspense } from "react";
import { Navbar } from "@/components/Navbar";
import { HeroSection } from "@/components/HeroSection";
import { HealthBadge } from "@/components/HealthBadge";
import { FilterChips } from "@/components/FilterChips";
import { Footer } from "@/components/Footer";

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar />

      <main className="flex-1">
        <HeroSection />

        {/* Opportunity type filter chips */}
        <section className="border-t border-gray-100 bg-gray-50 py-6">
          <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
            <p className="mb-4 text-sm font-medium text-gray-500 uppercase tracking-wide">
              Explore by category
            </p>
            <FilterChips />
          </div>
        </section>

        {/* Coming soon / teaser section */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-4 py-1.5 text-sm font-medium text-blue-700 mb-6">
              <span className="h-2 w-2 rounded-full bg-blue-500"></span>
              Now in development
            </div>
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl mb-4">
              Opportunities are coming soon
            </h2>
            <p className="text-lg text-gray-500 mb-8 text-balance">
              We&apos;re building integrations with trusted sources — hackathon
              platforms, developer meetup networks, open-source programs, and
              more. Sign up to be notified when we launch.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                type="button"
                disabled
                className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white opacity-60 cursor-not-allowed"
              >
                Notify me at launch
              </button>
              <button
                type="button"
                disabled
                className="rounded-lg border border-gray-200 bg-white px-6 py-3 text-sm font-semibold text-gray-700 opacity-60 cursor-not-allowed"
              >
                Submit an opportunity
              </button>
            </div>
            <p className="mt-4 text-xs text-gray-400">
              Coming in Stage 2 — authentication, events API, and more.
            </p>
          </div>
        </section>

        {/* Source connector status — transparency about data provenance */}
        <section className="border-t border-gray-100 py-12 px-4 sm:px-6 lg:px-8 bg-gray-50">
          <div className="mx-auto max-w-3xl text-center">
            <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">
              Data transparency
            </h3>
            <p className="text-sm text-gray-500 mb-2">
              TechHunt only uses official APIs, public permitted feeds, and
              organizer-submitted events.
            </p>
            <p className="text-sm text-gray-500">
              Live source integrations are activated only after credentials and
              permission status are confirmed.
            </p>
          </div>
        </section>
      </main>

      {/* Health status — proves frontend ↔ backend communication */}
      <div className="fixed bottom-4 right-4 z-50">
        <Suspense fallback={null}>
          <HealthBadge />
        </Suspense>
      </div>

      <Footer />
    </div>
  );
}
