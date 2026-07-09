# Publishing checklist

Use this before creating the first public GitHub repository.

## Do not commit

The following files are local-only and are ignored by `.gitignore`:

- `.env`
- `config.json`
- `Bewerbungen/`
- `assets/lebenslauf.pdf`
- `templates/anschreiben.odt`
- `_localtest/`
- `.agents/`
- `.codex/`
- `.tmp/`
- `__pycache__/`
- `build/`
- `dist/`

Keep these files on your machine. They are not required for the public source
release.

## Public files to include

- `app/`
- `run.py`
- `requirements.txt`
- `build.ps1`
- `README.md`
- `.env.example`
- `config.example.json`
- `.gitignore`
- `LICENSE`
- `PUBLISHING.md`

## Before first push

1. Run the syntax check:
   ```powershell
   python -c "import ast, pathlib; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8')) for p in pathlib.Path('app').glob('*.py')]; print('syntax ok')"
   ```
2. Run the app in mock mode with a copied `config.json`.
3. Run `git status --short` after `git init` and confirm no private file appears.
4. If a real secret was ever pushed by accident, rotate it at the provider.
