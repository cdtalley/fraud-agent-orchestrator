/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Orbitron", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        void: "#030508",
        cyan: { neon: "#00f5ff", dim: "rgba(0,245,255,0.12)" },
        magenta: { neon: "#ff2bd6", dim: "rgba(255,43,214,0.12)" },
        panel: "rgba(6, 14, 28, 0.55)",
      },
      boxShadow: {
        neon: "0 0 20px rgba(0,245,255,0.35), 0 0 60px rgba(255,43,214,0.15)",
        panel: "inset 0 1px 0 rgba(255,255,255,0.06), 0 0 0 1px rgba(0,245,255,0.15)",
      },
      animation: {
        pulseSlow: "pulseSlow 4s ease-in-out infinite",
        drift: "drift 18s ease-in-out infinite",
        flicker: "flicker 4s linear infinite",
      },
      keyframes: {
        pulseSlow: {
          "0%, 100%": { opacity: "0.5" },
          "50%": { opacity: "1" },
        },
        drift: {
          "0%, 100%": { transform: "translate(0,0) scale(1)" },
          "50%": { transform: "translate(-2%, 1%) scale(1.02)" },
        },
        flicker: {
          "0%, 100%": { opacity: "1" },
          "48%": { opacity: "1" },
          "49%": { opacity: "0.85" },
          "50%": { opacity: "0.95" },
          "51%": { opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
