"""Small deterministic event projection. Normalized fixtures, not vendor adapters."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
AS_OF = '2026-11-16T18:00:00Z'
TENANT = 'fleet-a'
SOURCES = {'alvys', 'samsara', 'quickbooks', 'documents'}


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('timezone required')
    return result.astimezone(timezone.utc)


def fingerprint(e):
    # Delivery timestamp is not part of event identity: a retry may arrive later.
    return json.dumps({k: v for k, v in e.items() if k != 'received_at'}, sort_keys=True)


def project(events, mapping, as_of=AS_OF, tenant=TENANT):
    cutoff = stamp(as_of)
    mapped = {(m['tenant'], m['source'], m['external_id']): m['load_id'] for m in mapping}
    accepted, groups, issues, conflict_loads = [], {}, [], set()
    for e in events:
        # Never include the other fleet's payload in this fleet's diagnostics.
        if e['tenant'] != tenant or stamp(e['received_at']) > cutoff:
            continue
        if e['source'] not in SOURCES or type(e['version']) is not int or e['version'] < 1:
            issues.append({'kind': 'schema', 'event': e['event_id']}); continue
        if stamp(e['occurred_at']) > stamp(e['received_at']):
            issues.append({'kind': 'future_event', 'event': e['event_id']}); continue
        key = (e['tenant'], e['source'], e['event_id'])
        groups.setdefault(key, []).append(e)
    duplicate_count = 0
    for group in groups.values():
        if len({fingerprint(e) for e in group}) != 1:
            issues.append({'kind': 'conflicting_event_id', 'event': group[0]['event_id']})
            for e in group:
                load = mapped.get((tenant, e['source'], e['external_id']))
                if load: conflict_loads.add(load)
            continue
        duplicate_count += len(group) - 1
        accepted.append(min(group, key=lambda e: stamp(e['received_at'])))
    lanes = {}
    trace = []
    for e in sorted(accepted, key=lambda e: (stamp(e['received_at']), e['event_id'])):
        load = mapped.get((tenant, e['source'], e['external_id']))
        if load is None:
            issues.append({'kind': 'unmapped_identity', 'event': e['event_id']}); continue
        key = (load, e['source'], e['entity_id'])
        lanes.setdefault(key, []).append(e)
    loads = {m['load_id']: {'load_id': m['load_id'], 'status': None, 'pod': None,
             'invoice_cents': 0, 'payment_cents': 0, 'gps': None, 'holds': [], 'evidence': []}
             for m in mapping if m['tenant'] == tenant}
    stale = 0
    for (load_id, source, entity_id), lane in sorted(lanes.items()):
        newest = max(e['version'] for e in lane)
        same = [e for e in lane if e['version'] == newest]
        if len({json.dumps(e['payload'], sort_keys=True) for e in same}) > 1:
            loads[load_id]['holds'].append('conflicting_revision')
            issues.append({'kind': 'conflicting_revision', 'load': load_id, 'source': source})
            continue
        chosen = min(same, key=lambda e: e['event_id'])
        stale += sum(e['version'] < newest for e in lane)
        row, p = loads[load_id], chosen['payload']
        row['evidence'].append(chosen['event_id'])
        for e in lane:
            trace.append({'load': load_id, 'source': source, 'event': e['event_id'],
                          'version': e['version'], 'received_at': e['received_at'],
                          'used': e is chosen, 'payload': e['payload']})
        if source == 'alvys': row['status'] = p.get('status')
        elif source == 'documents': row['pod'] = p.get('pod_verified', False)
        elif source == 'samsara': row['gps'] = p
        elif source == 'quickbooks':
            # An entity is a current snapshot, never an additive webhook delta.
            for field in ['invoice_cents', 'payment_cents']:
                value = p.get(field, 0)
                if type(value) is not int or value < 0:
                    row['holds'].append('invalid_money')
                else: row[field] += value
    for row in loads.values():
        if row['load_id'] in conflict_loads: row['holds'].append('conflicting_event_id')
        if row['status'] != 'delivered': row['holds'].append('delivery_not_confirmed')
        if row['pod'] is not True: row['holds'].append('pod_not_verified')
        if row['gps'] is None or (cutoff - stamp(row['gps']['observed_at'])).total_seconds() > 1800:
            row['holds'].append('location_stale')
        # Existing invoice/partial payment must never cause a second invoice.
        row['invoice_action'] = ('already_invoiced' if row['invoice_cents'] > 0 else
                                 'hold' if row['holds'] else 'ready_for_review')
        row['balance_cents'] = row['invoice_cents'] - row['payment_cents']
    return {'as_of': as_of, 'loads': list(loads.values()), 'trace': trace, 'issues': issues,
            'duplicates': duplicate_count, 'stale_versions': stale,
            'received': sum(e['tenant'] == tenant and stamp(e['received_at']) <= cutoff for e in events)}


def validate_note(proposal, result, tenant=TENANT):
    """Validate structured claims; generated prose is not executed or trusted."""
    if set(proposal) != {'tenant', 'load_id', 'action', 'claims'}:
        return {'status': 'hold', 'reason': 'schema_mismatch'}
    if proposal['tenant'] != tenant:
        return {'status': 'hold', 'reason': 'tenant_mismatch'}
    if proposal['action'] != 'draft_internal_note':
        return {'status': 'hold', 'reason': 'unauthorized_action'}
    row = next((r for r in result['loads'] if r['load_id'] == proposal['load_id']), None)
    if row is None: return {'status': 'hold', 'reason': 'unknown_load'}
    trace = {t['event']: t for t in result['trace'] if t['used'] and t['load'] == row['load_id']}
    fields = {'delivery_status': ('alvys', 'status'), 'pod_verified': ('documents', 'pod_verified')}
    if not proposal['claims']: return {'status': 'hold', 'reason': 'missing_evidence'}
    for claim in proposal['claims']:
        if set(claim) != {'field', 'value', 'event_id'}:
            return {'status': 'hold', 'reason': 'schema_mismatch'}
        spec = fields.get(claim['field']); event = trace.get(claim['event_id'])
        if spec is None or event is None: return {'status': 'hold', 'reason': 'missing_evidence'}
        if event['source'] != spec[0] or event['payload'].get(spec[1]) != claim['value']:
            return {'status': 'hold', 'reason': 'unsupported_claim'}
    return {'status': 'review', 'reason': 'supported_for_human_review'}


def release_gate(checks):
    blockers = [c['id'] for c in checks if c['required'] and c['status'] != 'passed']
    return {'decision': 'hold' if blockers else 'eligible_for_owner_review', 'blockers': blockers}


def main():
    f = json.loads((ROOT / 'fixtures.json').read_text())
    result = project(f['events'], f['mapping'])
    result['notes'] = [{**p, 'result': validate_note(p['proposal'], result)} for p in f['notes']]
    checks = f['release_checks']
    checks[1]['status'] = 'failed' if any(i['kind'].startswith('conflicting') for i in result['issues']) else 'passed'
    checks[2]['status'] = 'failed' if any(i['kind'] == 'unmapped_identity' for i in result['issues']) else 'passed'
    result['release_checks'] = checks
    result['release'] = release_gate(f['release_checks'])
    (ROOT / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ['received','duplicates','stale_versions','issues','release']},indent=2))

if __name__ == '__main__': main()
