/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        cyan: {
          400: "#22d3ee",
          500: "#00d4db",
          600: "#00b4c0",
        },
        dark: {
          DEFAULT: "#0a0f1e",
          surface: "#111827",
          card: "#1a2235",
          border: "#2a3450",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
