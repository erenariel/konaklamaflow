"""One explicit fictional hotel snapshot; projections never join records by order.

This is schema/reference validation and adaptation to the existing Python rule
engine, not PMS authorization or a new browser decision engine. Operationally
bad assignments are retained as facts for review. Real identities are excluded.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
import re

from .experience_engine import (AMENITY_FLAGS, BEDS, BOOKING_STATES, CATEGORIES,
                                CHANNELS, REQUEST_FLAGS, ROOM_STATES,
                                evaluate, validate as validate_review)

SCHEMA_VERSION = 'canonical-hotel.v1'
TOP = {'schema_version','scenario_id','property_id','as_of','at_time','default_currency',
       'fictional','privacy_policy','provenance','rooms','agencies','guests',
       'reservations','room_stays','folios','channel_events','tasks','room_blocks',
       'report_catalog','fx_rates','payment_methods','board_types',
       'reservation_statuses','report_versions','contact_fields_schema'}
REPORT_IDS = frozenset('active_folios monthly_revenue detailed_revenue folio_analysis daily_balance trial_balance transactions grouped_transactions fiscal_list room_list room_rate_control agency_monthly agency_sales agency_annual checkin_cancellations linen_list budget_analysis blockage_report it_report extra_bed email_report safe_deposit advance_payment posting_invoice invoice_register income_expense revenue_management occupancy city_ledger exchange_rates reservation_list guest_list'.split())
_IDENT = re.compile(r'^[A-Za-z0-9_-]{1,40}$')
_MONEY = re.compile(r'^(?:0|[1-9][0-9]{0,9})\.[0-9]{2}$')
_CURRENCIES = {'EUR','TRY','USD','GBP'}
_NULL_PII = {'identity_number','turkish_national_id','birth_place','date_of_birth',
             'address','telephone','email'}


class CanonicalError(ValueError):
    """Invalid fictional source; messages never reflect input values."""


def _bad():
    raise CanonicalError('Invalid canonical fictional hotel snapshot')


def _object(value, fields):
    if not isinstance(value, dict) or set(value) != set(fields):
        _bad()
    return value


def _id(value):
    if not isinstance(value, str) or _IDENT.fullmatch(value) is None:
        _bad()
    return value


def _text(value, maximum=160):
    if not isinstance(value, str) or not value or len(value) > maximum or any(ord(c) < 32 for c in value):
        _bad()
    return value


def _day(value):
    if not isinstance(value, str) or re.fullmatch(r'\d{4}-\d{2}-\d{2}',value) is None:
        _bad()
    try:
        return date.fromisoformat(value)
    except ValueError:
        _bad()


def _money(value, positive=False):
    if not isinstance(value,str) or _MONEY.fullmatch(value) is None:
        _bad()
    amount=Decimal(value)
    if positive and amount <= 0:
        _bad()
    return amount


def _rows(value, maximum):
    if not isinstance(value,list) or len(value)>maximum or any(not isinstance(row,dict) for row in value):
        _bad()
    return value


def _index(rows):
    result={}
    for row in rows:
        identifier=_id(row.get('id'))
        if identifier in result:
            _bad()
        result[identifier]=row
    return result


def _refs(value, known, maximum=1000):
    if (not isinstance(value,list) or len(value)>maximum
            or any(not isinstance(v,str) or v not in known for v in value)
            or len(value)!=len(set(value))):
        _bad()


def _source_ref(value, property_id, pms=False):
    fields={'kind','property_id','external_id'} if pms else {'kind','provider','property_id','external_id'}
    _object(value,fields)
    if value['property_id'] != property_id:
        _bad()
    _id(value['external_id'])
    if pms:
        if value['kind']!='pms':_bad()
    else:
        provider=value['provider']
        if provider not in CHANNELS:_bad()
        expected={'direct':'direct','agency':'agency','channel_manager':'channel_manager'}.get(provider,'ota')
        if value['kind']!=expected:_bad()


def _case_links(source):
    result={}
    for booking in source['reservations']:
        for stay_id in booking['room_stay_ids']:
            engine_id=booking['id'] if len(booking['room_stay_ids'])==1 else stay_id
            if engine_id in result or len(result)>=5000:_bad()
            result[engine_id]={'reservation_id':booking['id'],'room_stay_id':stay_id}
    return result


def _review_projection(source):
    stays={row['id']:row for row in source['room_stays']}
    bookings={row['id']:row for row in source['reservations']}
    links=_case_links(source)
    cases=[]
    for engine_id,link in links.items():
        booking=bookings[link['reservation_id']];stay=stays[link['room_stay_id']]
        cases.append({
            'id':engine_id,'channel':booking['source_ref']['provider'],
            'external_ref':booking['source_ref']['external_id'],
            'pms_ref':booking['pms_ref']['external_id'] if booking['pms_ref'] else None,
            'arrival':stay['arrival'],'departure':stay['departure'],
            'category':stay['category'],'persons':stay['adults']+stay['children'],
            'bed_request':stay['bed_request'],'status':booking['status'],
            'room_id':stay['room_id'],'identity_signal':booking['identity_signal'],
            'payment_signal':booking['payment_signal'],'pms_registration':booking['pms_registration'],
            'requests':deepcopy(stay['requests']),
            'price_total':stay['quote_total'],'currency':booking['currency'],
            'arrival_state':booking['arrival_state'],
        })
    rooms=[]
    for room in source['rooms']:
        value={k:deepcopy(v) for k,v in room.items() if k!='assets'}
        for block in source['room_blocks']:
            if block['room_id']!=room['id'] or block['status']!='active':continue
            if block['end'] is not None:
                window={'start':block['start'],'end':block['end']}
                if window not in value['maintenance']:value['maintenance'].append(window)
            elif block['start']<=source['as_of']:
                # An open-ended hold is not released merely because a booking
                # was cancelled. No invented end date is exposed in the model.
                value['housekeeping']='out_of_order' if block['kind']=='out_of_order' else 'out_of_service'
            else:
                # The legacy engine has no open-ended future window. Reject this
                # unsupported projection instead of silently making room available.
                _bad()
        rooms.append(value)
    events=[]
    for event in source['channel_events']:
        targets=[(eid,link) for eid,link in links.items() if link['reservation_id']==event['reservation_id']]
        if event['reservation_id'] is None:targets=[(None,None)]
        for eid,link in targets:
            identifier=event['id'] if len(targets)==1 else 'EV_'+sha256((event['id']+'\0'+link['room_stay_id']).encode()).hexdigest()[:24]
            events.append({'id':identifier,'channel':event['source_ref']['provider'],
                           'external_ref':event['source_ref']['external_id'],
                           'status':event['status'],'reservation_id':eid})
    tasks=[]
    for task in source['tasks']:
        targets=[(eid,link) for eid,link in links.items() if link['reservation_id']==task['reservation_id']
                 and (task['room_id'] is None or stays[link['room_stay_id']]['room_id']==task['room_id'])]
        if task['reservation_id'] is None:targets=[(None,None)]
        for eid,link in targets:
            identifier=task['id'] if len(targets)==1 else 'TASK_'+sha256((task['id']+'\0'+link['room_stay_id']).encode()).hexdigest()[:24]
            tasks.append({**deepcopy(task),'id':identifier,'reservation_id':eid})
    return {'schema_version':'0.3','property_id':source['property_id'],
            'as_of':source['as_of'],'at_time':source['at_time'],'rooms':rooms,
            'reservations':cases,'channel_events':events,'tasks':tasks}


def validate_canonical(source):
    """Validate structure and exact FKs; retain conflicts for authoritative review."""
    try:
        _object(source,TOP)
        value=deepcopy(source)
        if (value['schema_version']!=SCHEMA_VERSION or value['fictional'] is not True
                or value['privacy_policy']!='SYNTHETIC_NO_REAL_IDENTITIES'):_bad()
        _id(value['scenario_id']);_id(value['property_id']);_day(value['as_of'])
        if value['as_of']=='9999-12-31' or value['default_currency'] not in _CURRENCIES:_bad()
        if not isinstance(value['at_time'],str) or re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d',value['at_time']) is None:_bad()
        _object(value['provenance'],{'kind','legacy_financial_records_migrated','live_sources'})
        if (value['provenance']['kind']!='NEW_AUTHORED_SYNTHETIC_SCENARIO'
                or value['provenance']['legacy_financial_records_migrated'] is not False
                or value['provenance']['live_sources']!='source_not_connected'):_bad()
        limits={'rooms':500,'agencies':100,'guests':1000,'reservations':5000,'room_stays':5000,
                'folios':5000,'channel_events':5000,'tasks':5000,'room_blocks':1000,'report_catalog':100,'fx_rates':100}
        for key,limit in limits.items():_rows(value[key],limit)
        indices={key:_index(value[key]) for key in limits if key not in {'report_catalog','fx_rates'}}
        rooms,agencies,guests,bookings,stays,folios=(indices[k] for k in ('rooms','agencies','guests','reservations','room_stays','folios'))
        for room in rooms.values():
            _object(room,{'id','category','capacity','bed','housekeeping','floor','amenities','maintenance','assets'})
            if room['category'] not in CATEGORIES or room['bed'] not in BEDS or room['housekeeping'] not in ROOM_STATES:_bad()
            if type(room['capacity']) is not int or not 1<=room['capacity']<=20 or type(room['floor']) is not int or not -3<=room['floor']<=100:_bad()
            _refs(room['amenities'],AMENITY_FLAGS,30)
            if not isinstance(room['assets'],list) or len(room['assets'])>40:_bad()
            for item in room['assets']:_text(item,48)
            for window in _rows(room['maintenance'],100):
                _object(window,{'start','end'})
                if _day(window['start'])>=_day(window['end']):_bad()
        for agency in agencies.values():
            _object(agency,{'id','name','legal_name','type','city_ledger_terms_days','settlement_currency'})
            _text(agency['name']);
            if agency['legal_name'] is not None:_text(agency['legal_name'])
            if agency['type'] not in {'direct','ota','wholesale','agency'} or agency['settlement_currency'] not in _CURRENCIES:_bad()
            if type(agency['city_ledger_terms_days']) is not int or not 0<=agency['city_ledger_terms_days']<=365:_bad()
        for guest in guests.values():
            _object(guest,{'id','surname','given_name','identity_type','country','preferred_language','title','gender','privacy_status','display_label'}|_NULL_PII)
            if guest['privacy_status']!='NO_REAL_PERSONAL_DATA' or any(guest[k] is not None for k in _NULL_PII):_bad()
            if not isinstance(guest['surname'],str) or not guest['surname'].startswith('DEMO_') or guest['given_name']!='ÖRNEK':_bad()
            _text(guest['surname'],64);_text(guest['display_label'],80)
            if guest['identity_type'] not in {'passport','eu_identity','national_id','driving_licence','other'}:_bad()
            if guest['country'] not in {'TR','DE','FR','GB','GR','IL','SA','RU','ES','UA','US','IT','PT','CN','JP'}:_bad()
            if guest['preferred_language'] not in {'tr','en','fr','el','he','ar','de','ru','es','uk'}:_bad()
            if guest['title'] not in {'unspecified','mr','ms','mrs','dr'} or guest['gender'] not in {'unspecified','male','female','other'}:_bad()
        for booking in bookings.values():
            _object(booking,{'id','display_name','agency_id','source_ref','pms_ref','status','arrival_state','identity_signal','payment_signal','currency','room_stay_ids','guest_ids','board','payment_type','commission_type','group_name','option_expiry','pms_registration'})
            if booking['agency_id'] not in agencies or booking['status'] not in BOOKING_STATES or booking['currency'] not in _CURRENCIES:_bad()
            if not isinstance(booking['display_name'],str) or not booking['display_name'].startswith('ÖRNEK'):_bad()
            _text(booking['display_name']);_source_ref(booking['source_ref'],value['property_id'])
            if booking['pms_ref'] is not None:_source_ref(booking['pms_ref'],value['property_id'],True)
            if booking['arrival_state'] not in {'expected','arrived','checked_in','checked_out'} or booking['identity_signal'] not in {'pending_staff','staff_verified','not_required_for_demo'} or booking['payment_signal'] not in {'review','ready','agency_ledger'}:_bad()
            if booking['pms_registration'] not in {'not_recorded','recorded_by_authorized_staff'}:_bad()
            _refs(booking['room_stay_ids'],stays,12);_refs(booking['guest_ids'],guests,240)
            if not booking['room_stay_ids']:_bad()
            if booking['board'] not in {'BB','HB','RO','FB'} or booking['payment_type'] not in {'city_ledger','self_payment'} or booking['commission_type'] not in {'net','commission','none'}:_bad()
            if booking['group_name'] is not None and (not isinstance(booking['group_name'],str) or not booking['group_name'].startswith('DEMO')):_bad()
            if booking['option_expiry'] is not None:_day(booking['option_expiry'])
        seen_stays=set()
        for booking in bookings.values():
            assigned_guests=set()
            for stay_id in booking['room_stay_ids']:
                if stay_id in seen_stays or stays[stay_id]['reservation_id']!=booking['id']:_bad()
                seen_stays.add(stay_id);assigned_guests.update(stays[stay_id]['guest_ids'])
            if assigned_guests!=set(booking['guest_ids']):_bad()
        if seen_stays!=set(stays):_bad()
        for stay in stays.values():
            _object(stay,{'id','reservation_id','arrival','departure','room_id','category','adults','children','guest_ids','bed_request','requests','quote_total','nightly_rates'})
            if stay['reservation_id'] not in bookings or stay['room_id'] is not None and stay['room_id'] not in rooms or stay['category'] not in CATEGORIES:_bad()
            start,end=_day(stay['arrival']),_day(stay['departure'])
            if end<=start or (end-start).days>366:_bad()
            if type(stay['adults']) is not int or type(stay['children']) is not int or stay['adults']<1 or stay['children']<0 or not 1<=stay['adults']+stay['children']<=20:_bad()
            _refs(stay['guest_ids'],guests,20)
            if len(stay['guest_ids'])>stay['adults']+stay['children'] or stay['bed_request'] not in {'none','twin','double'}:_bad()
            _refs(stay['requests'],REQUEST_FLAGS,12);quote=_money(stay['quote_total'])
            rates=_rows(stay['nightly_rates'],366);seen_dates=set()
            for rate in rates:
                _object(rate,{'date','amount'});day=_day(rate['date']);_money(rate['amount'])
                if not start<=day<end or rate['date'] in seen_dates:_bad()
                seen_dates.add(rate['date'])
            if rates and (len(rates)!=(end-start).days or sum((_money(r['amount']) for r in rates),Decimal('0.00'))!=quote):_bad()
        transaction_ids=set()
        for folio in folios.values():
            _object(folio,{'id','reservation_id','room_stay_id','room_id','payer_type','agency_id','status','currency','invoice_status','invoice_region','explanation','origin','postings','payments','city_ledger_due','agency_invoice_reference'})
            if folio['reservation_id'] not in bookings or folio['room_stay_id'] not in stays:_bad()
            stay=stays[folio['room_stay_id']];booking=bookings[folio['reservation_id']]
            if stay['reservation_id']!=booking['id'] or stay['room_id']!=folio['room_id'] or folio['currency']!=booking['currency']:_bad()
            if folio['origin']!='EXPLICIT_CANONICAL_FIXTURE' or folio['status'] not in {'open','closed','void'} or folio['payer_type'] not in {'agency','guest'} or folio['invoice_status'] not in {'not_issued','draft'} or folio['invoice_region']!='TR':_bad()
            if (folio['payer_type']=='agency')!=(folio['agency_id'] is not None):_bad()
            if folio['agency_id'] is not None and folio['agency_id']!=booking['agency_id']:_bad()
            _text(folio['explanation'])
            if folio['city_ledger_due'] is not None:_day(folio['city_ledger_due'])
            if folio['agency_invoice_reference'] is not None:_id(folio['agency_invoice_reference'])
            for collection in ('postings','payments'):
                for row in _rows(folio[collection],5000):
                    _object(row,{'id','date','kind','description','amount'} if collection=='postings' else {'id','date','method','amount','reference'})
                    identifier=_id(row['id'])
                    if identifier in transaction_ids:_bad()
                    transaction_ids.add(identifier);_money(row['amount'],True);day=_day(row['date'])
                    if day>_day(value['as_of']):_bad()
                    if collection=='postings':
                        if not _day(stay['arrival'])<=day<_day(stay['departure']) or row['kind'] not in {'ROOM','RESTAURANT','MINIBAR','TRANSFER','EXTRA_BED','EXTRA_STAY','FX_DIFFERENCE','ADJUSTMENT','OTHER'}:_bad()
                        _text(row['description'])
                    else:
                        if row['method'] not in {'cash','credit_card','mail_order','bank_transfer'}:_bad()
                        _id(row['reference'])
        for event in value['channel_events']:
            _object(event,{'id','status','reservation_id','source_ref'})
            _source_ref(event['source_ref'],value['property_id'])
            if event['status'] not in {'received','mapped','needs_review','cancelled'} or event['reservation_id'] is not None and event['reservation_id'] not in bookings:_bad()
        for task in value['tasks']:
            _object(task,{'id','kind','room_id','reservation_id','status','priority'})
            if task['kind'] not in {'housekeeping','maintenance','guest_request','frontdesk'} or task['status'] not in {'open','in_progress','done'} or task['priority'] not in {'low','normal','high'}:_bad()
            if task['room_id'] is not None and task['room_id'] not in rooms or task['reservation_id'] is not None and task['reservation_id'] not in bookings:_bad()
            if task['room_id'] is None and task['reservation_id'] is None:_bad()
            if task['room_id'] is not None and task['reservation_id'] is not None:
                linked=[stays[s]['room_id'] for s in bookings[task['reservation_id']]['room_stay_ids']]
                if task['room_id'] not in linked:_bad()
        for block in value['room_blocks']:
            _object(block,{'id','room_id','start','end','kind','status'})
            if block['room_id'] not in rooms or block['kind'] not in {'out_of_order','out_of_service','maintenance','hold'} or block['status'] not in {'active','released'}:_bad()
            if block['end'] is not None and _day(block['start'])>=_day(block['end']):_bad()
            _day(block['start'])
        observed=set()
        for entry in value['report_catalog']:
            _object(entry,{'id','label','status'});_text(entry['label'])
            if entry['id'] not in REPORT_IDS or entry['id'] in observed or not isinstance(entry['status'],str) or not (entry['status']=='implemented' or re.fullmatch(r'requires_[a-z_]{1,40}',entry['status'])):_bad()
            observed.add(entry['id'])
        if observed!=REPORT_IDS:_bad()
        for rate in value['fx_rates']:
            _object(rate,{'currency','to','rate','as_of','source'})
            if rate['currency'] not in _CURRENCIES or rate['to'] not in _CURRENCIES or rate['source']!='FICTIONAL_DEMO_RATE':_bad()
            if not isinstance(rate['rate'],str) or re.fullmatch(r'\d{1,6}\.\d{4}',rate['rate']) is None or Decimal(rate['rate'])<=0:_bad()
            _day(rate['as_of'])
        if value['payment_methods']!=['cash','credit_card','mail_order','bank_transfer'] or value['board_types']!=['BB','HB','RO','FB']:_bad()
        if value['reservation_statuses']!=['confirmed','pending','cancelled','in_house','checked_out','no_show']:_bad()
        _object(value['report_versions'],{'accounting','fiscal','hotel_clock'})
        if value['report_versions']!={'accounting':'not_configured','fiscal':'not_configured','hotel_clock':value['as_of']}:_bad()
        if not isinstance(value['contact_fields_schema'],list) or len(value['contact_fields_schema'])>30:_bad()
        for field in value['contact_fields_schema']:_id(field)
        # Reuse the existing engine's strict minimized schema. This intentionally
        # retains room conflicts, cancelled physical holds and incompatible beds.
        validate_review(_review_projection(value))
        return value
    except CanonicalError:
        raise
    except (ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError,AttributeError):
        _bad()


def canonical_fingerprint(source):
    value=validate_canonical(source)
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()).hexdigest()


def project_review(source):
    return _review_projection(validate_canonical(source))


def review_links(source):
    return _case_links(validate_canonical(source))


def project_operations(source):
    value=validate_canonical(source);stays={s['id']:s for s in value['room_stays']}
    rooms=[]
    for room in value['rooms']:
        active=[b for b in value['room_blocks'] if b['room_id']==room['id'] and b['status']=='active' and b['start']<=value['as_of'] and (b['end'] is None or value['as_of']<b['end'])]
        rooms.append({**deepcopy(room),'blocked':bool(active) or room['housekeeping'] in {'out_of_order','out_of_service'},'room_block_ids':[b['id'] for b in active]})
    bookings=[]
    for booking in value['reservations']:
        parts=[stays[s] for s in booking['room_stay_ids']]
        bookings.append({
            'id':booking['id'],'name':booking['display_name'],'group_name':booking['group_name'],
            'checkin':min(p['arrival'] for p in parts),'checkout':max(p['departure'] for p in parts),
            'agency_id':booking['agency_id'],'agency_ref':booking['source_ref']['external_id'],
            'source_ref':deepcopy(booking['source_ref']),'pms_ref':deepcopy(booking['pms_ref']),
            'status':booking['status'],'source_status':booking['status'],'arrival_state':booking['arrival_state'],
            'board':booking['board'],'payment_type':booking['payment_type'],
            'commission_type':booking['commission_type'],'option_expiry':booking['option_expiry'],
            'room_stay_ids':list(booking['room_stay_ids']),'guest_ids':list(booking['guest_ids']),
            'rooms':[{'room_stay_id':p['id'],'room_id':p['room_id'],'category':p['category'],
                      'arrival':p['arrival'],'departure':p['departure'],'adults':p['adults'],'children':p['children'],
                      'guest_ids':list(p['guest_ids']),'nightly_rates':deepcopy(p['nightly_rates']),
                      'bed_request':p['bed_request'],'requests':deepcopy(p['requests']),
                      'arrival_state':booking['arrival_state'],'quote_total':p['quote_total']} for p in parts],
            'currency':booking['currency'],'notes':None,
            'special_requests':sorted({flag for p in parts for flag in p['requests']}),
        })
    return {**{k:deepcopy(v) for k,v in value.items() if k in {
        'property_id','as_of','default_currency','fictional','privacy_policy','agencies',
        'guests','folios','report_catalog','fx_rates','payment_methods','board_types',
        'reservation_statuses','report_versions','contact_fields_schema'}},
        'schema_version':'canonical-operations-projection.v1','scenario_id':value['scenario_id'],
        'rooms':rooms,'reservations':bookings,'room_stays':deepcopy(value['room_stays']),
        'room_blocks':deepcopy(value['room_blocks']),'tasks':deepcopy(value['tasks']),
        'channel_events':deepcopy(value['channel_events'])}


def aggregate_reservation_reviews(source):
    """Group engine results by explicit parent FK; never weaken a child blocker.

    The current per-stay engine conservatively flags shared source references
    in a multi-room booking. Those blockers are retained and disclosed, not
    hidden with fabricated references or a first-room-only readiness decision.
    """
    value=validate_canonical(source);raw=evaluate(_review_projection(value));links=_case_links(value)
    grouped=[]
    for booking in value['reservations']:
        children=[{**row,**links[row['id']]} for row in raw['arrivals'] if links[row['id']]['reservation_id']==booking['id']]
        blockers=sorted({code for row in children for code in row['blockers']})
        grouped.append({'reservation_id':booking['id'],'room_stay_ids':list(booking['room_stay_ids']),
                        'engine_case_ids':[row['id'] for row in children],
                        'status':'review_ready' if all(row['status']=='review_ready' for row in children) else 'blocked',
                        'blockers':blockers,'room_stay_reviews':children,
                        'review_scope':'per_room_stay_conservative',
                        'requires_multiroom_review':len(children)>1,
                        'scope_note':'SHARED_PARENT_REFERENCES_ARE_NOT_PROOF_OF_DUPLICATE_OTA' if len(children)>1 else 'SINGLE_ROOM_STAY_ENGINE_REVIEW',
                        'human_approval_required':True,
                        'live_operations_allowed':False})
    return {'schema':'canonical-reservation-review.v1','canonical_sha256':canonical_fingerprint(value),
            'as_of':value['as_of'],'reservations':grouped,'raw_review':raw}
