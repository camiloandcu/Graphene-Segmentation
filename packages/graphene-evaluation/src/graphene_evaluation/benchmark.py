"""Same-machine warmed validation inference; all inputs stay out of test."""
import platform
import resource
import time
import numpy as np
import torch
from graphene_dataset_contract import iter_samples
from graphene_dataset_contract.common import identity
from .report import checkpoint, scope
from .predict import logits
from graphene_training.engine import seed_all
from .experiments import environment


def benchmark(dataset, run, generation, *, size=None, geometry='letterbox', stride=384,
              device='cpu', warmup=2, repeats=5):
    if warmup < 1 or repeats < 2:
        raise ValueError('Benchmark needs warmup and repeated measurements')
    model, config, _, binding = checkpoint(run, generation, dataset)
    if device not in ('cpu', 'cuda') or (device == 'cuda' and not torch.cuda.is_available()):
        raise ValueError('Requested benchmark hardware unavailable')
    seed_all(config.seed)
    env=environment(config.model_copy(update={'device':device,'precision':'float32'}))
    torch.set_num_threads(1)
    model.to(device).eval()
    size = size or config.input_size
    rows = []
    def synchronize():
        if device == 'cuda': torch.cuda.synchronize()
    for sample, rgb, _ in iter_samples(dataset, 'validation'):
        for _ in range(warmup):
            logits(model, rgb, device=device, size=size, geometry=geometry, stride=stride)
        synchronize()
        if device == 'cuda': torch.cuda.reset_peak_memory_stats()
        times = []
        for _ in range(repeats):
            synchronize(); start = time.perf_counter()
            logits(model, rgb, device=device, size=size, geometry=geometry, stride=stride)
            synchronize(); times.append((time.perf_counter()-start)*1000)
        rows.append({'sample_id': sample.sample_id, 'height': int(rgb.shape[0]), 'width': int(rgb.shape[1]),
                     'milliseconds': times, 'median_ms': float(np.median(times)),
                     'p95_ms': float(np.percentile(times,95)),
                     'peak_cuda_allocated_bytes': torch.cuda.max_memory_allocated() if device=='cuda' else None,
                     'peak_cuda_reserved_bytes': torch.cuda.max_memory_reserved() if device=='cuda' else None})
    all_times = [t for r in rows for t in r['milliseconds']]
    if not all_times: raise ValueError('No validation benchmark inputs')
    result = {'schema_version':1, 'binding':scope(binding,size=size,geometry=geometry,stride=stride,threshold=None),
              'evaluation_environment':env, 'role':'validation', 'device':device, 'cpu':platform.processor() or platform.machine(),
              'gpu':torch.cuda.get_device_name() if device=='cuda' else None, 'torch':torch.__version__,
              'threads':1, 'warmup_per_image':warmup,'repeats_per_image':repeats,'samples':rows,
              'median_ms':float(np.median(all_times)), 'p95_ms':float(np.percentile(all_times,95)),
              'process_peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
              'definition':'Decoded RGB input through normalization, inference, original-coordinate restoration; excludes file decoding and plotting',
              'limitations':['Process RSS is cumulative high-water, not model-exclusive memory',
                             'Same-machine pilot; intended laboratory hardware acceptance remains stakeholder-reviewed']}
    result['benchmark_fingerprint']=identity(result)
    return result
