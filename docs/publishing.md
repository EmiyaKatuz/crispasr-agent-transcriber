# Publishing and distribution

There are five separate publishing steps. They serve different users and must
be completed in this order:

1. **GitHub Release and npm** provide the verified plugin ZIP and the `npx`
   installer.
2. **Codex Marketplace** distributes the complete Codex plugin, including its
   Skill, MCP configuration, and interface metadata.
3. **PyPI** distributes the Python CLI and MCP server independently of Codex.
4. **MCP Registry** makes the published PyPI package discoverable by compatible
   MCP clients. The registry stores metadata only, so PyPI must come first.
5. **Agent configurations** connect Codex, Claude Desktop, Cursor, VS Code, or
   another MCP client to the same local MCP server.

The examples below use `0.3.2` as the next release version. Replace it with the
version you are actually publishing. Keep the version identical in
`pyproject.toml`, `.codex-plugin/plugin.json`, the Git tag, PyPI, and
`server.json`.

### Step 0: publish the GitHub Release and npm installer

The npm package is a small installer. It does not include models or CrispASR
binaries. It downloads the matching plugin ZIP from GitHub Releases and refuses
to install it unless the SHA-256 checksum matches.

1. Create or sign in to the npm account that owns the `@emiyakatuz` scope.
   Enable two-factor authentication.

2. Create a granular npm access token that can publish
   `@emiyakatuz/crispasr-agent-transcriber`. In the GitHub repository:

   - create an environment named `npm` under **Settings > Environments**;
   - add the token as the Actions secret `NPM_TOKEN`;
   - never place the token in the repository or a command-line argument.

3. Keep the same version in `npm/package.json`, `pyproject.toml`,
   `.codex-plugin/plugin.json`, and `server.json`. Run all local checks:

   ```powershell
   uv run pytest
   uv run ruff check .
   Push-Location npm
   npm ci
   npm test
   npm pack --dry-run
   Pop-Location
   ```

4. Push the version tag. The Release workflow creates the plugin ZIP and
   `SHA256SUMS`:

   ```powershell
   git tag v0.3.2
   git push origin v0.3.2
   ```

5. After the GitHub Release succeeds, open **Actions > Publish npm installer >
   Run workflow**. The workflow verifies the matching ZIP and checksum assets
   before publishing the npm package.

6. Verify the public installer without changing files:

   ```powershell
   npm view @emiyakatuz/crispasr-agent-transcriber version
   npx @emiyakatuz/crispasr-agent-transcriber@latest install --dry-run
   ```

For every later version, publish the GitHub Release first and run the npm
workflow second. npm package versions are immutable and cannot be overwritten.

### Step 1: publish a Codex Marketplace repository

Use a separate public repository as the marketplace catalog. The marketplace
contains a released plugin bundle; it must not contain model files, media, or
generated transcripts.

1. Create the marketplace folder and download the plugin bundle from the
   matching GitHub Release:

   ```powershell
   $version = "0.3.2"
   $marketplace = Join-Path $HOME "src\crispasr-agent-marketplace"
   $archive = Join-Path $env:TEMP "crispasr-plugin-$version.zip"

   New-Item -ItemType Directory -Force `
     (Join-Path $marketplace ".agents\plugins"), `
     (Join-Path $marketplace "plugins") | Out-Null

   Invoke-WebRequest `
     "https://github.com/EmiyaKatuz/crispasr-agent-transcriber/releases/download/v$version/crispasr-agent-transcriber-plugin-$version.zip" `
     -OutFile $archive
   Expand-Archive $archive -DestinationPath (Join-Path $marketplace "plugins") -Force
   Remove-Item $archive
   ```

2. Create `.agents/plugins/marketplace.json` in the marketplace repository:

   ```json
   {
     "name": "emiyakatuz",
     "interface": {
       "displayName": "EmiyaKatuz Plugins"
     },
     "plugins": [
       {
         "name": "crispasr-agent-transcriber",
         "source": {
           "source": "local",
           "path": "./plugins/crispasr-agent-transcriber"
         },
         "policy": {
           "installation": "AVAILABLE",
           "authentication": "ON_INSTALL"
         },
         "category": "Productivity"
       }
     ]
   }
   ```

3. Confirm that the extracted plugin contains
   `plugins/crispasr-agent-transcriber/.codex-plugin/plugin.json`, then publish
   the marketplace repository:

   ```powershell
   Set-Location $marketplace
   git init
   git add .
   git commit -m "feat: publish CrispASR Transcriber plugin"
   gh repo create EmiyaKatuz/crispasr-agent-marketplace `
     --public --source . --remote origin --push
   ```

4. Test the public installation with a Codex build that supports plugin
   commands:

   ```powershell
   codex plugin marketplace add https://github.com/EmiyaKatuz/crispasr-agent-marketplace
   codex plugin add crispasr-agent-transcriber@emiyakatuz
   ```

   If the installed Codex CLI has no `codex plugin` command, add the marketplace
   in the Codex desktop Plugins view and install **CrispASR Transcriber** there.

For an update, publish a new release of this repository, replace only
`plugins/crispasr-agent-transcriber` in the marketplace repository with the new
release bundle, commit, and push. Users can then reinstall the plugin from the
same marketplace. See the [plugin installation guide](plugin_install.md).

### Step 2: publish the Python package to PyPI

PyPI is required for installation without Git and is also a prerequisite for
the MCP Registry entry. The package name is `crispasr-agent-transcriber`.

1. Choose a new version and update both `pyproject.toml` and
   `.codex-plugin/plugin.json`. Refresh the lock file and run all checks:

   ```powershell
   $version = "0.3.2"
   uv lock
   uv sync --extra dev --extra mcp
   uv run pytest
   uv run ruff check .
   uv build
   ```

2. Check the files that will be uploaded. There should be one wheel and one
   source archive for the selected version, with no models or media inside:

   ```powershell
   Get-ChildItem "dist\crispasr_agent_transcriber-$version*"
   tar -tf "dist\crispasr_agent_transcriber-$version.tar.gz"
   ```

3. Publish using one of these authentication methods:

   - **Recommended: PyPI Trusted Publishing.** In PyPI, create a pending
     publisher for GitHub owner `EmiyaKatuz`, repository
     `crispasr-agent-transcriber`, and workflow `publish-pypi.yml`. Then create
     `.github/workflows/publish-pypi.yml` with:

     ```yaml
     name: Publish to PyPI

     on:
       push:
         tags:
           - "v*"
       workflow_dispatch:

     permissions:
       contents: read
       id-token: write

     jobs:
       publish:
         runs-on: ubuntu-latest
         environment: pypi
         steps:
           - uses: actions/checkout@v4
           - uses: astral-sh/setup-uv@v5
           - run: uv sync --extra dev --extra mcp
           - run: uv run pytest
           - run: uv run ruff check .
           - run: uv build
           - run: uv publish --trusted-publishing always
     ```

     For the first release, use PyPI's **pending publisher** form because the
     project page does not exist yet. Set its environment to `pypi`. For later
     releases, manage the trusted publisher from the existing PyPI project's
     publishing settings.

   - **Manual fallback: scoped PyPI API token.** Never commit the token or put
     it in a command history file:

     ```powershell
     $env:UV_PUBLISH_TOKEN = Read-Host "PyPI token"
     uv publish "dist\crispasr_agent_transcriber-$version*"
     Remove-Item Env:UV_PUBLISH_TOKEN
     ```

4. Verify the public package in a clean, temporary environment:

   ```powershell
   uvx --from "crispasr-agent-transcriber[mcp]==$version" crispasr-agent-mcp
   ```

   The process should remain running and wait for an MCP client on standard
   input/output. Stop it with `Ctrl+C`. Publishing never includes or downloads
   ASR models.

References: [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
and [uv package publishing](https://docs.astral.sh/uv/guides/package/).

### Step 3: publish to the official MCP Registry

Do this only after the same version is visible on PyPI. The MCP Registry is
currently a preview service and stores metadata, not the Python package or any
models.

1. Keep this exact ownership marker in the README included by the PyPI package:

   ```html
   <!-- mcp-name: io.github.emiyakatuz/crispasr-agent-transcriber -->
   ```

2. Install the official publisher on Windows:

   ```powershell
   $arch = if (
     [System.Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture -eq "Arm64"
   ) { "arm64" } else { "amd64" }

   Invoke-WebRequest `
     "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_$arch.tar.gz" `
     -OutFile "mcp-publisher.tar.gz"
   tar xf mcp-publisher.tar.gz mcp-publisher.exe
   Remove-Item mcp-publisher.tar.gz
   .\mcp-publisher.exe --help
   ```

3. Create `server.json` at the repository root. Its version must already exist
   on PyPI:

   ```json
   {
     "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
     "name": "io.github.emiyakatuz/crispasr-agent-transcriber",
     "title": "CrispASR Agent Transcriber",
     "description": "Transcribe local audio and video with CrispASR and local models only.",
     "repository": {
       "url": "https://github.com/EmiyaKatuz/crispasr-agent-transcriber",
       "source": "github"
     },
     "version": "0.3.2",
     "packages": [
       {
         "registryType": "pypi",
         "registryBaseUrl": "https://pypi.org",
         "identifier": "crispasr-agent-transcriber",
         "version": "0.3.2",
         "runtimeHint": "uvx",
         "transport": {
           "type": "stdio"
         }
       }
     ]
   }
   ```

   The package exposes `crispasr-agent-transcriber` as an MCP entry point so
   registry clients can run the package directly. The older
   `crispasr-agent-mcp` command remains available.

4. Validate, authenticate with the GitHub account that owns `EmiyaKatuz`, and
   publish:

   ```powershell
   .\mcp-publisher.exe validate
   .\mcp-publisher.exe login github
   .\mcp-publisher.exe publish
   ```

5. Verify the registry record:

   ```powershell
   Invoke-RestMethod `
     "https://registry.modelcontextprotocol.io/v0.1/servers?search=io.github.emiyakatuz/crispasr-agent-transcriber"
   ```

For every later release, publish the new PyPI version first, update both
version fields in `server.json`, then run `validate` and `publish` again. See
the [official MCP Registry publishing guide](https://modelcontextprotocol.io/registry/quickstart).

### Step 4: connect other AI agents

Until the PyPI package is published, use the tagged GitHub command shown in
[Use with other AI agents](#use-with-other-ai-agents). After PyPI publication,
use this common launch command in MCP clients:

```powershell
uvx --from "crispasr-agent-transcriber[mcp]==0.3.2" crispasr-agent-mcp
```

First run `(Get-Command uvx).Source` in PowerShell. If a desktop client cannot
find `uvx`, use the returned absolute path as the configuration's `command`.

**Codex CLI**

```powershell
codex mcp add crispasr-agent-transcriber -- `
  uvx --from "crispasr-agent-transcriber[mcp]==0.3.2" crispasr-agent-mcp
```

Start a new Codex session and ask it to list the CrispASR tools.

**Claude Desktop and Cursor**

Claude Desktop uses `%APPDATA%\Claude\claude_desktop_config.json`. Cursor can
use `.cursor/mcp.json` in a project or `%USERPROFILE%\.cursor\mcp.json`
globally. Merge this server into the existing `mcpServers` object:

```json
{
  "mcpServers": {
    "crispasr-agent-transcriber": {
      "command": "uvx",
      "args": [
        "--from",
        "crispasr-agent-transcriber[mcp]==0.3.2",
        "crispasr-agent-mcp"
      ]
    }
  }
}
```

Restart the desktop client after saving the file.

**VS Code**

Create `.vscode/mcp.json` for one workspace, or run **MCP: Open User
Configuration** for a user-wide setup. VS Code uses `servers` instead of
`mcpServers`:

```json
{
  "servers": {
    "crispasr-agent-transcriber": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "crispasr-agent-transcriber[mcp]==0.3.2",
        "crispasr-agent-mcp"
      ]
    }
  }
}
```

Start the server from VS Code's MCP view and confirm that six tools appear:
health, backends, language detection, audio transcription, video
transcription, and folder transcription.

All clients still need local ffmpeg, CrispASR, and local model files. Give the
MCP tools explicit paths under the installed plugin's `models/` directory.
Connecting an MCP client does not upload media and does not automatically
download model files.
