import { useEffect, useRef, useState, type ReactNode } from "react";
import { InfoIcon } from "./icons";

/** A small "ⓘ" affordance that reveals detail on click -- works the same on touch and
 * desktop, unlike a hover-only tooltip. Closes on outside click, Escape, or scroll.
 *
 * Positioned with `position: fixed` from the trigger's actual viewport coordinates,
 * not CSS-anchored to its normal-flow parent -- most cards live inside a lane with its
 * own `overflow-y: auto` (OpportunityBoard.css, .opp-lane-body), and a plain
 * `position: absolute` panel gets silently clipped by that ancestor for any card that
 * isn't near the top of the list, which is most of them. `fixed` escapes that clipping
 * entirely since nothing upstream sets a transform/filter (which would otherwise give
 * fixed a new containing block); closing on scroll avoids a stale floating panel
 * instead of repositioning it every frame. */
export function InfoPopover({
  label = "Click for more info",
  align = "left",
  icon,
  children,
}: {
  label?: string;
  align?: "left" | "right";
  /** Override the default "ⓘ" trigger, e.g. with a colored data-source icon. */
  icon?: ReactNode;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const rect = triggerRef.current?.getBoundingClientRect();
    if (rect) {
      const panelWidth = Math.max(200, Math.min(260, window.innerWidth * 0.6));
      const desiredLeft = align === "right" ? rect.right - panelWidth : rect.left;
      const left = Math.min(Math.max(desiredLeft, 8), window.innerWidth - panelWidth - 8);
      // Flip above the trigger when there's not enough room below -- a card near the
      // bottom of the browser window, not just the lane's own scroll clipping this was
      // written to fix. Content here is a short blurb, so a fixed estimate is enough;
      // exact height would need a measure-then-place second pass for one extra pixel
      // of accuracy that's never visible.
      const estimatedHeight = 140;
      const openAbove = window.innerHeight - rect.bottom < estimatedHeight && rect.top > estimatedHeight;
      setPos({ top: openAbove ? rect.top - estimatedHeight - 6 : rect.bottom + 6, left });
    }

    function onDocClick(e: MouseEvent) {
      const target = e.target as Node;
      if (triggerRef.current?.contains(target) || panelRef.current?.contains(target)) return;
      setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    // Capture phase so this also fires for scrolling *inside* a lane, not just the page.
    function onScrollOrResize() {
      setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    window.addEventListener("scroll", onScrollOrResize, true);
    window.addEventListener("resize", onScrollOrResize);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("scroll", onScrollOrResize, true);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [open, align]);

  return (
    <div className="info-pop">
      <button
        ref={triggerRef}
        type="button"
        className="info-pop-trigger"
        aria-label={label}
        aria-expanded={open}
        title={label}
        onClick={(e) => {
          e.stopPropagation();
          setOpen((v) => !v);
        }}
      >
        {icon ?? <InfoIcon />}
      </button>
      {open && pos && (
        <div
          ref={panelRef}
          className="info-pop-panel"
          role="tooltip"
          style={{ top: pos.top, left: pos.left }}
          onClick={(e) => e.stopPropagation()}
        >
          {children}
        </div>
      )}
    </div>
  );
}
