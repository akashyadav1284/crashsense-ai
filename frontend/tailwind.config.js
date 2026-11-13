/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080B14",
        sidebar: "#0D1220",
        card: "#111827",
        border: "#263247",
        primary: {
          DEFAULT: "#7C5CFC",
          hover: "#6B46F5",
        },
        secondary: {
          DEFAULT: "#3B82F6",
          hover: "#2563EB",
        },
        success: "#16A34A",
        warning: "#F59E0B",
        danger: "#EF4444",
        foreground: "#F8FAFC",
        muted: "#94A3B8",
        surface: {
          DEFAULT: "#0F1629",
          muted: "#161F38",
          border: "#1F2C4C",
        },
        brand: {
          purple: "#7C3AED",
          cyan: "#06B6D4",
          blue: "#2563EB",
          neon: "#38BDF8",
        },
      },
    },
  },
  plugins: [],
};
