#!/usr/bin/env python3
"""Recover the already-stopped owner receipt without starting/stopping any process."""
import hashlib,json
from pathlib import Path
E=Path(__file__).resolve().parent;ROOT=E.parents[1];P=ROOT/'results'/E.name
read=lambda q:json.loads(q.read_text(encoding='utf-8-sig'))
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
def main():
 src=Path('/mnt/c/Users/Administrator/mobi-ego-policy-cert-stopped.json');out=P/'server_stopped.json';receipt=P/'cleanup_copy_recovery.json';assert not out.exists() and not receipt.exists()
 start=read(P/'server_start.json');stop=read(src);log=read(P/'server_stop.log');assert stop==log and stop['stopped'] and stop['experiment']==E.name
 for k in ('pid','executable','start_time_utc','experiment'):assert start[k]==stop[k]
 out.write_bytes(src.read_bytes());receipt.write_text(json.dumps(dict(original_receipt_path=str(src),recovered_receipt_sha256=sha(out),server_start_sha256=sha(P/'server_start.json'),original_stop_log_sha256=sha(P/'server_stop.log'),owned_pid=stop['pid'],already_stopped=True,no_recapture=True,no_process_restarted=True,scope='Original shell copied the wrong receipt basename; actual owner stop had succeeded.'),indent=2,sort_keys=True)+'\n');print(json.dumps(dict(owner=stop['pid'],recovered_sha256=sha(out))))
if __name__=='__main__':main()

