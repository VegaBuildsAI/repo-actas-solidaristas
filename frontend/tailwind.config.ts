import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#15141C",
        indigo: {
          DEFAULT: "#4B457B",
          dk: "#3A3560",
        },
        blue: {
          DEFAULT: "#41AAFD",
          dk: "#2E6FB8",
        },
        bg: "#FAFAFC",
        panel: "#FFFFFF",
        border: "#EAEAF0",
        sidebar: "#1C1B26",
        "sidebar-active": "#2C2B3A",
      },
    },
  },
  plugins: [],
} satisfies Config;
