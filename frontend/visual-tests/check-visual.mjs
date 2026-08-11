import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const ROOT = process.cwd();
const filter = process.argv[2] ?? null;

const runNode = (scriptPath, args = []) => {
  const result = spawnSync(process.execPath, [scriptPath, ...args], {
    cwd: ROOT,
    stdio: "inherit",
    shell: false,
  });

  if (result.error) {
    throw result.error;
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
};

const playwrightCli = path.join(
  ROOT,
  "node_modules",
  "@playwright",
  "test",
  "cli.js",
);

const comparator = path.join(ROOT, "visual-tests", "compare-visual.mjs");

if (!fs.existsSync(playwrightCli)) {
  throw new Error(`Playwright CLI not found:\n${playwrightCli}`);
}

if (!fs.existsSync(comparator)) {
  throw new Error(`Comparator not found:\n${comparator}`);
}

console.log("");
console.log("VISUAL CHECK");
console.log(filter ? `Filter: ${filter}` : "Filter: all");
console.log("");

console.log("1/2 React capture");
runNode(playwrightCli, ["test", "visual-tests/smoke.spec.ts"]);

console.log("");
console.log("2/2 Figma comparison");

const compareArgs = [];

if (filter) {
  compareArgs.push(`--filter=${filter}`);
}

runNode(comparator, compareArgs);
