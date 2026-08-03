import importlib
import pkgutil
import tomllib
import unittest
from pathlib import Path

import patternwright


ROOT = Path(__file__).resolve().parent.parent


class PackageTests(unittest.TestCase):
    def test_every_runtime_module_imports(self):
        for module in pkgutil.iter_modules(patternwright.__path__):
            if module.name != "__main__":
                importlib.import_module("patternwright." + module.name)

    def test_runtime_declares_no_dependencies(self):
        project = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        self.assertNotIn("dependencies", project)

    def test_runtime_has_no_book_or_scribewright_identity(self):
        shipped_roots = (ROOT / "src" / "patternwright", ROOT / "skills")
        paths = [
            path
            for root in shipped_roots
            for path in root.rglob("*")
            if path.is_file() and path.suffix in {".py", ".toml", ".md", ".yaml"}
        ]
        source = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
        self.assertNotIn("our revels", source)
        self.assertNotIn("scribewright", source)

    def test_package_has_no_pypi_upload_guard(self):
        project = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        self.assertIn("Private :: Do Not Upload", project["classifiers"])

    def test_public_version_matches_project_metadata(self):
        project = tomllib.loads(
            (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        )["project"]
        self.assertEqual(patternwright.__version__, project["version"])


if __name__ == "__main__":
    unittest.main()
