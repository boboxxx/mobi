#!/usr/bin/env python3
"""Deterministic descriptive profile summary using exact rational quantiles."""
import argparse,hashlib,json
from fractions import Fraction
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def quantile(xs,n,d):
 a=sorted(xs);x=Fraction(n*(len(a)-1),d);i=x.numerator//x.denominator;r=x-i;return float(a[i]*(1-r)+a[min(i+1,len(a)-1)]*r)
def stats(xs):return dict(n=len(xs),minimum=min(xs),median=quantile(xs,1,2),p95=quantile(xs,19,20),maximum=max(xs))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();p=a.results.resolve();d=read(p/'analysis_sheng.json');au=read(p/'audit_sheng.json');assert au['analysis_sha256']==sha(p/'analysis_sheng.json');out=dict(policies=d['policies'],setup=d['setup'],methods={m:{k:stats([r['methods'][m][k] for r in d['rows']]) for k in ('wire_bytes','source_us','receiver_us')} for m in ('hull','deadline')},audit_counts={k:au[k] for k in ('rows','actual_packet_checks','trace_checks','decision_checks')},grants_referencing_excluded_source=au['grants_referencing_excluded_source'],source_sha256=sha(Path(__file__)),analysis_sha256=sha(p/'analysis_sheng.json'),audit_sha256=sha(p/'audit_sheng.json'),scope=d['scope']);a.out.write_text(json.dumps(out,separators=(',',':'))+'\n');print(json.dumps(out['policies'],indent=2))
if __name__=='__main__':main()
