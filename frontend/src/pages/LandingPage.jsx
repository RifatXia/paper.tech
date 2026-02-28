import { useNavigate } from "react-router-dom";
import SearchBar from "../components/SearchBar";

const EXAMPLE_QUERIES = [
  "KV cache compression for multi-turn LLM inference",
  "Federated learning for medical imaging with differential privacy",
  "Reinforcement learning from human feedback in robotics",
  "Graph neural networks for drug discovery",
];

const FEATURES = [
  {
    title: "Smart Matching",
    desc: "Composite scoring: topic overlap, semantic similarity, and citation graph analysis.",
  },
  {
    title: "Geo Filter",
    desc: "Find collaborators at your university, city, state, or country.",
  },
  {
    title: "Multi-Scholar Chat",
    desc: "Handpick scholars and explore collaboration ideas with AI-powered context.",
  },
  {
    title: "Knowledge Graph",
    desc: "Live visualization of topics, scholars, papers, and how they connect.",
  },
];

export default function LandingPage() {
  const navigate = useNavigate();

  const handleSearch = (query) => {
    navigate(`/results?q=${encodeURIComponent(query)}`);
  };

  return (
    <main className="flex flex-col items-center pt-24 px-4">
      {/* Hero */}
      <h1 className="text-5xl md:text-6xl font-extrabold text-center mb-4">
        Find your next{" "}
        <span className="text-gradient-cyan">co-author</span>
      </h1>
      <p className="text-lg text-gray-400 text-center max-w-xl mb-10">
        AI-powered discovery of research collaborators. Describe your work,
        get ranked matches, and start collaborating.
      </p>

      <SearchBar onSearch={handleSearch} />

      {/* Example queries */}
      <div className="mt-6 flex flex-wrap gap-2 justify-center max-w-2xl">
        {EXAMPLE_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => handleSearch(q)}
            className="px-3 py-1.5 text-xs text-gray-400 bg-dark-card border border-dark-border rounded-lg hover:border-cyan-500/30 hover:text-cyan-400 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-20 max-w-5xl w-full mb-20">
        {FEATURES.map((f) => (
          <div
            key={f.title}
            className="p-5 bg-dark-card border border-dark-border rounded-xl card-hover"
          >
            <h3 className="text-sm font-semibold text-cyan-400 mb-2">{f.title}</h3>
            <p className="text-sm text-gray-400">{f.desc}</p>
          </div>
        ))}
      </div>
    </main>
  );
}
