"""v0.3 suite adapter over the shared v0.2 reservation/readiness engine.

Only pseudonymized snapshots are accepted. No network, credentials, provider
calls, authorization, persistent audit, check-in, payment or other writes exist.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal
from datetime import timedelta
from hashlib import sha256
import json
import re

from .core import InputError, Window, parse_input, read_date, read_money, review
from .operations import plan_operations


class SnapshotError(ValueError):
    """The minimized snapshot cannot be reviewed safely."""


IDENT = re.compile(r'^[A-Za-z0-9_-]{1,40}$')
CATEGORIES = {'economy', 'standard', 'superior', 'deluxe', 'triple', 'family'}
BEDS = {'double', 'twin', 'flex', 'single'}
REQUEST_FLAGS = {'twin', 'double', 'cot', 'quiet', 'cityview', 'balcony', 'extra-pillow',
                 'upper-floor', 'low-floor', 'accessible', 'late-arrival', 'no-feather',
                 'adjacent', 'high-floor'}
AMENITY_FLAGS = {'window', 'quiet', 'cityview', 'balcony', 'accessible', 'elevator',
                 'terrace', 'minibar', 'shower', 'bath', 'connecting'}
CHANNELS = {'booking', 'expedia', 'trip', 'ctrip', 'hotelbeds', 'direct', 'agency', 'channel_manager'}
ROOM_STATES = {'clean', 'dirty', 'inspected', 'in_progress', 'out_of_order', 'out_of_service'}
BOOKING_STATES = {'confirmed', 'cancelled', 'pending', 'in_house', 'checked_out', 'no_show'}
BLOCKER_CODES = {
    'CANCELLED_ASSIGNED', 'NOT_CONFIRMED', 'UNMAPPED_PMS', 'DUPLICATE_CHANNEL_REF',
    'DUPLICATE_PMS_REF', 'NO_ASSIGNED_ROOM', 'ROOM_INCOMPATIBLE',
    'HOUSEKEEPING_NOT_INSPECTED', 'ROOM_CONFLICT', 'IDENTITY_STAFF_REVIEW',
    'PAYMENT_REVIEW', 'ARRIVAL_NOT_TODAY', 'GUEST_NOT_ARRIVED', 'BEFORE_CHECKIN_TIME',
    'DEPARTURE_NOT_VERIFIED', 'ALREADY_IN_HOUSE', 'SPECIAL_REQUEST_REVIEW',
    'REQUEST_AMENITY_UNAVAILABLE', 'CONFLICTING_BED_REQUEST', 'MAINTENANCE_TASK_OPEN',
    'HOUSEKEEPING_TASK_OPEN', 'CHANNEL_EVENT_REVIEW', 'CHANNEL_REFERENCE_MISMATCH',
    'CHANNEL_STATUS_CONFLICT', 'CORE_REVIEW_REQUIRED', 'HISTORICAL_STAY',
}
_ALLOWED_SNAPSHOT = {'schema_version', 'property_id', 'as_of', 'at_time', 'rooms',
                     'reservations', 'channel_events', 'tasks'}
_ROOM_FIELDS = {'id', 'category', 'capacity', 'bed', 'housekeeping', 'floor', 'amenities', 'maintenance'}
_RES_FIELDS = {'id', 'channel', 'external_ref', 'pms_ref', 'arrival', 'departure',
               'category', 'persons', 'bed_request', 'status', 'room_id',
               'identity_signal', 'payment_signal', 'requests', 'price_total',
               'currency', 'arrival_state'}
_EVENT_FIELDS = {'id', 'channel', 'external_ref', 'status', 'reservation_id'}
_TASK_FIELDS = {'id', 'kind', 'room_id', 'reservation_id', 'status', 'priority'}
_SIDE_EFFECTS = {'pms_writes': False, 'payments': False, 'kbs': False,
                 'guest_messages': False, 'human_approval_required': True}


def _reject(label='snapshot'):
    raise SnapshotError('Invalid minimized ' + label)


def _dict(value, allowed, label, required=None):
    required = allowed if required is None else required
    if not isinstance(value, dict) or set(value) - allowed or not required <= set(value):
        _reject(label)
    return value


def _id(value, label):
    if not isinstance(value, str) or IDENT.fullmatch(value) is None:
        _reject(label)
    return value


def _enum(value, allowed, label):
    if not isinstance(value, str) or value not in allowed:
        _reject(label)
    return value


def _flags(value, allowed, maximum, label):
    if not isinstance(value, list) or len(value) > maximum:
        _reject(label)
    for flag in value:
        _enum(flag, allowed, label)
    if len(set(value)) != len(value):
        _reject(label)


def _day(value):
    try:
        return read_date(value, 'date')
    except InputError:
        _reject('date')


def _channel(value):
    return 'trip' if value == 'ctrip' else value


def validate(source):
    """Validate and own one canonical snapshot; identifiers are not anonymization."""
    _dict(source, _ALLOWED_SNAPSHOT, 'snapshot', _ALLOWED_SNAPSHOT - {'at_time'})
    for field, limit in (('rooms', 500), ('reservations', 5000), ('channel_events', 5000), ('tasks', 5000)):
        if not isinstance(source.get(field), list) or len(source[field]) > limit:
            _reject('collection')
    try:
        value = deepcopy(source)
    except (RecursionError, TypeError):
        _reject()
    if value.get('schema_version') != '0.3':
        _reject('schema')
    _id(value.get('property_id'), 'property')
    if _day(value.get('as_of')).isoformat() == '9999-12-31':
        _reject('date')
    value.setdefault('at_time', '14:00')
    if not isinstance(value['at_time'], str) or re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', value['at_time']) is None:
        _reject('clock')
    room_ids, booking_ids = set(), set()
    for room in value['rooms']:
        _dict(room, _ROOM_FIELDS, 'room', _ROOM_FIELDS - {'maintenance'})
        rid = _id(room.get('id'), 'room')
        if rid in room_ids:
            _reject('duplicate room')
        room_ids.add(rid)
        _enum(room.get('category'), CATEGORIES, 'category')
        _enum(room.get('bed'), BEDS, 'bed')
        _enum(room.get('housekeeping'), ROOM_STATES, 'housekeeping')
        if type(room.get('capacity')) is not int or not 1 <= room['capacity'] <= 20:
            _reject('capacity')
        if type(room.get('floor')) is not int or not -3 <= room['floor'] <= 100:
            _reject('floor')
        _flags(room.get('amenities'), AMENITY_FLAGS, 30, 'amenity')
        room.setdefault('maintenance', [])
        if not isinstance(room['maintenance'], list) or len(room['maintenance']) > 100:
            _reject('maintenance')
        for window in room['maintenance']:
            _dict(window, {'start', 'end'}, 'maintenance window')
            if _day(window['start']) >= _day(window['end']):
                _reject('maintenance window')
    for booking in value['reservations']:
        _dict(booking, _RES_FIELDS, 'reservation', _RES_FIELDS - {'arrival_state'})
        bid = _id(booking.get('id'), 'reservation')
        if bid in booking_ids:
            _reject('duplicate reservation')
        booking_ids.add(bid)
        for key, choices in (('channel', CHANNELS), ('status', BOOKING_STATES), ('category', CATEGORIES),
                             ('bed_request', {'none', 'twin', 'double'}),
                             ('identity_signal', {'pending_staff', 'staff_verified', 'not_required_for_demo'}),
                             ('payment_signal', {'review', 'ready', 'agency_ledger'}),
                             ('currency', {'EUR', 'TRY', 'USD', 'GBP'})):
            _enum(booking.get(key), choices, key)
        booking.setdefault('arrival_state', 'expected')
        _enum(booking['arrival_state'], {'expected', 'arrived', 'checked_in', 'checked_out'}, 'arrival state')
        if type(booking.get('persons')) is not int or not 1 <= booking['persons'] <= 20:
            _reject('persons')
        _id(booking.get('external_ref'), 'reference')
        for key in ('pms_ref', 'room_id'):
            if booking.get(key) is not None:
                _id(booking[key], 'reference')
        if booking.get('room_id') is not None and booking['room_id'] not in room_ids:
            _reject('unknown assigned room')
        if _day(booking.get('arrival')) >= _day(booking.get('departure')):
            _reject('stay')
        # No binary floats, nonfinite values or currency mixing in finance output.
        try:
            amount = read_money(booking.get('price_total'), 'price')
        except InputError:
            _reject('price')
        booking['price_total'] = f'{amount:.2f}'
        _flags(booking.get('requests'), REQUEST_FLAGS, 12, 'request')
    event_ids = set()
    for event in value['channel_events']:
        _dict(event, _EVENT_FIELDS, 'channel event')
        eid = _id(event.get('id'), 'event')
        if eid in event_ids:
            _reject('duplicate event')
        event_ids.add(eid)
        _enum(event.get('channel'), CHANNELS, 'channel')
        _enum(event.get('status'), {'received', 'mapped', 'needs_review', 'cancelled'}, 'event status')
        _id(event.get('external_ref'), 'reference')
        if event.get('reservation_id') is not None:
            _id(event['reservation_id'], 'reference')
    task_ids = set()
    by_id = {b['id']: b for b in value['reservations']}
    for task in value['tasks']:
        _dict(task, _TASK_FIELDS, 'task')
        tid = _id(task.get('id'), 'task')
        if tid in task_ids:
            _reject('duplicate task')
        task_ids.add(tid)
        _enum(task.get('kind'), {'housekeeping', 'maintenance', 'guest_request', 'frontdesk'}, 'task kind')
        _enum(task.get('status'), {'open', 'in_progress', 'done'}, 'task status')
        _enum(task.get('priority'), {'low', 'normal', 'high'}, 'task priority')
        for key, known in (('room_id', room_ids), ('reservation_id', booking_ids)):
            if task.get(key) is not None:
                _id(task[key], 'task target')
                if task[key] not in known:
                    _reject('unknown task target')
        if task.get('room_id') is None and task.get('reservation_id') is None:
            _reject('missing task target')
        if task.get('room_id') and task.get('reservation_id'):
            assigned = by_id[task['reservation_id']]['room_id']
            if assigned is not None and assigned != task['room_id']:
                _reject('conflicting task targets')
    return value


def overlap(a, b):
    """Compatibility helper; reuse the core interval rule rather than a second rule."""
    from .core import Window
    return Window(_day(a['arrival']), _day(a['departure'])).overlaps(Window(_day(b['arrival']), _day(b['departure'])))


def room_ok(room, booking):
    """Suite-only attribute constraints; inventory/date rules remain in core."""
    if room['category'] != booking['category'] or room['capacity'] < booking['persons']:
        return False
    if room['bed'] == 'single' and booking['persons'] > 1:
        return False
    preferences = ({booking['bed_request']} - {'none'}) | (set(booking['requests']) & {'twin', 'double'})
    if len(preferences) > 1:
        return False
    if 'twin' in preferences and room['bed'] not in {'twin', 'flex'}:
        return False
    if 'double' in preferences and room['bed'] not in {'double', 'flex'}:
        return False
    required = set(booking['requests']) & {'accessible', 'quiet', 'cityview', 'balcony'}
    if not required <= set(room['amenities']):
        return False
    return room['housekeeping'] not in {'out_of_order', 'out_of_service'}


def _normalized(snapshot):
    rooms = []
    room_ops = []
    for room in snapshot['rooms']:
        # Core has no single-bed type. Attribute compatibility above remains
        # authoritative for that extension; it is never represented as twin/flex.
        rooms.append({'id': room['id'], 'category': room['category'],
                      'beds': 'double' if room['bed'] == 'single' else room['bed'],
                      'active': room['housekeeping'] not in {'out_of_order', 'out_of_service'},
                      'maintenance': deepcopy(room['maintenance'])})
        room_ops.append({'room_id': room['id'],
                         'housekeeping': 'clean' if room['housekeeping'] in {'clean', 'inspected'} else 'dirty',
                         'inspection': 'approved' if room['housekeeping'] == 'inspected' else 'pending',
                         'maintenance_hold': room['housekeeping'] in {'out_of_order', 'out_of_service'}})
    reservations, arrivals = [], []
    for booking in snapshot['reservations']:
        status = booking['status']
        core_status = 'confirmed' if status in {'confirmed', 'in_house'} else 'pending' if status == 'pending' else 'cancelled'
        reservations.append({'ref': booking['id'], 'source': _channel(booking['channel']),
                             'status': core_status, 'checkin': booking['arrival'], 'checkout': booking['departure'],
                             'category': booking['category'], 'room_id': booking['room_id'],
                             'twin_requested': (({booking['bed_request']} - {'none'}) | (set(booking['requests']) & {'twin', 'double'})) == {'twin'}})
        arrivals.append({'ref': booking['id'], 'source': _channel(booking['channel']),
                         'arrival_state': 'checked_in' if status == 'in_house' or booking['arrival_state'] == 'checked_in' else 'checked_out' if status == 'checked_out' else booking['arrival_state'],
                         'identity_status': 'verified_by_authorized_staff' if booking['identity_signal'] == 'staff_verified' else 'not_checked',
                         'registration_status': 'not_checked',
                         'payment_review': 'review' if booking['payment_signal'] == 'review' else 'cleared',
                         'early_checkin_authorized': False})
    return {'property_id': snapshot['property_id'], 'rooms': rooms, 'reservations': reservations,
            'room_operations': room_ops, 'arrival_checks': arrivals}


def _events(snapshot):
    by_id = {b['id']: b for b in snapshot['reservations']}
    by_key = defaultdict(list)
    for b in snapshot['reservations']:
        by_key[(_channel(b['channel']), b['external_ref'])].append(b)
    issues = defaultdict(set)
    matched = set()
    reviews = []
    unmatched = []
    for event in snapshot['channel_events']:
        candidates = by_key[(_channel(event['channel']), event['external_ref'])]
        linked = by_id.get(event['reservation_id'])
        affected = {b['id'] for b in candidates}
        if linked:
            affected.add(linked['id'])
        exact = linked is not None and len(candidates) == 1 and candidates[0]['id'] == linked['id']
        codes = []
        if not exact:
            codes.append('CHANNEL_REFERENCE_MISMATCH')
            unmatched.append(event['id'])
        elif event['status'] == 'mapped':
            matched.add(linked['id'])
        if event['status'] in {'received', 'needs_review'}:
            codes.append('CHANNEL_EVENT_REVIEW')
        if event['status'] == 'cancelled' and linked and linked['status'] != 'cancelled':
            codes.append('CHANNEL_STATUS_CONFLICT')
        if event['status'] == 'mapped' and linked and linked['status'] in {'cancelled', 'no_show', 'checked_out'}:
            codes.append('CHANNEL_STATUS_CONFLICT')
        for bid in affected:
            issues[bid].update(codes)
        reviews.append({'id': event['id'], 'status': 'needs_review' if codes else 'matched',
                        'reservation_id': event['reservation_id'], 'reason_codes': codes})
    return issues, matched, reviews, unmatched


def _physically_in_house(booking):
    return booking['status'] == 'in_house' or booking['arrival_state'] == 'checked_in'


def _unreleased_departure(booking, today):
    active = booking['status'] in {'confirmed', 'pending', 'in_house'} or _physically_in_house(booking)
    return (active and booking['arrival'] < today and booking['departure'] <= today
            and booking['arrival_state'] != 'checked_out' and booking['status'] != 'checked_out'
            and (booking['departure'] == today or _physically_in_house(booking)))


def _room_plan(snapshot, normalized, room_tasks):
    """Current-day holds, not a live occupancy/vacancy guarantee."""
    _, core_rooms, core_bookings = parse_input({key: normalized[key] for key in ('property_id', 'rooms', 'reservations')})
    booking_index = {b['id']: b for b in snapshot['reservations']}
    core_room_index = {r.id: r for r in core_rooms}
    today = _day(snapshot['as_of'])
    day = Window(today, today + timedelta(days=1))
    result = []
    for room in snapshot['rooms']:
        held, all_holds = set(), set()
        for core_booking in core_bookings:
            if core_booking.room_id != room['id']:
                continue
            booking = booking_index[core_booking.ref]
            active = core_booking.status in {'confirmed', 'pending'}
            physical = _physically_in_house(booking)
            if active or physical:
                all_holds.add(booking['id'])
            if (active and core_booking.stay.overlaps(day)) or physical or _unreleased_departure(booking, snapshot['as_of']):
                held.add(booking['id'])
        reasons = []
        if held:
            reasons.append('INVENTORY_HOLD_OR_DEPARTURE_REVIEW')
        if not core_room_index[room['id']].available(day):
            reasons.append('OUT_OF_SERVICE_OR_MAINTENANCE')
        if room['housekeeping'] != 'inspected':
            reasons.append('HOUSEKEEPING_NOT_INSPECTED')
        reasons.extend(sorted(room_tasks.get(room['id'], set())))
        result.append({'id': room['id'], 'held_reservation_ids': sorted(held),
                       'reservation_ids_all_holds': sorted(all_holds),
                       'availability': 'BLOCKED_FOR_REVIEW' if reasons else 'REQUIRES_LIVE_REVALIDATION',
                       'reason_codes': reasons})
    return result


def _proposals(snapshot, normalized, unavailable):
    """Orchestrate core proposals with extended attributes and planned holds."""
    planned = []
    result = {}
    duplicate_keys = Counter((_channel(b['channel']), b['external_ref']) for b in snapshot['reservations'])
    duplicate_pms = Counter(b['pms_ref'] for b in snapshot['reservations'] if b['pms_ref'] and b['status'] not in {'cancelled', 'no_show', 'checked_out'})
    todo = sorted((b for b in snapshot['reservations'] if b['status'] == 'confirmed' and b['room_id'] is None and b['arrival'] >= snapshot['as_of']),
                  key=lambda b: (b['arrival'], 0 if b['bed_request'] != 'none' else 1, -len(b['requests']), b['id']))
    normalized_by_id = {b['ref']: b for b in normalized['reservations']}
    assigned = [r for r in normalized['reservations'] if r['room_id'] is not None]
    for booking in todo:
        if duplicate_keys[(_channel(booking['channel']), booking['external_ref'])] > 1 or (booking['pms_ref'] and duplicate_pms[booking['pms_ref']] > 1):
            result[booking['id']] = None
            continue
        candidates = {room['id'] for room in snapshot['rooms'] if room_ok(room, booking) and room['housekeeping'] == 'inspected' and room['id'] not in unavailable}
        rooms = [dict(room, active=room['active'] and room['id'] in candidates) for room in normalized['rooms']]
        request = normalized_by_id[booking['id']]
        # Exclude this target from assigned holds even if a future adapter changes
        # its shape. Previously suggested rooms are real *planning* holds here.
        source = {'property_id': snapshot['property_id'], 'rooms': rooms,
                  'reservations': assigned + planned + [request]}
        proposals = review(source, snapshot['as_of'])['room_proposals']
        proposed = next((p['room_id'] for p in proposals if p['reservation_ref'] == booking['id']), None)
        result[booking['id']] = proposed
        if proposed:
            planned.append(dict(request, room_id=proposed))
    return result


def propose_room(res, rooms, bookings):
    """Legacy helper using the same final evaluation and physical-hold rules.

    Full snapshots should use evaluate() so department tasks and event context
    are included. This compatibility helper cannot assert live readiness.
    """
    snapshot = {'schema_version': '0.3', 'property_id': 'PROPOSAL_DEMO', 'as_of': res['arrival'],
                'rooms': rooms, 'reservations': bookings if any(b['id'] == res['id'] for b in bookings) else bookings + [res],
                'channel_events': [], 'tasks': []}
    report = evaluate(snapshot)
    return next((row['suggested_room'] for row in report['arrivals'] if row['id'] == res['id']), None)


def evaluate(raw):
    """Produce a dry-run suite report, reusing core/v0.2 decisions."""
    s = validate(raw)
    canonical = json.dumps(s, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()
    fingerprint = sha256(canonical).hexdigest()
    normalized = _normalized(s)
    try:
        core = plan_operations(normalized, s['as_of'], s['at_time'])
    except InputError:
        _reject('shared engine snapshot')
    core_rows = {t['reservation_ref']: t for t in core['tasks']}
    event_issues, matched, event_reviews, unmatched = _events(s)
    duplicate_keys = Counter((_channel(b['channel']), b['external_ref']) for b in s['reservations'])
    duplicate_pms = Counter(b['pms_ref'] for b in s['reservations'] if b['pms_ref'] and b['status'] not in {'cancelled', 'no_show', 'checked_out'})
    room_index = {r['id']: r for r in s['rooms']}
    room_task_blocks = defaultdict(set)
    for task in s['tasks']:
        if task['room_id'] and task['status'] != 'done' and task['kind'] in {'housekeeping', 'maintenance'}:
            room_task_blocks[task['room_id']].add('MAINTENANCE_TASK_OPEN' if task['kind'] == 'maintenance' else 'HOUSEKEEPING_TASK_OPEN')
    unavailable = set(room_task_blocks)
    for booking in s['reservations']:
        physically_in_house = _physically_in_house(booking)
        terminal_but_occupied = physically_in_house and booking['status'] in {'cancelled', 'no_show', 'checked_out'}
        unreleased_departure = _unreleased_departure(booking, s['as_of'])
        if booking['room_id'] and (terminal_but_occupied or unreleased_departure):
            unavailable.add(booking['room_id'])
    proposals = _proposals(s, normalized, unavailable)
    reason_map = {'room_unassigned': 'NO_ASSIGNED_ROOM', 'room_not_clean': 'HOUSEKEEPING_NOT_INSPECTED',
                  'room_not_inspected': 'HOUSEKEEPING_NOT_INSPECTED', 'maintenance_hold': 'ROOM_INCOMPATIBLE',
                  'ROOM_OUT_OF_SERVICE': 'ROOM_INCOMPATIBLE', 'CATEGORY_MISMATCH': 'ROOM_INCOMPATIBLE',
                  'TWIN_NOT_GUARANTEED': 'ROOM_INCOMPATIBLE', 'ROOM_OVERLAP': 'ROOM_CONFLICT',
                  'identity_needs_authorized_verification': 'IDENTITY_STAFF_REVIEW',
                  'payment_review_needed': 'PAYMENT_REVIEW', 'reservation_not_confirmed': 'NOT_CONFIRMED',
                  'arrival_date_not_today': 'ARRIVAL_NOT_TODAY', 'before_checkin_time': 'BEFORE_CHECKIN_TIME',
                  'guest_not_arrived': 'GUEST_NOT_ARRIVED', 'already_marked_checked_in': 'ALREADY_IN_HOUSE',
                  'departure_not_verified': 'DEPARTURE_NOT_VERIFIED', 'past_arrival_needs_review': 'ARRIVAL_NOT_TODAY'}
    rows = []
    for b in s['reservations']:
        blockers = set(event_issues[b['id']])
        notes = []
        assigned = room_index.get(b['room_id'])
        task = core_rows.get(b['id'])
        core_reasons = list(task['reasons']) if task else []
        blockers.update(reason_map.get(code, 'CORE_REVIEW_REQUIRED') for code in core_reasons)
        if b['status'] == 'cancelled' and assigned:
            blockers.add('CANCELLED_ASSIGNED')
        if b['status'] not in {'confirmed', 'in_house'}:
            blockers.add('NOT_CONFIRMED')
        if b['status'] == 'in_house' or b['arrival_state'] == 'checked_in':
            blockers.add('ALREADY_IN_HOUSE')
        if b['status'] == 'confirmed' and task is None:
            blockers.add('HISTORICAL_STAY')
        mapping_ok = bool(b['pms_ref']) and (b['channel'] in {'direct', 'agency'} or b['id'] in matched)
        if not mapping_ok:
            blockers.add('UNMAPPED_PMS')
        if duplicate_keys[(_channel(b['channel']), b['external_ref'])] > 1:
            blockers.add('DUPLICATE_CHANNEL_REF')
        if b['pms_ref'] and duplicate_pms[b['pms_ref']] > 1:
            blockers.add('DUPLICATE_PMS_REF')
        compatible = bool(assigned and room_ok(assigned, b))
        if assigned and not compatible:
            blockers.add('ROOM_INCOMPATIBLE')
        if b['room_id']:
            blockers.update(room_task_blocks[b['room_id']])
        preferred = {b['bed_request']} - {'none'}
        requested_beds = set(b['requests']) & {'twin', 'double'}
        if len(preferred | requested_beds) > 1:
            blockers.add('CONFLICTING_BED_REQUEST')
        if requested_beds and assigned and any((x == 'twin' and assigned['bed'] not in {'twin', 'flex'}) or (x == 'double' and assigned['bed'] not in {'double', 'flex'}) for x in requested_beds):
            blockers.add('ROOM_INCOMPATIBLE')
        special = set(b['requests']) - {'twin', 'double'}
        if special:
            blockers.add('SPECIAL_REQUEST_REVIEW')
        required = special & {'accessible', 'quiet', 'cityview', 'balcony'}
        if assigned and not required <= set(assigned['amenities']):
            blockers.add('REQUEST_AMENITY_UNAVAILABLE')
        if b['arrival'] > s['as_of']:
            notes.append('İleri tarihli giriş; bugün için hazır sayılmaz.')
        if special:
            notes.append('Özel talepler yetkili personel tarafından doğrulanmalıdır.')
        status = 'blocked' if blockers else 'review_ready' if b['status'] == 'confirmed' else 'other'
        rows.append({'id': b['id'], 'channel': b['channel'], 'arrival': b['arrival'], 'departure': b['departure'],
                     'room_id': b['room_id'], 'status': status, 'blockers': sorted(blockers), 'core_reasons': core_reasons,
                     'notes': notes, 'suggested_room': proposals.get(b['id']), 'human_approval_required': True,
                     'task_id': sha256((fingerprint + '|' + b['id'] + '|review').encode()).hexdigest()[:24],
                     'checklist': {'pms_match': mapping_ok and not event_issues[b['id']] and duplicate_pms[b['pms_ref']] <= 1,
                                   'reservation_confirmed': b['status'] == 'confirmed', 'room_compatible': compatible and not ({'ROOM_CONFLICT', 'ROOM_INCOMPATIBLE', 'DEPARTURE_NOT_VERIFIED'} & blockers),
                                   'housekeeping_inspected': bool(assigned and assigned['housekeeping'] == 'inspected' and b['room_id'] not in room_task_blocks),
                                   'identity_staff_reviewed': b['identity_signal'] == 'staff_verified',
                                   'payment_reviewed': b['payment_signal'] != 'review'}})
    totals = defaultdict(Decimal)
    for b in s['reservations']:
        if b['status'] in {'confirmed', 'in_house'}:
            totals[b['currency']] += Decimal(b['price_total'])
    counts = Counter(r['status'] for r in rows)
    return {'schema_version': '0.3', 'mode': 'DRY_RUN_ONLY', 'property_id': s['property_id'],
            'as_of': s['as_of'], 'at_time': s['at_time'], 'snapshot_sha256': fingerprint,
            'summary': {'reservations': len(rows), 'rooms': len(room_index), 'blocked': counts['blocked'],
                        'review_ready': counts['review_ready'], 'pending_channel_events': sum(r['status'] == 'needs_review' for r in event_reviews)},
            'arrivals': rows, 'unmatched_channel_events': unmatched, 'event_reviews': event_reviews,
            'room_plan': _room_plan(s, normalized, room_task_blocks),
            'tasks': sorted(deepcopy(s['tasks']), key=lambda t: ({'high': 0, 'normal': 1, 'low': 2}[t['priority']], t['id'])),
            'financial_review': {'basis': 'FICTIONAL_RESERVATION_TOTALS_NOT_DAILY_REVENUE',
                                 'reservation_totals_by_currency': {c: f'{v:.2f}' for c, v in sorted(totals.items())},
                                 'folio_reconciliation': 'NOT_IMPLEMENTED_NO_LEDGER_INPUT',
                                 'payment_review_ids': [b['id'] for b in s['reservations'] if b['status'] in {'confirmed', 'in_house'} and b['payment_signal'] == 'review'],
                                 'departures_today_ids': [b['id'] for b in s['reservations'] if b['departure'] == s['as_of'] and b['status'] in {'confirmed', 'in_house'}],
                                 'no_financial_postings': True},
            'engine_report': core, 'approval_policy': dict(_SIDE_EFFECTS)}
