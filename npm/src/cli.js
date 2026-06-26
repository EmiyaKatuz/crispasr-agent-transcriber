import { PACKAGE_NAME, PACKAGE_VERSION } from "./constants.js";
import { InstallerError } from "./errors.js";
import { doctor, downloadModels, installPlugin, uninstallPlugin } from "./installer.js";

const HELP = `CrispASR Agent Transcriber installer

Usage:
  crispasr-agent-transcriber [install] [options]
  crispasr-agent-transcriber update [options]
  crispasr-agent-transcriber models [options]
  crispasr-agent-transcriber doctor [options]
  crispasr-agent-transcriber uninstall [options]

Commands:
  install      Install the Codex plugin, MCP dependencies, and CrispASR (default)
  update       Update plugin files and the GPU-preferred CrispASR binary
  models       Download approved local GGUF models into the plugin models directory
  doctor       Check prerequisites, plugin files, CrispASR, and local models
  uninstall    Remove managed plugin files and Codex registration

Options:
  --target-dir PATH       Plugin directory; use with --no-marketplace if custom
  --marketplace-path PATH Personal Codex marketplace.json path
  --release VERSION       Install a matching GitHub Release version
  --json                  Print stable JSON to stdout
  --dry-run               Show install/update actions without changing files
  --model-id ID           With models, download this model id; repeat for many
  --overwrite-models      With models, replace existing local model files
  --skip-crispasr         Do not install or update the CrispASR binary
  --skip-deps             Do not run uv sync
  --no-marketplace        Do not modify the Personal Codex marketplace
  --purge-data            With uninstall, also remove models, binaries, and outputs
  -v, --version           Print installer version
  -h, --help              Show this help

Models are never downloaded during install/update. Run the models command to
download the recommended local English, Chinese, and language-detection bundle.
`;

function parseArgs(argv) {
  const options = {};
  let command = null;
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (["install", "update", "models", "doctor", "uninstall"].includes(value) && !command) {
      command = value;
      continue;
    }
    if (value === "--json") options.json = true;
    else if (value === "--dry-run") options.dryRun = true;
    else if (value === "--skip-crispasr") options.skipCrispASR = true;
    else if (value === "--skip-deps") options.skipDependencies = true;
    else if (value === "--no-marketplace") options.skipMarketplace = true;
    else if (value === "--purge-data") options.purgeData = true;
    else if (value === "--overwrite-models") options.overwrite = true;
    else if (value === "--help" || value === "-h") options.help = true;
    else if (value === "--version" || value === "-v") options.version = true;
    else if (["--target-dir", "--marketplace-path", "--release", "--model-id"].includes(value)) {
      const next = argv[index + 1];
      if (!next || next.startsWith("--")) {
        throw new InstallerError(`${value} requires a value.`, "invalid_arguments");
      }
      index += 1;
      if (value === "--target-dir") options.targetDir = next;
      if (value === "--marketplace-path") options.marketplacePath = next;
      if (value === "--release") options.releaseVersion = next.replace(/^v/, "");
      if (value === "--model-id") {
        options.modelIds ||= [];
        options.modelIds.push(next);
      }
    } else {
      throw new InstallerError(`Unknown argument: ${value}`, "invalid_arguments");
    }
  }
  return { command: command || "install", options };
}

function printHumanResult(result) {
  if (result.dryRun) {
    process.stdout.write(`Dry run for ${result.command}:\n`);
    for (const step of result.plan) process.stdout.write(`- ${step}\n`);
    return;
  }
  if (result.command === "doctor") {
    process.stdout.write(`Ready: ${result.ready ? "yes" : "no"}\n`);
    for (const [name, check] of Object.entries(result.checks)) {
      process.stdout.write(`${check.ok ? "[ok]" : "[missing]"} ${name}\n`);
    }
    return;
  }
  if (result.command === "models") {
    process.stdout.write(`Models directory: ${result.modelsDir}\n`);
    for (const item of result.results) {
      process.stdout.write(
        `${item.downloaded ? "[downloaded]" : "[skipped]"} ${item.id} -> ${item.path}\n`,
      );
    }
    process.stdout.write(`Recommended bundle ready: ${result.ready ? "yes" : "no"}\n`);
    if (!result.ready) {
      process.stdout.write("Missing recommended models:\n");
      for (const model of result.missingModels) {
        process.stdout.write(`- ${model.id}: ${model.url}\n`);
      }
    }
    return;
  }
  if (result.command === "uninstall") {
    process.stdout.write(
      result.removed ? "Plugin registration and managed files removed.\n" : "Plugin was not installed.\n",
    );
    if (result.preserved) {
      process.stdout.write("Preserved local data:\n");
      for (const item of result.preserved) process.stdout.write(`- ${item}\n`);
    }
    return;
  }

  process.stdout.write(`Plugin ${result.command} complete: ${result.targetDir}\n`);
  if (result.ready) {
    process.stdout.write("CrispASR and all required models are ready. Restart Codex.\n");
    return;
  }
  process.stdout.write("\nSetup paused: download these model files manually:\n");
  for (const model of result.missingModels) {
    process.stdout.write(`- ${model.filename}\n  ${model.url}\n  Save to: ${model.path}\n`);
  }
  process.stdout.write(
    `\nAfter downloading, run: npx ${PACKAGE_NAME}@latest doctor\n`,
  );
}

function printError(error, jsonMode) {
  const installerError =
    error instanceof InstallerError
      ? error
      : new InstallerError(error.message || String(error));
  if (jsonMode) {
    process.stdout.write(
      `${JSON.stringify({ ok: false, error: installerError.toJSON() })}\n`,
    );
  } else {
    process.stderr.write(`Error: ${installerError.message}\n`);
    if (installerError.code === "missing_prerequisite") {
      process.stderr.write(
        "Install uv from https://docs.astral.sh/uv/ and ffmpeg from https://ffmpeg.org/, then retry.\n",
      );
    }
  }
}

export async function main(argv = []) {
  let parsed;
  try {
    parsed = parseArgs(argv);
  } catch (error) {
    printError(error, argv.includes("--json"));
    return 2;
  }

  if (parsed.options.help) {
    process.stdout.write(HELP);
    return 0;
  }
  if (parsed.options.version) {
    process.stdout.write(`${PACKAGE_VERSION}\n`);
    return 0;
  }

  const progress = parsed.options.json
    ? (message) => process.stderr.write(`${message}\n`)
    : (message) => process.stdout.write(`${message}\n`);

  try {
    let result;
    if (parsed.command === "doctor") {
      result = doctor(parsed.options);
    } else if (parsed.command === "models") {
      result = await downloadModels(parsed.options);
    } else if (parsed.command === "uninstall") {
      result = uninstallPlugin(parsed.options);
    } else {
      result = await installPlugin({
        ...parsed.options,
        update: parsed.command === "update",
        captureCommands: parsed.options.json,
        onProgress: progress,
      });
    }
    if (parsed.options.json) {
      process.stdout.write(`${JSON.stringify({ ok: true, ...result })}\n`);
    } else {
      printHumanResult(result);
    }
    return 0;
  } catch (error) {
    printError(error, parsed.options.json);
    return 1;
  }
}

export { HELP, parseArgs };
