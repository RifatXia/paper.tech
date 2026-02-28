import { useState } from "react";

export default function SearchBar({ onSearch, initialQuery = "" }) {
  const [query, setQuery] = useState(initialQuery);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) onSearch(query.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Describe your research interest..."
          className="w-full px-5 py-3.5 bg-dark-card border border-dark-border rounded-xl text-gray-100 placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/30 transition-all"
        />
        <button
          type="submit"
          className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-dark font-semibold rounded-lg transition-colors"
        >
          Search
        </button>
      </div>
    </form>
  );
}
