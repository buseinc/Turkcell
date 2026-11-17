"""Windows launcher with a bounded WSL preflight; never restarts user services."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--distro')
    parser.add_argument('--workers',type=int,default=3)
    args = parser.parse_args()
    state = {'checked_at_utc':datetime.now(timezone.utc).isoformat()}
    try:
        check = subprocess.run(['wsl','--list','--quiet'],capture_output=True,timeout=30)
        if check.returncode:
            raise RuntimeError(check.stderr.decode('utf-16-le',errors='replace'))
        state.update(wsl_list_returncode=check.returncode,status='wsl_list_responded')
    except (subprocess.TimeoutExpired,RuntimeError,OSError) as exc:
        state.update(status='blocked_wsl_preflight',reason=str(exc),native_runs_started=False)
        (HERE/'environment_status.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
        print('WSL preflight failed; no native simulation was started. See environment_status.json.',flush=True)
        return 2
    drive = HERE.drive[0].lower()
    path = '/mnt/'+drive+HERE.as_posix()[2:]
    cmd = ['wsl']
    if args.distro: cmd += ['-d',args.distro]
    cmd += ['--cd',path,'--exec','python3','study.py','--workers',str(args.workers)]
    state.update(status='native_runner_started',command=cmd,native_runs_started=True)
    (HERE/'environment_status.json').write_text(json.dumps(state,indent=2),encoding='utf-8')
    return subprocess.run(cmd).returncode


if __name__=='__main__':
    sys.exit(main())
