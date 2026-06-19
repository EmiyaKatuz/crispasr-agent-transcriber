import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  hasMarketplaceEntry,
  installMarketplaceEntry,
  removeMarketplaceEntry,
} from "../src/marketplace.js";

test("marketplace update preserves unrelated plugins", () => {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "crispasr-market-test-"));
  try {
    const marketplacePath = path.join(temporary, ".agents", "plugins", "marketplace.json");
    fs.mkdirSync(path.dirname(marketplacePath), { recursive: true });
    fs.writeFileSync(
      marketplacePath,
      JSON.stringify({
        name: "personal",
        interface: { displayName: "My Plugins" },
        plugins: [{ name: "existing-plugin" }],
      }),
    );

    installMarketplaceEntry(marketplacePath);
    const installed = JSON.parse(fs.readFileSync(marketplacePath, "utf8"));
    assert.equal(installed.interface.displayName, "My Plugins");
    assert.deepEqual(
      installed.plugins.map((entry) => entry.name),
      ["existing-plugin", "crispasr-agent-transcriber"],
    );
    assert.equal(hasMarketplaceEntry(marketplacePath), true);

    assert.equal(removeMarketplaceEntry(marketplacePath), true);
    const removed = JSON.parse(fs.readFileSync(marketplacePath, "utf8"));
    assert.deepEqual(removed.plugins.map((entry) => entry.name), ["existing-plugin"]);
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
});
