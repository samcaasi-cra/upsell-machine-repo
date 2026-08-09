import { useEffect, useState } from "react";

export function PromptImportModal({
  title,
  placeholder,
  getPrompt,
  onImport,
  onClose,
  onImported,
}: {
  title: string;
  placeholder: string;
  getPrompt: () => Promise<{ prompt: string }>;
  onImport: (text: string) => Promise<void>;
  onClose: () => void;
  onImported: () => void;
}) {
  const [prompt, setPrompt] = useState("");
  const [loadingPrompt, setLoadingPrompt] = useState(true);
  const [copied, setCopied] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);

  useEffect(() => {
    getPrompt()
      .then((res) => setPrompt(res.prompt))
      .finally(() => setLoadingPrompt(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCopy() {
    await navigator.clipboard.writeText(prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  async function handleImport() {
    setImporting(true);
    setImportError(null);
    try {
      await onImport(pasteText);
      onImported();
      onClose();
    } catch (err) {
      setImportError(err instanceof Error ? err.message : String(err));
    } finally {
      setImporting(false);
    }
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 50,
        padding: 16,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--surface-1)",
          borderRadius: 12,
          border: "1px solid var(--border)",
          maxWidth: 720,
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: 20,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>{title}</h3>
          <button onClick={onClose} style={{ border: "none", background: "none", fontSize: 18, cursor: "pointer" }}>
            ×
          </button>
        </div>

        <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>
          1. Copy this prompt and run it in Claude (claude.ai, Claude Code, wherever). 2. Paste the JSON result it
          returns back in below and import it.
        </p>

        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 6 }}>
          <button onClick={handleCopy} disabled={loadingPrompt} style={buttonStyle}>
            {copied ? "Copied!" : "Copy prompt"}
          </button>
        </div>
        <textarea
          readOnly
          value={loadingPrompt ? "Loading…" : prompt}
          style={{
            width: "100%",
            height: 180,
            fontFamily: "monospace",
            fontSize: 12,
            padding: 10,
            borderRadius: 8,
            border: "1px solid var(--border)",
            background: "var(--surface-2)",
            color: "var(--text-primary)",
            resize: "vertical",
          }}
        />

        <div style={{ marginTop: 16 }}>
          <label style={{ fontSize: 13, fontWeight: 600, display: "block", marginBottom: 6 }}>
            Paste the JSON result here
          </label>
          <textarea
            value={pasteText}
            onChange={(e) => setPasteText(e.target.value)}
            placeholder={placeholder}
            style={{
              width: "100%",
              height: 140,
              fontFamily: "monospace",
              fontSize: 12,
              padding: 10,
              borderRadius: 8,
              border: "1px solid var(--border)",
              background: "var(--surface-2)",
              color: "var(--text-primary)",
              resize: "vertical",
            }}
          />
          {importError && (
            <p style={{ color: "var(--status-critical)", fontSize: 13, marginTop: 6 }}>{importError}</p>
          )}
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
            <button
              onClick={handleImport}
              disabled={!pasteText.trim() || importing}
              style={{ ...buttonStyle, background: "var(--series-1)", color: "white", border: "none" }}
            >
              {importing ? "Importing…" : "Import result"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

const buttonStyle = {
  fontSize: 13,
  fontWeight: 600,
  padding: "6px 12px",
  borderRadius: 8,
  border: "1px solid var(--border)",
  background: "var(--surface-2)",
  color: "var(--text-primary)",
  cursor: "pointer",
} as const;
