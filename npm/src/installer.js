import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

import {
  MANAGED_ENTRIES,
  MODEL_SPECS,
  PACKAGE_VERSION,
  PLUGIN_NAME,
  RECOMMENDED_MODEL_IDS,
  defaultMarketplacePath,
  defaultReleaseBase,
  defaultTargetDir,
} from "./constants.js";
import { InstallerError } from "./errors.js";
import {
  hasMarketplaceEntry,
  installMarketplaceEntry,
  removeMarketplaceEntry,
} from "./marketplace.js";
import { extractZipSafely, fetchReleaseBundle } from "./release.js";
import { crispasrExecutableName, findCommand, runCommand } from "./system.js";

const MARKER_FILE = ".crispasr-installer.json";
const MODEL_MANIFEST = "model-manifest.json";
const RELEASE_VERSION_RE = /^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$/;

function resolvedPath(value) {
  return path.resolve(value);
}

export function assertSafeTarget(targetDir, homeDir = os.homedir()) {
  const requested = resolvedPath(targetDir);
  const target = fs.existsSync(requested) ? fs.realpathSync(requested) : requested;
  const root = path.parse(target).root;
  const home = resolvedPath(homeDir);
  if (target === root || target === home) {
    throw new InstallerError(
      "Refusing to use a filesystem root or home directory as the plugin target.",
      "unsafe_target",
      { target },
    );
  }
  return target;
}

function readPluginManifest(targetDir) {
  const manifestPath = path.join(targetDir, ".codex-plugin", "plugin.json");
  if (!fs.existsSync(manifestPath)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  } catch {
    return null;
  }
}

function readMarker(targetDir) {
  const markerPath = path.join(targetDir, MARKER_FILE);
  if (!fs.existsSync(markerPath)) {
    return null;
  }
  try {
    return JSON.parse(fs.readFileSync(markerPath, "utf8"));
  } catch {
    return null;
  }
}

function targetIsRecognized(targetDir) {
  const marker = readMarker(targetDir);
  const manifest = readPluginManifest(targetDir);
  return Boolean(
    (marker && marker.plugin === PLUGIN_NAME) ||
      (manifest && manifest.name === PLUGIN_NAME),
  );
}

function ensureInstallableTarget(targetDir) {
  if (!fs.existsSync(targetDir)) {
    return;
  }
  const entries = fs.readdirSync(targetDir);
  if (entries.length === 0 || targetIsRecognized(targetDir)) {
    return;
  }
  const dataOnly = entries.every((entry) =>
    ["bin", "models", "outputs", MARKER_FILE].includes(entry),
  );
  if (!dataOnly) {
    throw new InstallerError(
      "The target directory is not empty and is not a recognized CrispASR plugin installation.",
      "target_not_managed",
      { target: targetDir },
    );
  }
}

function removeManagedEntries(targetDir) {
  for (const entry of MANAGED_ENTRIES) {
    fs.rmSync(path.join(targetDir, entry), { recursive: true, force: true });
  }
}

function copyPluginFiles(sourceDir, targetDir) {
  fs.mkdirSync(targetDir, { recursive: true });
  for (const entry of fs.readdirSync(sourceDir)) {
    fs.cpSync(path.join(sourceDir, entry), path.join(targetDir, entry), {
      recursive: true,
      force: true,
    });
  }
}

function writeMarker(targetDir, version, installed = true) {
  const marker = {
    plugin: PLUGIN_NAME,
    version,
    installed,
    updatedAt: new Date().toISOString(),
  };
  fs.writeFileSync(
    path.join(targetDir, MARKER_FILE),
    `${JSON.stringify(marker, null, 2)}\n`,
    "utf8",
  );
}

function locatePluginSource(extractDir, version) {
  const sourceDir = path.join(extractDir, PLUGIN_NAME);
  const manifest = readPluginManifest(sourceDir);
  if (!manifest || manifest.name !== PLUGIN_NAME) {
    throw new InstallerError(
      "The release archive does not contain the expected Codex plugin.",
      "invalid_release_bundle",
    );
  }
  if (manifest.version !== version) {
    throw new InstallerError(
      "The release archive version does not match the npm installer version.",
      "release_version_mismatch",
      { expected: version, actual: manifest.version },
    );
  }
  return sourceDir;
}

function resolvePrerequisites(options) {
  const commandFinder = options.commandFinder || findCommand;
  const uv = options.uvPath || commandFinder("uv");
  const ffmpeg = options.ffmpegPath || commandFinder("ffmpeg");
  const missing = [];
  if (!uv) missing.push("uv");
  if (!ffmpeg) missing.push("ffmpeg");
  if (missing.length > 0) {
    throw new InstallerError(
      `Missing required command${missing.length > 1 ? "s" : ""}: ${missing.join(", ")}.`,
      "missing_prerequisite",
      { missing },
    );
  }
  return { uv, ffmpeg };
}

export function inspectModels(targetDir) {
  const modelsDir = path.join(targetDir, "models");
  return MODEL_SPECS.map((model) => ({
    ...model,
    path: path.join(modelsDir, model.filename),
    installed: fs.existsSync(path.join(modelsDir, model.filename)),
  }));
}

function recommendedModels(targetDir) {
  return inspectModels(targetDir).filter((model) => RECOMMENDED_MODEL_IDS.includes(model.id));
}

export function resolveModelPaths(targetDir) {
  const recommended = recommendedModels(targetDir);
  return {
    targetDir,
    modelsDir: path.join(targetDir, "models"),
    ready: recommended.every((model) => model.installed),
    recommendedModelIds: RECOMMENDED_MODEL_IDS,
    englishModel: recommended.find((model) => model.role === "english")?.path || null,
    chineseModel: recommended.find((model) => model.role === "chinese")?.path || null,
    lidModel: recommended.find((model) => model.role === "lid")?.path || null,
    missingModels: recommended.filter((model) => !model.installed),
  };
}

function findModelSpec(modelId) {
  const normalized = modelId.toLowerCase();
  const match = MODEL_SPECS.find(
    (model) => model.id === normalized || model.filename.toLowerCase() === normalized,
  );
  if (!match) {
    throw new InstallerError("Unknown CrispASR model id.", "unknown_model", {
      modelId,
      knownIds: MODEL_SPECS.map((model) => model.id),
    });
  }
  return match;
}

async function writeResponseBody(response, destination) {
  if (response.body) {
    await pipeline(Readable.fromWeb(response.body), fs.createWriteStream(destination));
    return;
  }
  if (response.arrayBuffer) {
    fs.writeFileSync(destination, Buffer.from(await response.arrayBuffer()));
    return;
  }
  throw new InstallerError("The model download response did not include a body.", "empty_model_download");
}

function writeModelManifest(modelsDir, entries) {
  const manifestPath = path.join(modelsDir, MODEL_MANIFEST);
  let existing = { models: [] };
  if (fs.existsSync(manifestPath)) {
    try {
      existing = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    } catch {
      existing = { models: [] };
    }
  }
  const byId = new Map(
    (existing.models || []).filter((item) => item.id).map((item) => [item.id, item]),
  );
  for (const entry of entries) byId.set(entry.id, entry);
  const manifest = {
    updatedAt: new Date().toISOString(),
    models: [...byId.values()].sort((a, b) => a.id.localeCompare(b.id)),
  };
  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  return manifestPath;
}

async function downloadOneModel(spec, modelsDir, options) {
  const destination = path.join(modelsDir, spec.filename);
  if (fs.existsSync(destination) && !options.overwrite) {
    return {
      id: spec.id,
      filename: spec.filename,
      path: destination,
      downloaded: false,
      skipped: true,
      reason: "already_exists",
      url: spec.url,
    };
  }

  const fetchImpl = options.fetchImpl || globalThis.fetch;
  if (!fetchImpl) {
    throw new InstallerError("This Node.js runtime does not provide fetch.", "fetch_unavailable");
  }

  const partial = `${destination}.part`;
  try {
    const response = await fetchImpl(spec.downloadUrl);
    if (!response.ok) {
      throw new InstallerError("Model download request failed.", "model_download_failed", {
        modelId: spec.id,
        status: response.status,
        url: spec.downloadUrl,
      });
    }
    await writeResponseBody(response, partial);
    if (options.overwrite) fs.rmSync(destination, { force: true });
    fs.renameSync(partial, destination);
  } catch (error) {
    fs.rmSync(partial, { force: true });
    if (error instanceof InstallerError) throw error;
    throw new InstallerError("Model download failed.", "model_download_failed", {
      modelId: spec.id,
      url: spec.downloadUrl,
      message: error.message,
    });
  }

  return {
    id: spec.id,
    role: spec.role,
    filename: spec.filename,
    path: destination,
    downloaded: true,
    skipped: false,
    url: spec.url,
    downloadUrl: spec.downloadUrl,
    downloadedAt: new Date().toISOString(),
    sizeBytes: fs.statSync(destination).size,
  };
}

export async function downloadModels(options = {}) {
  const homeDir = options.homeDir || os.homedir();
  const targetDir = assertSafeTarget(options.targetDir || defaultTargetDir(homeDir), homeDir);
  const modelsDir = path.join(targetDir, "models");
  const requestedIds = options.modelIds?.length ? options.modelIds : RECOMMENDED_MODEL_IDS;
  const specs = requestedIds.map((modelId) => findModelSpec(modelId));

  if (options.dryRun) {
    return {
      command: "models",
      dryRun: true,
      targetDir,
      plan: specs.map((spec) => `Download ${spec.id} (${spec.filename}) to ${modelsDir}`),
    };
  }

  fs.mkdirSync(modelsDir, { recursive: true });
  const results = [];
  for (const spec of specs) {
    results.push(await downloadOneModel(spec, modelsDir, options));
  }
  const downloaded = results.filter((item) => item.downloaded);
  const manifestPath = downloaded.length > 0 ? writeModelManifest(modelsDir, downloaded) : null;
  const paths = resolveModelPaths(targetDir);
  return {
    command: "models",
    targetDir,
    modelsDir,
    modelIds: requestedIds,
    results,
    manifestPath,
    ready: paths.ready,
    recommendedModelIds: RECOMMENDED_MODEL_IDS,
    recommendedPaths: {
      englishModel: paths.englishModel,
      chineseModel: paths.chineseModel,
      lidModel: paths.lidModel,
    },
    missingModels: paths.missingModels,
  };
}

function installPlan({ targetDir, version, marketplacePath, update }) {
  return [
    `Download and verify GitHub Release v${version}`,
    `${update ? "Update" : "Install"} plugin files in ${targetDir}`,
    "Install Python and MCP dependencies with uv",
    `${update ? "Update" : "Install"} the GPU-preferred CrispASR binary`,
    `Register the Codex Personal marketplace entry in ${marketplacePath}`,
    "Check for the three recommended local model files",
  ];
}

export async function installPlugin(options = {}) {
  const homeDir = options.homeDir || os.homedir();
  const defaultTarget = assertSafeTarget(defaultTargetDir(homeDir), homeDir);
  const targetDir = assertSafeTarget(
    options.targetDir || defaultTarget,
    homeDir,
  );
  const marketplacePath =
    options.marketplacePath || defaultMarketplacePath(homeDir);
  const version = options.releaseVersion || PACKAGE_VERSION;
  const releaseBase = options.releaseBase || defaultReleaseBase();
  const update = Boolean(options.update);
  const progress = options.onProgress || (() => {});

  if (!RELEASE_VERSION_RE.test(version)) {
    throw new InstallerError(
      "Release versions must use semantic version syntax such as 0.3.5.",
      "invalid_release_version",
      { version },
    );
  }

  if (!options.skipMarketplace && targetDir !== defaultTarget) {
    throw new InstallerError(
      "A custom target directory requires --no-marketplace because the Personal marketplace path is fixed.",
      "custom_target_marketplace",
      { target: targetDir, expected: defaultTarget },
    );
  }

  const plan = installPlan({ targetDir, version, marketplacePath, update });
  if (options.dryRun) {
    return { command: update ? "update" : "install", dryRun: true, targetDir, plan };
  }

  const commands = resolvePrerequisites(options);
  ensureInstallableTarget(targetDir);

  const temporaryDir = fs.mkdtempSync(path.join(os.tmpdir(), "crispasr-installer-"));
  try {
    progress(`Downloading and verifying plugin release v${version}...`);
    const bundle = await fetchReleaseBundle({
      version,
      releaseBase,
      destinationDir: temporaryDir,
      fetchImpl: options.fetchImpl,
    });
    const extractDir = path.join(temporaryDir, "extracted");
    extractZipSafely(bundle.archivePath, extractDir);
    const sourceDir = locatePluginSource(extractDir, version);

    progress(`${update ? "Updating" : "Installing"} plugin files...`);
    if (readMarker(targetDir)) {
      removeManagedEntries(targetDir);
    }
    copyPluginFiles(sourceDir, targetDir);
    fs.mkdirSync(path.join(targetDir, "models"), { recursive: true });
    fs.mkdirSync(path.join(targetDir, "outputs"), { recursive: true });
    writeMarker(targetDir, version, true);

    const runner = options.commandRunner || runCommand;
    if (!options.skipDependencies) {
      progress("Installing Python and MCP dependencies...");
      runner(commands.uv, ["sync", "--extra", "mcp"], {
        cwd: targetDir,
        capture: Boolean(options.captureCommands),
      });
    }

    const crispasrPath = path.join(
      targetDir,
      "bin",
      crispasrExecutableName(options.platform),
    );
    if (!options.skipCrispASR && (update || !fs.existsSync(crispasrPath))) {
      progress(`${update ? "Updating" : "Installing"} CrispASR...`);
      runner(
        commands.uv,
        [
          "run",
          "python",
          "scripts/transcribe.py",
          update ? "--update-crispasr" : "--install-crispasr",
          "--crispasr-bin-dir",
          path.join(targetDir, "bin"),
        ],
        { cwd: targetDir, capture: Boolean(options.captureCommands) },
      );
    }

    if (!options.skipMarketplace) {
      progress("Registering the Codex Personal marketplace entry...");
      installMarketplaceEntry(marketplacePath);
    }

    const models = inspectModels(targetDir);
    const missingModels = models.filter((model) => model.recommended && !model.installed);
    return {
      command: update ? "update" : "install",
      targetDir,
      marketplacePath,
      version,
      archiveSha256: bundle.sha256,
      ready: missingModels.length === 0,
      models,
      missingModels,
    };
  } finally {
    fs.rmSync(temporaryDir, { recursive: true, force: true });
  }
}

export function doctor(options = {}) {
  const homeDir = options.homeDir || os.homedir();
  const targetDir = assertSafeTarget(
    options.targetDir || defaultTargetDir(homeDir),
    homeDir,
  );
  const marketplacePath =
    options.marketplacePath || defaultMarketplacePath(homeDir);
  const commandFinder = options.commandFinder || findCommand;
  const manifest = readPluginManifest(targetDir);
  const crispasrPath = path.join(
    targetDir,
    "bin",
    crispasrExecutableName(options.platform),
  );
  const models = inspectModels(targetDir);
  const checks = {
    plugin: {
      ok: manifest?.name === PLUGIN_NAME,
      version: manifest?.version || null,
      path: targetDir,
    },
    uv: { ok: Boolean(commandFinder("uv")), path: commandFinder("uv") },
    ffmpeg: {
      ok: Boolean(commandFinder("ffmpeg")),
      path: commandFinder("ffmpeg"),
    },
    crispasr: { ok: fs.existsSync(crispasrPath), path: crispasrPath },
    marketplace: {
      ok: hasMarketplaceEntry(marketplacePath),
      path: marketplacePath,
    },
    models: {
      ok: models.filter((model) => model.recommended).every((model) => model.installed),
      items: models,
      recommendedModelIds: RECOMMENDED_MODEL_IDS,
    },
  };
  return {
    command: "doctor",
    ready: Object.values(checks).every((check) => check.ok),
    checks,
  };
}

export function uninstallPlugin(options = {}) {
  const homeDir = options.homeDir || os.homedir();
  const defaultTarget = assertSafeTarget(defaultTargetDir(homeDir), homeDir);
  const targetDir = assertSafeTarget(
    options.targetDir || defaultTarget,
    homeDir,
  );
  const marketplacePath =
    options.marketplacePath || defaultMarketplacePath(homeDir);

  if (!fs.existsSync(targetDir)) {
    if (!options.skipMarketplace && targetDir === defaultTarget) {
      removeMarketplaceEntry(marketplacePath);
    }
    return { command: "uninstall", removed: false, targetDir };
  }
  if (!targetIsRecognized(targetDir)) {
    throw new InstallerError(
      "Refusing to uninstall an unrecognized directory.",
      "target_not_managed",
      { target: targetDir },
    );
  }

  if (!options.skipMarketplace && targetDir === defaultTarget) {
    removeMarketplaceEntry(marketplacePath);
  }
  if (options.purgeData) {
    if (!readMarker(targetDir)) {
      throw new InstallerError(
        "Refusing to purge data without an npm installer ownership marker.",
        "purge_requires_marker",
        { target: targetDir },
      );
    }
    fs.rmSync(targetDir, { recursive: true, force: true });
    return {
      command: "uninstall",
      removed: true,
      purgedData: true,
      targetDir,
    };
  }

  removeManagedEntries(targetDir);
  writeMarker(targetDir, readMarker(targetDir)?.version || PACKAGE_VERSION, false);
  return {
    command: "uninstall",
    removed: true,
    purgedData: false,
    preserved: [
      path.join(targetDir, "models"),
      path.join(targetDir, "bin"),
      path.join(targetDir, "outputs"),
    ],
    targetDir,
  };
}
