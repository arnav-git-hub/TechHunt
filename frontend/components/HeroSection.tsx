/**
 * HeroSection component.
 * Landing page hero with brand headline, subheadline, search bar UI,
 * and primary CTA. Search is visual-only in Stage 1.
 */

export function HeroSection() {
  return (
    <section
      className="relative overflow-hidden bg-white px-4 pb-16 pt-20 sm:px-6 sm:pb-24 sm:pt-28 lg:px-8"
      aria-labelledby="hero-heading"
    >
      {/* Background decoration */}
      <div
        className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-gradient-to-b from-blue-50/60 to-transparent"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-4xl text-center">
        {/* Eyebrow badge */}
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-4 py-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-500" aria-hidden="true" />
          <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide">
            Find your next technical opportunity
          </span>
        </div>

        {/* Hero headline */}
        <h1
          id="hero-heading"
          className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl lg:text-6xl text-balance"
        >
          Your next hackathon{" "}
          <span className="text-blue-600">is waiting.</span>
        </h1>

        {/* Subheadline */}
        <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-500 sm:text-xl text-balance">
          Hackathons, contests, workshops, meetups, fellowships, grants, and
          open-source programs — from legitimate sources, all in one place.
        </p>

        {/* Search bar — visual UI, not functional in Stage 1 */}
        <div className="mt-10 mx-auto max-w-2xl">
          <div
            role="search"
            aria-label="Search opportunities (coming soon)"
          >
            <div className="flex items-center gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm focus-within:border-blue-400 focus-within:ring-1 focus-within:ring-blue-400">
              {/* Search icon */}
              <svg
                className="h-5 w-5 flex-shrink-0 text-gray-400"
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
                placeholder="Search hackathons, fellowships, workshops…"
                disabled
                aria-disabled="true"
                aria-label="Search opportunities — coming in a future release"
                className="flex-1 bg-transparent text-sm text-gray-500 placeholder-gray-400 focus:outline-none cursor-not-allowed"
              />

              <span className="hidden sm:block text-xs text-gray-400 font-medium whitespace-nowrap">
                Coming soon
              </span>
            </div>
          </div>

          {/* Hint text */}
          <p className="mt-2 text-xs text-gray-400 text-center">
            Full search with filters, saved events, and personalized
            recommendations — coming in Stage 2.
          </p>
        </div>

        {/* CTA buttons */}
        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
          <a
            href="/events"
            className="w-full sm:w-auto rounded-xl bg-blue-600 px-8 py-3.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors text-center"
          >
            Explore opportunities
          </a>
          <button
            type="button"
            disabled
            className="w-full sm:w-auto rounded-xl border border-gray-200 bg-white px-8 py-3.5 text-sm font-semibold text-gray-700 shadow-sm cursor-not-allowed opacity-70 hover:bg-gray-50 transition-colors"
          >
            Submit an event
          </button>
        </div>

        {/* Social proof / stats — placeholder */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-4 text-sm text-gray-400">
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Official sources only</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>No spam, no tracking</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="h-4 w-4 text-green-500" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Always free to discover</span>
          </div>
        </div>
      </div>
    </section>
  );
}
