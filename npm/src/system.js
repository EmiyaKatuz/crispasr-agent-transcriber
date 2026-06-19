import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

import { InstallerError } from "./errors.js";

export function findCommand(name, env = process.env, platform = process.platform) {
  const pathValue = env.PATH || env.Path || env.path || "";
  const pathEntries = pathValue.split(path.delimiter).filter(Boolean);
  const extensions =
    platform === "win32"
      ? (env.PATHEXT || ".EXE;.CMD;.BAT;.COM").split(";")
      : [""];

  for (const directory of pathEntries) {
    for (const extension of extensions) {
      const candidate = path.join(directory, `${name}${extension}`);
      try {
        if (fs.statSync(candidate).isFile()) {
          return candidate;
        }
      } catch {
        // Continue searching PATH.
      }
    }
  }
  return null;
}

export function runCommand(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd,
    env: options.env || process.env,
    encoding: "utf8",
    shell: false,
    timeout: options.timeoutMs || 10 * 60 * 1000,
    stdio: options.capture ? "pipe" : "inherit",
  });

  if (result.error) {
    throw new InstallerError(
      `Failed to run ${path.basename(command)}: ${result.error.message}`,
      "command_failed",
      { command: path.basename(command) },
    );
  }
  if (result.status !== 0) {
    throw new InstallerError(
      `${path.basename(command)} exited with status ${result.status}.`,
      "command_failed",
      {
        command: path.basename(command),
        status: result.status,
        stderr: options.capture ? (result.stderr || "").trim().slice(-2000) : undefined,
      },
    );
  }
  return result;
}

export function crispasrExecutableName(platform = process.platform) {
  return platform === "win32" ? "crispasr.exe" : "crispasr";
}
