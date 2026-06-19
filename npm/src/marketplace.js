import fs from "node:fs";
import path from "node:path";

import { PLUGIN_NAME } from "./constants.js";
import { InstallerError } from "./errors.js";

export const MARKETPLACE_ENTRY = {
  name: PLUGIN_NAME,
  source: {
    source: "local",
    path: `./plugins/${PLUGIN_NAME}`,
  },
  policy: {
    installation: "AVAILABLE",
    authentication: "ON_INSTALL",
  },
  category: "Productivity",
};

function readMarketplace(filePath) {
  if (!fs.existsSync(filePath)) {
    return {
      name: "personal",
      interface: { displayName: "Personal" },
      plugins: [],
    };
  }
  try {
    const value = JSON.parse(fs.readFileSync(filePath, "utf8"));
    if (!value || typeof value !== "object" || Array.isArray(value)) {
      throw new Error("root must be a JSON object");
    }
    if (value.plugins !== undefined && !Array.isArray(value.plugins)) {
      throw new Error("plugins must be an array");
    }
    value.plugins ||= [];
    return value;
  } catch (error) {
    throw new InstallerError(
      `Cannot read the existing Codex marketplace file: ${error.message}`,
      "invalid_marketplace",
      { path: filePath },
    );
  }
}

function writeMarketplace(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  const temporary = `${filePath}.tmp-${process.pid}`;
  const backup = `${filePath}.bak`;
  fs.writeFileSync(temporary, `${JSON.stringify(value, null, 2)}\n`, "utf8");
  if (fs.existsSync(filePath)) {
    fs.copyFileSync(filePath, backup);
    fs.rmSync(filePath);
  }
  fs.renameSync(temporary, filePath);
}

export function installMarketplaceEntry(filePath) {
  const marketplace = readMarketplace(filePath);
  const existingIndex = marketplace.plugins.findIndex(
    (entry) => entry && entry.name === PLUGIN_NAME,
  );
  if (existingIndex >= 0) {
    marketplace.plugins[existingIndex] = MARKETPLACE_ENTRY;
  } else {
    marketplace.plugins.push(MARKETPLACE_ENTRY);
  }
  writeMarketplace(filePath, marketplace);
  return filePath;
}

export function removeMarketplaceEntry(filePath) {
  if (!fs.existsSync(filePath)) {
    return false;
  }
  const marketplace = readMarketplace(filePath);
  const originalLength = marketplace.plugins.length;
  marketplace.plugins = marketplace.plugins.filter(
    (entry) => !entry || entry.name !== PLUGIN_NAME,
  );
  if (marketplace.plugins.length === originalLength) {
    return false;
  }
  writeMarketplace(filePath, marketplace);
  return true;
}

export function hasMarketplaceEntry(filePath) {
  if (!fs.existsSync(filePath)) {
    return false;
  }
  try {
    return readMarketplace(filePath).plugins.some(
      (entry) => entry && entry.name === PLUGIN_NAME,
    );
  } catch {
    return false;
  }
}
