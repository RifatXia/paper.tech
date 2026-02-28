import { useEffect, useState } from "react";
import { getGraphState } from "../api/client";

export default function GraphPlaceholder() {
  const [graph, setGraph] = useState(null);

  useEffect(() => {
    getGraphState().then(setGraph).catch(() => {});
  }, []);

  return (
    <div className="bg-dark-card border border-dark-border rounded-xl p-6 h-[500px] flex flex-col items-center justify-center">
      {graph ? (
        <>
          <div className="text-sm text-gray-400 mb-4">
            Knowledge Graph — {graph.nodes.length} nodes, {graph.edges.length} edges
          </div>
          <div className="flex flex-wrap gap-2 justify-center mb-6">
            {graph.nodes.map((n) => (
              <span
                key={n.id}
                className={`px-3 py-1 rounded-full text-xs border ${
                  n.type === "scholar"
                    ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/20"
                    : n.type === "topic"
                      ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
                      : n.type === "paper"
                        ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
                        : n.type === "institution"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-blue-500/10 text-blue-400 border-blue-500/20"
                }`}
              >
                {n.label}
              </span>
            ))}
          </div>
          <p className="text-xs text-gray-500 text-center max-w-md">
            Interactive D3 Force Graph coming soon. This placeholder shows the graph data
            from the API. Nodes update as you search, handpick, and chat.
          </p>
        </>
      ) : (
        <p className="text-gray-500">Loading graph...</p>
      )}
    </div>
  );
}
