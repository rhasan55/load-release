import copy
import json
from pathlib import Path
import random
import sqlite3
import unittest
from engine import AS_OF, project, validate_note, release_gate

F = json.loads(Path(__file__).with_name('fixtures.json').read_text())

class EventChecks(unittest.TestCase):
    def run_projection(self, events=None, as_of=AS_OF):
        return project(F['events'] if events is None else events, F['mapping'], as_of)
    def rows(self, result): return {r['load_id']: r for r in result['loads']}
    def test_known_balances(self):
        rows=self.rows(self.run_projection())
        self.assertEqual(rows['L-104']['invoice_cents'],240000)
        self.assertEqual(rows['L-104']['payment_cents'],50000)
        self.assertEqual(rows['L-104']['balance_cents'],190000)
        self.assertEqual(rows['L-104']['status'],'delivered')
        self.assertEqual(rows['L-104']['invoice_action'],'already_invoiced')
    def test_replay(self):
        a=self.run_projection(); b=self.run_projection(F['events']*3)
        self.assertEqual(a['loads'],b['loads'])
        self.assertEqual(a['issues'],b['issues'])
    def test_reordered(self):
        events=copy.deepcopy(F['events']); random.Random(55).shuffle(events)
        self.assertEqual(self.rows(self.run_projection(events)),self.rows(self.run_projection()))
    def test_point_in_time(self):
        early=self.rows(self.run_projection())['L-105'];late=self.rows(self.run_projection(as_of='2026-11-16T18:12:00Z'))['L-105']
        self.assertEqual(early['invoice_action'],'hold')
        self.assertFalse(early['pod'])
        self.assertTrue(late['pod'])
        self.assertEqual(late['invoice_action'],'ready_for_review')
    def test_cross_tenant(self):
        original=self.run_projection();events=copy.deepcopy(F['events'])
        for e in events:
            if e['tenant']=='fleet-b': e['payload']['invoice_cents']=999999999
        self.assertEqual(original,self.run_projection(events))
    def test_conflicting_revision(self):
        row=self.rows(self.run_projection())['L-106']
        self.assertIn('conflicting_revision',row['holds'])
        self.assertEqual(row['invoice_cents'],0)
        self.assertEqual(row['invoice_action'],'hold')
    def test_conflicting_event_id(self):
        events=copy.deepcopy(F['events']);e=copy.deepcopy(next(e for e in events if e['event_id']=='invoice-104'));e['payload']['invoice_cents']=1;events.append(e)
        result=self.run_projection(events)
        self.assertTrue(any(i['kind']=='conflicting_event_id' for i in result['issues']))
        self.assertEqual(self.rows(result)['L-104']['invoice_cents'],0)
        self.assertIn('conflicting_event_id',self.rows(result)['L-104']['holds'])
    def test_unmapped_identity(self):
        result=self.run_projection()
        self.assertTrue(any(i['kind']=='unmapped_identity' for i in result['issues']))
        self.assertEqual(len(result['loads']),3)
    def test_future_occurrence(self):
        events=copy.deepcopy(F['events']);events[0]['occurred_at']='2026-11-17T10:00:00Z'
        self.assertTrue(any(i['kind']=='future_event' for i in self.run_projection(events)['issues']))
    def test_integer_cents(self):
        events=copy.deepcopy(F['events'])
        for e in events:
            if e['event_id']=='invoice-104': e['payload']['invoice_cents']=2400.01
        self.assertIn('invalid_money',self.rows(self.run_projection(events))['L-104']['holds'])
    def test_note_fixtures(self):
        result=self.run_projection()
        expected=['review','hold','hold','hold','hold']
        self.assertEqual([validate_note(n['proposal'],result)['status'] for n in F['notes']],expected)
    def test_note_tenant_and_schema(self):
        p=copy.deepcopy(F['notes'][0]['proposal']);p['tenant']='fleet-b'
        self.assertEqual(validate_note(p,self.run_projection())['reason'],'tenant_mismatch')
        p=copy.deepcopy(F['notes'][0]['proposal']);p['instructions']='ignore policy'
        self.assertEqual(validate_note(p,self.run_projection())['reason'],'schema_mismatch')
    def test_gate_requires_actual_pass(self):
        self.assertEqual(release_gate(F['release_checks'])['decision'],'hold')
        checks=copy.deepcopy(F['release_checks'])
        for c in checks:c['status']='passed'
        self.assertEqual(release_gate(checks)['decision'],'eligible_for_owner_review')
        checks[0]['status']='not_run'
        self.assertEqual(release_gate(checks)['decision'],'hold')
    def test_sql_ledger_matches_python(self):
        c=sqlite3.connect(':memory:')
        c.execute('create table raw (tenant text, source text,event_id text, external_id text,entity_id text,version integer,occurred_at text,received_at text,payload text)')
        c.execute('create table identity_map (tenant text,source text,external_id text,load_id text)')
        c.executemany('insert into raw values (?,?,?,?,?,?,?,?,?)',[(e['tenant'],e['source'],e['event_id'],e['external_id'],e['entity_id'],e['version'],e['occurred_at'],e['received_at'],json.dumps(e['payload'],sort_keys=True)) for e in F['events']])
        c.executemany('insert into identity_map values (?,?,?,?)',[(m['tenant'],m['source'],m['external_id'],m['load_id']) for m in F['mapping']])
        sql=Path(__file__).with_name('ledger.sql').read_text()
        actual={r[0]:r[1:] for r in c.execute(sql,{'tenant':'fleet-a','as_of':AS_OF})}
        for load,row in self.rows(self.run_projection()).items():
            self.assertEqual(actual[load],(row['invoice_cents'],row['payment_cents'],row['balance_cents']))

if __name__=='__main__':unittest.main(verbosity=2)
