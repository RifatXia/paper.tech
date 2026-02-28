import { useState } from "react";

const active = (f) => [f.country, f.state, f.university].some(Boolean);

function Select({ label, value, options, onChange, placeholder }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-gray-500 uppercase tracking-wide">{label}</label>
      <div className="relative">
        <select
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          disabled={options.length === 0}
          className={`w-full appearance-none px-3 py-2 pr-8 bg-dark border border-dark-border rounded-lg text-sm transition-colors focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 ${
            options.length === 0
              ? "text-gray-600 cursor-not-allowed"
              : value
              ? "text-gray-200"
              : "text-gray-500"
          }`}
        >
          <option value="">{placeholder}</option>
          {options.map((o) => (
            <option key={o} value={o}>
              {o}
            </option>
          ))}
        </select>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  );
}

// scholars: the full (unfiltered) result list — used to derive available options
export default function GeoFilter({ filter, onChange, scholars = [] }) {
  const [open, setOpen] = useState(false);

  // Cascading options derived from the current result set
  const countries = [...new Set(scholars.map((s) => s.country).filter(Boolean))].sort();

  const states = [
    ...new Set(
      scholars
        .filter((s) => !filter.country || s.country === filter.country)
        .map((s) => s.state)
        .filter(Boolean)
    ),
  ].sort();

  const universities = [
    ...new Set(
      scholars
        .filter((s) => {
          if (filter.country && s.country !== filter.country) return false;
          if (filter.state && s.state !== filter.state) return false;
          return true;
        })
        .map((s) => s.university)
        .filter(Boolean)
    ),
  ].sort();

  const update = (field, value) => {
    if (field === "country") {
      onChange({ ...filter, country: value || null, state: null, university: null });
    } else if (field === "state") {
      onChange({ ...filter, state: value || null, university: null });
    } else {
      onChange({ ...filter, [field]: value || null });
    }
  };

  const clear = () => onChange({ country: null, state: null, university: null });

  const isActive = active(filter);
  const activeCount = [filter.country, filter.state, filter.university].filter(Boolean).length;

  return (
    <div className="w-full">
      {/* Toggle row */}
      <div className="flex items-center justify-center gap-2">
        <button
          onClick={() => setOpen((o) => !o)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm transition-colors ${
            isActive
              ? "border-cyan-500/50 text-cyan-400 bg-cyan-500/10"
              : "border-dark-border text-gray-400 bg-dark-card hover:border-cyan-500/30 hover:text-gray-300"
          }`}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="w-3.5 h-3.5"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5S10.62 6.5 12 6.5s2.5 1.12 2.5 2.5S13.38 11.5 12 11.5z" />
          </svg>
          Filter results
          {isActive && (
            <span className="ml-1 px-1.5 py-0.5 bg-cyan-500/20 text-cyan-400 rounded text-xs font-medium">
              {activeCount} active
            </span>
          )}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className={`w-3.5 h-3.5 transition-transform ${open ? "rotate-180" : ""}`}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </button>

        {isActive && (
          <button
            onClick={clear}
            className="px-2 py-1.5 text-xs text-gray-500 hover:text-red-400 transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Filter dropdowns */}
      {open && (
        <div className="mt-3 p-4 bg-dark-card border border-dark-border rounded-xl grid grid-cols-1 sm:grid-cols-3 gap-3">
          <Select
            label="Country"
            value={filter.country}
            options={countries}
            onChange={(v) => update("country", v)}
            placeholder="Any country"
          />
          <Select
            label="State / Province"
            value={filter.state}
            options={states}
            onChange={(v) => update("state", v)}
            placeholder="Any state"
          />
          <Select
            label="University"
            value={filter.university}
            options={universities}
            onChange={(v) => update("university", v)}
            placeholder="Any university"
          />
        </div>
      )}
    </div>
  );
}
