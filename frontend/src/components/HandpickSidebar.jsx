import { useNavigate } from "react-router-dom";

export default function HandpickSidebar({ scholars, onStartSession, sessionId }) {
  const navigate = useNavigate();
  if (scholars.length === 0) return null;

  return (
    <div className="w-72 bg-dark-card border-l border-dark-border p-4 flex flex-col">
      <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide mb-3">
        Handpicked ({scholars.length})
      </h3>
      <div className="flex-1 space-y-2 overflow-y-auto">
        {scholars.map((s) => (
          <div
            key={s.scholar_id}
            className="p-3 bg-dark-surface rounded-lg border border-dark-border"
          >
            <p className="text-sm font-medium text-gray-200">{s.name}</p>
            <p className="text-xs text-gray-500">{s.affiliation}</p>
            <button
              onClick={() => navigate("/email", { state: { scholar: s } })}
              className="mt-2 w-full py-1.5 text-xs font-medium text-cyan-400 border border-cyan-400/30 hover:bg-cyan-400/10 rounded-md transition-colors"
            >
              Send email
            </button>
          </div>
        ))}
      </div>
      {!sessionId && scholars.length >= 2 && (
        <button
          onClick={onStartSession}
          className="mt-4 w-full py-2.5 bg-cyan-500 hover:bg-cyan-600 text-dark font-semibold rounded-lg transition-colors"
        >
          Start Session ({scholars.length} scholars)
        </button>
      )}
      {sessionId && (
        <div className="mt-4 px-3 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-400 text-center">
          Session active
        </div>
      )}
    </div>
  );
}
