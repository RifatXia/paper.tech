import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <nav className="border-b border-dark-border bg-dark-surface/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="text-xl font-bold text-gradient-cyan">paper.tech</span>
        </Link>
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-cyan-400 transition-colors"
          >
            API Docs
          </a>
        </div>
      </div>
    </nav>
  );
}
