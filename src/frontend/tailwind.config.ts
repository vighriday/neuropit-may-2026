import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        "apex-black": "#0a0a0a",
        "apex-surface": "#131313",
        "apex-red": "#ff1801",
        "apex-cyan": "#00f0ff",
        "apex-amber": "#ffb800",
        "neuropit-black": "#050505",
        "neuropit-dark": "#0f1115",
        "neuropit-panel": "#13161c",
        "neuropit-red": "#ff1801",
        "neuropit-amber": "#ffb800",
        "neuropit-emerald": "#00f0ff",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        display: ["Archivo Narrow", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
