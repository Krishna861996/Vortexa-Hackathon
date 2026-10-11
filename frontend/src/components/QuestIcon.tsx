import type { Difficulty } from "@/lib/api";

export type IconName = "lock" | "arrow" | "check" | "spark" | "leaf" | "layers" | "mountain" | "diamond" | "terminal" | "branch" | "text" | "loop" | "list" | "flag" | "medal" | "compass";
const paths: Record<IconName, React.ReactNode> = {
  lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2" /></>,
  arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
  check: <path d="m5 12 4 4L19 6" />,
  spark: <><path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z" /><path d="M20 3v4m-2-2h4" /></>,
  leaf: <><path d="M20 4C8 2 2 10 6 17c7 4 15-2 14-13Z" /><path d="m4 20 11-11" /></>,
  layers: <><path d="m12 3 9 5-9 5-9-5Z" /><path d="m3 12 9 5 9-5M3 16l9 5 9-5" /></>,
  mountain: <><path d="m2 20 7-13 4 6 3-9 6 16Z" /><path d="m14 10 2 2 2-2" /></>,
  diamond: <><path d="m3 8 4-5h10l4 5-9 13Z" /><path d="M3 8h18M7 3l5 18 5-18" /></>,
  terminal: <><rect x="3" y="4" width="18" height="16" rx="3" /><path d="m7 9 3 3-3 3m6 0h4" /></>,
  branch: <><circle cx="6" cy="5" r="2" /><circle cx="18" cy="6" r="2" /><circle cx="6" cy="19" r="2" /><path d="M6 7v10m0-4c8 0 12-1 12-5" /></>,
  text: <><path d="M4 5h16M12 5v14m-4 0h8M4 5v3m16-3v3" /></>,
  loop: <><path d="M20 8a8 8 0 0 0-13-3L4 8m0-5v5h5M4 16a8 8 0 0 0 13 3l3-3m0 5v-5h-5" /></>,
  list: <><path d="M9 6h11M9 12h11M9 18h11" /><circle cx="4" cy="6" r=".7" /><circle cx="4" cy="12" r=".7" /><circle cx="4" cy="18" r=".7" /></>,
  flag: <><path d="M5 21V3m0 0c5-3 9 3 14 0v10c-5 3-9-3-14 0" /></>,
  medal: <><circle cx="12" cy="9" r="6" /><path d="m8 14-2 7 6-3 6 3-2-7m-4-16 1.1 2.2 2.4.4-1.8 1.7.4 2.5L12 10l-2.1 1.2.4-2.5-1.8-1.7 2.4-.4Z" /></>,
  compass: <><circle cx="12" cy="12" r="9" /><path d="m16 8-2 6-6 2 2-6Z" /></>,
};
export function QuestIcon({ name, className = "h-5 w-5" }: { name: IconName; className?: string }) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">{paths[name]}</svg>;
}
export const difficultyIcons: Record<Difficulty, IconName> = { beginner: "leaf", easy: "spark", medium: "layers", hard: "mountain", advanced: "diamond" };
export const challengeIcons: Record<string, IconName> = { "add-numbers": "terminal", "is-even": "branch", "reverse-text": "text", "count-vowels": "compass", "sum-list": "list", "fizz-buzz": "loop" };

export function PythonMark({ className = "h-10 w-10" }: { className?: string }) {
  return <svg viewBox="0 0 128 128" className={className} aria-hidden="true"><linearGradient id="python-original-a" gradientUnits="userSpaceOnUse" x1="70.252" y1="1237.476" x2="170.659" y2="1151.089" gradientTransform="matrix(.563 0 0 -.568 -29.215 707.817)"><stop offset="0" stopColor="#5A9FD4"/><stop offset="1" stopColor="#306998"/></linearGradient><linearGradient id="python-original-b" gradientUnits="userSpaceOnUse" x1="209.474" y1="1098.811" x2="173.62" y2="1149.537" gradientTransform="matrix(.563 0 0 -.568 -29.215 707.817)"><stop offset="0" stopColor="#FFD43B"/><stop offset="1" stopColor="#FFE873"/></linearGradient><path fill="url(#python-original-a)" d="M63.391 1.988c-4.222.02-8.252.379-11.8 1.007-10.45 1.846-12.346 5.71-12.346 12.837v9.411h24.693v3.137H29.977c-7.176 0-13.46 4.313-15.426 12.521-2.268 9.405-2.368 15.275 0 25.096 1.755 7.311 5.947 12.519 13.124 12.519h8.491V67.234c0-8.151 7.051-15.34 15.426-15.34h24.665c6.866 0 12.346-5.654 12.346-12.548V15.833c0-6.693-5.646-11.72-12.346-12.837-4.244-.706-8.645-1.027-12.866-1.008zM50.037 9.557c2.55 0 4.634 2.117 4.634 4.721 0 2.593-2.083 4.69-4.634 4.69-2.56 0-4.633-2.097-4.633-4.69-.001-2.604 2.073-4.721 4.633-4.721z" transform="translate(0 10.26)"/><path fill="url(#python-original-b)" d="M91.682 28.38v10.966c0 8.5-7.208 15.655-15.426 15.655H51.591c-6.756 0-12.346 5.783-12.346 12.549v23.515c0 6.691 5.818 10.628 12.346 12.547 7.816 2.297 15.312 2.713 24.665 0 6.216-1.801 12.346-5.423 12.346-12.547v-9.412H63.938v-3.138h37.012c7.176 0 9.852-5.005 12.348-12.519 2.578-7.735 2.467-15.174 0-25.096-1.774-7.145-5.161-12.521-12.348-12.521h-9.268zM77.809 87.927c2.561 0 4.634 2.097 4.634 4.692 0 2.602-2.074 4.719-4.634 4.719-2.55 0-4.633-2.117-4.633-4.719 0-2.595 2.083-4.692 4.633-4.692z" transform="translate(0 10.26)"/><radialGradient id="python-original-c" cx="1825.678" cy="444.45" r="26.743" gradientTransform="matrix(0 -.24 -1.055 0 532.979 557.576)" gradientUnits="userSpaceOnUse"><stop offset="0" stopColor="#B8B8B8" stopOpacity=".498"/><stop offset="1" stopColor="#7F7F7F" stopOpacity="0"/></radialGradient><path opacity=".444" fill="url(#python-original-c)" d="M97.309 119.597c0 3.543-14.816 6.416-33.091 6.416-18.276 0-33.092-2.873-33.092-6.416 0-3.544 14.815-6.417 33.092-6.417 18.275 0 33.091 2.872 33.091 6.417z"/></svg>;
}
