import type { SVGProps } from "react";

/** Small, single-purpose inline icons -- kept intentionally simple so a glance reads
 * the meaning (live vs. sample vs. concept, info, link, search) without a caption. */

export function LiveIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true" {...props}>
      <circle cx="5" cy="5" r="4.5" fill="currentColor" />
    </svg>
  );
}

export function ResearchedIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true" {...props}>
      <path d="M5 0.5 6.1 3.6 9.5 3.8 6.8 5.9 7.7 9.3 5 7.3 2.3 9.3 3.2 5.9 0.5 3.8 3.9 3.6Z" fill="currentColor" />
    </svg>
  );
}

export function SampleIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true" {...props}>
      <rect x="0.75" y="0.75" width="8.5" height="8.5" rx="1.5" stroke="currentColor" strokeWidth="1.3" strokeDasharray="2.3 2" />
    </svg>
  );
}

export function ConceptIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true" {...props}>
      <path d="M2 1.5v9M2 1.5h6.5L7 4l1.5 2.5H2" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" />
    </svg>
  );
}

export function InfoIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.4" />
      <rect x="7.15" y="6.6" width="1.7" height="5.4" rx="0.6" fill="currentColor" />
      <circle cx="8" cy="4.3" r="1" fill="currentColor" />
    </svg>
  );
}

export function ExternalLinkIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <path
        d="M6.5 3.5H3.5A1 1 0 0 0 2.5 4.5V12.5A1 1 0 0 0 3.5 13.5H11.5A1 1 0 0 0 12.5 12.5V9.5"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
      <path d="M9 2.5H13.5V7M13.5 2.5 7.5 8.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function SearchIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true" {...props}>
      <circle cx="7" cy="7" r="4.5" stroke="currentColor" strokeWidth="1.4" />
      <path d="M13.5 13.5 10.3 10.3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export function ChevronDownIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true" {...props}>
      <path d="M2.5 4.5 6 8l3.5-3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function CloseIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true" {...props}>
      <path d="M2 2l8 8M10 2l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}
