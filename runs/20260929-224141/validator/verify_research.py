"""G1 only. Does not validate Figma, visual quality, source truth, or G2/G3."""
import json, sys
from pathlib import Path

IDS = ['G1.services', 'G1.references', 'G1.fields', 'G1.patterns', 'G1.support', 'G1.coverage']

def verify(data, config):
    out=[]
    refs=data.get('references') if isinstance(data,dict) else None
    patterns=data.get('patterns') if isinstance(data,dict) else None
    ref_valid=isinstance(refs,list) and bool(refs) and all(isinstance(r,dict) for r in refs)
    pat_valid=isinstance(patterns,list) and bool(patterns) and all(isinstance(p,dict) for p in patterns)
    refs=refs if ref_valid else []
    patterns=patterns if pat_valid else []
    lookup={r.get('id'):r for r in refs if isinstance(r.get('id'),str)}
    for rule in config['rules']:
        rid=rule['id']
        if rid not in IDS: continue
        value=rule['threshold']; result='not_tested'; observed=None
        if ref_valid:
            if rid=='G1.services':
                observed=len({r['service'].strip() for r in refs if isinstance(r.get('service'),str) and r['service'].strip()})
                result='pass' if observed>=value else 'fail'
            elif rid=='G1.references':
                observed=len({r['url'].strip() for r in refs if isinstance(r.get('url'),str) and r['url'].startswith('https://')})
                result='pass' if observed>=value else 'fail'
            elif rid=='G1.fields':
                invalid=[]
                for r in refs:
                    if any(not isinstance(r.get(k),str) or not r[k].strip() for k in ['id','service','url','observation']) or not r.get('screen_ids') or not isinstance(r.get('screen_ids'),list): invalid.append(r.get('id','missing'))
                ids=[r.get('id') for r in refs]
                observed=len(invalid)+(len(ids)-len(set(str(x) for x in ids)))
                result='pass' if observed==value else 'fail'
            elif rid=='G1.coverage':
                covered={s for r in refs for s in (r.get('screen_ids') or []) if isinstance(s,str)}
                observed=sorted(set(value)-covered)
                result='pass' if not observed else 'fail'
        if pat_valid:
            if rid=='G1.patterns':
                observed=len({p.get('id') for p in patterns if p.get('id') and p.get('description')})
                result='pass' if observed>=value else 'fail'
            elif rid=='G1.support' and ref_valid:
                bad=[]
                for p in patterns:
                    links=p.get('reference_ids',[])
                    services={lookup[k]['service'] for k in links if k in lookup and lookup[k].get('service')}
                    if not links or any(k not in lookup for k in links) or len(services)<value: bad.append(p.get('id'))
                observed=bad;result='pass' if not bad else 'fail'
        out.append({'rule_id':rid,'status':result,'observed':observed,'evidence':'research/references.json'})
    if set(x['rule_id'] for x in out)!=set(IDS):
        out.append({'rule_id':'G1.config','status':'not_tested','observed':'Missing required rule configuration'})
    return {'gate':'G1','status':'pass' if all(x['status']=='pass' for x in out) else 'blocked','checks':out,'scope':'Counts and reference relationships only; factual and visual quality require separate review.'}

if __name__=='__main__':
    try:
        report=verify(json.loads(Path(sys.argv[1]).read_text()),json.loads(Path(sys.argv[2]).read_text()))
    except Exception as e:
        report={'gate':'G1','status':'blocked','error':str(e),'checks':[]}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    sys.exit(0 if report['status']=='pass' else 1)
