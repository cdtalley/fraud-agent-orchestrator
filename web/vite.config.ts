import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// When port 8000 is taken, run API on another port and set e.g. FRAUD_API_ORIGIN=http://127.0.0.1:8010
const fraudApiOrigin = process.env.FRAUD_API_ORIGIN ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: fraudApiOrigin,
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          three: ["three", "@react-three/fiber", "@react-three/drei"],
        },
      },
    },
    chunkSizeWarningLimit: 1200,
  },
});
