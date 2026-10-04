#!/usr/bin/env python3
"""Round presentation-only binomial upper bounds, preserving raw summaries."""
import argparse,hashlib,json
from pathlib import Path
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--input',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();d=json.loads(a.input.read_bytes());d['raw_summarizer_source_sha256']=d['source_sha256'];d['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 for c in d['classes']:
  for k in ('single_class_risk_upper95','simultaneous_six_class_risk_upper95'):c[k]=round(c[k],15)
 d['presentation_normalization']='Only the two descriptive binomial risk upper fields per class are rounded to15 decimal places; no score, model, trace, age or qualification calculation changes. Raw local/sheng summaries are preserved.'
 a.out.write_text(json.dumps(d,separators=(',',':'))+'\n')
if __name__=='__main__':main()
