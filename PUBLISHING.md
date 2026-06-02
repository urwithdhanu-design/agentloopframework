# Publishing agentloop (like npm registry)

Python’s public package registry is **[PyPI](https://pypi.org)** (Python Package Index). After you publish, anyone can install with:

```bash
pip install agentloop-framework
```

Then use the same imports as in this repo:

```python
from agentloop import Agent
```

> **Name on PyPI:** The name `agentloop` is already used by [another package](https://pypi.org/project/agentloop/). This project publishes as **`agentloop-framework`**. You can change the `name` in `pyproject.toml` before the first upload if you prefer another unique name.

---

## 1. One-time setup

1. Create an account: [pypi.org/account/register](https://pypi.org/account/register/)
2. Enable 2FA (recommended).
3. Create an **API token**: Account settings → API tokens → “Add API token” (scope: entire account or project `agentloop-framework`).
4. Save the token (starts with `pypi-`). Do not commit it.

Optional test registry (like npm’s dry-run registry):

- [test.pypi.org](https://test.pypi.org) — same flow, upload there first.

---

## 2. Install build tools

```powershell
cd "c:\Agentic AI\agentloop"
python -m pip install --upgrade build twine
```

---

## 3. Build the package

```powershell
python -m build
```

This creates `dist/agentloop_framework-0.1.0-py3-none-any.whl` and a `.tar.gz` source distribution.

Check the wheel:

```powershell
pip install dist\agentloop_framework-0.1.0-py3-none-any.whl
python -c "from agentloop import Agent; print(Agent)"
```

---

## 4. Upload to TestPyPI (recommended first)

```powershell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-..."   # your TestPyPI token from test.pypi.org

python -m twine upload --repository testpypi dist\*
```

Install from TestPyPI:

```powershell
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agentloop-framework
```

(`--extra-index-url` pulls dependencies like `httpx` from real PyPI.)

---

## 5. Upload to PyPI (production)

```powershell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-..."   # your PyPI token

python -m twine upload dist\*
```

After success, the package page will be:

**https://pypi.org/project/agentloop-framework/**

Users install with:

```bash
pip install agentloop-framework
pip install "agentloop-framework[openai]"   # optional httpx provider
```

---

## 6. Releasing a new version

1. Bump `version` in `pyproject.toml` (e.g. `0.1.0` → `0.1.1`).
2. Delete old artifacts: `Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue`
3. Rebuild and upload:

```powershell
python -m build
python -m twine upload dist\*
```

You cannot overwrite an existing version on PyPI; each upload must be a new version number.

---

## 7. CI publish (GitHub Actions)

If the repo is on GitHub, use the workflow in `.github/workflows/publish.yml`:

1. Add secret **`PYPI_API_TOKEN`** (PyPI token value, including `pypi-` prefix).
2. Create a GitHub **release tag** (e.g. `v0.1.0`) or run the workflow manually.

The workflow builds and publishes to PyPI when you tag a release.

---

## Other “deploy” options (not PyPI)

| Option | Use when |
|--------|----------|
| **Git install** | Internal only, no registry: `pip install git+https://github.com/you/agentloop.git` |
| **Private PyPI** | Company mirror (Artifactory, DevPI, AWS CodeArtifact) |
| **GitHub Packages** | `pip install` from GitHub with token |
| **Editable local** | Development: `pip install -e ".[dev]"` |

---

## npm vs Python (quick map)

| npm | Python |
|-----|--------|
| npm registry | [pypi.org](https://pypi.org) |
| `package.json` `name` | `pyproject.toml` `[project] name` |
| `npm publish` | `twine upload dist/*` |
| `npm install foo` | `pip install foo` |
| scoped `@org/pkg` | usually unique name like `agentloop-framework` |

---

## Checklist before first publish

- [ ] Unique PyPI name in `pyproject.toml`
- [ ] `LICENSE` present
- [ ] `README.md` describes install: `pip install agentloop-framework`
- [ ] `pytest` passes
- [ ] Tested upload on TestPyPI
- [ ] GitHub repo URL updated in `pyproject.toml` `[project.urls]`
