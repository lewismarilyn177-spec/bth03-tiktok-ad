import { copyFileSync, mkdirSync, readFileSync } from "node:fs";

// The deliverable of this entry is VIDEO.json: it names the TikTok video
// posted for this bounty. The house reads it from the repository and reads
// the video itself through its own reader; nothing this program writes to
// /output beyond the copy of VIDEO.json is used.
const repoVideoPath = new URL("./VIDEO.json", import.meta.url);
// Fail loudly if the video pointer is missing or malformed — the entry is
// worthless without it.
const parsed = JSON.parse(readFileSync(repoVideoPath, "utf8"));
if (typeof parsed.url !== "string" || !parsed.url.startsWith("https://www.tiktok.com/")) {
  throw new Error("VIDEO.json must name a https://www.tiktok.com/ video url");
}

const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
mkdirSync(outDir, { recursive: true });
copyFileSync(repoVideoPath, `${outDir}/VIDEO.json`);
console.log(`copied VIDEO.json (${parsed.url}) to ${outDir}`);
