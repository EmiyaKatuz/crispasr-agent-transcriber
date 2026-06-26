import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import AdmZip from "adm-zip";

import { doctor, downloadModels, installPlugin, uninstallPlugin } from "../src/installer.js";
import { MODEL_SPECS } from "../src/constants.js";
import { InstallerError } from "../src/errors.js";

const VERSION = "0.3.5";
const ARCHIVE_NAME = `crispasr-agent-transcriber-plugin-${VERSION}.zip`;

function createBundle(filePath, readmeText) {
  const archive = new AdmZip();
  const root = "crispasr-agent-transcriber/";
  archive.addFile(
    `${root}.codex-plugin/plugin.json`,
    Buffer.from(
      JSON.stringify({ name: "crispasr-agent-transcriber", version: VERSION }),
    ),
  );
  archive.addFile(`${root}README.md`, Buffer.from(readmeText));
  archive.addFile(`${root}pyproject.toml`, Buffer.from("[project]\nname='test'\n"));
  archive.writeZip(filePath);
}

test("model sources point to exact Hugging Face repositories", () => {
  assert.equal(
    MODEL_SPECS.find((model) => model.id === "english-q4")?.url,
    "https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF",
  );
  assert.equal(
    MODEL_SPECS.find((model) => model.id === "english-q4")?.downloadUrl,
    "https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF/resolve/main/cohere-transcribe-q4_k.gguf",
  );
  for (const model of MODEL_SPECS) {
    assert.notEqual(model.url, "https://huggingface.co/cstr");
  }
});

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

async function startReleaseServer(archivePath) {
  const server = http.createServer((request, response) => {
    if (request.url === `/v${VERSION}/${ARCHIVE_NAME}`) {
      response.writeHead(200, { "content-type": "application/zip" });
      fs.createReadStream(archivePath).pipe(response);
      return;
    }
    if (request.url === `/v${VERSION}/SHA256SUMS`) {
      response.writeHead(200, { "content-type": "text/plain" });
      response.end(`${sha256(archivePath)}  ${ARCHIVE_NAME}\n`);
      return;
    }
    response.writeHead(404);
    response.end();
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise((resolve) => server.close(resolve)),
  };
}

test("install, update, doctor, and uninstall preserve local data", async () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "crispasr-install-test-"));
  const archivePath = path.join(temporary, ARCHIVE_NAME);
  const homeDir = path.join(temporary, "home");
  const targetDir = path.join(homeDir, "plugins", "crispasr-agent-transcriber");
  const marketplacePath = path.join(homeDir, ".agents", "plugins", "marketplace.json");
  createBundle(archivePath, "first\n");
  const releaseServer = await startReleaseServer(archivePath);

  const commonOptions = {
    homeDir,
    targetDir,
    marketplacePath,
    releaseVersion: VERSION,
    releaseBase: releaseServer.baseUrl,
    uvPath: "uv-test",
    ffmpegPath: "ffmpeg-test",
    skipDependencies: true,
    skipCrispASR: true,
  };

  try {
    const installed = await installPlugin(commonOptions);
    assert.equal(installed.ready, false);
    assert.equal(installed.missingModels.length, 3);
    assert.equal(fs.readFileSync(path.join(targetDir, "README.md"), "utf8"), "first\n");

    const modelPath = path.join(targetDir, "models", "cohere-transcribe.gguf");
    const binaryPath = path.join(targetDir, "bin", "crispasr.exe");
    fs.mkdirSync(path.dirname(binaryPath), { recursive: true });
    fs.writeFileSync(modelPath, "model-data");
    fs.writeFileSync(binaryPath, "binary-data");

    createBundle(archivePath, "updated\n");
    await installPlugin({ ...commonOptions, update: true });
    assert.equal(fs.readFileSync(path.join(targetDir, "README.md"), "utf8"), "updated\n");
    assert.equal(fs.readFileSync(modelPath, "utf8"), "model-data");
    assert.equal(fs.readFileSync(binaryPath, "utf8"), "binary-data");

    const report = doctor({
      homeDir,
      targetDir,
      marketplacePath,
      platform: "win32",
      commandFinder: (name) => `${name}-test`,
    });
    assert.equal(report.checks.plugin.ok, true);
    assert.equal(report.checks.marketplace.ok, true);
    assert.equal(report.checks.models.ok, false);

    const removed = uninstallPlugin({ homeDir, targetDir, marketplacePath });
    assert.equal(removed.purgedData, false);
    assert.equal(fs.existsSync(modelPath), true);
    assert.equal(fs.existsSync(binaryPath), true);
    assert.equal(fs.existsSync(path.join(targetDir, "README.md")), false);
  } finally {
    await releaseServer.close();
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});

test("custom targets cannot silently register the default marketplace path", async () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "crispasr-target-test-"));
  try {
    await assert.rejects(
      installPlugin({
        homeDir: path.join(temporary, "home"),
        targetDir: path.join(temporary, "custom-plugin"),
        dryRun: true,
      }),
      (error) =>
        error instanceof InstallerError && error.code === "custom_target_marketplace",
    );
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});

test("release version input cannot change the download path", async () => {
  await assert.rejects(
    installPlugin({ releaseVersion: "../../latest", dryRun: true }),
    (error) =>
      error instanceof InstallerError && error.code === "invalid_release_version",
  );
});

test("purge requires the npm installer ownership marker", () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "crispasr-purge-test-"));
  const homeDir = path.join(temporary, "home");
  const targetDir = path.join(homeDir, "plugins", "crispasr-agent-transcriber");
  try {
    fs.mkdirSync(path.join(targetDir, ".codex-plugin"), { recursive: true });
    fs.writeFileSync(
      path.join(targetDir, ".codex-plugin", "plugin.json"),
      JSON.stringify({ name: "crispasr-agent-transcriber", version: VERSION }),
    );
    assert.throws(
      () => uninstallPlugin({ homeDir, targetDir, purgeData: true }),
      (error) =>
        error instanceof InstallerError && error.code === "purge_requires_marker",
    );
    assert.equal(fs.existsSync(targetDir), true);
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});

test("downloadModels downloads only approved model ids and writes a manifest", async () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "crispasr-model-test-"));
  const homeDir = path.join(temporary, "home");
  const targetDir = path.join(homeDir, "plugins", "crispasr-agent-transcriber");
  const requests = [];
  try {
    const result = await downloadModels({
      homeDir,
      targetDir,
      modelIds: ["english-q4"],
      fetchImpl: async (url) => {
        requests.push(url);
        return {
          ok: true,
          status: 200,
          arrayBuffer: async () => Buffer.from("model-data"),
        };
      },
    });

    const modelPath = path.join(targetDir, "models", "cohere-transcribe-q4_k.gguf");
    assert.equal(requests.length, 1);
    assert.equal(
      requests[0],
      "https://huggingface.co/cstr/cohere-transcribe-03-2026-GGUF/resolve/main/cohere-transcribe-q4_k.gguf",
    );
    assert.equal(fs.readFileSync(modelPath, "utf8"), "model-data");
    assert.equal(fs.existsSync(path.join(targetDir, "models", "model-manifest.json")), true);
    assert.equal(result.results[0].downloaded, true);

    const skipped = await downloadModels({
      homeDir,
      targetDir,
      modelIds: ["english-q4"],
      fetchImpl: async () => {
        throw new Error("should not refetch");
      },
    });
    assert.equal(skipped.results[0].skipped, true);
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});

test("downloadModels dry run does not fetch", async () => {
  const result = await downloadModels({
    homeDir: os.tmpdir(),
    targetDir: path.join(os.tmpdir(), "crispasr-dry-run-models"),
    modelIds: ["lid-q4"],
    dryRun: true,
    fetchImpl: async () => {
      throw new Error("should not fetch in dry run");
    },
  });
  assert.equal(result.dryRun, true);
  assert.equal(result.plan.length, 1);
  assert.match(result.plan[0], /lid-q4/);
});
