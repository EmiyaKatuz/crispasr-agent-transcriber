import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const PLUGIN_NAME = "crispasr-agent-transcriber";
export const GITHUB_REPOSITORY = "EmiyaKatuz/crispasr-agent-transcriber";

const packageDir = path.dirname(fileURLToPath(import.meta.url));
const packageJson = JSON.parse(
  fs.readFileSync(path.join(packageDir, "..", "package.json"), "utf8"),
);

export const PACKAGE_NAME = packageJson.name;
export const PACKAGE_VERSION = packageJson.version;

export const MODEL_SPECS = [
  {
    purpose: "English transcription",
    filename: "cohere-transcribe.gguf",
    url: "https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF",
  },
  {
    purpose: "Chinese transcription",
    filename: "qwen3-asr-1.7b-q4_k.gguf",
    url: "https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF",
  },
  {
    purpose: "English/Chinese language detection",
    filename: "firered-lid-q2_k.gguf",
    url: "https://huggingface.co/cstr/firered-lid-GGUF",
  },
];

export const MANAGED_ENTRIES = [
  ".codex-plugin",
  ".mcp.json",
  ".venv",
  "AGENTS.md",
  "LICENSE",
  "README.md",
  "assets",
  "docs",
  "mcp_server",
  "pyproject.toml",
  "scripts",
  "skills",
  "src",
  "uv.lock",
];

export function defaultTargetDir(homeDir = os.homedir()) {
  return path.join(homeDir, "plugins", PLUGIN_NAME);
}

export function defaultMarketplacePath(homeDir = os.homedir()) {
  return path.join(homeDir, ".agents", "plugins", "marketplace.json");
}

export function defaultReleaseBase() {
  return (
    process.env.CRISPASR_INSTALLER_RELEASE_BASE ||
    `https://github.com/${GITHUB_REPOSITORY}/releases/download`
  );
}
