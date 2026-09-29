import copy,json,sys,unittest
from pathlib import Path
from verify_research import verify, IDS
CONFIG=json.loads(Path(sys.argv.pop(1)).read_text())
SCREENS=['S1','S2','S3','S4','S5']
GOOD={'references':[{'id':f'R{i}','service':f'Service{i%3}','url':f'https://example.invalid/{i}','observation':'Synthetic test fixture, not research evidence','screen_ids':SCREENS.copy()} for i in range(6)],'patterns':[{'id':f'P{i}','description':'Synthetic pattern','reference_ids':['R0','R1']} for i in range(3)]}

def status(data,rid): return next(x['status'] for x in verify(data,CONFIG)['checks'] if x['rule_id']==rid)

def invalid(rid):
    d=copy.deepcopy(GOOD)
    if rid=='G1.services':
        for r in d['references']:r['service']='one'
    elif rid=='G1.references':
        for r in d['references']:r['url']='https://example.invalid/same'
    elif rid=='G1.fields':d['references'][0]['observation']=''
    elif rid=='G1.patterns':d['patterns']=d['patterns'][:1]
    elif rid=='G1.support':d['patterns'][0]['reference_ids']=['R0']
    elif rid=='G1.coverage':
        for r in d['references']:r['screen_ids']=['S1']
    return d

class Tests(unittest.TestCase):pass
for rid in IDS:
    def passing(self,rid=rid):self.assertEqual(status(GOOD,rid),'pass')
    def failing(self,rid=rid):self.assertEqual(status(invalid(rid),rid),'fail')
    def missing(self,rid=rid):self.assertEqual(status({},rid),'not_tested')
    for name,fn in [('pass',passing),('fail',failing),('missing',missing)]:setattr(Tests,'test_'+rid.replace('.','_')+'_'+name,fn)
if __name__=='__main__':unittest.main()
