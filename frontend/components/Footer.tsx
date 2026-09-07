/**
 * Footer component.
 */

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-gray-100 bg-white">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-md bg-blue-600">
              <svg
                width="12"
                height="12"
                viewBox="0 0 16 16"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M8 1L10.5 6H14L10.5 9.5L12 14L8 11L4 14L5.5 9.5L2 6H5.5L8 1Z"
                  fill="white"
                />
              </svg>
            </div>
            <span className="text-sm font-semibold text-gray-900">
              TECHHUNT
            </span>
          </div>

          {/* Tagline */}
          <p className="text-sm text-gray-400 text-center">
            Find your next technical opportunity.
          </p>

          {/* Copyright */}
          <p className="text-xs text-gray-400">
            &copy; {currentYear} TechHunt. All rights reserved.
          </p>
        </div>

        {/* Data transparency notice */}
        <div className="mt-6 border-t border-gray-50 pt-6 text-center">
          <p className="text-xs text-gray-400">
            TechHunt only uses official APIs, public permitted feeds, and
            organizer-submitted events. We never bypass platform terms of
            service.
          </p>
        </div>
      </div>
    </footer>
  );
}
