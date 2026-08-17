import { CustomerLogo } from "./CustomerLogo";
import type { ViewMode } from "./BoardControls";
import { LiveIcon, MockupIcon, ResearchedIcon, SampleIcon } from "./icons";
import { InfoPopover } from "./InfoPopover";
import type { DataSource, Sentiment } from "../types";

/** The fields Ticket actually renders -- a structural subset of OpportunityCard, so
 * other views (Today) can build one from whatever shape they have without needing to
 * fabricate recipient/subject/body fields a real board card carries but a ticket
 * never displays. */
export interface TicketData {
  customer_name: string;
  data_source: DataSource;
  source_detail: string | null;
  concept_trigger: string | null;
  badge: string | null;
  value: string;
  label: string;
  sentiment: Sentiment;
  description: string;
  detail: string | null;
  detected_at: string;
}

export function relTime(iso: string): string {
  const then = new Date(iso + "T00:00:00");
  if (Number.isNaN(then.getTime())) return "";
  const diffDays = Math.round((then.getTime() - Date.now()) / 86_400_000);
  if (diffDays === 0) return "today";
  if (diffDays > 0) return `in ${diffDays} day${diffDays === 1 ? "" : "s"}`;
  const past = Math.abs(diffDays);
  return `${past} day${past === 1 ? "" : "s"} ago`;
}

/** The same card shell used across the app -- the Opportunities board, and (visually
 * only) Today's worklist -- so a signal looks like the same kind of thing wherever a
 * CSM sees it. */
export function OpportunityTicket({
  card,
  domain,
  viewMode,
  actioned,
  onOpen,
}: {
  card: TicketData;
  domain: string;
  viewMode: ViewMode;
  actioned: boolean;
  onOpen: () => void;
}) {
  const showDetailInline = viewMode === "detailed" && card.detail;
  const showDetailPopover = viewMode !== "detailed" && viewMode !== "compact" && card.detail;

  return (
    <article
      className="opp-ticket"
      tabIndex={0}
      role="button"
      data-actioned={actioned}
      data-source={card.data_source}
      aria-label={`Open drafted email for ${card.customer_name}`}
      onClick={onOpen}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onOpen();
        }
      }}
    >
      <div className="opp-ticket-top">
        <span className="opp-ticket-account">
          <CustomerLogo domain={domain} name={card.customer_name} size={16} />
          {card.customer_name}
        </span>
        <span className="opp-ticket-source" onClick={(e) => e.stopPropagation()}>
          {card.data_source === "live" && (
            <InfoPopover
              label="Where this data comes from"
              align="right"
              icon={<LiveIcon style={{ color: "var(--moss)" }} />}
            >
              <span className="opp-source-pop-head">Live — SecurityScorecard API</span>
              {card.source_detail}
            </InfoPopover>
          )}
          {card.data_source === "researched" && (
            <InfoPopover
              label="Where this data comes from"
              align="right"
              icon={<ResearchedIcon style={{ color: "var(--petrol)" }} />}
            >
              <span className="opp-source-pop-head">Researched — assembled, then cached</span>
              {card.source_detail}
            </InfoPopover>
          )}
          {card.data_source === "sample" && (
            <InfoPopover
              label="Where this data comes from"
              align="right"
              icon={<SampleIcon style={{ color: "var(--slate)" }} />}
            >
              <span className="opp-source-pop-head">Sample data — placeholder</span>
              {card.source_detail}
            </InfoPopover>
          )}
          {card.data_source === "concept" && (
            <InfoPopover
              label="Not built — proposed source"
              align="right"
              icon={<span className="opp-concept-tag">⚑</span>}
            >
              <span className="opp-source-pop-head">
                Not built — concept{card.concept_trigger ? ` · Trigger ${card.concept_trigger}` : ""}
              </span>
              {card.source_detail}
            </InfoPopover>
          )}
          {card.data_source === "mockup" && (
            <InfoPopover
              label="Mockup — source not yet integrated"
              align="right"
              icon={<MockupIcon style={{ color: "var(--petrol)" }} />}
            >
              <span className="opp-source-pop-head">Mockup — not yet integrated</span>
              {card.source_detail}
            </InfoPopover>
          )}
        </span>
      </div>
      {card.badge && <span className="opp-ticket-badge">{card.badge}</span>}
      <div className="opp-ticket-metric">
        <span className={`opp-metric-value sent-${card.sentiment}`}>{card.value}</span>
        <span className="opp-metric-sub">{card.label}</span>
      </div>
      <div className="opp-ticket-desc">
        {card.description}
        {showDetailPopover && (
          <span className="opp-ticket-desc-info" onClick={(e) => e.stopPropagation()}>
            <InfoPopover label="Click for more info" align="right">
              {card.detail}
            </InfoPopover>
          </span>
        )}
      </div>
      {showDetailInline && <p className="opp-ticket-detail">{card.detail}</p>}
      <div className="opp-ticket-foot">
        <time dateTime={card.detected_at}>{relTime(card.detected_at)}</time>
        <span className="opp-ticket-cta">Click to take action →</span>
      </div>
    </article>
  );
}
