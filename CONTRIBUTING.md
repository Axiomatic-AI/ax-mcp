# Contributing to Axiomatic MCP Servers

Thank you for contributing! Here's how to submit a pull request.

## Making a Pull Request

### 1. Fork and Clone
```bash
git clone https://github.com/YOUR_USERNAME/ax-mcp.git
cd ax-mcp
```

### 2. Create a Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes
- Test your changes thoroughly
- Follow existing code style
- Update docs if needed

### 4. Commit
```bash
git commit -m "feat: add new feature"
```

Use conventional commits:
- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation
- `test:` tests
- `chore:` maintenance

### 5. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then:
1. Go to [github.com/Axiomatic-AI/ax-mcp](https://github.com/Axiomatic-AI/ax-mcp)
2. Click "Pull requests" → "New pull request"
3. Select your fork and branch
4. Fill in the PR template
5. Reference any issues (e.g., "Fixes #123")

## Development Setup

```bash
# Install dependencies
uv pip install -e .

# Set API key
export AXIOMATIC_API_KEY="your-api-key"

# Test locally
uvx --from . equations  # or documents, annotations, pic, plots, all
```

## Questions?

- [Discord](https://discord.gg/KKU97ZR5)
- [Issues](https://github.com/Axiomatic-AI/ax-mcp/issues)
- Email: developers@axiomatic-ai.com