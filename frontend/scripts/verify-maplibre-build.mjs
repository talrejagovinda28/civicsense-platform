import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = join(dirname(fileURLToPath(import.meta.url)), "..");
const workerPath = join(frontendRoot, "public", "maplibre", "maplibre-gl-csp-worker.js");
const chunksDir = join(frontendRoot, ".next", "static", "chunks");

if (!existsSync(workerPath)) {
  console.error("Missing worker file:", workerPath);
  process.exit(1);
}

if (!existsSync(chunksDir)) {
  console.error("Missing build output. Run npm run build first.");
  process.exit(1);
}

let foundWorkerUrl = false;
let foundBadWorkerUrl = false;

function walk(dir) {
  for (const entry of readdirSync(dir)) {
    const fullPath = join(dir, entry);
    if (statSync(fullPath).isDirectory()) {
      walk(fullPath);
      continue;
    }
    if (!entry.endsWith(".js")) {
      continue;
    }
    const source = readFileSync(fullPath, "utf8");
    if (source.includes("unpkg.com/maplibre-gl")) {
      foundBadWorkerUrl = true;
      console.error("Found unpkg worker URL in", fullPath);
    }
    if (source.includes("/maplibre/maplibre-gl-csp-worker.js")) {
      foundWorkerUrl = true;
    }
  }
}

walk(chunksDir);

if (foundBadWorkerUrl) {
  process.exit(1);
}

if (!foundWorkerUrl) {
  console.error("Expected self-hosted MapLibre worker URL in client chunks.");
  process.exit(1);
}

console.log("MapLibre build verification passed.");
