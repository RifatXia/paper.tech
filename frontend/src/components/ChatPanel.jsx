import { useState } from "react";
import { chat } from "../api/client";

export default function ChatPanel({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || !sessionId) return;

    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await chat(sessionId, userMsg);
      setMessages((prev) => [...prev, { role: "assistant", content: res.reply }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Sorry, something went wrong. Please try again." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[500px] bg-dark-card border border-dark-border rounded-xl">
      <div className="px-4 py-3 border-b border-dark-border">
        <h3 className="text-sm font-semibold text-gray-300">Multi-Scholar Chat</h3>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-sm text-gray-500 text-center mt-8">
            Ask about overlapping research themes, collaboration ideas, or draft outreach emails.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`max-w-[85%] px-4 py-2.5 rounded-xl text-sm whitespace-pre-wrap ${
              msg.role === "user"
                ? "ml-auto bg-cyan-500/10 text-cyan-100 border border-cyan-500/20"
                : "bg-dark-surface text-gray-300 border border-dark-border"
            }`}
          >
            {msg.content}
          </div>
        ))}
        {loading && (
          <div className="bg-dark-surface text-gray-500 px-4 py-2.5 rounded-xl text-sm border border-dark-border w-fit">
            Thinking...
          </div>
        )}
      </div>

      <form onSubmit={handleSend} className="p-3 border-t border-dark-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={sessionId ? "Ask about these scholars..." : "Start a session first"}
            disabled={!sessionId}
            className="flex-1 px-4 py-2 bg-dark-surface border border-dark-border rounded-lg text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-cyan-500/50 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!sessionId || loading}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 disabled:opacity-50 text-dark font-medium rounded-lg text-sm transition-colors"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
