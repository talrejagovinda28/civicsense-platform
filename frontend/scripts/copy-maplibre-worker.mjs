import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(scriptDir, "..");
const source = join(
  frontendRoot,
  "node_modules",
  "maplibre-gl",
  "dist",
  "maplibre-gl-csp-worker.js",
);
const targetDir = join(frontendRoot, "public", "maplibre");
const target = join(targetDir, "maplibre-gl-csp-worker.js");

mkdirSync(targetDir, { recursive: true });
copyFileSync(source, target);
console.log("Copied MapLibre CSP worker to public/maplibre/");
