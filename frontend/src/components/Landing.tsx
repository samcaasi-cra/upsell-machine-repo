import { useEffect, useState } from "react";
import { GAIA_ACTIONS, type Tab } from "../actions";
import "./Landing.css";

/* Product intro shown before the dashboard.

   One screen at a time, moved with a Next button rather than scrolling: the board
   opens on 100+ signals, and meeting that cold is the thing this exists to prevent.
   There is no separate "tour" -- this page is the tour, so the same explanation never
   appears twice in two formats. */

interface Props {
  onEnter: (tab: Tab) => void;
}

const STEPS = [
  { key: "hero" },
  { key: "how" },
  ...GAIA_ACTIONS.map((a) => ({ key: a.tab, action: a })),
  { key: "trust" },
  { key: "purpose" },
] as const;

const LOOP = [
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

export function Landing({ onEnter }: Props) {
  const [i, setI] = useState(0);
  const step = STEPS[i];
  const last = i === STEPS.length - 1;

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") setI((n) => Math.min(n + 1, STEPS.length - 1));
      if (e.key === "ArrowLeft") setI((n) => Math.max(n - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="landing">
      <button type="button" className="landing-skip" onClick={() => onEnter("opportunities")}>
        Skip to the dashboard
      </button>

      <div className="landing-stage" key={step.key}>
        {step.key === "hero" && (
          <div className="landing-panel landing-panel-hero">
            <p className="landing-kicker">Growth agentic AI · built on SecurityScorecard</p>
            <h1 className="landing-wordmark">Gaia</h1>
            <p className="landing-lede">
              Finds the moment a customer is ready to grow — and hands your CSM the next move.
            </p>
          </div>
        )}

        {step.key === "how" && (
          <div className="landing-panel">
            <p className="landing-kicker">How it works</p>
            <h2 className="landing-h2">Three moves, every day, for every customer.</h2>
            <div className="landing-loop">
              {LOOP.map((s) => (
                <div className="landing-loop-item" key={s.word}>
                  <span className="landing-loop-word">{s.word}</span>
                  <p>{s.body}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {"action" in step && step.action && (
          <div className="landing-panel landing-panel-action">
            <p className="landing-kicker">
              View {step.action.number} of {GAIA_ACTIONS.length}
            </p>
            <span className="landing-action-num">{step.action.number}</span>
            <h2 className="landing-h2">{step.action.title}</h2>
            <p className="landing-body">{step.action.explainer}</p>
            <p className="landing-payoff">{step.action.payoff}</p>
          </div>
        )}

        {step.key === "trust" && (
          <div className="landing-panel">
            <p className="landing-kicker">What it stands for</p>
            <h2 className="landing-h2">Fast, but never unsupervised.</h2>
            <div className="landing-values">
              {VALUES.map((v) => (
                <div className="landing-value" key={v.title}>
                  <h3>{v.title}</h3>
                  <p>{v.body}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {step.key === "purpose" && (
          <div className="landing-panel">
            <p className="landing-kicker">Purpose</p>
            <h2 className="landing-h2">Named for the mother of the Titans.</h2>
            <p className="landing-body">
              Gaia nurtures growth: it helps Titan Watch and Assess customers grow into Secure and MAX by acting on
              the signals that say they're ready — designed to add $10M a year in recurring revenue, with partner
              products such as Cytactic as the next step.
            </p>
          </div>
        )}
      </div>

      <div className="landing-nav">
        <button type="button" className="landing-btn" onClick={() => setI(i - 1)} disabled={i === 0}>
          Back
        </button>
        <div className="landing-dots" aria-hidden="true">
          {STEPS.map((s, n) => (
            <span key={s.key} className={n === i ? "on" : ""} />
          ))}
        </div>
        {last ? (
          <button type="button" className="landing-btn primary" onClick={() => onEnter("opportunities")}>
            Open Gaia →
          </button>
        ) : (
          <button type="button" className="landing-btn primary" onClick={() => setI(i + 1)}>
            {i === 0 ? "Start" : "Next"}
          </button>
        )}
      </div>
    </div>
  );
}
