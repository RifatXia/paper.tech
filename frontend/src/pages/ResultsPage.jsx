import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import GeoFilter from "../components/GeoFilter";
import ScholarCard from "../components/ScholarCard";
import HandpickSidebar from "../components/HandpickSidebar";
import ChatPanel from "../components/ChatPanel";
import GraphPlaceholder from "../components/GraphPlaceholder";
import { matchScholars, handpickScholars } from "../api/client";

const TABS = ["Results", "Chat", "Graph"];

export default function ResultsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get("q") || "";

  const [scholars, setScholars] = useState([]);
  const [loading, setLoading] = useState(false);
  const [geoFilter, setGeoFilter] = useState({
    country: null,
    state: null,
    city: null,
    university: null,
  });
  const [handpicked, setHandpicked] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [activeTab, setActiveTab] = useState("Results");

  const doSearch = async (q, geo = geoFilter) => {
    setLoading(true);
    try {
      const hasGeo = Object.values(geo).some(Boolean);
      const res = await matchScholars(q, 10, hasGeo ? geo : null);
      setScholars(res.scholars);
    } catch {
      setScholars([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (query) doSearch(query);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = (q) => {
    setSearchParams({ q });
    doSearch(q);
  };

  const handleHandpick = (scholar) => {
    if (!handpicked.find((s) => s.scholar_id === scholar.scholar_id)) {
      setHandpicked((prev) => [...prev, scholar]);
    }
  };

  const handleStartSession = async () => {
    try {
      const res = await handpickScholars(handpicked.map((s) => s.scholar_id));
      setSessionId(res.session_id);
      setActiveTab("Chat");
    } catch {
      // handle error
    }
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      <div className="flex-1 overflow-y-auto p-6">
        {/* Search + filter */}
        <div className="max-w-3xl mx-auto mb-6 space-y-3">
          <SearchBar onSearch={handleSearch} initialQuery={query} />
          <GeoFilter filter={geoFilter} onChange={(f) => { setGeoFilter(f); if (query) doSearch(query, f); }} />
        </div>

        {/* Tabs */}
        <div className="max-w-3xl mx-auto mb-4 flex gap-1 bg-dark-surface rounded-lg p-1">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-2 text-sm rounded-md transition-colors ${
                activeTab === tab
                  ? "bg-dark-card text-cyan-400 font-medium"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="max-w-3xl mx-auto">
          {activeTab === "Results" && (
            <div className="space-y-4">
              {loading && <p className="text-gray-500 text-center py-8">Searching...</p>}
              {!loading && scholars.length === 0 && query && (
                <p className="text-gray-500 text-center py-8">No results found.</p>
              )}
              {scholars.map((s) => (
                <ScholarCard
                  key={s.scholar_id}
                  scholar={s}
                  onHandpick={handleHandpick}
                  isHandpicked={handpicked.some((h) => h.scholar_id === s.scholar_id)}
                />
              ))}
            </div>
          )}
          {activeTab === "Chat" && <ChatPanel sessionId={sessionId} />}
          {activeTab === "Graph" && <GraphPlaceholder />}
        </div>
      </div>

      {/* Sidebar */}
      <HandpickSidebar
        scholars={handpicked}
        onStartSession={handleStartSession}
        sessionId={sessionId}
      />
    </div>
  );
}
