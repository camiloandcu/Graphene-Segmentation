# Graphene dataset contract

Offline dataset preparation for the Graphene Colab trainer. Validates the supported
COCO polygon export, requires explicit human review and split decisions, and
produces checksummed original-resolution images and canonical masks. No cloud
account or inference runtime is required.

Install the local model and dataset packages together; use the
[dataset workflow](../../docs/13_VALIDATED_DATASETS.md) for setup, review fields,
commands, limits and consumer examples. Python 3.10–3.13 is supported by package
metadata; the verified environment is Python 3.12 on Linux.

```python
from graphene_dataset_contract import check, iter_samples

manifest = check("reviewed-dataset")
for sample, rgb, mask in iter_samples("reviewed-dataset", "train"):
    # rgb: original H×W×3 uint8; mask: original H×W uint8
    # Labels 0 background, 1 few-layer, 2 bulk, 255 ignored.
    pass
```

The supplied lab export remains blocked until genuine label/group/split review is
provided. Successful validation records reviewer claims; it does not authenticate
physical thickness or certify independent evaluation. Predictions and unknown
annotation origins are ineligible under v1.

## Partial schema 2

Package 2.0 continues to check dense schema 1 without changing its semantics.
`prepare --partial` produces a schema-2 review template; a schema-2 review also
selects partial preparation explicitly. Unannotated pixels remain 255. Source-bound
reviewed background anchors or positively reviewed blank images supply class 0.
Consumers reconstruct supervision from declared source polygons and reviewed
anchors, in addition to checking digests and split/group invariants. Source support
and supervised support remain distinct. V1-only schema validators reject v2.
See [partial review and training](../../docs/14_COLAB_BASELINE_TRAINING.md).
