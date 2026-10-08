"""Create synthetic UI fixtures; no lab quality or trained-model claim."""
import argparse
import importlib.util
import json
import zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('exporter',root/'packages/graphene-model-contract/examples/make_synthetic_package.py')
exporter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=Path)
out=parser.parse_args().output
out.mkdir(parents=True,exist_ok=True)
model=exporter.identity_graph()
for filename,name,reported in [('unmeasured.zip','Synthetic identity fixture',False),('reported.zip','<img src=x onerror=alert(1)> Synthetic lab model with a long name for local workflow verification only',True)]:
    manifest,evaluation=exporter.fixture_documents(model)
    manifest['name']=name
    if reported:
        for key in ('dataset_fingerprint','split_fingerprint'):
            manifest['provenance'][key]={'status':'known','value':'synthetic-fixture-'+key}
        evaluation['evidence']={'kind':'reported','source':'Synthetic report for UI verification only','dataset_fingerprint':manifest['provenance']['dataset_fingerprint']['value'],'split_fingerprint':manifest['provenance']['split_fingerprint']['value'],'metrics':[{'name':'few-layer pixel recall','value':0.5,'unit':'fraction','support':2,'definition':'Illustrative fixture only, not measured lab performance','unavailable_reason':None,'support_unknown_reason':None}]}
    with zipfile.ZipFile(out/filename,'w') as archive:
        for member,data in [('model.onnx',model),('manifest.json',json.dumps(manifest).encode()),('evaluation.json',json.dumps(evaluation).encode())]: archive.writestr(member,data)
(out/'invalid.zip').write_bytes(b'not a valid package')
print(out)
