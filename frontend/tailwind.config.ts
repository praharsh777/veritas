import type { Config } from "tailwindcss";

const v = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

// All colors come from CSS variables (see globals.css) so the dark/light themes swap instantly.
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { 950: v("ink-950"), 900: v("ink-900"), 800: v("ink-800"), 700: v("ink-700"), 600: v("ink-600"), 500: v("ink-500") },
        mist: { 100: v("mist-100"), 300: v("mist-300"), 400: v("mist-400"), 500: v("mist-500") },
        brand: { 400: v("brand-400"), 500: v("brand-500"), 600: v("brand-600") },
        risk: { high: v("risk-high"), mid: v("risk-mid"), low: v("risk-low") },
        prov: { obs: v("prov-obs"), rule: v("prov-rule"), ext: v("prov-ext"), ai: v("prov-ai") },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      keyframes: {
        fadeUp: { "0%": { opacity: "0", transform: "translateY(10px)" }, "100%": { opacity: "1", transform: "none" } },
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideIn: { "0%": { transform: "translateX(100%)" }, "100%": { transform: "none" } },
        float: { "0%,100%": { transform: "translate3d(0,0,0)" }, "50%": { transform: "translate3d(0,-18px,0)" } },
        floatSlow: { "0%,100%": { transform: "translate3d(0,0,0)" }, "50%": { transform: "translate3d(14px,10px,0)" } },
        shimmer: { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
        gradientShift: { "0%,100%": { backgroundPosition: "0% 50%" }, "50%": { backgroundPosition: "100% 50%" } },
        pulseRing: { "0%": { boxShadow: "0 0 0 0 rgb(var(--risk-high) / .45)" }, "100%": { boxShadow: "0 0 0 14px rgb(var(--risk-high) / 0)" } },
        pop: { "0%": { transform: "scale(.92)", opacity: "0" }, "100%": { transform: "scale(1)", opacity: "1" } },
        scan: { "0%": { transform: "translateY(-100%)" }, "100%": { transform: "translateY(400%)" } },
      },
      animation: {
        fadeUp: "fadeUp .5s cubic-bezier(.2,.7,.2,1) both",
        fadeIn: "fadeIn .35s ease both",
        slideIn: "slideIn .3s cubic-bezier(.2,.7,.2,1) both",
        float: "float 8s ease-in-out infinite",
        floatSlow: "floatSlow 11s ease-in-out infinite",
        shimmer: "shimmer 1.6s linear infinite",
        gradientShift: "gradientShift 8s ease infinite",
        pulseRing: "pulseRing 1.8s ease-out infinite",
        pop: "pop .35s cubic-bezier(.2,.9,.3,1.2) both",
        scan: "scan 2.4s linear infinite",
      },
    },
  },
  plugins: [],
};
export default config;
