import { useState, type FormEvent } from "react";
import { api } from "../api/client";

export function AddCustomerModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [sponsor, setSponsor] = useState("");
  const [csm, setCsm] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.createCustomer({
        name,
        domain,
        sponsor: sponsor || null,
        csm: csm || null,
      });
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
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
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={handleSubmit}
        style={{
          background: "var(--surface-1)",
          borderRadius: 12,
          border: "1px solid var(--border)",
          maxWidth: 420,
          width: "100%",
          padding: 20,
          display: "grid",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ margin: 0 }}>Add customer</h3>
          <button
            type="button"
            onClick={onClose}
            style={{ border: "none", background: "none", fontSize: 18, cursor: "pointer" }}
          >
            ×
          </button>
        </div>

        <Field label="Name" value={name} onChange={setName} required />
        <Field label="Domain" value={domain} onChange={setDomain} placeholder="example.com" required />
        <Field label="Sponsor" value={sponsor} onChange={setSponsor} />
        <Field label="CSM" value={csm} onChange={setCsm} placeholder="Leave blank if unassigned" />

        {error && <p style={{ color: "var(--status-critical)", fontSize: 13, margin: 0 }}>{error}</p>}

        <button
          type="submit"
          disabled={saving || !name || !domain}
          style={{
            fontSize: 13,
            fontWeight: 600,
            padding: "8px 12px",
            borderRadius: 8,
            border: "none",
            background: "var(--series-1)",
            color: "white",
            cursor: "pointer",
          }}
        >
          {saving ? "Adding…" : "Add customer"}
        </button>
      </form>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <label style={{ display: "grid", gap: 4, fontSize: 13 }}>
      <span style={{ fontWeight: 600 }}>
        {label}
        {required && " *"}
      </span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          padding: "8px 10px",
          borderRadius: 8,
          border: "1px solid var(--border)",
          background: "var(--surface-2)",
          color: "var(--text-primary)",
          fontSize: 14,
        }}
      />
    </label>
  );
}
