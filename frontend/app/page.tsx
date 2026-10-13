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

        {/* Call to action */}
        <section className="py-20 px-4 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full bg-green-50 px-4 py-1.5 text-sm font-medium text-green-700 mb-6">
              <span className="h-2 w-2 rounded-full bg-green-500"></span>
              Live — browse opportunities now
            </div>
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl mb-4">
              Your next opportunity is waiting
            </h2>
            <p className="text-lg text-gray-500 mb-8 text-balance">
              Browse hackathons, workshops, fellowships, and more. Save events,
              get personalised recommendations, and export to your calendar —
              all in one place.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <a
                href="/events"
                className="rounded-lg bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
              >
                Browse opportunities
              </a>
              <a
                href="/auth/register"
                className="rounded-lg border border-gray-200 bg-white px-6 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Create an account
              </a>
            </div>
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
