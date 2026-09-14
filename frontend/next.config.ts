import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "standalone",
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      // Use the CSP build so the self-hosted csp-worker.js is protocol-compatible.
      "maplibre-gl": path.resolve(
        process.cwd(),
        "node_modules/maplibre-gl/dist/maplibre-gl-csp.js",
      ),
    };
    return config;
  },
};

export default nextConfig;
