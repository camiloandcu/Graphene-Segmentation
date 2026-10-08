import json

import numpy as np
import pytest

from graphene_model_contract import ContractError, parse_contract
from graphene_model_contract.geometry import (
    GeometryLimits,
    TileAccumulator,
    decide,
    prepare_letterbox,
    prepare_tiles,
    restore_letterbox,
    tile_records,
)


def manifest_for(documents, geometry=None, decision=None):
    _, raw, report = documents
    if geometry:
        raw["geometry"] = report["geometry"] = geometry
    if decision:
        raw["decision"] = report["decision"] = decision
    return parse_contract(json.dumps(raw).encode(), json.dumps(report).encode())[0]


def test_independent_rgb_normalization_layout_and_asymmetric_padding(documents):
    _, raw, report = documents
    raw["preprocessing"]["mean"] = report["preprocessing"]["mean"] = [0.5, 0.25, 0.0]
    raw["preprocessing"]["std"] = report["preprocessing"]["std"] = [0.5, 0.25, 1.0]
    manifest = manifest_for(documents)
    rgb = np.zeros((5, 9, 3), dtype=np.uint8)
    rgb[:] = [255, 0, 128]
    prepared = prepare_letterbox(rgb, manifest)
    assert prepared.geometry.original_hw == (5, 9)
    assert prepared.geometry.resized_hw == (18, 32)
    assert (prepared.geometry.top, prepared.geometry.left) == (7, 0)
    np.testing.assert_allclose(
        prepared.tensor[0, :, 10, 10], [1.0, -1.0, 128 / 255], atol=1e-7
    )
    np.testing.assert_allclose(
        prepared.tensor[0, :, 0, 0], [-1.0, -1.0, 0.0], atol=1e-7
    )
    assert prepared.tensor.flags.c_contiguous and prepared.tensor.dtype == np.float32


@pytest.mark.parametrize("hw", [(32, 32), (17, 32), (32, 17), (31, 32), (32, 31)])
def test_inverse_coordinates_match_independent_spatial_expectation(documents, hw):
    manifest = manifest_for(documents)
    prepared = prepare_letterbox(np.zeros((*hw, 3), dtype=np.uint8), manifest)
    record = prepared.geometry
    logits = np.full((1, 3, 32, 32), -999.0, dtype=np.float32)
    h, w = hw
    # These shapes have scale=1; no interpolation ambiguity hides coordinate bugs.
    y, x = np.indices(hw)
    planes = np.stack((x, y, x + y)).astype(np.float32)
    logits[0, :, record.top : record.top + h, record.left : record.left + w] = planes
    restored = restore_letterbox(logits, record)
    np.testing.assert_array_equal(restored, planes)
    assert set(np.unique(decide(restored, manifest))) <= {0, 1, 2}


def test_float_logit_resize_has_independent_bilinear_ramp_values(documents):
    manifest = manifest_for(documents)
    record = prepare_letterbox(np.zeros((64, 64, 3), dtype=np.uint8), manifest).geometry
    logits = np.zeros((1, 3, 32, 32), dtype=np.float32)
    logits[0, 1] = np.arange(32, dtype=np.float32)[None, :]
    result = restore_letterbox(logits, record)
    # Pixel-center bilinear mapping: clip((x+.5)/2-.5, 0,31).
    expected = np.clip((np.arange(64) + 0.5) / 2 - 0.5, 0, 31)
    np.testing.assert_allclose(result[1, 20], expected, atol=1e-6)


@pytest.mark.parametrize("hw", [(17, 19), (33, 49), (64, 75)])
def test_native_tiles_preserve_coordinates_edges_and_mean_logits(documents, hw):
    manifest = manifest_for(
        documents,
        {"mode": "tiles", "version": 1, "stride": [16, 16], "merge": "mean_logits"},
    )
    h, w = hw
    y, x = np.indices(hw)
    rgb = np.stack((x % 256, y % 256, (x + y) % 256), axis=-1).astype(np.uint8)
    accumulator = TileAccumulator(hw, manifest)
    reference = np.zeros((3, h, w), np.float64)
    counts = np.zeros(hw, np.int32)
    for index, prepared in enumerate(prepare_tiles(rgb, manifest)):
        record = prepared.geometry
        oy, ox = record.origin_yx
        rh, rw = record.resized_hw
        # Independent arithmetic expectation on original pixels, including overlaps.
        expected = (
            rgb[oy : oy + rh, ox : ox + rw].transpose(2, 0, 1).astype(np.float32) / 255
        )
        np.testing.assert_allclose(prepared.tensor[0, :, :rh, :rw], expected, atol=1e-7)
        logits = prepared.tensor.copy() + np.float32(index)
        accumulator.add(logits, record)
        reference[:, oy : oy + rh, ox : ox + rw] += expected + index
        counts[oy : oy + rh, ox : ox + rw] += 1
    np.testing.assert_allclose(
        accumulator.finish(), reference / counts[None], atol=2e-6
    )
    assert np.all(counts > 0)


def test_missing_duplicate_tiles_and_resource_budget_rejected(documents):
    manifest = manifest_for(
        documents,
        {"mode": "tiles", "version": 1, "stride": [1, 1], "merge": "mean_logits"},
    )
    with pytest.raises(ContractError, match="work budget"):
        tile_records((128, 128), manifest, GeometryLimits(max_tiles=10))
    with pytest.raises(ContractError, match="pixel budget"):
        tile_records((128, 128), manifest, GeometryLimits(max_pixels=10))
    accumulator = TileAccumulator((32, 32), manifest)
    prepared = next(prepare_tiles(np.zeros((32, 32, 3), np.uint8), manifest))
    with pytest.raises(ContractError, match="contributions"):
        accumulator.finish()
    accumulator.add(np.zeros((1, 3, 32, 32), np.float32), prepared.geometry)
    with pytest.raises(ContractError, match="duplicate"):
        accumulator.add(prepared.tensor, prepared.geometry)


@pytest.mark.parametrize(
    "array",
    [
        np.zeros((32, 32, 3), np.uint16),
        np.zeros((32, 32), np.uint8),
        np.zeros((3, 32, 32), np.uint8),
        np.zeros((0, 32, 3), np.uint8),
    ],
)
def test_unsupported_pixels_rejected(documents, array):
    with pytest.raises(ContractError):
        prepare_letterbox(array, manifest_for(documents))


def test_threshold_inclusive_and_background_bulk_tie(documents):
    threshold = {
        "kind": "few_layer_threshold",
        "threshold": 0.5,
        "ties": "lower_id",
        "evidence_ref": "evaluation",
    }
    manifest = manifest_for(documents, decision=threshold)
    logits = np.array(
        [[[0, 1, 0]], [[np.log(2), -1, 0]], [[0, 1, 2]]], dtype=np.float32
    )
    # Exact boundary case: exp(0), exp(log(2)), exp(0) -> p_few = 0.5.
    result = decide(logits, manifest)
    np.testing.assert_array_equal(result, [[1, 0, 2]])
    argmax = manifest_for(
        documents,
        decision={"kind": "argmax", "ties": "lower_id", "evidence_ref": "evaluation"},
    )
    np.testing.assert_array_equal(
        decide(np.zeros((3, 2, 2), np.float32), argmax), np.zeros((2, 2), np.uint8)
    )
