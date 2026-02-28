import { useState, useEffect } from "react";
import { useSearchParams, useLocation } from "react-router-dom";
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
  const { state: navState } = useLocation();
  const query = searchParams.get("q") || "";

  const [scholars, setScholars] = useState([]);
  const [loading, setLoading] = useState(false);
  const [geoFilter, setGeoFilter] = useState(
    navState?.geoFilter ?? { country: null, state: null, university: null }
  );
  const [handpicked, setHandpicked] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [activeTab, setActiveTab] = useState("Results");

  const filteredScholars = scholars.filter((s) => {
    if (geoFilter.country && s.country !== geoFilter.country) return false;
    if (geoFilter.state && s.state !== geoFilter.state) return false;
    if (geoFilter.university && s.university !== geoFilter.university) return false;
    return true;
  });

  const doSearch = async (q) => {
    setLoading(true);
    try {
      const res = await matchScholars(q, 10, null);
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
          <div className="flex justify-center">
            <GeoFilter filter={geoFilter} onChange={setGeoFilter} scholars={scholars} />
          </div>
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
              {!loading && filteredScholars.length === 0 && query && (
                <p className="text-gray-500 text-center py-8">No results found.</p>
              )}
              {filteredScholars.map((s) => (
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
