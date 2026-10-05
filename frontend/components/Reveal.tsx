"use client";
import { useInView } from "@/lib/hooks";

/** Fades/slides children in when scrolled into view. `delay` is in ms (for staggering). */
export default function Reveal({ children, delay = 0, className = "" }: { children: React.ReactNode; delay?: number; className?: string }) {
  const [ref, seen] = useInView<HTMLDivElement>();
  return (
    <div ref={ref} className={`reveal ${seen ? "in" : ""} ${className}`} style={{ transitionDelay: seen ? `${delay}ms` : "0ms" }}>
      {children}
    </div>
  );
}
