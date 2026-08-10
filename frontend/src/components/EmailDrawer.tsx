import { useEffect, useMemo, useState, type CSSProperties } from "react";
import type { OpportunityCard } from "../types";

/**
 * The drafted email is a starting point, not a finished artefact -- a CSM will usually
 * want to adjust the wording or send it to someone else. Edits are session-only and the
 * generated default is always one click away, so the template can't be lost by accident.
 */
export function EmailDrawer({
  card,
  groupLabel,
  actioned,
  onClose,
  onToggleActioned,
}: {
  card: OpportunityCard;
  groupLabel: string;
  actioned: boolean;
  onClose: () => void;
  onToggleActioned: () => void;
}) {
  const [status, setStatus] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [recipientName, setRecipientName] = useState(card.recipient_name);
  const [subject, setSubject] = useState(card.subject);
  const [body, setBody] = useState(card.body);

  const recipientRole = useMemo(() => {
    const match = card.recipient_options.find((o) => o.name === recipientName);
    return match ? match.role : card.recipient_role;
  }, [recipientName, card.recipient_options, card.recipient_role]);

  // Re-point the greeting when the recipient changes, but never clobber manual edits.
  useEffect(() => {
    if (editing) return;
    const first = recipientName.split(" ")[0] || "there";
    setBody(card.body.replace(/^Hello [^,]+,/, `Hello ${first},`));
  }, [recipientName, card.body, editing]);

  const isDirty = subject !== card.subject || body !== card.body || recipientName !== card.recipient_name;

  useEffect(() => {
    function onKeydown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeydown);
    return () => document.removeEventListener("keydown", onKeydown);
  }, [onClose]);

  function resetToDefault() {
    setRecipientName(card.recipient_name);
    setSubject(card.subject);
    setBody(card.body);
    setEditing(false);
    setStatus("Reset to the generated draft.");
  }

  async function handleCopy() {
    const text = `To: ${recipientName}${recipientRole ? ` (${recipientRole})` : ""}\nSubject: ${subject}\n\n${body}`;
    try {
      await navigator.clipboard.writeText(text);
      setStatus("Email copied to clipboard.");
    } catch {
      setStatus("Could not copy — select the text above manually.");
    }
  }

  return (
    <>
      <div className="opp-scrim" onClick={onClose} />
      <aside className="opp-drawer" role="dialog" aria-modal="true">
        <div className="opp-drawer-header">
          <span className="opp-drawer-eyebrow">
            {groupLabel} · {card.customer_name}
          </span>
          <button className="opp-drawer-close" onClick={onClose} aria-label="Close email draft">
            ×
          </button>
        </div>
        <div className="opp-drawer-body">
          {editing ? (
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              aria-label="Email subject"
              style={inputStyle}
            />
          ) : (
            <h2>{subject}</h2>
          )}

          <dl className="opp-drawer-meta">
            <dt>To</dt>
            <dd>
              {card.recipient_options.length > 1 ? (
                <select
                  value={recipientName}
                  onChange={(e) => setRecipientName(e.target.value)}
                  aria-label="Recipient"
                  style={{ ...inputStyle, fontWeight: 600, padding: "3px 6px", width: "auto", maxWidth: "100%" }}
                >
                  {card.recipient_options.map((o) => (
                    <option key={o.name} value={o.name}>
                      {o.name}
                    </option>
                  ))}
                </select>
              ) : (
                recipientName
              )}
            </dd>
            <dt>Role</dt>
            <dd>{recipientRole}</dd>
            <dt>Account</dt>
            <dd>{card.customer_name}</dd>
          </dl>

          {card.detail && <p className="opp-drawer-detail">{card.detail}</p>}

          {card.data_source === "sample" && (
            <p style={{ margin: "0 0 10px" }}>
              <span className="opp-sample-tag">◇ Sample data</span>{" "}
              <span style={{ fontSize: "0.72rem", color: "var(--slate)" }}>
                This signal is based on placeholder platform-usage data.
              </span>
            </p>
          )}
          {card.data_source === "concept" && (
            <p style={{ margin: "0 0 10px" }}>
              <span className="opp-concept-tag">⚑ Not built — concept</span>{" "}
              <span style={{ fontSize: "0.72rem", color: "var(--slate)" }}>
                Illustrative only. Every number here is invented.
                {card.concept_trigger ? ` Trigger ${card.concept_trigger}.` : ""}
              </span>
            </p>
          )}

          {editing ? (
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              aria-label="Email body"
              style={{ ...inputStyle, minHeight: 260, lineHeight: 1.6, resize: "vertical" }}
            />
          ) : (
            <div className="opp-drawer-email-body">{body}</div>
          )}

          <p className="opp-drawer-source">
            {isDirty ? "Edited from the generated draft" : "Static template — pre-written, not generated by an LLM"}
          </p>

          <div className="opp-drawer-actions">
            <button className="opp-btn opp-btn-primary" onClick={handleCopy}>
              Copy email
            </button>
            <button className="opp-btn" aria-pressed={editing} onClick={() => setEditing((v) => !v)}>
              {editing ? "Done editing" : "Edit"}
            </button>
            {isDirty && (
              <button className="opp-btn" onClick={resetToDefault}>
                Reset to default
              </button>
            )}
            <button className="opp-btn" aria-pressed={actioned} onClick={onToggleActioned}>
              {actioned ? "Actioned ✓" : "Mark as actioned"}
            </button>
          </div>
          {status && <p className="opp-drawer-status">{status}</p>}
        </div>
      </aside>
    </>
  );
}

const inputStyle: CSSProperties = {
  width: "100%",
  background: "var(--surface-2)",
  border: "1px solid var(--border-strong)",
  borderRadius: 3,
  color: "var(--ink)",
  font: "inherit",
  fontSize: "0.85rem",
  padding: "8px 10px",
  marginBottom: 10,
};
