/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#090d16",
        surface: "#0f172a",
        border: "#1e293b",
        accent: {
          blue: "#38bdf8",
          red: "#f43f5e",
          amber: "#f59e0b",
          emerald: "#10b981",
          purple: "#a855f7"
        }
      },
      animation: {
        pulse_fast: "pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        glow: "glow 2s ease-in-out infinite alternate"
      }
    },
  },
  plugins: [],
};
