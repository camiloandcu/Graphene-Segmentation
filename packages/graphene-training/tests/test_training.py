import copy
import json
from pathlib import Path
import numpy as np
import pytest
import torch
from graphene_dataset_contract.common import identity
from graphene_training import TrainingConfig, preflight, run, resume
from graphene_training.data import RoleDataset, transform
from graphene_training.objective import loss, metrics
from graphene_training.storage import inspect, load_state, persist


def tiny():
    return torch.nn.Sequential(torch.nn.Conv2d(3, 8, 3, padding=1), torch.nn.ReLU(),
                               torch.nn.Dropout2d(.2), torch.nn.Conv2d(8, 3, 1))


@pytest.fixture(autouse=True)
def cpu_threads():
    torch.set_num_threads(1)


def test_ignore_gradients_and_background_loss():
    logits = torch.zeros(1,3,2,2, requires_grad=True)
    target = torch.tensor([[[0,1],[2,255]]])
    value = loss(logits,target); value.backward()
    assert torch.all(logits.grad[0,:,1,1] == 0)
    changed = logits.detach().clone(); changed[0,:,1,1] = torch.tensor([100.,-100.,200.])
    assert loss(changed,target) == value.detach()
    bg = loss(torch.zeros(1,3,2,2), torch.zeros(1,2,2,dtype=torch.long))
    assert float(bg) == pytest.approx(np.log(3))
    with pytest.raises(ValueError, match='ignored'): loss(logits,torch.full_like(target,255))


def test_metrics_absence_is_unavailable():
    m = metrics([[1,0,0],[0,0,0],[0,0,0]])
    assert m['classes'][1]['dice'] is None
    assert m['classes'][1]['precision'] is None
    assert m['foreground_macro_dice'] is None
    assert metrics([[0,1,0],[0,1,0],[0,0,1]])['foreground_macro_dice'] == pytest.approx((2/3+1)/2)


def test_shared_geometry_and_padding(dataset):
    cfg = TrainingConfig(input_size=64)
    evidence = preflight(dataset,cfg)
    assert evidence['roles']['train']['samples'] == 3
    data = RoleDataset(dataset,'train',cfg)
    _, rgb, mask = data.items[0]
    x,y,g = transform(rgb,mask,64)
    assert x.shape == (3,64,64)
    assert set(torch.unique(y).tolist()) == {0,1,2,255}
    assert torch.all(y[:g.top] == 255)
    with pytest.raises(ValueError): RoleDataset(dataset,'test',cfg)


def test_resume_matches_uninterrupted_cpu(dataset,tmp_path):
    cfg = TrainingConfig(input_size=64,epochs=3,horizontal_flip=.5,vertical_flip=.5)
    full, interrupted = tmp_path/'full',tmp_path/'interrupted'
    run(dataset,cfg,full,_fixture_factory=tiny)
    run(dataset,cfg,interrupted,_fixture_factory=tiny,_stop_after=1)
    # An incomplete staging epoch cannot become authoritative.
    (interrupted/'epochs'/'.staging-abandoned').mkdir()
    (interrupted/'epochs'/'.staging-abandoned'/'checkpoint.pt').write_bytes(b'incomplete')
    assert inspect(interrupted)['last'] == 'epoch-000001'
    resume(dataset,interrupted,'epoch-000001',_fixture_factory=tiny)
    a,b = load_state(full,'epoch-000003'),load_state(interrupted,'epoch-000003')
    for key,value in a['model'].items(): assert torch.equal(value,b['model'][key])
    assert a['scheduler'] == b['scheduler']
    assert torch.equal(a['generator'],b['generator'])
    assert torch.equal(a['rng']['torch'],b['rng']['torch'])
    ha = json.loads((full/'epochs'/'epoch-000003'/'history.json').read_text())
    hb = json.loads((interrupted/'epochs'/'epoch-000003'/'history.json').read_text())
    for row in ha+hb: row.pop('elapsed_seconds')
    assert ha == hb
    assert inspect(full)['best'] == inspect(interrupted)['best']
    dest = tmp_path/'durable'
    persist(interrupted,dest)
    assert inspect(dest)['last'] == 'epoch-000003'
    assert inspect(dest)['best_checkpoint_sha256'] == inspect(full)['best_checkpoint_sha256']


def test_corruption_and_mismatch_no_mutation(dataset,tmp_path):
    output = tmp_path/'run'
    run(dataset,TrainingConfig(input_size=64,epochs=2),output,_fixture_factory=tiny,_stop_after=1)
    record = json.loads((output/'run.json').read_text())
    record['environment']['packages']['torch'] = 'incompatible'
    record['run_fingerprint'] = identity({k:v for k,v in record.items() if k != 'run_fingerprint'})
    # Changing run metadata alone contradicts generation identity.
    (output/'run.json').write_text(json.dumps(record))
    before = {p: p.read_bytes() for p in output.rglob('*') if p.is_file()}
    with pytest.raises(ValueError,match='identity'): resume(dataset,output,'epoch-000001',_fixture_factory=tiny)
    assert before == {p: p.read_bytes() for p in output.rglob('*') if p.is_file()}


def test_missing_background_stops_before_initialization(dataset,tmp_path,monkeypatch):
    import graphene_training.engine as engine
    def fail(*a,**k): raise AssertionError('Model initialization must not happen')
    monkeypatch.setattr(engine,'initialize',fail)
    import graphene_training.data as data
    original = data.iter_samples
    def without_bg(directory,role):
        for s,rgb,mask in original(directory,role):
            mask[mask == 0] = 255
            yield s,rgb,mask
    monkeypatch.setattr(data,'iter_samples',without_bg)
    with pytest.raises(ValueError,match=r'missing \[0\]'):
        run(dataset,TrainingConfig(input_size=64),tmp_path/'forbidden')
    assert not (tmp_path/'forbidden').exists()


def test_byte_corruption_is_rejected(dataset,tmp_path):
    output = tmp_path/'run'
    run(dataset,TrainingConfig(input_size=64,epochs=1),output,_fixture_factory=tiny)
    checkpoint = output/'epochs'/'epoch-000001'/'checkpoint.pt'
    checkpoint.write_bytes(checkpoint.read_bytes() + b'tampered')
    with pytest.raises(ValueError,match='checksum'): inspect(output)


def test_best_is_distinct_and_ties_choose_earlier(dataset,tmp_path,monkeypatch):
    import graphene_training.engine as engine
    scores = iter([.8,.8,.5])
    def measured(*args): return {'foreground_macro_dice': next(scores)}
    monkeypatch.setattr(engine,'evaluate',measured)
    output = tmp_path/'run'
    status = run(dataset,TrainingConfig(input_size=64,epochs=3),output,_fixture_factory=tiny)
    assert status['last'] == 'epoch-000003'
    assert status['best'] == 'epoch-000001'
    assert status['best_score'] == .8
    assert status['best_checkpoint_sha256'] != __import__('graphene_training.storage',fromlist=['file_hash']).file_hash(output/'epochs'/'epoch-000003'/'checkpoint.pt')


def test_failed_epoch_repeats_from_completed_boundary(dataset,tmp_path,monkeypatch):
    import graphene_training.engine as engine
    output = tmp_path/'run'
    cfg = TrainingConfig(input_size=64,epochs=3,horizontal_flip=.5)
    original = engine.save_generation
    def interrupted(*args,**kwargs):
        if args[1] == 2: raise OSError('Simulated disk failure')
        return original(*args,**kwargs)
    monkeypatch.setattr(engine,'save_generation',interrupted)
    with pytest.raises(OSError,match='disk failure'): run(dataset,cfg,output,_fixture_factory=tiny)
    assert inspect(output)['last'] == 'epoch-000001'
    monkeypatch.setattr(engine,'save_generation',original)
    resume(dataset,output,'epoch-000001',_fixture_factory=tiny)
    full = tmp_path/'full'; run(dataset,cfg,full,_fixture_factory=tiny)
    for k,v in load_state(full,'epoch-000003')['model'].items():
        assert torch.equal(v,load_state(output,'epoch-000003')['model'][k])


def test_persistence_failure_keeps_previous_durable_epoch(dataset,tmp_path,monkeypatch):
    import graphene_training.storage as storage
    output,durable = tmp_path/'run',tmp_path/'durable'
    cfg = TrainingConfig(input_size=64,epochs=2,persistence_directory=str(durable))
    real_copy = storage.shutil.copyfile
    def fail_new(source,destination):
        if 'epoch-000002' in str(source): raise OSError('Simulated Drive failure')
        return real_copy(source,destination)
    monkeypatch.setattr(storage.shutil,'copyfile',fail_new)
    with pytest.raises(OSError,match='Drive failure'): run(dataset,cfg,output,_fixture_factory=tiny)
    assert inspect(durable)['last'] == 'epoch-000001'
    assert inspect(output)['last'] == 'epoch-000002'
    monkeypatch.setattr(storage.shutil,'copyfile',real_copy)
    resume(dataset,output,'epoch-000002',_fixture_factory=tiny)
    assert inspect(durable)['last'] == 'epoch-000002'


def test_safe_loader_rejects_non_tensor_objects(dataset,tmp_path):
    import graphene_training.storage as storage
    output = tmp_path/'run'
    run(dataset,TrainingConfig(input_size=64,epochs=1),output,_fixture_factory=tiny)
    gen = output/'epochs'/'epoch-000001'
    torch.save({'unsafe': Path('/tmp/fixture')},gen/'checkpoint.pt')
    meta = json.loads((gen/'metadata.json').read_text())
    meta['best_checkpoint_sha256'] = storage.file_hash(gen/'checkpoint.pt')
    (gen/'metadata.json').write_text(json.dumps(meta))
    marker = json.loads((gen/'complete.json').read_text())
    marker['files'] = {n:storage.file_hash(gen/n) for n in storage.MEMBERS}
    (gen/'complete.json').write_text(json.dumps(marker))
    with pytest.raises(ValueError,match='safe supported'): storage.load_state(output,'epoch-000001')


def test_writer_lock(dataset,tmp_path):
    from graphene_training.storage import lock
    output = tmp_path/'run';output.mkdir()
    with lock(output):
        with pytest.raises(ValueError,match='Another writer'):
            with lock(output): pass


def test_source_environment_mismatch_rejected_before_write(dataset,tmp_path,monkeypatch):
    import graphene_training.engine as engine
    output = tmp_path/'run'
    run(dataset,TrainingConfig(input_size=64,epochs=2),output,_fixture_factory=tiny,_stop_after=1)
    original = engine.environment
    def incompatible(config):
        record = original(config); record['training_source_sha256'] = '0'*64
        return record
    monkeypatch.setattr(engine,'environment',incompatible)
    before = {p:p.read_bytes() for p in output.rglob('*') if p.is_file()}
    with pytest.raises(ValueError,match='incompatible'): resume(dataset,output,'epoch-000001',_fixture_factory=tiny)
    assert before == {p:p.read_bytes() for p in output.rglob('*') if p.is_file()}


def test_dataset_role_fingerprint_mismatch_before_write(dataset,tmp_path,monkeypatch):
    import graphene_training.engine as engine
    output = tmp_path/'run'
    run(dataset,TrainingConfig(input_size=64,epochs=2),output,_fixture_factory=tiny,_stop_after=1)
    original = engine.preflight
    def changed(*args):
        record=original(*args);record['split_fingerprint']='0'*64;return record
    monkeypatch.setattr(engine,'preflight',changed)
    before = {p:p.read_bytes() for p in output.rglob('*') if p.is_file()}
    with pytest.raises(ValueError,match='changed'): resume(dataset,output,'epoch-000001',_fixture_factory=tiny)
    assert before == {p:p.read_bytes() for p in output.rglob('*') if p.is_file()}


def test_pretrained_cache_corruption_has_no_random_fallback(tmp_path):
    from graphene_training.model import initialize, URL
    cache = tmp_path/'weights';cache.mkdir()
    (cache/URL.rsplit('/',1)[1]).write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='digest'): initialize(cache)


def test_original_coordinate_scoring_ignores_unknown_and_padding(dataset):
    from graphene_training.objective import evaluate
    config=TrainingConfig(input_size=64)
    data=RoleDataset(dataset,'validation',config)
    class PaddingTrap(torch.nn.Module):
        def forward(self,x):
            logits=torch.zeros(len(x),3,64,64)
            logits[:,1]=2
            logits[:,2,:10]=100
            logits[:,2,53:]=100
            return logits
    result=evaluate(PaddingTrap(),data,config)
    expected=np.zeros((3,3),dtype=np.int64)
    for _,_,mask in data.items:
        for c in range(3): expected[c,1]+=int((mask==c).sum())
    assert result['confusion_matrix'] == expected.tolist()
    assert sum(sum(row) for row in result['confusion_matrix']) == 304
    assert result['foreground_macro_dice'] == pytest.approx(120/424)


def test_training_and_selection_never_request_test_role(dataset,tmp_path,monkeypatch):
    import graphene_training.data as data
    original=data.iter_samples; requested=[]
    def monitored(directory,role):
        requested.append(role)
        assert role in ('train','validation')
        yield from original(directory,role)
    monkeypatch.setattr(data,'iter_samples',monitored)
    run(dataset,TrainingConfig(input_size=64,epochs=1),tmp_path/'run',_fixture_factory=tiny)
    assert set(requested)=={'train','validation'}


def test_persistence_cannot_mutate_generation_directory(dataset,tmp_path):
    output=tmp_path/'run'
    run(dataset,TrainingConfig(input_size=64,epochs=1),output,_fixture_factory=tiny)
    before={p:p.read_bytes() for p in output.rglob('*') if p.is_file()}
    with pytest.raises(ValueError,match='separate'):
        persist(output,output/'epochs'/'epoch-000001')
    assert before=={p:p.read_bytes() for p in output.rglob('*') if p.is_file()}


def test_changed_dataset_after_preflight_is_rejected(dataset):
    with pytest.raises(ValueError,match='after preflight'):
        RoleDataset(dataset,'train',TrainingConfig(input_size=64),expected_fingerprint='0'*64)


def test_actual_unet_architecture_resume_matches_cpu(dataset,tmp_path):
    from graphene_training.model import architecture
    config=TrainingConfig(input_size=64,epochs=2,horizontal_flip=.5)
    full,split=tmp_path/'full-unet',tmp_path/'split-unet'
    run(dataset,config,full,_fixture_factory=architecture)
    run(dataset,config,split,_fixture_factory=architecture,_stop_after=1)
    resume(dataset,split,'epoch-000001',_fixture_factory=architecture)
    a,b=load_state(full,'epoch-000002'),load_state(split,'epoch-000002')
    assert all(torch.equal(v,b['model'][k]) for k,v in a['model'].items())
    assert a['scheduler']==b['scheduler']
    for pid,values in a['optimizer']['state'].items():
        for key,value in values.items():
            assert torch.equal(value,b['optimizer']['state'][pid][key])
