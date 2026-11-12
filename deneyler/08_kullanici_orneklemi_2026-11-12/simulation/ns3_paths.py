"""Locate the pinned simulator without depending on the original computer."""
import os
from pathlib import Path


def ns3_root():
    configured = os.environ.get('NS3_ROOT')
    candidates = [Path(configured).expanduser()] if configured else [
        Path.home() / 'ns3/ns-3.44',
        Path.home() / 'ns-allinone-3.44/ns-3.44',
        Path('/home/umut/ns-allinone-3.44/ns-3.44'),
    ]
    for root in candidates:
        version = root / 'VERSION'
        if version.is_file() and version.read_text().strip() == '3.44':
            return root.resolve()
    raise RuntimeError(
        'ns-3.44 not found. Set NS3_ROOT to a configured ns-3.44 directory. '
        'Checked: ' + ', '.join(map(str, candidates)))
