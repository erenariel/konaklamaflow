"""Scripted UI stories grounded in the authoritative fictional suite report.

This is presentation data, not an AI/provider runner. No clock is read and no
source, task, room, payment, guest message or official registration is changed.
The embedded AI envelope is the real read-only protocol shape; its fixed demo
issuance time is explicitly fictional and must never be used as authorization.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from .experience_engine import evaluate, validate
from .suite_agent_protocol import make_suite_handoff

_STORIES = (
    ('twin-review', 'KF1002', 'İki ayrı yatak ve oda uygunluğu',
     'Oda talebini, envanter blokajlarını ve personel kontrolünü aynı akışta izle.'),
    ('housekeeping-review', 'KF1003', 'Oda hazırlığı ve housekeeping',
     'Oda görünüşte uygun olsa da temizlik onayı ve açık işlerin neden önemli olduğunu gör.'),
    ('channel-review', 'KF1008', 'OTA kaydı ve PMS eşleştirmesi',
     'Bir kanal kaydının dolu bir formdan ibaret olmadığını, kaynak kanıtıyla incele.'),
    ('arrival-review', 'KF1010', 'Hazır gelişin personel ön kontrolü',
     'Kontroller geçtiğinde sonucun neden hâlâ yetkili personelin incelemesine sunulduğunu gör.'),
)
_CHANNEL_LABELS = {'booking': 'Booking.com', 'expedia': 'Expedia', 'trip': 'Trip.com',
                   'ctrip': 'Ctrip', 'direct': 'Direkt', 'agency': 'Acente',
                   'hotelbeds': 'Hotelbeds', 'channel_manager': 'Channel manager'}


def report_fingerprint(report: Any) -> str:
    """Canonical report checksum used only to bind presentation to evaluation."""
    return sha256(json.dumps(report, sort_keys=True, ensure_ascii=True,
                             separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _evidence(label, value):
    return {'label': label, 'value': str(value)}


def build_demo_stories(snapshot: Any) -> dict[str, Any]:
    """Build reproducible stories from validated source and current rule results.

    Story IDs select the supplied fictional fixture's four example records.
    If a record is absent, its story is omitted rather than inventing a guest or
    decision. Adapted snapshots are re-evaluated; no stale success text is reused.
    """
    source = validate(snapshot)
    report = evaluate(source)
    # This is a demonstrative protocol envelope, never a production clock/token.
    issued = source['as_of'] + 'T11:00:00Z'
    manifest = make_suite_handoff(source, issued)
    if manifest['report_sha256'] != report_fingerprint(report):
        raise ValueError('Story report does not match the read-only protocol')
    bookings = {b['id']: b for b in source['reservations']}
    rows = {r['id']: r for r in report['arrivals']}
    tasks = {r['id']: task for r, task in zip(report['arrivals'], manifest['tasks'], strict=True)}
    room_plan = {r['id']: r for r in report['room_plan']}
    stories = []
    for story_id, booking_id, title, summary in _STORIES:
        if booking_id not in bookings:
            continue
        booking, row = bookings[booking_id], rows[booking_id]
        # This is a visual grouping, not a second room-eligibility calculation.
        related = ([booking['room_id']] if booking['room_id'] else
                   [r['id'] for r in source['rooms'] if r['category'] == booking['category']])
        related = sorted(related)
        events = [e for e in report['event_reviews'] if e['reservation_id'] == booking_id]
        source_result = ('İnceleme gerekiyor' if not row['checklist']['pms_match'] else
                         'Rapor içinde eşleştirme kontrolü geçti')
        room_evidence = []
        for rid in related:
            room_state = ', '.join(room_plan[rid]['reason_codes']) or 'Canlı yeniden doğrulama gerekir'
            holds = room_plan[rid]['reservation_ids_all_holds']
            if holds:
                room_state += ' · Blokaj kayıtları: ' + ', '.join(
                    bid + ' (' + bookings[bid]['arrival'] + ' → ' + bookings[bid]['departure'] + ')'
                    for bid in holds)
            room_evidence.append(_evidence('Oda ' + rid, room_state))
        if story_id == 'twin-review' and 'twin' not in ({booking['bed_request']} | set(booking['requests'])):
            title = 'Yatak ve oda uygunluğu'
        base = {'reason_codes': [], 'room_ids': related}
        steps = [
            {**base, 'id': 'source', 'actor': 'ai1', 'title': 'Kaynak kaydı görünür hale getir',
             'body': 'AI-1 rolünün bu kurgusal turdaki görevi, kanal ve PMS sinyallerini personele açıklamaktır. Gerçek sağlayıcıya istek gönderilmez.',
             'view': 'ota', 'evidence': [
                 _evidence('Kanal', _CHANNEL_LABELS[booking['channel']]),
                 _evidence('Kurgusal kayıt', booking_id),
                 _evidence('PMS sinyali', booking['pms_ref'] or 'Yok'),
                 _evidence('Eşleştirme sonucu', source_result),
                 _evidence('İlgili olaylar', ', '.join(e['id'] for e in events) or 'Bu kayda bağlı olay yok')]},
            {**base, 'id': 'constraints', 'actor': 'ai1', 'title': 'Oda ve misafir talebini incele',
             'body': 'Kategori, kişi sayısı, yatak tercihi ve özel talep bayrakları görünürdür. Bir odayı vurgulamak müsaitlik veya oda teslim garantisi değildir.',
             'view': 'rooms', 'evidence': [
                 _evidence('Kategori', booking['category']),
                 _evidence('Kişi sayısı', booking['persons']),
                 _evidence('Yatak talebi', booking['bed_request']),
                 _evidence('Talep bayrakları', ', '.join(booking['requests']) or 'Yok'),
                 _evidence('Atanan oda', booking['room_id'] or 'Atanmadı')]},
            {**base, 'id': 'validation', 'actor': 'rule_engine', 'title': 'Deterministik motorla doğrula',
             'body': ('Python raporunda bulunan engeller korunur. İkinci bir tarayıcı kural motoru veya AI yorumu bu sonucu onaya çeviremez.'
                      if row['status'] == 'blocked' else
                      'Python raporu bu snapshot için ön inceleme sonucu üretir. Bu sonuç gerçek check-in veya işlem yetkisi değildir.'),
             'view': 'housekeeping' if story_id == 'housekeeping-review' else 'rooms',
             'reason_codes': list(row['blockers']), 'evidence': [
                 _evidence('Motor sonucu', row['status']),
                 _evidence('Engel sayısı', len(row['blockers'])),
                 _evidence('Güvenli oda önerisi', row['suggested_room'] or 'Yok'),
                 _evidence('Ortak motor notları', ', '.join(row['core_reasons']) or 'Ek motor notu yok'),
                 _evidence('Kontrol listesi sinyalleri',
                           str(sum(v is True for v in row['checklist'].values()))
                           + ' / ' + str(len(row['checklist']))),
                 *room_evidence]},
            {**base, 'id': 'crosscheck', 'actor': 'ai2', 'title': 'İkinci asistanın sınırını göster',
             'body': 'AI-2 rolü yalnızca aynı motor sonucunu açıklamak ve kontrol listesi hazırlamak üzere tasarlanır. Bu oynatım yazılmış bir senaryodur; gerçek model çağrısı yapılmaz.',
             'view': 'ai', 'reason_codes': list(row['blockers']), 'evidence': [
                 _evidence('İzinli amaç', tasks[booking_id]['intent']),
                 _evidence('Opak görev', tasks[booking_id]['task_id']),
                 _evidence('Snapshot', manifest['snapshot_sha256'][:16]),
                 _evidence('İşlem yürütme', 'Kapalı')]},
            {**base, 'id': 'handoff', 'actor': 'human',
             'title': ('Hazır: yetkili personel ön incelemesi' if row['status'] == 'review_ready' else
                       'Personel incelemesi gerekli'),
             'body': 'Sonuç ve gerekçeler yetkili personele sunulur. Bu tur rezervasyon değiştirmez, görev oluşturmaz, mesaj göndermez, check-in yapmaz, ödeme almaz veya KBS bildirimi göndermez.',
             'view': 'arrivals', 'reason_codes': list(row['blockers']), 'evidence': [
                 _evidence('Son durum', row['status']),
                 _evidence('İnsan kontrolü', 'Zorunlu'),
                 _evidence('Gerçek işlem', 'Yapılmadı')]},
        ]
        stories.append({'id': story_id, 'title': title, 'summary': summary,
                        'booking_id': booking_id, 'room_ids': related,
                        'final_status': row['status'], 'reason_codes': list(row['blockers']),
                        'steps': steps,
                        # Safe model envelope has no raw property/room/channel/booking refs.
                        'ai_payload': {k: manifest[k] for k in ('protocol', 'mode', 'snapshot_sha256',
                                                                'report_sha256', 'issued_at', 'expires_at')}
                                      | {'tasks': [tasks[booking_id]]}})
    return {'schema_version': '1.0', 'mode': 'SCRIPTED_FICTIONAL_REVIEW',
            'label': 'Kurgusal AI rol simülasyonu · gerçek model veya PMS çağrısı yok',
            'timing': 'VISUAL_PLAYBACK_ONLY',
            'snapshot_sha256': report['snapshot_sha256'],
            'report_sha256': report_fingerprint(report),
            'as_of': report['as_of'], 'at_time': report['at_time'],
            'side_effects': {'pms_writes': False, 'checkin': False, 'payments': False,
                             'kbs': False, 'guest_messages': False, 'identity_documents': False,
                             'ai_provider_calls': False},
            'stories': stories}
