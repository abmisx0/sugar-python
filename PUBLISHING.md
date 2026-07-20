# Publishing to PyPI

The distribution name is **`sugar-defi`** (`sugar-python` is taken by an
unrelated project). The import name stays `sugar`. Build backend is `flit`.

## One-time setup

1. Create a PyPI account and a project-scoped **API token** at
   <https://pypi.org/manage/account/token/>.
2. Store it (either works):
   - `~/.pypirc`:
     ```ini
     [pypi]
       username = __token__
       password = pypi-AgE...your-token...
     ```
   - or export for the session: `export FLIT_USERNAME=__token__ FLIT_PASSWORD=pypi-AgE...`

## Release steps

```bash
# 0. from a clean checkout on main, in the project venv
source .venv/bin/activate

# 1. bump the version in BOTH places (keep them in sync)
#    pyproject.toml  ->  version = "X.Y.Z"
#    sugar/__init__.py -> __version__ = "X.Y.Z"

# 2. sanity: tests + lint + build + metadata check
python -m pytest tests/unit/ -q
ruff check sugar/ tests/
rm -rf dist && python -m flit build
python -m twine check dist/*        # both wheel + sdist must PASS

# 3. (recommended) dry-run on TestPyPI first
python -m flit publish --repository testpypi
#    then in a scratch venv:
#    pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple "sugar-defi[export]"

# 4. publish to PyPI
python -m flit publish

# 5. tag the release
git tag -a vX.Y.Z -m "vX.Y.Z" && git push origin main --follow-tags
```

After step 4, `pip install sugar-defi` (and `sugar-defi[export]`) works for
anyone. A GitHub **Release** also triggers `.github/workflows/python-publish.yml`
if you prefer publishing from CI (set the `PYPI_API_TOKEN` repo secret).

## Verify

```bash
python -m venv /tmp/verify && /tmp/verify/bin/pip install "sugar-defi[export]"
/tmp/verify/bin/python -c "import sugar; print(sugar.__version__)"
```
