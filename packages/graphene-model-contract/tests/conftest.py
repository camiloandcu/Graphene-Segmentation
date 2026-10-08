import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "fixture_exporter", Path(__file__).parents[1] / "examples/make_synthetic_package.py"
)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


@pytest.fixture
def documents():
    model = exporter.identity_graph()
    manifest, evaluation = exporter.fixture_documents(model)
    return model, manifest, evaluation
