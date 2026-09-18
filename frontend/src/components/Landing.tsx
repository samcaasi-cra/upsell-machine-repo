import { useEffect, useRef, useState } from "react";
import { GAIA_ACTIONS, type Tab } from "../actions";
import "./Landing.css";

/* Product intro shown before the dashboard: one idea per screen, large type, so a
   first-time viewer learns what Gaia is and what the four actions do before facing
   a board of 100 signals. */

const STEPS = [
  {
    word: "Seek",
    body: "Every day, Gaia reads every account: score changes and supplier risk from the SecurityScorecard API, and the news for acquisitions, new offices and launches.",
  },
  {
    word: "Select",
    body: "It ranks what changed, so the signals that matter reach the CSM who owns the account — not just the loudest customers.",
  },
  {
    word: "Serve",
    body: "Each signal arrives as a next action: who to contact, why now, and an email ready to send once a person approves it.",
  },
];

const VALUES = [
  { title: "A person decides", body: "Nothing reaches a customer until a CSM approves it." },
  { title: "Every signal shows its source", body: "Each card names the API call or article behind it." },
  { title: "Identities masked", body: "Customer names become labels before the AI sees them." },
  { title: "Built on SecurityScorecard", body: "Scores and supplier risk come straight from the API." },
];

interface Props {
  onEnter: (tab: Tab) => void;
}

export function Landing({ onEnter }: Props) {
  const [touring, setTouring] = useState(false);
  const root = useRef<HTMLDivElement>(null);

  // Reveal each section as it scrolls into view. Without IntersectionObserver, or
  // with reduced motion, everything is simply visible.
  useEffect(() => {
    const els = root.current?.querySelectorAll<HTMLElement>(".reveal") ?? [];
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced || !("IntersectionObserver" in window)) {
      els.forEach((el) => el.classList.add("in"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("in");
            io.unobserve(e.target);
          }
        }),
      { threshold: 0.18 },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <div className="landing" ref={root}>
      <section className="landing-hero">
        <p className="landing-eyebrow reveal">Growth agentic AI · built on SecurityScorecard</p>
        <h1 className="landing-wordmark reveal">Gaia</h1>
        <p className="landing-lede reveal">
          Finds the moment a customer is ready to grow — and hands your CSM the next move.
        </p>
        <div className="landing-ctas reveal">
          <button type="button" className="landing-btn primary" onClick={() => setTouring(true)}>
            Start the tour
          </button>
          <button type="button" className="landing-btn" onClick={() => onEnter("opportunities")}>
            Open Gaia
          </button>
        </div>
        <a className="landing-scroll" href="#landing-how" aria-label="Scroll to how Gaia works">
          How it works ↓
        </a>
      </section>

      <section className="landing-section" id="landing-how">
        <p className="landing-kicker reveal">How it works</p>
        <h2 className="landing-h2 reveal">Three moves, every day, for every customer.</h2>
        <div className="landing-steps">
          {STEPS.map((s) => (
            <div className="landing-step reveal" key={s.word}>
              <span className="landing-step-word">{s.word}</span>
              <p>{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section landing-purpose">
        <p className="landing-kicker reveal">Purpose</p>
        <h2 className="landing-h2 reveal">Named for the mother of the Titans.</h2>
        <p className="landing-body reveal">
          Gaia nurtures growth: it helps Titan Watch and Assess customers grow into Secure and MAX by acting on the
          signals that say they're ready — designed to add $10M a year in recurring revenue, with partner products
          such as Cytactic as the next step.
        </p>
      </section>

      <section className="landing-section">
        <p className="landing-kicker reveal">What it stands for</p>
        <h2 className="landing-h2 reveal">Fast, but never unsupervised.</h2>
        <div className="landing-values">
          {VALUES.map((v) => (
            <div className="landing-value reveal" key={v.title}>
              <h3>{v.title}</h3>
              <p>{v.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-section">
        <p className="landing-kicker reveal">Four ways in</p>
        <h2 className="landing-h2 reveal">Pick where to start.</h2>
        <div className="landing-actions">
          {GAIA_ACTIONS.map((a) => (
            <button type="button" className="landing-action reveal" key={a.tab} onClick={() => onEnter(a.tab)}>
              <span className="landing-action-num">{a.number}</span>
              <span className="landing-action-title">{a.title}</span>
              <span className="landing-action-more">
                <span>{a.explainer}</span>
                <span className="landing-action-go">Open {a.title} →</span>
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="landing-section landing-final">
        <h2 className="landing-h2 reveal">Ready when you are.</h2>
        <div className="landing-ctas reveal">
          <button type="button" className="landing-btn primary" onClick={() => onEnter("today")}>
            See today's top signals
          </button>
          <button type="button" className="landing-btn" onClick={() => setTouring(true)}>
            Take the tour
          </button>
        </div>
      </section>

      {touring && <Tour onClose={() => setTouring(false)} onEnter={onEnter} />}
    </div>
  );
}

/* The tour: one thing at a time, full screen. Arrow keys move, Escape closes. */
function Tour({ onClose, onEnter }: { onClose: () => void; onEnter: (tab: Tab) => void }) {
  const slides = [
    {
      kicker: "Welcome",
      title: "This is Gaia.",
      body: "An AI agent that watches every customer and tells your CSMs who to contact, why now, and what to say.",
    },
    {
      kicker: "How it works",
      title: "Seek. Select. Serve.",
      body: STEPS.map((s) => `${s.word}: ${s.body}`).join("\n\n"),
    },
    ...GAIA_ACTIONS.map((a) => ({
      kicker: `Action ${a.number} of ${GAIA_ACTIONS.length}`,
      title: a.title,
      body: `${a.explainer}\n\n${a.payoff}`,
      tab: a.tab,
    })),
    {
      kicker: "You stay in control",
      title: "Gaia suggests. You decide.",
      body: "Every action waits for a person to approve or dismiss it. Every signal shows its source. Customer names are masked before the AI sees them.",
    },
  ];
  const [i, setI] = useState(0);
  const last = i === slides.length - 1;
  const slide = slides[i];
  const nextRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    nextRef.current?.focus();
  }, [i]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowRight") setI((n) => Math.min(n + 1, slides.length - 1));
      if (e.key === "ArrowLeft") setI((n) => Math.max(n - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, slides.length]);

  return (
    <div className="tour" role="dialog" aria-modal="true" aria-label="Gaia tour">
      <button type="button" className="tour-close" onClick={onClose} aria-label="Close tour">
        ×
      </button>
      <div className="tour-slide" key={i}>
        <p className="landing-kicker">{slide.kicker}</p>
        <h2 className="tour-title">{slide.title}</h2>
        {slide.body.split("\n\n").map((p) => (
          <p className="tour-body" key={p}>
            {p}
          </p>
        ))}
        {"tab" in slide && slide.tab && (
          <button type="button" className="tour-try" onClick={() => onEnter(slide.tab as Tab)}>
            Open this now →
          </button>
        )}
      </div>
      <div className="tour-nav">
        <button type="button" className="landing-btn" onClick={() => setI(i - 1)} disabled={i === 0}>
          Back
        </button>
        <div className="tour-dots" aria-hidden="true">
          {slides.map((_, n) => (
            <span key={n} className={n === i ? "on" : ""} />
          ))}
        </div>
        {last ? (
          <button ref={nextRef} type="button" className="landing-btn primary" onClick={() => onEnter("opportunities")}>
            Open Gaia
          </button>
        ) : (
          <button ref={nextRef} type="button" className="landing-btn primary" onClick={() => setI(i + 1)}>
            Next
          </button>
        )}
      </div>
    </div>
  );
}
