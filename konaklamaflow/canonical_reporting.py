"""Source-bound reporting over one validated, entirely fictional hotel model.

The original hotel_ops API remains strict and backwards compatible. This
adapter accepts operational conflicts as *review facts*, after canonical schema
validation, and shares its existing Decimal report formatter. It cannot post,
settle, connect to a provider or authorize an operation.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from decimal import Decimal

from .experience_engine import evaluate
from .hotel_ops import HotelOpsError, _assemble_operations_report, _SUPPORTED_REPORTS

FOLIO_REPORTS = frozenset({
    'active_folios', 'folio_analysis', 'transactions', 'posting_invoice',
    'detailed_revenue', 'daily_balance', 'monthly_revenue', 'grouped_transactions',
    'agency_monthly', 'agency_annual', 'agency_sales', 'city_ledger', 'extra_bed',
    'advance_payment',
})
MISSING_REPORT_SOURCES = {
    'trial_balance': 'accounting', 'fiscal_list': 'fiscal',
    'checkin_cancellations': 'immutable_checkin_audit', 'linen_list': 'linen_usage',
    'budget_analysis': 'budget', 'it_report': 'system_logs',
    'email_report': 'mail_permissions', 'safe_deposit': 'safe_ledger',
    'invoice_register': 'fiscal_invoices', 'income_expense': 'expense_ledger',
    'revenue_management': 'revenue_management_inputs',
}
REPORT_IDS = frozenset(_SUPPORTED_REPORTS) | frozenset(MISSING_REPORT_SOURCES)


def _explicit_transactions(ops):
    """Retain source record IDs, not just a copied ordinal or derived amount."""
    postings, payments = [], []
    bookings = {booking['id']: booking for booking in ops['reservations']}
    for folio in ops['folios']:
        common = {
            'folio_id': folio['id'], 'reservation_id': folio['reservation_id'],
            'room_stay_id': folio['room_stay_id'], 'room_id': folio['room_id'],
            'currency': folio['currency'],
            'agency_id': folio['agency_id'],
            'booking_agency_id': bookings[folio['reservation_id']]['agency_id'],
        }
        for row in folio['postings']:
            postings.append({**common, 'posting_id': row['id'],
                             'date': row['date'], 'kind': row['kind'],
                             'amount': row['amount'], 'description': row['description']})
        for row in folio['payments']:
            payments.append({**common, 'payment_id': row['id'],
                             'date': row['date'], 'method': row['method'],
                             'amount': row['amount']})
    return postings, payments


def build_canonical_operations_report(source):
    """Derive all registry views from canonical references and explicit sources.

    A quoted reservation price is never expanded into nightly rates, a posting,
    a payment or a folio. Missing data stays missing. An empty balance is not
    invented for a reservation that has no recorded folio.
    """
    from .canonical import (canonical_fingerprint, project_operations,
                            project_review, review_links, validate_canonical)

    canonical = validate_canonical(source)
    ops = project_operations(canonical)
    checksum = canonical_fingerprint(canonical)
    if len(ops['report_catalog']) != 32 or {entry['id'] for entry in ops['report_catalog']} != REPORT_IDS:
        raise HotelOpsError('Invalid canonical report registry')
    # The legacy arithmetic helper is private and receives only this validated
    # projection. Its implementation flags are technical formatter switches;
    # actual source availability is classified below, separately.
    assembly = deepcopy(ops)
    for entry in assembly['report_catalog']:
        entry['status'] = 'implemented' if entry['id'] in _SUPPORTED_REPORTS else 'not_implemented'
    report = _assemble_operations_report(assembly)
    reports = report['reports']
    postings, payments = _explicit_transactions(ops)
    reports['transactions']['rows'] = postings + payments
    reports['posting_invoice']['rows'] = deepcopy(postings)
    reports['detailed_revenue']['rows'] = deepcopy(postings)
    reports['extra_bed']['rows'] = [row for row in postings if row['kind'] == 'EXTRA_BED']
    reports['advance_payment']['rows'] = [row for row in payments if row['date'] < ops['as_of']]
    reports['room_rate_control']['rows'] = [
        {'reservation_id': booking['id'], 'room_stay_id': part['room_stay_id'],
         'date': nightly['date'], 'room': part['room_id'],
         'category': part['category'], 'amount': nightly['amount'],
         'currency': booking['currency']}
        for booking in ops['reservations'] for part in booking['rooms']
        for nightly in part['nightly_rates']
    ]

    # "Daily" means the declared business date, not the entire lifetime of
    # every folio. It remains source movements, not a reconciled cash ledger.
    daily = defaultdict(lambda: {'postings': Decimal('0.00'), 'payments': Decimal('0.00')})
    for row in postings:
        if row['date'] == ops['as_of']:
            daily[row['currency']]['postings'] += Decimal(row['amount'])
    for row in payments:
        if row['date'] == ops['as_of']:
            daily[row['currency']]['payments'] += Decimal(row['amount'])
    reports['daily_balance']['rows'] = [
        {'date': ops['as_of'], 'currency': currency,
         'postings': f"{amounts['postings']:.2f}",
         'payments': f"{amounts['payments']:.2f}",
         'net': f"{amounts['postings'] - amounts['payments']:.2f}"}
        for currency, amounts in sorted(daily.items())
    ]

    booking_map = {row['id']: row for row in canonical['reservations']}
    raw_folios = {row['id']: row for row in ops['folios']}
    for folio in report['folios']:
        folio['room_stay_id'] = raw_folios[folio['folio_id']]['room_stay_id']
        folio['source_record_id'] = folio['folio_id']
        folio['source_kind'] = 'explicit_fictional_folio'
        folio['agency_id'] = raw_folios[folio['folio_id']]['agency_id']
        folio['booking_agency_id'] = booking_map[folio['reservation_id']]['agency_id']
    for folio in report['city_ledger']:
        folio['room_stay_id'] = raw_folios[folio['folio_id']]['room_stay_id']
        folio['source_record_id'] = folio['folio_id']
        folio['source_kind'] = 'explicit_fictional_folio'
        folio['agency_id'] = raw_folios[folio['folio_id']]['agency_id']
        folio['booking_agency_id'] = booking_map[folio['reservation_id']]['agency_id']

    # IDs, not company-name or array-position matching, carry agency identity.
    agencies = {agency['id']: agency for agency in ops['agencies']}
    agency_postings = [row for row in postings if row['agency_id'] is not None]
    reports['agency_sales']['rows'] = [
        {**row, 'agency': agencies[row['agency_id']]['name'],
         'legal_name': agencies[row['agency_id']]['legal_name']}
        for row in agency_postings
    ]
    for key, width, period in (('agency_monthly', 7, 'month'), ('agency_annual', 4, 'year')):
        totals = defaultdict(lambda: Decimal('0.00'))
        for row in agency_postings:
            totals[(row['agency_id'], row['date'][:width], row['currency'])] += Decimal(row['amount'])
        reports[key]['rows'] = [
            {'agency_id': agency_id, 'agency': agencies[agency_id]['name'],
             period: interval, 'currency': currency, 'total': f'{amount:.2f}'}
            for (agency_id, interval, currency), amount in sorted(totals.items())
        ]

    reports['room_list']['rows'] = [
        {**room,
         'reservation_ids': sorted({stay['reservation_id'] for stay in canonical['room_stays']
                                    if stay['room_id'] == room['id']}),
         'room_stay_ids': sorted(stay['id'] for stay in canonical['room_stays']
                                 if stay['room_id'] == room['id'])}
        for room in ops['rooms']
    ]
    source_guests = {guest['id']: guest for guest in canonical['guests']}
    reports['guest_list']['rows'] = [
        {**guest, 'display_label': source_guests[guest['id']]['display_label'],
         'reservation_ids': sorted(booking['id'] for booking in canonical['reservations']
                                    if guest['id'] in booking['guest_ids']),
         'room_stay_ids': sorted(stay['id'] for stay in canonical['room_stays']
                                 if guest['id'] in stay['guest_ids'])}
        for guest in reports['guest_list']['rows']
    ]

    # Room hold facts come from the same authoritative review engine used by
    # the dashboard. They are not a new browser availability calculation.
    review = evaluate(project_review(canonical))
    links = review_links(canonical)
    room_rows = []
    for room in review['room_plan']:
        held = [links[identifier] for identifier in room['held_reservation_ids']]
        all_holds = [links[identifier] for identifier in room['reservation_ids_all_holds']]
        source_blocks = [block['id'] for block in canonical['room_blocks']
                         if block['room_id'] == room['id'] and block['status'] == 'active'
                         and block['start'] <= canonical['as_of']
                         and (block['end'] is None or canonical['as_of'] < block['end'])]
        # Preserve explicit physical signals as source facts. A hold alone does
        # not prove that an actual guest physically occupies the room.
        physical_signals = [
            {'reservation_id': link['reservation_id'], 'room_stay_id': link['room_stay_id'],
             'status': booking_map[link['reservation_id']]['status'],
             'arrival_state': booking_map[link['reservation_id']]['arrival_state']}
            for link in all_holds
        ]
        room_rows.append({
            'room': room['id'], 'held_in_review_snapshot': bool(held),
            'reservation_ids': sorted({link['reservation_id'] for link in held}),
            'room_stay_ids': sorted({link['room_stay_id'] for link in held}),
            'all_hold_reservation_ids': sorted({link['reservation_id'] for link in all_holds}),
            'source_physical_signals': physical_signals,
            'room_block_ids': source_blocks, 'reason_codes': list(room['reason_codes']),
        })
    reports['occupancy']['rows'] = room_rows
    reports['blockage_report']['rows'] = [
        row for row in room_rows if row['held_in_review_snapshot'] or row['room_block_ids']
        or 'OUT_OF_SERVICE_OR_MAINTENANCE' in row['reason_codes']
    ]

    all_bookings = set(booking_map)
    financial_bookings = {folio['reservation_id'] for folio in ops['folios']}
    priced_bookings = {row['id'] for row in ops['reservations']
                       if any(part['nightly_rates'] for part in row['rooms'])}
    for key, entry in reports.items():
        missing = []
        if key in MISSING_REPORT_SOURCES:
            missing = [MISSING_REPORT_SOURCES[key]]
        elif key in FOLIO_REPORTS and not ops['folios']:
            missing = ['explicit_folios']
        elif key == 'room_rate_control' and not priced_bookings:
            missing = ['explicit_nightly_rates']
        elif key == 'exchange_rates' and not ops['fx_rates']:
            missing = ['fx_rates']
        entry['status'] = 'not_implemented' if missing else 'implemented'
        entry['source_state'] = ('source_not_connected' if key == 'exchange_rates' and missing
                                 else 'missing_source' if missing else 'synthetic_snapshot')
        entry['missing_sources'] = missing
        entry['canonical_sha256'] = checksum
        entry['scope'] = (
            'recorded_folio_movements_on_business_date_not_cash_reconciliation' if key == 'daily_balance'
            else 'recorded_folio_postings_only_not_earned_revenue' if key in {
                'monthly_revenue', 'detailed_revenue', 'agency_monthly', 'agency_annual', 'agency_sales'}
            else 'recorded_folio_postings_only_not_a_fiscal_invoice' if key == 'posting_invoice'
            else 'review_engine_hold_signals_not_verified_physical_occupancy' if key in {'occupancy', 'blockage_report'}
            else 'explicit_nightly_rates_only_not_inferred_from_quote' if key == 'room_rate_control'
            else 'explicit_canonical_source_only'
        )
        covered = financial_bookings if key in FOLIO_REPORTS else priced_bookings if key == 'room_rate_control' else all_bookings
        entry['coverage'] = {
            'reservation_ids': sorted(covered) if not missing else [],
            'missing_reservation_ids': sorted(all_bookings - covered) if not missing else sorted(all_bookings),
        }
        if missing:
            entry['rows'] = []

    reservation_links = {}
    for identifier, booking in booking_map.items():
        folios = sorted(folio['id'] for folio in ops['folios'] if folio['reservation_id'] == identifier)
        reservation_links[identifier] = {
            'reservation_id': identifier, 'room_stay_ids': list(booking['room_stay_ids']),
            'folio_ids': folios, 'finance_status': 'available' if folios else 'not_applicable',
            'reason_code': 'EXPLICIT_FOLIO_SOURCE' if folios else 'NO_FOLIO_IN_SYNTHETIC_SOURCE',
            'report_ids': ['reservation_list', 'occupancy']
                          + (['room_rate_control'] if identifier in priced_bookings else [])
                          + (['folio_analysis', 'transactions'] if folios else []),
        }
    report.update({
        'schema': 'konaklamaflow.canonical-operations-report.v1',
        'canonical_sha256': checksum, 'source_state': 'synthetic_snapshot',
        'scenario_id': canonical['scenario_id'], 'reservation_links': reservation_links,
        'integrations': {name: 'source_not_connected'
                         for name in ('pms', 'ota', 'ai', 'payments', 'kbs')},
        'review_snapshot_sha256': review['snapshot_sha256'],
    })
    return report
