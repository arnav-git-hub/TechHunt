/**
 * Event detail page — /events/[slug]
 */

import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { fetchEvent } from "@/lib/api";

interface EventPageProps {
  params: { slug: string };
}

export async function generateMetadata({
  params,
}: EventPageProps): Promise<Metadata> {
  const result = await fetchEvent(params.slug);
  if (result.error || !result.data) {
    return { title: "Event not found" };
  }
  return {
    title: result.data.title,
    description: result.data.description ?? undefined,
  };
}

export default async function EventPage({ params }: EventPageProps) {
  const result = await fetchEvent(params.slug);

  // 404 — use Next.js not-found page
  if (result.error?.status === 404) {
    notFound();
  }

  // Other backend error — show graceful error page
  if (result.error) {
    return (
      <div className="flex min-h-screen flex-col bg-white">
        <Navbar />
        <main className="flex-1 flex items-center justify-center px-4 py-20">
          <div className="text-center max-w-md">
            <p className="text-gray-500 mb-4">
              Could not load this event. The backend may be unavailable.
            </p>
            <p className="text-xs text-red-400">{result.error.message}</p>
            <Link
              href="/events"
              className="mt-6 inline-block rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
            >
              Back to opportunities
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Satisfy TypeScript — data is non-null after both error branches above
  if (!result.data) {
    notFound();
  }
  const event = result.data;

  const formatDate = (iso: string | null) =>
    iso
      ? new Intl.DateTimeFormat("en-US", {
          dateStyle: "long",
          timeStyle: "short",
          timeZone: "UTC",
        }).format(new Date(iso))
      : null;

  const startDate = formatDate(event.start_at_utc);
  const endDate = formatDate(event.end_at_utc);
  const deadline = formatDate(event.registration_deadline_utc);

  const typeLabel =
    {
      hackathon: "Hackathon",
      coding_competition: "Coding Competition",
      technical_competition: "Technical Competition",
      meetup: "Meetup",
      workshop: "Workshop",
      conference: "Conference",
      ai_ml_event: "AI / ML Event",
      open_source_program: "Open Source Program",
      fellowship: "Fellowship",
      scholarship: "Scholarship",
      startup_event: "Startup Event",
      startup_competition: "Startup Competition",
      accelerator: "Accelerator",
      grant: "Grant",
      student_opportunity: "Student Opportunity",
      other: "Other",
    }[event.opportunity_type] ?? event.opportunity_type;

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar />
      <main className="flex-1">
        {/* Breadcrumb */}
        <div className="border-b border-gray-100 bg-gray-50 px-4 py-3 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-4xl">
            <nav className="flex items-center gap-2 text-sm text-gray-500" aria-label="Breadcrumb">
              <Link href="/" className="hover:text-gray-700 transition-colors">Home</Link>
              <span aria-hidden="true">/</span>
              <Link href="/events" className="hover:text-gray-700 transition-colors">Opportunities</Link>
              <span aria-hidden="true">/</span>
              <span className="text-gray-700 truncate max-w-xs">{event.title}</span>
            </nav>
          </div>
        </div>

        {/* Main content */}
        <article className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
          {/* Header */}
          <header className="mb-8">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                {typeLabel}
              </span>
              {event.price_type === "free" && (
                <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
                  Free
                </span>
              )}
              {event.is_online && (
                <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700">
                  Online
                </span>
              )}
              {event.difficulty && (
                <span className="rounded-full bg-yellow-50 px-3 py-1 text-xs font-semibold text-yellow-700 capitalize">
                  {event.difficulty}
                </span>
              )}
            </div>

            <h1 className="text-2xl font-bold text-gray-900 sm:text-3xl leading-snug mb-2">
              {event.title}
            </h1>

            {event.organizer && (
              <p className="text-sm text-gray-500">
                Organized by{" "}
                <span className="font-medium text-gray-700">{event.organizer}</span>
              </p>
            )}
          </header>

          <div className="grid gap-8 lg:grid-cols-3">
            {/* Main description */}
            <div className="lg:col-span-2">
              {event.description && (
                <section className="mb-8">
                  <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
                    About
                  </h2>
                  <div className="prose prose-sm max-w-none text-gray-700 whitespace-pre-wrap">
                    {event.description}
                  </div>
                </section>
              )}

              {event.eligibility && (
                <section className="mb-8">
                  <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
                    Eligibility
                  </h2>
                  <p className="text-sm text-gray-700">{event.eligibility}</p>
                </section>
              )}

              {event.skills.length > 0 && (
                <section className="mb-8">
                  <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
                    Skills
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {event.skills.map((s) => (
                      <span
                        key={s}
                        className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-600"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {event.tags.length > 0 && (
                <section className="mb-8">
                  <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-gray-500">
                    Tags
                  </h2>
                  <div className="flex flex-wrap gap-2">
                    {event.tags.map((tag) => (
                      <span
                        key={tag}
                        className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs text-gray-600"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </section>
              )}
            </div>

            {/* Sidebar */}
            <aside className="space-y-4">
              {/* CTA */}
              {event.event_url && (
                <a
                  href={event.event_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition-colors"
                >
                  View event
                  <svg
                    className="h-4 w-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                    aria-hidden="true"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6m4-3h6m0 0v6m0-6L10 14"
                    />
                  </svg>
                </a>
              )}

              {/* Details card */}
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-5 space-y-3 text-sm">
                {startDate && (
                  <div>
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-0.5">
                      Starts
                    </p>
                    <p className="text-gray-700">{startDate}</p>
                  </div>
                )}
                {endDate && (
                  <div>
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-0.5">
                      Ends
                    </p>
                    <p className="text-gray-700">{endDate}</p>
                  </div>
                )}
                {deadline && (
                  <div>
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-0.5">
                      Registration deadline
                    </p>
                    <p className="font-medium text-orange-600">{deadline}</p>
                  </div>
                )}
                {event.location && (
                  <div>
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-0.5">
                      Location
                    </p>
                    <p className="text-gray-700">{event.location}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-0.5">
                    Source
                  </p>
                  <p className="text-gray-500 capitalize">{event.source}</p>
                </div>
              </div>

              <Link
                href="/events"
                className="block text-center text-sm text-blue-600 hover:text-blue-700 transition-colors"
              >
                ← Back to opportunities
              </Link>
            </aside>
          </div>
        </article>
      </main>
      <Footer />
    </div>
  );
}
