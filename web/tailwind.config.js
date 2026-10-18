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
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        // One cool-gray family, tinted slightly blue
        ink: {
          950: "#0a0c0f",
          900: "#0f1216",
          850: "#13171c",
          800: "#191e24",
          700: "#232a32",
          600: "#323a44",
          500: "#535d69",
          400: "#7b8590",
          300: "#a3abb4",
          200: "#cbd0d6",
          100: "#e7e9ec",
        },
        // Single brand accent: where the agents are looking
        focus: {
          DEFAULT: "#7fb2e5",
          dim: "#7fb2e51f",
        },
        // Status semantics only, never decoration
        crit: { DEFAULT: "#e5534b", dim: "#e5534b1f" },
        warn: { DEFAULT: "#d9a440", dim: "#d9a4401f" },
        ok: { DEFAULT: "#57ab5a", dim: "#57ab5a1f" },
        anom: { DEFAULT: "#d9774b", dim: "#d9774b1f" },
      },
      fontSize: {
        "2xs": ["0.6875rem", { lineHeight: "1rem" }],
      },
      zIndex: {
        flyout: "20",
        drawer: "40",
        modal: "50",
        grain: "60",
      },
      transitionTimingFunction: {
        spring: "cubic-bezier(0.32, 0.72, 0, 1)",
      },
    },
  },
  plugins: [],
};
