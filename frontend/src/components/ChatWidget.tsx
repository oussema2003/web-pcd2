import { useState, useRef, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const INITIAL_MESSAGE: Message = {
  role: "assistant",
  content:
    "Bonjour, je suis l'assistant du site de recrutement. Je peux vous aider à utiliser le site : recherche d'offres, dépôt de candidatures, espace candidat, etc.",
};

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMessage: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const history = messages.slice(1).map((m) => ({ role: m.role, content: m.content }));

    try {
      const response = await fetch(`${API_URL}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          history,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errMsg = data.error || `Erreur ${response.status}`;
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `Erreur : ${errMsg}` },
        ]);
        return;
      }

      if (data.answer != null) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.answer },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Réponse invalide du serveur." },
        ]);
      }
    } catch (e) {
      const errMsg =
        e instanceof Error ? e.message : "Impossible de contacter le serveur.";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Erreur réseau : ${errMsg}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const buttonStyle: React.CSSProperties = {
    position: "fixed",
    bottom: 20,
    right: 20,
    zIndex: 1000,
    width: 56,
    height: 56,
    padding: 0,
    borderRadius: "50%",
    border: "none",
    backgroundColor: "transparent",
    cursor: "pointer",
    boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  };

  const windowStyle: React.CSSProperties = {
    position: "fixed",
    bottom: 80,
    right: 20,
    zIndex: 1000,
    width: 320,
    maxWidth: "calc(100vw - 40px)",
    height: 420,
    backgroundColor: "white",
    borderRadius: 12,
    boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  };

  const headerStyle: React.CSSProperties = {
    padding: "12px 16px",
    backgroundColor: "#1e40af",
    color: "white",
    fontWeight: 600,
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  };

  const closeBtnStyle: React.CSSProperties = {
    background: "none",
    border: "none",
    color: "white",
    fontSize: 20,
    cursor: "pointer",
    lineHeight: 1,
    padding: "0 4px",
  };

  const messagesStyle: React.CSSProperties = {
    flex: 1,
    overflowY: "auto",
    padding: 12,
    display: "flex",
    flexDirection: "column",
    gap: 10,
  };

  const bubbleBase: React.CSSProperties = {
    maxWidth: "85%",
    padding: "10px 14px",
    borderRadius: 12,
    wordBreak: "break-word",
  };

  const inputAreaStyle: React.CSSProperties = {
    padding: 12,
    borderTop: "1px solid #e5e7eb",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  };

  return (
    <>
      {!isOpen && (
        <button
          type="button"
          style={buttonStyle}
          onClick={() => setIsOpen(true)}
          aria-label="Ouvrir l’aide du site"
        >
        <img
          src="/robot-chat-icon.png"
          alt="Aide du site"
          style={{ width: 56, height: 56, objectFit: "contain" }}
        />
      </button>
      )}

      {isOpen && (
        <div style={windowStyle} role="dialog" aria-label="Assistant du site">
          <div style={headerStyle}>
            <span>Assistant du site</span>
            <button
              type="button"
              style={closeBtnStyle}
              onClick={() => setIsOpen(false)}
              aria-label="Fermer"
            >
              ×
            </button>
          </div>

          <div style={messagesStyle}>
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  ...bubbleBase,
                  alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                  backgroundColor:
                    msg.role === "user" ? "#2563eb" : "#e5e7eb",
                  color: msg.role === "user" ? "white" : "#1f2937",
                }}
              >
                {msg.content}
              </div>
            ))}
            {loading && (
              <div
                style={{
                  ...bubbleBase,
                  alignSelf: "flex-start",
                  backgroundColor: "#e5e7eb",
                  color: "#6b7280",
                  fontStyle: "italic",
                }}
              >
                L'assistant écrit…
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div style={inputAreaStyle}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Votre question…"
              rows={2}
              disabled={loading}
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: 10,
                borderRadius: 8,
                border: "1px solid #d1d5db",
                resize: "none",
                fontFamily: "inherit",
                fontSize: 14,
              }}
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              style={{
                padding: "10px 16px",
                borderRadius: 8,
                border: "none",
                backgroundColor: "#2563eb",
                color: "white",
                fontWeight: 600,
                cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                opacity: loading || !input.trim() ? 0.7 : 1,
              }}
            >
              Envoyer
            </button>
          </div>
        </div>
      )}
    </>
  );
}
