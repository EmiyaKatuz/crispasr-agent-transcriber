import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

import AdmZip from "adm-zip";

import { InstallerError } from "./errors.js";

export function assertSafeReleaseBase(releaseBase) {
  let parsed;
  try {
    parsed = new URL(releaseBase);
  } catch {
    throw new InstallerError("The release base URL is invalid.", "invalid_release_url");
  }
  const localHttp =
    parsed.protocol === "http:" &&
    ["127.0.0.1", "localhost", "::1"].includes(parsed.hostname);
  if (parsed.protocol !== "https:" && !localHttp) {
    throw new InstallerError(
      "Release downloads require HTTPS (except localhost test servers).",
      "invalid_release_url",
      { url: releaseBase },
    );
  }
  return parsed.toString().replace(/\/$/, "");
}

export async function downloadFile(url, destination, fetchImpl = globalThis.fetch) {
  const response = await fetchImpl(url, {
    headers: { "User-Agent": "crispasr-agent-transcriber-installer" },
    redirect: "follow",
  });
  if (!response.ok || !response.body) {
    throw new InstallerError(
      `Download failed with HTTP ${response.status}.`,
      "download_failed",
      { url, status: response.status },
    );
  }
  await pipeline(Readable.fromWeb(response.body), fs.createWriteStream(destination));
}

export function sha256File(filePath) {
  const hash = crypto.createHash("sha256");
  hash.update(fs.readFileSync(filePath));
  return hash.digest("hex");
}

export function expectedChecksum(checksumText, filename) {
  for (const line of checksumText.split(/\r?\n/)) {
    const match = line.trim().match(/^([0-9a-fA-F]{64})\s+\*?(.+)$/);
    if (match && path.basename(match[2].trim()) === filename) {
      return match[1].toLowerCase();
    }
  }
  return null;
}

export function assertSafeArchiveEntry(entryName) {
  const normalized = entryName.replaceAll("\\", "/");
  const parts = normalized.split("/").filter(Boolean);
  if (
    normalized.startsWith("/") ||
    /^[a-zA-Z]:/.test(normalized) ||
    parts.includes("..")
  ) {
    throw new InstallerError(
      "The plugin archive contains an unsafe path.",
      "unsafe_archive",
      { entry: entryName },
    );
  }
}

export function extractZipSafely(archivePath, destination) {
  const archive = new AdmZip(archivePath);
  const entries = archive.getEntries();
  for (const entry of entries) {
    assertSafeArchiveEntry(entry.entryName);
  }
  fs.mkdirSync(destination, { recursive: true });
  for (const entry of entries) {
    archive.extractEntryTo(entry, destination, true, true);
  }
}

export async function fetchReleaseBundle({
  version,
  releaseBase,
  destinationDir,
  fetchImpl = globalThis.fetch,
}) {
  const filename = `crispasr-agent-transcriber-plugin-${version}.zip`;
  const archivePath = path.join(destinationDir, filename);
  const checksumPath = path.join(destinationDir, "SHA256SUMS");
  const versionBase = `${assertSafeReleaseBase(releaseBase)}/v${version}`;

  await downloadFile(`${versionBase}/SHA256SUMS`, checksumPath, fetchImpl);
  await downloadFile(`${versionBase}/${filename}`, archivePath, fetchImpl);

  const checksumText = fs.readFileSync(checksumPath, "utf8");
  const expected = expectedChecksum(checksumText, filename);
  if (!expected) {
    throw new InstallerError(
      "The release checksum file does not list the plugin archive.",
      "checksum_missing",
      { filename },
    );
  }
  const actual = sha256File(archivePath);
  if (actual !== expected) {
    throw new InstallerError(
      "The downloaded plugin archive failed SHA-256 verification.",
      "checksum_mismatch",
      { filename, expected, actual },
    );
  }
  return { archivePath, filename, sha256: actual };
}
