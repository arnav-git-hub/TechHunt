/**
 * NavbarClient — client component for auth-aware navbar CTA.
 * Reads auth state from localStorage and shows Sign in / Get started
 * or user name + Logout when logged in.
 */

"use client";

import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export function NavbarClient() {
  const { isLoggedIn, user, logout, isLoading } = useAuth();

  if (isLoading) {
    return <div className="h-8 w-24 animate-pulse rounded-lg bg-gray-100" />;
  }

  if (isLoggedIn && user) {
    return (
      <div className="flex items-center gap-3">
        <span className="hidden text-sm text-gray-600 sm:block truncate max-w-[120px]">
          {user.name}
        </span>
        <button
          type="button"
          onClick={logout}
          className="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <Link
        href="/auth/login"
        className="hidden text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors sm:block"
      >
        Sign in
      </Link>
      <Link
        href="/auth/register"
        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
      >
        Get started
      </Link>
    </div>
  );
}
