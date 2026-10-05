# Making ax-mcp private and stopping the PyPI releases

Status: **documented, not executed.** The decision is with Jake and Kavitha (ax-stack#4922,
user decision 2026-10-02). Nothing in Phase 1 of that issue waits on it. This page records
what depends on the repository being public today, what Phase 1 removes from that list,
and the steps left when the decision is taken.

## What depends on `ax-mcp` being public today

| Consumer | How | Breaks when |
| --- | --- | --- |
| Every `.mcp.json` the ax-forge checkout and wheel write | `uvx --from ${AX_MCP_PATH:-axiomatic-mcp} axiomatic-<op>` resolves `axiomatic-mcp` from PyPI | PyPI releases stop |
| ax-forge `e2e-claude.yml` | clones this repo anonymously | repo goes private |
| ax-stack's own agent | pins `axiomatic-mcp==0.1.18` in `api/src/config/mcp/mcp_config_*.json` and `api/Dockerfile` | PyPI releases stop |
| Public README links and the key sign-up form | point at the GitHub repo and the PyPI page | repo goes private |

## What Phase 1 of #4922 removes from that list

The AxiPH plugin bundles this repo's source under `<plugin>/operators/` and launches the
servers with `uvx --from <plugin root>/operators` (Claude Code, Cursor) or from a uv tool
installed from that tree (Codex, opencode, Copilot, pi, portable). The plugin install path
therefore depends on neither PyPI nor GitHub access to this repo. The ax-forge release
job clones this repo with the same read token it already uses for the content repos and
checks out the ref `manifest.yaml` pins.

Still on PyPI after Phase 1: the ax-forge wheel and checkout paths (`axiph install`),
which keep today's `.mcp.json` shape, and ax-stack's agent.

## Steps when approved

1. Final `axiomatic-mcp` release on PyPI whose README points at the plugin and at
   `AX_MCP_PATH=<clone>` for the checkout path.
2. Disable the PyPI job in `release.yml`; leave existing versions up.
3. ax-forge: switch the wheel and checkout `.mcp.json` seeds to a cloned tree
   (`AX_MCP_PATH`) or to the plugin's bundled operators; drop the anonymous clone in
   `e2e-claude.yml` for the token the release job already uses.
4. ax-stack: give the API build a read token for this repo, or move its agent
   in-process (follow-up ticket).
5. Flip the repository visibility.

The acceptance criterion "nothing in the public install path depends on `ax-mcp` being
public" is met for the plugin path at Phase 1 regardless of these steps.
