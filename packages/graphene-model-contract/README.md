# Graphene model contract

A shared v1 ONNX package and geometry contract for a Colab exporter and local
microscopy app. It defines canonical classes, explicit preprocessing, original
coordinates and bounded CPU compatibility validation.

This library does not train a model, certify lab accuracy or provide the app's
upload/predict workflow. The supplied synthetic example is only a contract fixture.

Install core preprocessing/types from the repository root:

```bash
python -m pip install ./packages/graphene-model-contract
```

For Linux CPU package validation:

```bash
python -m pip install './packages/graphene-model-contract[validation]'
graphene-model-check /path/to/model-package.zip
```

Core supports Python 3.10–3.13; tested versions and dependency locks are recorded
in the project evidence. The local backend has an optional `models` extra;
its default runtime remains independent of this package.

[Full contract and export guidance](../../docs/10_PORTABLE_MODEL_CONTRACT.md).
JSON Schemas are shipped in `graphene_model_contract/schemas`. Structural schemas
and the strict parser are complemented by cross-document, graph and resource checks.
