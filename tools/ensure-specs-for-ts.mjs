import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname } from "node:path";
import { globSync } from "glob";

const TS_GLOB = "src/**/*.ts";

const IGNORE = [
  "**/*.spec.ts",
  "**/*.d.ts",
  "**/node_modules/**",
  "**/dist/**",
  "**/coverage/**",
  "**/main.ts",
  "**/polyfills.ts",
  "**/test.ts",
  "**/environment*.ts",
  "**/*.routes.ts",
  "**/*.config.ts",
  "**/*.module.ts"
];

const files = globSync(TS_GLOB, { ignore: IGNORE });

let created = 0;

for (const file of files) {
  const spec = file.replace(/\.ts$/, ".spec.ts");
  if (existsSync(spec)) continue;

  mkdirSync(dirname(spec), { recursive: true });

  writeFileSync(
    spec,
    `// Auto-created placeholder spec for ${file}\n`,
    "utf-8"
  );

  console.log(`Created: ${spec}`);
  created++;
}

console.log(`\nDone. Created ${created} missing spec files.`);