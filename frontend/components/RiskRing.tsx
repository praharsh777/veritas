"use client";
import { useCountUp, useMounted } from "@/lib/hooks";

/** Circular gauge that draws itself and counts up. `tone` is a Tailwind text-* class used via currentColor. */
export default function RiskRing({ value, tone, label, size = 150 }: { value: number; tone: string; label: string; size?: number }) {
  const mounted = useMounted(150);
  const shown = useCountUp(value, 1100, 150);
  const r = 54;
  const c = 2 * Math.PI * r;
  const offset = mounted ? c * (1 - value / 100) : c;
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }} role="meter" aria-label={label} aria-valuenow={value} aria-valuemin={0} aria-valuemax={100}>
      <svg viewBox="0 0 128 128" width={size} height={size} className="-rotate-90">
        <circle cx="64" cy="64" r={r} fill="none" stroke="rgb(var(--ink-600))" strokeWidth="9" opacity=".7" />
        <circle
          cx="64" cy="64" r={r} fill="none" stroke="currentColor" strokeWidth="9" strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={offset}
          className={`${tone} transition-[stroke-dashoffset] duration-[1200ms] ease-out`}
          style={{ filter: "drop-shadow(0 0 6px currentColor)" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <div className={`font-mono text-4xl font-bold leading-none ${tone}`}>{shown}</div>
          <div className="mt-1 text-[11px] font-semibold uppercase tracking-wider text-mist-400">{label}</div>
        </div>
      </div>
    </div>
  );
}
