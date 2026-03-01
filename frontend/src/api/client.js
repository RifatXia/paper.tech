import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
  headers: { "Content-Type": "application/json" },
});

export async function matchScholars(query, topK = 10, geoFilter = null) {
  const { data } = await api.post("/api/match", {
    query,
    top_k: topK,
    geo_filter: geoFilter,
  });
  return data;
}

export async function getScholars() {
  const { data } = await api.get("/api/scholars");
  return data;
}

export async function handpickScholars(scholarIds) {
  const { data } = await api.post("/api/handpick", {
    scholar_ids: scholarIds,
  });
  return data;
}

export async function chat(sessionId, message) {
  const { data } = await api.post("/api/chat", {
    session_id: sessionId,
    message,
  });
  return data;
}

export async function askScholar(scholarId, question) {
  const { data } = await api.post("/api/ask-scholar", {
    scholar_id: scholarId,
    question,
  });
  return data;
}

export async function getGraphState() {
  const { data } = await api.get("/api/graph-state");
  return data;
}

export async function getProjectIdeas(sessionId) {
  const { data } = await api.post("/api/project-ideas", {
    session_id: sessionId,
  });
  return data;
}

export async function generateEmail(scholarName, affiliation, topics, hIndex = 0, paperCount = 0) {
  const { data } = await api.post("/api/generate_email", {
    scholar_name: scholarName,
    affiliation,
    topics,
    h_index: hIndex,
    paper_count: paperCount,
  });
  return data;
}

export default api;
