"""Read-only room-card facts over the canonical snapshot and Python review.

Source assignments and inventory holds are not physical occupancy evidence.
An unassigned room is never presented as verified vacant or sellable.
"""
from __future__ import annotations

from collections import Counter

from .canonical import (canonical_fingerprint, project_review, review_links,
                        validate_canonical)
from .experience_engine import evaluate


def build_room_graph(source):
    """Prepare deterministic graphical-room facts; no network, writes or ledger."""
    canonical = validate_canonical(source)
    review = evaluate(project_review(canonical))
    links = review_links(canonical)
    plans = {row['id']: row for row in review['room_plan']}
    cases = {row['id']: row for row in review['arrivals']}
    bookings = {row['id']: row for row in canonical['reservations']}
    guests = {row['id']: row for row in canonical['guests']}
    today = canonical['as_of']
    rooms = []

    for room in sorted(canonical['rooms'], key=lambda row: (row['floor'], row['id'])):
        stays = sorted((row for row in canonical['room_stays'] if row['room_id'] == room['id']),
                       key=lambda row: row['id'])
        parents = {stay['reservation_id'] for stay in stays}
        active = [stay for stay in stays
                  if stay['arrival'] <= today < stay['departure']
                  and bookings[stay['reservation_id']]['status'] in {'confirmed', 'pending', 'in_house'}]
        physical = {stay['reservation_id'] for stay in stays
                    if bookings[stay['reservation_id']]['status'] == 'in_house'
                    or bookings[stay['reservation_id']]['arrival_state'] == 'checked_in'}
        no_show_hold = {stay['reservation_id'] for stay in stays
                        if bookings[stay['reservation_id']]['status'] == 'no_show'
                        and bookings[stay['reservation_id']]['arrival_state'] != 'checked_out'}
        planned = [stay for stay in stays if bookings[stay['reservation_id']]['status']
                   in {'confirmed', 'pending', 'in_house'}
                   and bookings[stay['reservation_id']]['arrival_state'] != 'checked_out']
        arrivals = {stay['reservation_id'] for stay in planned if stay['arrival'] == today
                    and stay['reservation_id'] not in physical}
        departures = {stay['reservation_id'] for stay in planned if stay['departure'] == today}
        blocks = [row for row in canonical['room_blocks'] if row['room_id'] == room['id']
                  and row['status'] == 'active' and row['start'] <= today
                  and (row['end'] is None or today < row['end'])]
        maintenance = (any(window['start'] <= today < window['end']
                           for window in room['maintenance'])
                       or any(block['kind'] == 'maintenance' for block in blocks))
        stay_ids = {stay['id'] for stay in stays}
        room_case_ids = [identifier for identifier, link in links.items()
                         if link['room_stay_id'] in stay_ids]
        reasons = set(plans[room['id']]['reason_codes'])
        for identifier in room_case_ids:
            reasons.update(cases[identifier]['blockers'])
        states = set()
        if physical:
            states.add('occupied')
        elif no_show_hold:
            states.add('no_show_hold')
            states.add('blocked')
        elif not active:
            states.add('vacant_unverified')
        if arrivals:
            states.add('expected_arrival')
        if departures:
            states.add('expected_departure')
        terminal_physical = any(bookings[identifier]['status'] in {'cancelled', 'no_show', 'checked_out'}
                                for identifier in physical)
        if (blocks or maintenance or terminal_physical
                or 'MAINTENANCE_TASK_OPEN' in plans[room['id']]['reason_codes']
                or room['housekeeping'] in {'out_of_order', 'out_of_service'}):
            states.add('blocked')
        kinds = {row['kind'] for row in blocks}
        if room['housekeeping'] == 'out_of_order' or 'out_of_order' in kinds:
            states.add('out_of_order')
        if room['housekeeping'] == 'out_of_service' or 'out_of_service' in kinds:
            states.add('out_of_service')
        if 'ROOM_CONFLICT' in reasons:
            states.add('conflict')
        room_reviews = [cases[identifier]['status'] for identifier in room_case_ids]
        rooms.append({
            'id': room['id'], 'floor': room['floor'], 'category': room['category'],
            'capacity': room['capacity'], 'bed': room['bed'],
            'housekeeping': room['housekeeping'],
            'housekeeping_cleanliness': room['housekeeping'] if room['housekeeping'] in
                {'dirty', 'clean', 'inspected', 'in_progress'} else 'unknown',
            'occupancy_state': 'occupied' if physical else 'unknown',
            'occupancy_source': 'synthetic_checked_in_signal' if physical else 'source_not_connected',
            'assignment_state': 'assigned' if active or no_show_hold else 'unassigned',
            'state_codes': sorted(states), 'reservation_ids': sorted(parents),
            'active_reservation_ids': sorted({stay['reservation_id'] for stay in active}),
            'physical_reservation_ids': sorted(physical),
            'room_stay_ids': [stay['id'] for stay in stays],
            'guest_labels': sorted({guests[identifier]['display_label'] for stay in active
                                    for identifier in stay['guest_ids']}),
            'assigned_people': sum(stay['adults'] + stay['children'] for stay in active),
            'arrivals': sorted(arrivals), 'departures': sorted(departures),
            'block_ids': sorted(row['id'] for row in blocks), 'maintenance_active': maintenance,
            'reason_codes': sorted(reasons),
            'review_status': 'blocked' if ('blocked' in room_reviews or
                set(plans[room['id']]['reason_codes']) - {'INVENTORY_HOLD_OR_DEPARTURE_REVIEW'}) else
                'review_ready' if 'review_ready' in room_reviews else 'requires_live_revalidation',
            'held_reservation_ids': sorted({links[identifier]['reservation_id']
                                           for identifier in plans[room['id']]['held_reservation_ids']}),
        })
    counts = Counter(code for room in rooms for code in room['state_codes'])
    return {
        'schema_version': 'aurora-room-graph.v1',
        'canonical_sha256': canonical_fingerprint(canonical), 'as_of': today,
        'source_state': 'synthetic_snapshot', 'authority': 'PYTHON_PRECOMPUTED_REVIEW',
        'physical_occupancy_source': 'source_not_connected', 'rooms': rooms,
        'summary': {'rooms': len(rooms), 'floors': len({room['floor'] for room in rooms}),
                    'assigned_rooms': sum(room['assignment_state'] == 'assigned' for room in rooms),
                    'physical_occupied_signals': sum(room['occupancy_state'] == 'occupied' for room in rooms),
                    'physical_unknown_rooms': sum(room['occupancy_state'] == 'unknown' for room in rooms),
                    'state_counts': dict(sorted(counts.items()))},
        'safety': {'read_only': True, 'human_approval_required': True,
                   'pms_writes': False, 'payments': False, 'kbs': False,
                   'guest_messages': False, 'live_ai_calls': False},
    }
