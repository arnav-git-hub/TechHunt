/**
 * Navbar component — Stage 2 update.
 * Adds links to /events, /auth/login, /auth/register.
 * Auth state is shown client-side via NavbarClient.
 */

import Link from "next/link";
import { NavbarClient } from "@/components/NavbarClient";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-gray-100 bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand */}
        <div className="flex items-center gap-2">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M8 1L10.5 6H14L10.5 9.5L12 14L8 11L4 14L5.5 9.5L2 6H5.5L8 1Z"
                  fill="white"
                  strokeWidth="0"
                />
              </svg>
            </div>
            <span className="text-lg font-bold tracking-tight text-gray-900">
              TECHHUNT
            </span>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="hidden items-center gap-6 sm:flex" aria-label="Primary">
          <Link
            href="/events"
            className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
          >
            Opportunities
          </Link>
          <a
            href="#"
            className="text-sm font-medium text-gray-400 cursor-not-allowed"
            aria-disabled="true"
            tabIndex={-1}
          >
            Open Source
          </a>
          <a
            href="#"
            className="text-sm font-medium text-gray-400 cursor-not-allowed"
            aria-disabled="true"
            tabIndex={-1}
          >
            Fellowships
          </a>
        </nav>

        {/* Auth CTA — client component to read localStorage */}
        <NavbarClient />
      </div>
    </header>
  );
}
