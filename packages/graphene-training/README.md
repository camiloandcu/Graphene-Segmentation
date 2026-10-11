# Graphene baseline training

A separate CLI for a pretrained three-class U-Net/ResNet-18 baseline, reviewed
partial labels, supervised development metrics, and completed-epoch recovery.
It consumes the dataset contract rather than application predictions or directories
of unreviewed images. There is no final-test evaluation or ONNX export here.

See [setup, Colab and recovery](../../docs/14_COLAB_BASELINE_TRAINING.md) and
[verification and remaining real-data gates](../../docs/review/14_WI_06_VERIFICATION.md).
The notebook calls this same package; training does not become an app dependency.

```bash
graphene-train check DATASET --config CONFIG.json
graphene-train run DATASET --config CONFIG.json --output NEW_RUN
graphene-train inspect RUN
graphene-train resume DATASET --run RUN --checkpoint epoch-000001
graphene-train persist RUN DURABLE_COPY
```

The best checkpoint is selected by masked foreground macro Dice in original image
coordinates. `inspect` reports its generation and SHA-256 separately from the last
completed epoch. Unknown pixels are excluded; these scores cannot establish
complete-image detection accuracy when annotation coverage is uncertain.
