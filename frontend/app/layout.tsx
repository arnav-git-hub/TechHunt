/**
 * Root layout — wraps every page in the application.
 * Sets global metadata, fonts, and the HTML shell.
 */

import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "TechHunt — Find Your Next Technical Opportunity",
    template: "%s | TechHunt",
  },
  description:
    "Discover hackathons, coding contests, workshops, meetups, conferences, AI/ML events, open-source programs, fellowships, and startup competitions — all in one place.",
  keywords: [
    "hackathon",
    "coding competition",
    "tech events",
    "developer meetup",
    "open source",
    "fellowship",
    "AI events",
    "machine learning",
  ],
  authors: [{ name: "TechHunt" }],
  creator: "TechHunt",
  openGraph: {
    type: "website",
    locale: "en_US",
    title: "TechHunt — Find Your Next Technical Opportunity",
    description:
      "Discover hackathons, coding contests, workshops, meetups, conferences, AI/ML events, and more.",
    siteName: "TechHunt",
  },
  twitter: {
    card: "summary_large_image",
    title: "TechHunt — Find Your Next Technical Opportunity",
    description: "Discover your next hackathon, contest, or tech event.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-white text-gray-900 antialiased">
        {children}
      </body>
    </html>
  );
}
