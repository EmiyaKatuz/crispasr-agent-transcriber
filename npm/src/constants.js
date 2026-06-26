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
    id: "english-q4",
    role: "english",
    purpose: "English transcription",
    filename: "cohere-transcribe-q4_k.gguf",
    quantization: "q4_k",
    recommended: true,
    repo: "cstr/cohere-transcribe-03-2026-GGUF",
    description: "Default English model with lower disk and memory use.",
  },
  {
    id: "english-q5-0",
    role: "english",
    purpose: "English transcription",
    filename: "cohere-transcribe-q5_0.gguf",
    quantization: "q5_0",
    recommended: false,
    repo: "cstr/cohere-transcribe-03-2026-GGUF",
    description: "Higher quality English option than q4_k.",
  },
  {
    id: "english-q5-1",
    role: "english",
    purpose: "English transcription",
    filename: "cohere-transcribe-q5_1.gguf",
    quantization: "q5_1",
    recommended: false,
    repo: "cstr/cohere-transcribe-03-2026-GGUF",
    description: "Alternate q5 English quantization.",
  },
  {
    id: "english-q6",
    role: "english",
    purpose: "English transcription",
    filename: "cohere-transcribe-q6_k.gguf",
    quantization: "q6_k",
    recommended: false,
    repo: "cstr/cohere-transcribe-03-2026-GGUF",
    description: "Larger English model for quality-focused local use.",
  },
  {
    id: "english-q8",
    role: "english",
    purpose: "English transcription",
    filename: "cohere-transcribe-q8_0.gguf",
    quantization: "q8_0",
    recommended: false,
    repo: "cstr/cohere-transcribe-03-2026-GGUF",
    description: "Large English model with less quantization.",
  },
  {
    id: "english-f16",
    role: "english",
    purpose: "English transcription",
    filename: "cohere-transcribe.gguf",
    quantization: "f16",
    recommended: false,
    repo: "cstr/cohere-transcribe-03-2026-GGUF",
    description: "Largest English option from the upstream GGUF repo.",
  },
  {
    id: "chinese-q4",
    role: "chinese",
    purpose: "Chinese transcription",
    filename: "qwen3-asr-1.7b-q4_k.gguf",
    quantization: "q4_k",
    recommended: true,
    repo: "cstr/qwen3-asr-1.7b-GGUF",
    description: "Default Chinese model with practical disk and memory use.",
  },
  {
    id: "chinese-q8",
    role: "chinese",
    purpose: "Chinese transcription",
    filename: "qwen3-asr-1.7b-q8_0.gguf",
    quantization: "q8_0",
    recommended: false,
    repo: "cstr/qwen3-asr-1.7b-GGUF",
    description: "Larger Chinese model with less quantization.",
  },
  {
    id: "chinese-f16",
    role: "chinese",
    purpose: "Chinese transcription",
    filename: "qwen3-asr-1.7b-f16.gguf",
    quantization: "f16",
    recommended: false,
    repo: "cstr/qwen3-asr-1.7b-GGUF",
    description: "Largest Chinese option from the upstream GGUF repo.",
  },
  {
    id: "lid-q2",
    role: "lid",
    purpose: "English/Chinese language detection",
    filename: "firered-lid-q2_k.gguf",
    quantization: "q2_k",
    recommended: false,
    repo: "cstr/firered-lid-GGUF",
    description: "Smallest local language-detection option.",
  },
  {
    id: "lid-q4",
    role: "lid",
    purpose: "English/Chinese language detection",
    filename: "firered-lid-q4_k.gguf",
    quantization: "q4_k",
    recommended: true,
    repo: "cstr/firered-lid-GGUF",
    description: "Default local language-detection model.",
  },
  {
    id: "lid-q8",
    role: "lid",
    purpose: "English/Chinese language detection",
    filename: "firered-lid-q8_0.gguf",
    quantization: "q8_0",
    recommended: false,
    repo: "cstr/firered-lid-GGUF",
    description: "Larger language-detection option with less quantization.",
  },
  {
    id: "lid-f16",
    role: "lid",
    purpose: "English/Chinese language detection",
    filename: "firered-lid-f16.gguf",
    quantization: "f16",
    recommended: false,
    repo: "cstr/firered-lid-GGUF",
    description: "Largest language-detection option from the upstream GGUF repo.",
  },
].map((model) => ({
  ...model,
  url: `https://huggingface.co/${model.repo}`,
  downloadUrl: `https://huggingface.co/${model.repo}/resolve/main/${model.filename}`,
}));

export const RECOMMENDED_MODEL_IDS = MODEL_SPECS.filter((model) => model.recommended).map(
  (model) => model.id,
);

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
