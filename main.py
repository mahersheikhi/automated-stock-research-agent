from app.cli import run_cli
from app.version import __version__

print(f"AI Stock Research Assistant v{__version__}")

if __name__ == "__main__":
    run_cli()