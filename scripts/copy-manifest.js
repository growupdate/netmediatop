import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const projectDirectory = process.cwd();
const sourcePath = resolve(projectDirectory, "public/.well-known/ard.json");
const outputDirectory = resolve(projectDirectory, "dist");
const wellKnownDirectory = resolve(outputDirectory, ".well-known");
const manifest = readFileSync(sourcePath, "utf8");
const parsedManifest = JSON.parse(manifest);

if (!Array.isArray(parsedManifest.entries)) {
  throw new Error("ARD manifest harus memiliki properti entries berupa array.");
}

mkdirSync(wellKnownDirectory, { recursive: true });
writeFileSync(resolve(wellKnownDirectory, "ard.json"), manifest);
writeFileSync(resolve(outputDirectory, "ai-catalog.json"), manifest);

console.log("ARD manifest disiapkan di dist/.well-known/ard.json");
console.log("Katalog kompatibilitas ARD disiapkan di dist/ai-catalog.json");
