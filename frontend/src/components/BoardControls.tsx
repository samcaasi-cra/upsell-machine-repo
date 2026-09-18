import { useEffect } from "react";

export type ViewMode = "default" | "detailed" | "compact";
export type Audience = "csm" | "customer";
export type Theme = "light" | "dark";

const FONT_SCALES = [87.5, 100, 112.5, 125] as const;
const FONT_STORAGE_KEY = "gaia.fontScalePct";
const VIEW_STORAGE_KEY = "gaia.viewMode";
const AUDIENCE_STORAGE_KEY = "gaia.audience";
const THEME_STORAGE_KEY = "gaia.theme";

// Bumped from 100 -- the default board reads small at arm's length (a demo screen,
// a laptop across a table), and every surface here is already sized in rem so this
// one change scales the whole app rather than needing per-component tuning.
export function loadFontScale(): number {
  const raw = Number(localStorage.getItem(FONT_STORAGE_KEY));
  return FONT_SCALES.includes(raw as (typeof FONT_SCALES)[number]) ? raw : 112.5;
}

/** No stored choice yet -- follow the OS, same as the CSS's own
 * @media (prefers-color-scheme: dark) fallback (index.css, OpportunityBoard.css). */
export function loadTheme(): Theme {
  const raw = localStorage.getItem(THEME_STORAGE_KEY);
  if (raw === "light" || raw === "dark") return raw;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

/** Sets data-theme on <html>, which both index.css's global tokens and
 * OpportunityBoard.css's .opp-board-scoped tokens key off of. */
export function useTheme(theme: Theme) {
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);
}

export function loadViewMode(): ViewMode {
  const raw = localStorage.getItem(VIEW_STORAGE_KEY);
  return raw === "detailed" || raw === "compact" ? raw : "default";
}

export function loadAudience(): Audience {
  return localStorage.getItem(AUDIENCE_STORAGE_KEY) === "customer" ? "customer" : "csm";
}

export function AudienceToggle({ audience, onAudience }: { audience: Audience; onAudience: (a: Audience) => void }) {
  useEffect(() => {
    localStorage.setItem(AUDIENCE_STORAGE_KEY, audience);
  }, [audience]);

  return (
    <div className="board-controls-group" role="group" aria-label="Viewing as">
      {(["csm", "customer"] as Audience[]).map((a) => (
        <button
          key={a}
          type="button"
          className="board-controls-btn"
          aria-pressed={audience === a}
          onClick={() => onAudience(a)}
        >
          {a === "csm" ? "View as CSM" : "View as Customer"}
        </button>
      ))}
    </div>
  );
}

/** Global font scale works by resizing the document root, since every component here is
 * sized in rem -- one change point instead of threading a scale prop through everything. */
export function useFontScale(scalePct: number) {
  useEffect(() => {
    document.documentElement.style.fontSize = `${(16 * scalePct) / 100}px`;
    localStorage.setItem(FONT_STORAGE_KEY, String(scalePct));
    return () => {
      document.documentElement.style.fontSize = "";
    };
  }, [scalePct]);
}

export function BoardControls({
  viewMode,
  onViewMode,
  fontScale,
  onFontScale,
}: {
  viewMode: ViewMode;
  onViewMode: (v: ViewMode) => void;
  fontScale: number;
  onFontScale: (v: number) => void;
}) {
  useEffect(() => {
    localStorage.setItem(VIEW_STORAGE_KEY, viewMode);
  }, [viewMode]);

  const scaleIndex = FONT_SCALES.indexOf(fontScale as (typeof FONT_SCALES)[number]);

  return (
    <div className="board-controls">
      <div className="board-controls-group" role="group" aria-label="View density">
        {(["default", "detailed", "compact"] as ViewMode[]).map((v) => (
          <button
            key={v}
            type="button"
            className="board-controls-btn"
            aria-pressed={viewMode === v}
            onClick={() => onViewMode(v)}
          >
            {v[0].toUpperCase() + v.slice(1)}
          </button>
        ))}
      </div>
      <div className="board-controls-group" role="group" aria-label="Text size">
        <button
          type="button"
          className="board-controls-btn board-controls-font"
          disabled={scaleIndex <= 0}
          onClick={() => onFontScale(FONT_SCALES[Math.max(0, scaleIndex - 1)])}
          aria-label="Decrease text size"
        >
          A−
        </button>
        <button
          type="button"
          className="board-controls-btn board-controls-font"
          disabled={scaleIndex >= FONT_SCALES.length - 1}
          onClick={() => onFontScale(FONT_SCALES[Math.min(FONT_SCALES.length - 1, scaleIndex + 1)])}
          aria-label="Increase text size"
        >
          A+
        </button>
      </div>
    </div>
  );
}
