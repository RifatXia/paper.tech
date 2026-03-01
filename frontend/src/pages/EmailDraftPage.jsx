import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function EmailDraftPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const scholar = location.state?.scholar;

  const [to, setTo] = useState(scholar?.email || "");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    const text = `To: ${to}\nSubject: ${subject}\n\n${body}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const handleOpenGmail = () => {
    const params = new URLSearchParams({
      to,
      su: subject,
      body,
    });
    window.open(`https://mail.google.com/mail/?view=cm&${params.toString()}`, "_blank");
  };

  return (
    <main className="flex-1 flex items-start justify-center px-4 py-12">
      <div className="w-full max-w-2xl space-y-6">
        <button
          onClick={() => navigate(-1)}
          className="text-sm text-gray-400 hover:text-cyan-400 transition-colors"
        >
          ← Back to results
        </button>

        <h1 className="text-2xl font-bold text-gray-100">
          Draft Email
          {scholar?.name && (
            <span className="text-gray-400 font-normal"> to {scholar.name}</span>
          )}
        </h1>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">To</label>
            <input
              type="email"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="recipient@example.com"
              className="w-full px-4 py-2.5 bg-dark-surface border border-dark-border rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Subject</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Email subject"
              className="w-full px-4 py-2.5 bg-dark-surface border border-dark-border rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Body</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Write your email..."
              rows={12}
              className="w-full px-4 py-3 bg-dark-surface border border-dark-border rounded-lg text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-400 transition-colors resize-y"
            />
          </div>

          <div className="flex justify-between">
            <button
              onClick={handleCopy}
              className="px-5 py-2.5 text-sm font-medium text-gray-200 border border-dark-border hover:border-cyan-400/30 hover:text-cyan-400 rounded-lg transition-colors"
            >
              {copied ? "Copied!" : "Copy to Clipboard"}
            </button>
            <button
              onClick={handleOpenGmail}
              className="px-5 py-2.5 text-sm font-medium bg-cyan-500 hover:bg-cyan-600 text-dark font-semibold rounded-lg transition-colors"
            >
              Open in Gmail
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
