import { useEffect, useRef, useState } from "react";
import { AudienceToggle, BoardControls, type Audience, type ViewMode } from "./BoardControls";
import { SettingsIcon } from "./icons";

/** Tucks the CSM/Customer, density and text-size controls behind a gear icon instead
 * of leaving them always on screen -- same click-to-toggle, close-on-outside-click
 * pattern as InfoPopover, just holding interactive controls instead of read-only text. */
export function SettingsMenu({
  audience,
  onAudience,
  viewMode,
  onViewMode,
  fontScale,
  onFontScale,
}: {
  audience: Audience;
  onAudience: (a: Audience) => void;
  viewMode: ViewMode;
  onViewMode: (v: ViewMode) => void;
  fontScale: number;
  onFontScale: (v: number) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
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

  return (
    <div className="settings-menu" ref={ref}>
      <button
        type="button"
        className="settings-menu-trigger"
        aria-label="Settings"
        aria-expanded={open}
        title="Settings"
        onClick={() => setOpen((v) => !v)}
      >
        <SettingsIcon />
      </button>
      {open && (
        // Also carries opp-board: AudienceToggle/BoardControls reuse .board-controls-btn,
        // whose active-state colors are custom properties scoped under .opp-board (see
        // the nav-tab-btn fix in index.css for the same issue elsewhere).
        <div className="opp-board settings-menu-panel" role="menu">
          <div className="settings-menu-group">
            <span className="settings-menu-label">Viewing as</span>
            <AudienceToggle audience={audience} onAudience={onAudience} />
          </div>
          <div className="settings-menu-group">
            <span className="settings-menu-label">Density &amp; text size</span>
            <BoardControls
              viewMode={viewMode}
              onViewMode={onViewMode}
              fontScale={fontScale}
              onFontScale={onFontScale}
            />
          </div>
        </div>
      )}
    </div>
  );
}
