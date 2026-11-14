"""Build read-only UI projections from one canonical fictional source.

Projection IDs and links are explicit foreign keys, never positional aliases.
The existing rule engine and Decimal ledger formatter remain the authorities.
"""
from __future__ import annotations

from datetime import date, timedelta

from .canonical import (canonical_fingerprint, project_operations, project_review,
                        review_links, validate_canonical)
from .canonical_reporting import build_canonical_operations_report
from .demo_stories import build_demo_stories
from .experience_engine import evaluate
from .reason_i18n import CODES, localize_code

LOCALES = ('tr', 'en', 'fr', 'el', 'he', 'ar', 'de', 'ru', 'es', 'uk')


def build_presentation(source):
    canonical = validate_canonical(source)
    review = project_review(canonical)
    evaluation = evaluate(review)
    operations = project_operations(canonical)
    financial = build_canonical_operations_report(canonical)
    checksum = canonical_fingerprint(canonical)
    links = {'schema_version': 'canonical-links.v1', 'canonical_sha256': checksum,
             'as_of': canonical['as_of'], 'review_links': review_links(canonical),
             'reservations': {}}
    stays = {row['id']: row for row in canonical['room_stays']}
    for booking in canonical['reservations']:
        portions = [stays[identifier] for identifier in booking['room_stay_ids']]
        folios = [row['id'] for row in canonical['folios'] if row['reservation_id'] == booking['id']]
        links['reservations'][booking['id']] = {
            'reservation_id': booking['id'], 'room_stay_ids': list(booking['room_stay_ids']),
            'room_ids': sorted({row['room_id'] for row in portions if row['room_id'] is not None}),
            'guest_ids': list(booking['guest_ids']), 'folio_ids': folios,
            'agency_id': booking['agency_id'],
            'finance_status': 'available' if folios else 'not_applicable',
        }
    dates = [(date.fromisoformat(canonical['as_of']) + timedelta(days=i)).isoformat()
             for i in range(-1, 6)]
    room_plan = {row['id']: row for row in evaluation['room_plan']}
    blocked = {row['id'] for row in evaluation['arrivals'] if row['status'] == 'blocked'}
    timeline = {'dates': dates, 'rows': []}
    for room in canonical['rooms']:
        plan = room_plan[room['id']]
        cells = []
        for day in dates:
            # Geometry of declared source assignments, not a new availability
            # decision or a prediction of future physical occupancy.
            assigned = {row['reservation_id'] for row in canonical['room_stays']
                        if row['room_id'] == room['id'] and row['arrival'] <= day < row['departure']}
            current = day == canonical['as_of']
            if current:
                assigned.update(links['review_links'][identifier]['reservation_id']
                                for identifier in plan['held_reservation_ids'])
            technical = any(block['room_id'] == room['id'] and block['status'] == 'active'
                            and block['start'] <= day and (block['end'] is None or day < block['end'])
                            for block in canonical['room_blocks'])
            cells.append({'date': day, 'reservation_ids': sorted(assigned),
                          'reason_codes': list(plan['reason_codes']) if current else [],
                          'current_day_hold': current and bool(plan['held_reservation_ids']),
                          'technical': technical,
                          'requires_review': current and bool(set(plan['held_reservation_ids']) & blocked)})
        timeline['rows'].append({'room_id': room['id'], 'cells': cells})
    today_ids = {links['review_links'][booking['id']]['reservation_id'] for booking in review['reservations']
                 if booking['arrival'] == review['as_of'] and booking['status'] != 'checked_out'}
    blocked_parents = {links['review_links'][row['id']]['reservation_id']
                       for row in evaluation['arrivals'] if row['status'] == 'blocked'}
    stories = build_demo_stories(review)
    concept = {'schema_version': 'canonical-concept.v1', 'canonical_sha256': checksum,
               'as_of': canonical['as_of'], 'rooms': review['rooms'],
               'reservations': review['reservations'], 'room_plan': evaluation['room_plan'],
               'arrivals': evaluation['arrivals'], 'summary': evaluation['summary'],
               'stories': stories['stories'], 'timeline': timeline,
               'metrics': {'rooms': len(canonical['rooms']), 'arrivals_today': len(today_ids),
                           'blocked_today': len(today_ids & blocked_parents)},
               'reason_text': {locale: {code: localize_code(code, locale)['text'] for code in CODES}
                               for locale in LOCALES}}
    return {'canonical': canonical, 'canonical_links': links, 'review_data': review,
            'review_report': evaluation, 'stories': stories, 'operations_data': operations,
            'operations_report': financial, 'concept': concept}
