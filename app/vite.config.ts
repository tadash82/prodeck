import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    // o agente serve a PWA: o build sai direto no pacote Python
    outDir: "../agent/prodeck_agent/static",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/ws": { target: "ws://localhost:8710", ws: true },
      "/qr": "http://localhost:8710",
    },
  },
});
