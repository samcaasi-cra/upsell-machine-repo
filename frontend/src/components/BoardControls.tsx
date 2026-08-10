import { useEffect } from "react";

export type ViewMode = "default" | "detailed" | "compact";

const FONT_SCALES = [87.5, 100, 112.5, 125] as const;
const FONT_STORAGE_KEY = "gaia.fontScalePct";
const VIEW_STORAGE_KEY = "gaia.viewMode";

export function loadFontScale(): number {
  const raw = Number(localStorage.getItem(FONT_STORAGE_KEY));
  return FONT_SCALES.includes(raw as (typeof FONT_SCALES)[number]) ? raw : 100;
}

export function loadViewMode(): ViewMode {
  const raw = localStorage.getItem(VIEW_STORAGE_KEY);
  return raw === "detailed" || raw === "compact" ? raw : "default";
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
