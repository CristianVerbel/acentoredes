import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        positive: "#16a34a",
        negative: "#dc2626",
        neutral: "#94a3b8",
        ink: "#0f172a",
        panel: "#111827",
      },
    },
  },
  plugins: [],
};

export default config;
