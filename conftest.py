# conftest.py — project-root conftest loaded automatically by pytest before any test.
# Ensures sys.path is set correctly for all test modules.
import paths  # noqa: F401  (side-effect: wires sys.path)
