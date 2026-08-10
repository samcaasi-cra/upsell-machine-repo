import { useEffect, useMemo, useRef, useState } from "react";
import type { AccountChip } from "../types";
import { CustomerLogo } from "./CustomerLogo";
import { ChevronDownIcon, CloseIcon, SearchIcon } from "./icons";

/** Replaces the old always-visible account-chip banner: the default state is a single
 * line of text ("Showing all customers"), and filtering to specific accounts is an
 * explicit, on-demand action via search + multi-select rather than a permanent shelf. */
export function CustomerPicker({
  chips,
  selected,
  onChange,
}: {
  chips: AccountChip[];
  selected: Set<string>;
  onChange: (next: Set<string>) => void;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    function onDocClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return chips;
    return chips.filter((c) => c.customer_name.toLowerCase().includes(q));
  }, [chips, query]);

  function toggle(id: string) {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange(next);
  }

  const selectedChips = chips.filter((c) => selected.has(c.customer_id));

  return (
    <div className="cust-picker" ref={ref}>
      <div className="cust-picker-summary">
        {selected.size === 0 ? (
          <span>Showing all customers</span>
        ) : (
          <span>
            Showing {selected.size} of {chips.length} customers
          </span>
        )}
        {selected.size > 0 && (
          <button type="button" className="cust-picker-clear" onClick={() => onChange(new Set())}>
            Clear
          </button>
        )}
      </div>

      {selectedChips.length > 0 && (
        <div className="cust-picker-pills">
          {selectedChips.map((c) => (
            <button
              type="button"
              key={c.customer_id}
              className="cust-picker-pill"
              onClick={() => toggle(c.customer_id)}
              title="Click to remove"
            >
              <CustomerLogo domain={c.domain} name={c.customer_name} size={14} />
              {c.customer_name}
              <CloseIcon />
            </button>
          ))}
        </div>
      )}

      <button type="button" className="cust-picker-trigger" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <SearchIcon />
        Select customers
        <ChevronDownIcon />
      </button>

      {open && (
        <div className="cust-picker-panel">
          <div className="cust-picker-search">
            <SearchIcon />
            <input
              ref={inputRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search customers…"
              aria-label="Search customers"
            />
          </div>
          <div className="cust-picker-list">
            {filtered.length === 0 ? (
              <div className="cust-picker-empty">No customers match.</div>
            ) : (
              filtered.map((c) => (
                <label key={c.customer_id} className="cust-picker-row">
                  <input type="checkbox" checked={selected.has(c.customer_id)} onChange={() => toggle(c.customer_id)} />
                  <CustomerLogo domain={c.domain} name={c.customer_name} size={20} />
                  <span className="cust-picker-row-name">{c.customer_name}</span>
                  {c.score !== null && <span className="cust-picker-row-score">{c.score}</span>}
                </label>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
