/**
 * FilterChips component.
 * Quick-filter chips for opportunity categories.
 * Visual-only in Stage 1 — filtering is implemented in Stage 2.
 */

interface FilterChip {
  label: string;
  icon: string;
  ariaLabel: string;
}

const FILTER_CHIPS: FilterChip[] = [
  { label: "AI", icon: "🤖", ariaLabel: "Filter by Artificial Intelligence" },
  { label: "ML", icon: "🧠", ariaLabel: "Filter by Machine Learning" },
  { label: "Web", icon: "🌐", ariaLabel: "Filter by Web Development" },
  { label: "Cybersecurity", icon: "🔐", ariaLabel: "Filter by Cybersecurity" },
  { label: "Cloud", icon: "☁️", ariaLabel: "Filter by Cloud Computing" },
  { label: "Blockchain", icon: "⛓️", ariaLabel: "Filter by Blockchain" },
  { label: "Open Source", icon: "🔓", ariaLabel: "Filter by Open Source" },
  { label: "Hackathons", icon: "🏆", ariaLabel: "Filter by Hackathons" },
  { label: "Fellowships", icon: "🎓", ariaLabel: "Filter by Fellowships" },
  { label: "Meetups", icon: "🤝", ariaLabel: "Filter by Meetups" },
  { label: "Workshops", icon: "🛠️", ariaLabel: "Filter by Workshops" },
  { label: "Startups", icon: "🚀", ariaLabel: "Filter by Startup Events" },
];

export function FilterChips() {
  return (
    <div
      className="flex flex-wrap gap-2"
      role="group"
      aria-label="Filter opportunities by category (coming soon)"
    >
      {FILTER_CHIPS.map((chip) => (
        <button
          key={chip.label}
          type="button"
          disabled
          aria-label={`${chip.ariaLabel} — coming soon`}
          aria-disabled="true"
          className="inline-flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3.5 py-1.5 text-sm font-medium text-gray-600 cursor-not-allowed opacity-70 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700 transition-colors"
        >
          <span aria-hidden="true" className="text-base leading-none">
            {chip.icon}
          </span>
          {chip.label}
        </button>
      ))}
      <span className="inline-flex items-center px-3.5 py-1.5 text-sm text-gray-400">
        + more
      </span>
    </div>
  );
}
