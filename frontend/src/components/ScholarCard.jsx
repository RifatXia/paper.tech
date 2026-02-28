export default function ScholarCard({ scholar, onHandpick, isHandpicked }) {
  const { score_breakdown: sb } = scholar;

  return (
    <div className="p-5 bg-dark-card border border-dark-border rounded-xl card-hover">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-100">{scholar.name}</h3>
          <p className="text-sm text-gray-400">{scholar.affiliation}</p>
          <p className="text-xs text-gray-500 mt-0.5">
            {scholar.city}, {scholar.state}, {scholar.country}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gradient-cyan">
            {(scholar.score * 100).toFixed(0)}
          </div>
          <div className="text-xs text-gray-500">match score</div>
        </div>
      </div>

      {/* Score breakdown chips */}
      <div className="flex gap-2 mb-3">
        <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Jaccard {(sb.jaccard * 100).toFixed(0)}
        </span>
        <span className="px-2 py-0.5 text-xs rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
          Semantic {(sb.semantic * 100).toFixed(0)}
        </span>
        <span className="px-2 py-0.5 text-xs rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
          Citation {(sb.citation * 100).toFixed(0)}
        </span>
      </div>

      {/* Topics */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {scholar.topics.map((t) => (
          <span
            key={t}
            className="px-2 py-0.5 text-xs rounded-md bg-dark-surface text-gray-400 border border-dark-border"
          >
            {t}
          </span>
        ))}
      </div>

      {/* Stats */}
      <div className="flex gap-4 text-xs text-gray-500 mb-3">
        <span>h-index: {scholar.h_index}</span>
        <span>{scholar.paper_count} papers</span>
      </div>

      {/* Explanation */}
      <p className="text-sm text-gray-400 mb-4">{scholar.match_explanation}</p>

      <button
        onClick={() => onHandpick(scholar)}
        disabled={isHandpicked}
        className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
          isHandpicked
            ? "bg-dark-surface text-gray-500 border border-dark-border cursor-default"
            : "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/20"
        }`}
      >
        {isHandpicked ? "Handpicked" : "Handpick"}
      </button>
    </div>
  );
}
