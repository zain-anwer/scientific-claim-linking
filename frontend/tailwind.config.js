import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Forwards /api/* → http://127.0.0.1:8000/*
      // Strips the /api prefix so FastAPI routes stay unchanged.
      // e.g. POST /api/query in the frontend hits POST /query on FastAPI.
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});