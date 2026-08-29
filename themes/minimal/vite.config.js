import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  build: {
    outDir: resolve(__dirname, "../../static/themes/minimal"),
    emptyOutDir: false,
    manifest: true,
    rollupOptions: {
      input: {
        theme: resolve(__dirname, "src/main.js"),
      },
      output: {
        entryFileNames: "js/[name].js",
        chunkFileNames: "js/[name]-[hash].js",
        assetFileNames: ({ name }) => {
          if (name && name.endsWith(".css")) return "css/theme.css";
          return "assets/[name][extname]";
        },
      },
    },
  },
  server: {
    origin: "http://localhost:5175",
  },
});
