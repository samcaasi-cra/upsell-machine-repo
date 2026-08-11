import { useEffect, useRef, useState, type ReactNode } from "react";
import { InfoIcon } from "./icons";

/** A small "ⓘ" affordance that reveals detail on click -- works the same on touch and
 * desktop, unlike a hover-only tooltip. Closes on outside click or Escape. */
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
    <div className="info-pop" ref={ref}>
      <button
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
      {open && (
        <div className={`info-pop-panel info-pop-panel-${align}`} role="tooltip" onClick={(e) => e.stopPropagation()}>
          {children}
        </div>
      )}
    </div>
  );
}
