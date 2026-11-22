import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const videoPath = join(__dirname, "VIDEO.json");
const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

function validateTiktokUrl(data: Record<string, unknown>): void {
  if (typeof data.url !== "string" || !data.url.startsWith("https://www.tiktok.com/")) {
    const received = typeof data.url === "string" ? data.url : String(data.url);
    throw new Error(
      `VIDEO.json must contain a "url" string beginning with "https://www.tiktok.com/"; received ${received}`,
    );
  }
}

const raw = readFileSync(videoPath, "utf8");
const data = JSON.parse(raw);

validateTiktokUrl(data);

mkdirSync(outputDir, { recursive: true });
writeFileSync(join(outputDir, "VIDEO.json"), raw);