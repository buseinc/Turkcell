"""Snapshot the installed pinned simulator sources used in the radio audit."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
NS3 = Path.home()/'ns3/ns-3.44'
FILES = [
    'src/lte/model/lte-ue-phy.cc','src/lte/model/lte-ue-phy.h',
    'src/lte/model/lte-spectrum-phy.cc','src/lte/model/lte-spectrum-phy.h',
    'src/lte/model/lte-interference.cc','src/lte/model/lte-interference.h',
    'src/lte/model/lte-chunk-processor.cc','src/lte/model/lte-chunk-processor.h',
    'src/lte/model/lte-spectrum-value-helper.cc',
    'src/lte/helper/lte-helper.cc','src/antenna/model/cosine-antenna-model.cc',
    'src/antenna/model/angles.cc','src/propagation/model/propagation-loss-model.cc',
    'src/lte/model/lte-enb-phy.cc','src/spectrum/model/multi-model-spectrum-channel.cc']

manifest = {'ns3_root':str(NS3),'version':(NS3/'VERSION').read_text().strip(),'files':{}}
assert manifest['version'] == '3.44'
for relative in FILES:
    source = NS3/relative
    data = source.read_bytes()
    target = HERE/'sources'/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(data)
    manifest['files'][relative] = hashlib.sha256(data).hexdigest()
(HERE/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
print('Pinned ns-3 sources captured:',len(FILES))
