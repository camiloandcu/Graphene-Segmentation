"""Same-machine warmed validation inference; all inputs stay out of test."""
import platform
import resource
import time
from pathlib import Path
import numpy as np
import torch
from graphene_dataset_contract.common import identity, read_bytes, digest, decode
from .report import checkpoint, scope
from .predict import logits, decision
from graphene_training.engine import seed_all
from .experiments import environment


def benchmark(dataset, run, generation, *, size=None, geometry='letterbox', stride=384,
              device='cpu', warmup=2, repeats=5, threshold=None):
    if warmup < 1 or repeats < 2:
        raise ValueError('Benchmark needs warmup and repeated measurements')
    if threshold is not None and not 0 < threshold < 1:
        raise ValueError('Few-layer threshold must be strictly between zero and one')
    torch.set_num_threads(1)
    initialized = time.perf_counter()
    model, config, manifest, binding = checkpoint(run, generation, dataset)
    if device not in ('cpu', 'cuda') or (device == 'cuda' and not torch.cuda.is_available()):
        raise ValueError('Requested benchmark hardware unavailable')
    seed_all(config.seed)
    env=environment(config.model_copy(update={'device':device,'precision':'float32'}))
    model.to(device).eval()
    if device == 'cuda': torch.cuda.synchronize()
    initialization_seconds = time.perf_counter()-initialized
    size = size or config.input_size
    rows = []
    def synchronize():
        if device == 'cuda': torch.cuda.synchronize()
    for sample in manifest.samples:
        if sample.role != 'validation': continue
        def predict():
            start = time.perf_counter()
            image_bytes = read_bytes(Path(dataset)/sample.image_path)
            if digest(image_bytes) != sample.image_sha256:
                raise ValueError('Artifact changed after validation')
            rgb = decode(image_bytes)
            decoded = time.perf_counter()
            value = logits(model, rgb, device=device, size=size, geometry=geometry, stride=stride)
            synchronize(); inferred = time.perf_counter()
            prediction = decision(value, threshold)
            finished = time.perf_counter()
            return rgb, prediction, [(decoded-start)*1000, (inferred-decoded)*1000,
                                     (finished-inferred)*1000, (finished-start)*1000]
        for _ in range(warmup):
            predict()
        synchronize()
        if device == 'cuda': torch.cuda.reset_peak_memory_stats()
        phases = []
        for _ in range(repeats):
            synchronize()
            rgb, _, measured = predict()
            phases.append(measured)
        times = [p[3] for p in phases]
        rows.append({'sample_id': sample.sample_id, 'height': int(rgb.shape[0]), 'width': int(rgb.shape[1]),
                     'milliseconds': times, 'median_ms': float(np.median(times)),
                     'decode_and_integrity_ms': [p[0] for p in phases],
                     'inference_and_restoration_ms': [p[1] for p in phases],
                     'decision_ms': [p[2] for p in phases],
                     'p95_ms': float(np.percentile(times,95)),
                     'peak_cuda_allocated_bytes': torch.cuda.max_memory_allocated() if device=='cuda' else None,
                     'peak_cuda_reserved_bytes': torch.cuda.max_memory_reserved() if device=='cuda' else None})
    all_times = [t for r in rows for t in r['milliseconds']]
    if not all_times: raise ValueError('No validation benchmark inputs')
    result = {'schema_version':1, 'binding':scope(binding,size=size,geometry=geometry,stride=stride,threshold=threshold),
              'evaluation_environment':env, 'role':'validation', 'device':device, 'cpu':platform.processor() or platform.machine(),
              'gpu':torch.cuda.get_device_name() if device=='cuda' else None, 'torch':torch.__version__,
              'threads':1, 'warmup_per_image':warmup,'repeats_per_image':repeats,'samples':rows,
              'median_ms':float(np.median(all_times)), 'p95_ms':float(np.percentile(all_times,95)),
              'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
              'initialization_seconds':initialization_seconds,
              'initialization_definition':'Checkpoint/data verification, model construction/state loading and device transfer; measured separately before warmup',
              'definition':'Image read/checksum/decode, normalization, inference, original-coordinate restoration and decision; excludes plotting and initial checkpoint/data validation',
              'limitations':['Process RSS is cumulative high-water, not model-exclusive memory',
                             'Repeated image reads use the operating system cache; not cold disk latency',
                             'Same-machine pilot; intended laboratory hardware acceptance remains stakeholder-reviewed']}
    result['benchmark_fingerprint']=identity(result)
    return result
