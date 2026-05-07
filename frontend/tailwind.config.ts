import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#18201f",
        paper: "#f7f4ec",
        panel: "#fffdf7",
        line: "#d7d0c1",
        risk: "#b93f35",
        amber: "#b26b2f",
        docket: "#315f72",
        sage: "#61715d"
      },
      boxShadow: {
        warroom: "0 16px 40px rgba(24,32,31,0.08)"
      }
    }
  },
  plugins: []
};

export default config;

