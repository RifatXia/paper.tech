import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import LandingPage from "./pages/LandingPage";
import ResultsPage from "./pages/ResultsPage";
import EmailDraftPage from "./pages/EmailDraftPage";

export default function App() {
  return (
    <div className="min-h-screen bg-dark bg-grid">
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/results" element={<ResultsPage />} />
        <Route path="/email" element={<EmailDraftPage />} />
      </Routes>
    </div>
  );
}
