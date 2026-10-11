import type { ReactNode } from "react";

interface StatusStateProps {
  title: string;
  description: string;
  action?: ReactNode;
  tone?: "neutral" | "error";
}

export function StatusState({ title, description, action, tone = "neutral" }: StatusStateProps) {
  return (
    <div className={`state-card ${tone === "error" ? "state-card-error" : ""}`} role={tone === "error" ? "alert" : "status"}>
      <span className={`mb-5 flex h-11 w-11 items-center justify-center rounded-xl ${tone === "error" ? "bg-rose-400/10 text-rose-300" : "bg-lime-300/10 text-lime-300"}`} aria-hidden="true">
        {tone === "error" ? "!" : "<>"}
      </span>
      <h2 className="text-xl font-semibold text-white">{title}</h2>
      <p className="mt-2 max-w-lg text-sm leading-6 text-slate-400">{description}</p>
      {action ? <div className="mt-6">{action}</div> : null}
    </div>
  );
}
