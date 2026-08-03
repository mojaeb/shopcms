import { resolve } from "node:path";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [tailwindcss()],
  // Django serves this theme under /static/themes/gohar/
  base: "/static/themes/gohar/",
  build: {
    outDir: resolve(__dirname, "../../static/themes/gohar"),
    emptyOutDir: true,
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
    origin: "http://localhost:5173",
  },
});
