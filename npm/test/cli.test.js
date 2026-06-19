import assert from "node:assert/strict";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import test from "node:test";

const testDir = path.dirname(fileURLToPath(import.meta.url));
const cliPath = path.join(testDir, "..", "bin", "crispasr-agent-transcriber.js");

test("help and version are available through the bin entry point", () => {
  const help = spawnSync(process.execPath, [cliPath, "--help"], {
    encoding: "utf8",
    shell: false,
  });
  assert.equal(help.status, 0);
  assert.match(help.stdout, /install.*update.*doctor.*uninstall/s);

  const version = spawnSync(process.execPath, [cliPath, "--version"], {
    encoding: "utf8",
    shell: false,
  });
  assert.equal(version.status, 0);
  assert.equal(version.stdout.trim(), "0.3.3");
});

test("doctor emits one JSON object", () => {
  const target = path.join(testDir, "missing-plugin");
  const report = spawnSync(
    process.execPath,
    [cliPath, "doctor", "--json", "--target-dir", target],
    { encoding: "utf8", shell: false },
  );
  assert.equal(report.status, 0);
  const value = JSON.parse(report.stdout);
  assert.equal(value.ok, true);
  assert.equal(value.command, "doctor");
  assert.equal(value.ready, false);
});
