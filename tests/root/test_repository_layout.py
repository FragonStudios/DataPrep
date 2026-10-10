from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_root_files_exist():
    for filename in (".gitignore", ".editorconfig", "Makefile", "README.md"):
        assert (ROOT / filename).is_file()


def test_readme_mentions_dataprep():
    assert "DataPrep" in (ROOT / "README.md").read_text(encoding="utf-8")
