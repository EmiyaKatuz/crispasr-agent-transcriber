import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import AdmZip from "adm-zip";

import { InstallerError } from "../src/errors.js";
import {
  assertSafeArchiveEntry,
  assertSafeReleaseBase,
  expectedChecksum,
  extractZipSafely,
} from "../src/release.js";

test("checksum parser selects the requested asset", () => {
  const hash = "a".repeat(64);
  assert.equal(expectedChecksum(`${hash}  plugin.zip\n`, "plugin.zip"), hash);
  assert.equal(expectedChecksum(`${hash}  other.zip\n`, "plugin.zip"), null);
});

test("unsafe archive paths are rejected", () => {
  for (const entry of ["../escape.txt", "/absolute.txt", "C:/escape.txt"]) {
    assert.throws(() => assertSafeArchiveEntry(entry), InstallerError);
  }
});

test("release downloads require HTTPS except for localhost tests", () => {
  assert.equal(assertSafeReleaseBase("https://github.com/example/releases/"), "https://github.com/example/releases");
  assert.equal(assertSafeReleaseBase("http://127.0.0.1:8080"), "http://127.0.0.1:8080");
  assert.throws(
    () => assertSafeReleaseBase("http://downloads.example.com/releases"),
    InstallerError,
  );
});

test("safe zip extracts under the destination", () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "crispasr-zip-test-"));
  try {
    const archivePath = path.join(temporary, "plugin.zip");
    const outputPath = path.join(temporary, "output");
    const archive = new AdmZip();
    archive.addFile("plugin/README.md", Buffer.from("ready\n"));
    archive.writeZip(archivePath);

    extractZipSafely(archivePath, outputPath);
    assert.equal(
      fs.readFileSync(path.join(outputPath, "plugin", "README.md"), "utf8"),
      "ready\n",
    );
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});
