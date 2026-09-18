/* The four things a CSM can do in Gaia. Defined once so the landing page, the guided
   tour and the dashboard's tab bar all describe each action the same way. */

export type Tab = "opportunities" | "today" | "ask" | "success-plan" | "partner-fit" | "cr-tracker";

export interface GaiaAction {
  tab: Tab;
  number: number;
  title: string;
  /** Longer description under the title; for 1–3 this is the original tab label,
      kept verbatim because the demo script reads it aloud. */
  subtitle: string;
  /** One or two sentences for the landing page and tour. */
  explainer: string;
  /** What the CSM gets out of it, in their words. */
  payoff: string;
}

export const GAIA_ACTIONS: GaiaAction[] = [
  {
    tab: "opportunities",
    number: 1,
    title: "All growth signals",
    subtitle: "Best action recommendations this month to drive growth across customers",
    explainer:
      "Every signal Gaia found across the portfolio, sorted into four kinds of change: in score, in usage, in risk, and at the customer. Each card says what happened, what to do, and where the data came from.",
    payoff: "The whole portfolio, reviewed — not just the loudest accounts.",
  },
  {
    tab: "today",
    number: 2,
    title: "Today",
    subtitle: "Today’s top new signals of ‘We’re ready to buy’",
    explainer:
      "Gaia's agent reviews every account and picks the three worth acting on today, with a drafted email for each.",
    payoff: "Three decisions a day instead of a board to scan.",
  },
  {
    tab: "ask",
    number: 3,
    title: "Ask Gaia",
    subtitle: "Ask Gaia any question about your customers",
    explainer:
      "Ask in plain English — which suppliers are getting riskier, who is ready for an upgrade — and Gaia answers from live portfolio data, showing which tools it used.",
    payoff: "Answers in seconds, grounded in the data.",
  },
  {
    tab: "success-plan",
    number: 4,
    title: "Joint success plan",
    subtitle: "What each customer is trying to fix, and what moved in the last 30 days",
    explainer:
      "For one customer: what they're trying to fix, what was agreed to measure, and everything that moved in the last 30 days.",
    payoff: "A plan that reflects this week, not the kickoff call.",
  },
  {
    tab: "partner-fit",
    number: 5,
    title: "Partner fit",
    subtitle: "Which customers are ready for a SecurityScorecard partner product",
    explainer:
      "The same signals, one more question alongside the Titan case: who's also ready for a partner product. Cytactic's rules are live; EY and Grip are next.",
    payoff: "Partner conversations CSMs would never have time to find.",
  },
];

/* Cyber Rescue's own account tracking is internal -- not a customer-facing growth
   signal, so it doesn't belong alongside the five actions above as a peer tile. It's
   reached through a separate toggle in the dashboard header instead. */
export const INTERNAL_ACTION: GaiaAction = {
  tab: "cr-tracker",
  number: 6,
  title: "Our accounts",
  subtitle: "Cyber Rescue's own tracking: who we haven't met, and who is overdue",
  explainer:
    "Internal view over Cyber Rescue's working spreadsheet: meetings coming up, who has gone longest without one, who has no next action planned.",
  payoff: "The follow-ups that quietly slip.",
};
