"use client";
import { useEffect } from "react";
import { usePathname } from "next/navigation";

export function ScrollEffects() {
  const pathname = usePathname();
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const observed = new WeakSet<Element>();
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(({ target, isIntersecting }) => {
        if (!isIntersecting) return;
        target.classList.add("quest-enter");
        observer.unobserve(target);
      });
    }, { threshold: 0.08 });
    const scan = () => document.querySelectorAll("main .panel, main [data-reveal]").forEach((element) => {
      if (observed.has(element)) return;
      observed.add(element);
      observer.observe(element);
    });
    scan();
    const changes = new MutationObserver(scan);
    changes.observe(document.body, { childList: true, subtree: true });
    return () => { observer.disconnect(); changes.disconnect(); };
  }, [pathname]);
  return null;
}
