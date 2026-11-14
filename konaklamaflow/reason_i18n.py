"""Ten-language, *presentation-only* catalog for the v0.3 rule codes.

No automatic translation, provider API, network access, PMS action or
authorization. Every reason code remains a stable language-independent value.
Translations are editorial drafts pending native-speaker and a11y review.
"""
from __future__ import annotations

import re

from .experience_engine import BLOCKER_CODES, SnapshotError, evaluate

# A stable catalog order: adding a new blocker requires updating *every* locale.
CODES = (
    "CANCELLED_ASSIGNED", "NOT_CONFIRMED", "UNMAPPED_PMS",
    "DUPLICATE_CHANNEL_REF", "DUPLICATE_PMS_REF", "NO_ASSIGNED_ROOM",
    "ROOM_INCOMPATIBLE", "HOUSEKEEPING_NOT_INSPECTED", "ROOM_CONFLICT",
    "IDENTITY_STAFF_REVIEW", "PAYMENT_REVIEW", "ARRIVAL_NOT_TODAY",
    "GUEST_NOT_ARRIVED", "BEFORE_CHECKIN_TIME", "DEPARTURE_NOT_VERIFIED",
    "ALREADY_IN_HOUSE", "SPECIAL_REQUEST_REVIEW",
    "REQUEST_AMENITY_UNAVAILABLE", "CONFLICTING_BED_REQUEST",
    "MAINTENANCE_TASK_OPEN", "HOUSEKEEPING_TASK_OPEN",
    "CHANNEL_EVENT_REVIEW", "CHANNEL_REFERENCE_MISMATCH",
    "CHANNEL_STATUS_CONFLICT", "CORE_REVIEW_REQUIRED", "HISTORICAL_STAY",
    "NO_SHOW_RELEASE_REVIEW", "PMS_REGISTRATION_NOT_CONFIRMED",
)
if set(CODES) != BLOCKER_CODES or len(CODES) != len(set(CODES)):
    raise RuntimeError("Translation catalog must track all engine blocker codes")

# Exactly six fixed safety/UI labels for every supported language:
# blocked, review_ready, other, source_notice, staff_action, no_live_write.
_UI = {
"en": ("Staff review needed", "Ready for staff pre-review", "Other / not ready",
       "Unverified fictional or minimized snapshot",
       "Verify the live source and obtain authorized staff approval",
       "No check-in, payment, KBS or PMS update was performed"),
"tr": ("Personel incelemesi gerekli", "Personel ön incelemesine hazır", "Diğer / hazır değil",
       "Doğrulanmamış kurgusal veya azaltılmış veri anlık görüntüsü",
       "Canlı kaynağı doğrula ve yetkili personel onayı al",
       "Check-in, ödeme, KBS veya PMS güncellemesi yapılmadı"),
"fr": ("Vérification du personnel requise", "Prêt pour l'examen préalable du personnel", "Autre / non prêt",
       "Instantané fictif ou minimisé non vérifié",
       "Vérifier la source réelle et obtenir l'accord du personnel habilité",
       "Aucun enregistrement, paiement, signalement officiel ni changement PMS effectué"),
"el": ("Απαιτείται έλεγχος προσωπικού", "Έτοιμο για προκαταρκτικό έλεγχο", "Άλλο / μη έτοιμο",
       "Μη επαληθευμένα εικονικά ή ελαχιστοποιημένα δεδομένα",
       "Ελέγξτε την πραγματική πηγή και ζητήστε έγκριση από εξουσιοδοτημένο υπάλληλο",
       "Δεν πραγματοποιήθηκε check-in, πληρωμή, δήλωση KBS ή ενημέρωση PMS"),
"he": ("נדרשת בדיקת צוות", "מוכן לבדיקה ראשונית של הצוות", "אחר / לא מוכן",
       "נתוני הדגמה או נתונים מצומצמים שלא אומתו",
       "יש לבדוק את המערכת האמיתית ולקבל אישור מעובד מורשה",
       "לא בוצעו צ'ק-אין, תשלום, דיווח KBS או שינוי במערכת PMS"),
"ar": ("يلزم تدقيق الموظفين", "جاهز للمراجعة الأولية من الموظفين", "حالة أخرى / غير جاهز",
       "بيانات تجريبية أو محدودة لم يتم التحقق منها",
       "تحقق من المصدر الفعلي واحصل على موافقة الموظف المخوّل",
       "لم يُنفّذ تسجيل وصول أو دفع أو بلاغ KBS أو تعديل PMS"),
"de": ("Prüfung durch Personal erforderlich", "Bereit für die Personal-Vorprüfung", "Sonstiges / nicht bereit",
       "Nicht geprüfter fiktiver oder minimierter Datenstand",
       "Live-Quelle prüfen und Freigabe durch befugtes Personal einholen",
       "Kein Check-in, keine Zahlung, keine KBS-Meldung und keine PMS-Änderung"),
"ru": ("Требуется проверка сотрудника", "Готово к предварительной проверке", "Другое / не готово",
       "Непроверенные тестовые или минимизированные данные",
       "Сверьте с реальным источником и получите согласование уполномоченного сотрудника",
       "Заселение, оплата, уведомление KBS и изменение PMS не выполнялись"),
"es": ("Se requiere revisión del personal", "Listo para revisión preliminar", "Otro / no listo",
       "Datos ficticios o minimizados sin verificar",
       "Verifica la fuente real y obtén la aprobación de personal autorizado",
       "No se realizó registro, pago, notificación KBS ni modificación del PMS"),
"uk": ("Потрібна перевірка персоналу", "Готово до попередньої перевірки", "Інше / не готово",
       "Неперевірені тестові або мінімізовані дані",
       "Перевір реальне джерело й отримай схвалення уповноваженого працівника",
       "Поселення, оплату, повідомлення KBS і зміну PMS не виконано"),
}

# Each locale contains exactly one human-readable *draft* for each entry in CODES.
_REASONS = {
"en": (
"Cancelled booking still has a room assigned",
"Reservation is not confirmed",
"PMS mapping has not been verified",
"Duplicate channel reference",
"Duplicate PMS reference",
"No room has been assigned",
"Room does not meet reservation requirements",
"Housekeeping inspection has not been confirmed",
"Overlapping room assignments or holds",
"Identity requires authorized staff review",
"Payment signal requires staff review",
"Arrival is not scheduled for today",
"Reception has not confirmed guest arrival",
"Standard check-in time has not been reached",
"Previous departure and room release are unverified",
"Booking is already marked as in-house",
"Special request needs staff review",
"Requested room feature is not available",
"Bed preferences conflict",
"Maintenance task remains open",
"Housekeeping task remains open",
"Channel event needs reconciliation",
"Channel reservation reference does not match",
"Channel and reservation statuses conflict",
"Additional review required by core rules",
"Historical stay requires staff review",
"No-show room stays held until staff releases it",
"PMS registration is not confirmed; this is not a KBS notification",
),
"tr": (
"İptal edilen rezervasyona hâlâ oda atanmış",
"Rezervasyon onaylanmamış",
"PMS eşleştirmesi doğrulanmamış",
"Yinelenen kanal rezervasyon referansı",
"Yinelenen PMS referansı",
"Oda ataması yapılmamış",
"Oda, rezervasyon gereksinimlerini karşılamıyor",
"Kat hizmetleri kontrolü doğrulanmamış",
"Çakışan oda atamaları veya blokajlar",
"Kimlik için yetkili personel kontrolü gerekli",
"Ödeme sinyali personel incelemesi gerektiriyor",
"Giriş tarihi bugün değil",
"Resepsiyon misafirin gelişini doğrulamamış",
"Standart giriş saati henüz gelmemiş",
"Önceki çıkış ve odanın boşaltılması doğrulanmamış",
"Rezervasyon zaten otelde konaklıyor olarak işaretli",
"Özel talep personel incelemesi gerektiriyor",
"Talep edilen oda özelliği mevcut değil",
"Yatak tercihleri birbiriyle çelişiyor",
"Bakım görevi hâlâ açık",
"Kat hizmetleri görevi hâlâ açık",
"Kanal olayı uzlaştırma gerektiriyor",
"Kanal rezervasyon referansı eşleşmiyor",
"Kanal ve rezervasyon durumları çelişiyor",
"Temel kurallar ek inceleme gerektiriyor",
"Geçmiş tarihli konaklama inceleme gerektiriyor",
"No-show odası personel bırakmadan yeniden önerilmez",
"PMS kaydı onaylı değil; bu bir KBS bildirimi değildir",
),
"fr": (
"Une chambre reste attribuée à une réservation annulée",
"La réservation n'est pas confirmée",
"La correspondance PMS n'est pas vérifiée",
"Référence de canal en double",
"Référence PMS en double",
"Aucune chambre attribuée",
"La chambre ne respecte pas les exigences de la réservation",
"Inspection du ménage non confirmée",
"Attributions ou blocages de chambres qui se chevauchent",
"Vérification d'identité par un agent habilité nécessaire",
"Signal de paiement à examiner par le personnel",
"L'arrivée n'est pas prévue aujourd'hui",
"La réception n'a pas confirmé l'arrivée du client",
"L'heure normale d'arrivée n'est pas atteinte",
"Départ précédent et libération de la chambre non vérifiés",
"La réservation est déjà indiquée comme présente",
"Demande spéciale à examiner par le personnel",
"Équipement demandé indisponible",
"Préférences de literie contradictoires",
"Intervention de maintenance encore ouverte",
"Tâche de ménage encore ouverte",
"Événement de canal à rapprocher",
"Référence de réservation du canal incohérente",
"Statuts du canal et de la réservation contradictoires",
"Examen supplémentaire exigé par les règles centrales",
"Séjour historique à faire vérifier par le personnel",
"La chambre no-show reste retenue jusqu'à validation du personnel",
"L'enregistrement PMS n'est pas confirmé ; ce n'est pas une notification KBS",
),
"el": (
"Η ακυρωμένη κράτηση εξακολουθεί να έχει δωμάτιο",
"Η κράτηση δεν έχει επιβεβαιωθεί",
"Η αντιστοίχιση με το PMS δεν έχει επαληθευτεί",
"Διπλότυπος κωδικός καναλιού",
"Διπλότυπος κωδικός PMS",
"Δεν έχει ανατεθεί δωμάτιο",
"Το δωμάτιο δεν καλύπτει τις απαιτήσεις της κράτησης",
"Δεν έχει επιβεβαιωθεί ο έλεγχος καθαριότητας",
"Επικαλυπτόμενες αναθέσεις ή δεσμεύσεις δωματίων",
"Απαιτείται έλεγχος ταυτότητας από εξουσιοδοτημένο προσωπικό",
"Η ένδειξη πληρωμής χρειάζεται έλεγχο προσωπικού",
"Η άφιξη δεν έχει προγραμματιστεί για σήμερα",
"Η υποδοχή δεν έχει επιβεβαιώσει την άφιξη",
"Δεν έχει φτάσει η κανονική ώρα check-in",
"Δεν έχει επιβεβαιωθεί η αναχώρηση και η αποδέσμευση δωματίου",
"Η κράτηση έχει ήδη επισημανθεί ως διαμένουσα",
"Ειδικό αίτημα χρειάζεται έλεγχο προσωπικού",
"Το ζητούμενο χαρακτηριστικό δωματίου δεν διατίθεται",
"Αντικρουόμενες προτιμήσεις κρεβατιών",
"Η εργασία συντήρησης παραμένει ανοικτή",
"Η εργασία καθαριότητας παραμένει ανοικτή",
"Το συμβάν καναλιού χρειάζεται συμφωνία",
"Ο κωδικός κράτησης καναλιού δεν αντιστοιχεί",
"Οι καταστάσεις καναλιού και κράτησης διαφέρουν",
"Οι βασικοί κανόνες απαιτούν επιπλέον έλεγχο",
"Η παλαιότερη διαμονή χρειάζεται έλεγχο προσωπικού",
"Το δωμάτιο no-show παραμένει δεσμευμένο έως την έγκριση προσωπικού",
"Η καταχώριση PMS δεν έχει επιβεβαιωθεί· δεν είναι δήλωση KBS",
),
"he": (
"להזמנה שבוטלה עדיין משויך חדר",
"ההזמנה לא אושרה",
"ההתאמה למערכת PMS לא אומתה",
"מזהה הזמנה כפול בערוץ",
"מזהה PMS כפול",
"לא הוקצה חדר",
"החדר אינו מתאים לדרישות ההזמנה",
"לא אושר שהחדר עבר בדיקת ניקיון",
"הקצאות או חסימות חדרים חופפות",
"נדרשת בדיקת זהות בידי עובד מורשה",
"חיווי התשלום דורש בדיקת צוות",
"ההגעה אינה מתוכננת להיום",
"הקבלה לא אישרה את הגעת האורח",
"שעת הצ'ק-אין הרגילה טרם הגיעה",
"יציאת האורח הקודם ושחרור החדר לא אומתו",
"ההזמנה כבר מסומנת כמתארחת במלון",
"נדרשת בדיקת צוות עבור בקשה מיוחדת",
"המאפיין המבוקש בחדר אינו זמין",
"דרישות המיטות סותרות זו את זו",
"משימת תחזוקה עדיין פתוחה",
"משימת ניקיון עדיין פתוחה",
"נדרשת התאמה של אירוע מהערוץ",
"מזהה ההזמנה בערוץ אינו תואם",
"מצבי הערוץ וההזמנה סותרים",
"הכללים המרכזיים דורשים בדיקה נוספת",
"שהייה מתאריך עבר דורשת בדיקת צוות",
"חדר no-show נשאר תפוס עד שחרור על ידי הצוות",
"רישום PMS לא אושר; זו אינה הודעת KBS",
),
"ar": (
"لا تزال غرفة مخصصة لحجز ملغى",
"لم يتم تأكيد الحجز",
"لم يتم التحقق من مطابقة نظام PMS",
"مرجع حجز مكرر في القناة",
"مرجع PMS مكرر",
"لم يتم تخصيص غرفة",
"الغرفة لا تستوفي متطلبات الحجز",
"لم يتم تأكيد فحص النظافة",
"تخصيصات أو حجوزات غرف متداخلة",
"يلزم التحقق من الهوية بواسطة موظف مخوّل",
"تتطلب حالة الدفع مراجعة الموظفين",
"موعد الوصول ليس اليوم",
"لم يؤكد الاستقبال وصول الضيف",
"لم يحن وقت تسجيل الوصول المعتاد",
"لم يتم التحقق من المغادرة السابقة وإخلاء الغرفة",
"الحجز مسجل بالفعل على أنه إقامة جارية",
"يتطلب الطلب الخاص مراجعة الموظفين",
"الميزة المطلوبة في الغرفة غير متاحة",
"تفضيلات الأسرّة متعارضة",
"مهمة الصيانة لا تزال مفتوحة",
"مهمة النظافة لا تزال مفتوحة",
"يجب مراجعة حدث القناة ومطابقته",
"مرجع الحجز في القناة غير مطابق",
"حالة القناة تتعارض مع حالة الحجز",
"تتطلب القواعد الأساسية مراجعة إضافية",
"الإقامة السابقة تتطلب مراجعة الموظفين",
"غرفة عدم الحضور تبقى محجوزة حتى يحررها الموظف",
"تسجيل PMS غير مؤكد؛ هذا ليس بلاغ KBS",
),
"de": (
"Stornierter Buchung ist noch ein Zimmer zugewiesen",
"Buchung ist nicht bestätigt",
"PMS-Zuordnung wurde nicht geprüft",
"Doppelte Kanalreferenz",
"Doppelte PMS-Referenz",
"Kein Zimmer zugewiesen",
"Zimmer erfüllt die Buchungsanforderungen nicht",
"Housekeeping-Prüfung wurde nicht bestätigt",
"Überlappende Zimmerbelegungen oder Sperren",
"Identitätsprüfung durch befugtes Personal erforderlich",
"Zahlungssignal muss durch Personal geprüft werden",
"Anreise ist nicht für heute geplant",
"Rezeption hat die Ankunft nicht bestätigt",
"Reguläre Check-in-Zeit ist noch nicht erreicht",
"Vorherige Abreise und Zimmerfreigabe nicht geprüft",
"Buchung ist bereits als eingecheckt markiert",
"Sonderwunsch muss durch Personal geprüft werden",
"Gewünschte Zimmerausstattung nicht verfügbar",
"Widersprüchliche Bettenwünsche",
"Wartungsaufgabe ist noch offen",
"Housekeeping-Aufgabe ist noch offen",
"Kanalereignis muss abgeglichen werden",
"Kanal-Buchungsreferenz stimmt nicht überein",
"Kanal- und Buchungsstatus widersprechen sich",
"Kernregeln erfordern zusätzliche Prüfung",
"Früherer Aufenthalt muss geprüft werden",
"No-show-Zimmer bleibt gesperrt, bis das Personal es freigibt",
"PMS-Registrierung ist nicht bestätigt; das ist keine KBS-Meldung",
),
"ru": (
"За отменённым бронированием всё ещё закреплён номер",
"Бронирование не подтверждено",
"Соответствие PMS не проверено",
"Повторяющийся номер бронирования канала",
"Повторяющийся идентификатор PMS",
"Номер не назначен",
"Номер не соответствует условиям бронирования",
"Проверка уборки не подтверждена",
"Пересекающиеся назначения или блокировки номеров",
"Требуется проверка личности уполномоченным сотрудником",
"Статус оплаты требует проверки сотрудником",
"Заезд запланирован не на сегодня",
"Стойка регистрации не подтвердила прибытие гостя",
"Стандартное время заселения ещё не наступило",
"Предыдущий выезд и освобождение номера не подтверждены",
"Бронирование уже отмечено как проживающее",
"Особый запрос требует проверки сотрудником",
"Запрошенное оснащение номера недоступно",
"Противоречивые пожелания к кроватям",
"Задача техобслуживания ещё открыта",
"Задача уборки ещё открыта",
"Событие канала требует сверки",
"Код бронирования канала не совпадает",
"Статусы канала и бронирования противоречат друг другу",
"Основные правила требуют дополнительной проверки",
"Предыдущий период проживания требует проверки",
"Номер no-show остаётся занятым, пока сотрудник его не освободит",
"Запись PMS не подтверждена; это не уведомление KBS",
),
"es": (
"Una reserva cancelada aún tiene una habitación asignada",
"La reserva no está confirmada",
"No se ha verificado la vinculación con el PMS",
"Referencia de canal duplicada",
"Referencia PMS duplicada",
"No hay habitación asignada",
"La habitación no cumple los requisitos de la reserva",
"No se ha confirmado la inspección de limpieza",
"Asignaciones o bloqueos de habitación superpuestos",
"Se requiere revisión de identidad por personal autorizado",
"El estado del pago requiere revisión del personal",
"La llegada no está prevista para hoy",
"Recepción no ha confirmado la llegada del huésped",
"Aún no se ha alcanzado la hora normal de entrada",
"No se han verificado la salida anterior ni la liberación del cuarto",
"La reserva ya figura como huésped alojado",
"La solicitud especial requiere revisión del personal",
"El equipamiento solicitado no está disponible",
"Preferencias de camas contradictorias",
"La tarea de mantenimiento sigue abierta",
"La tarea de limpieza sigue abierta",
"El evento del canal requiere conciliación",
"La referencia de reserva del canal no coincide",
"Los estados del canal y la reserva son contradictorios",
"Las reglas centrales requieren revisión adicional",
"La estancia anterior requiere revisión del personal",
"La habitación no-show sigue retenida hasta que el personal la libere",
"El registro PMS no está confirmado; no es una notificación KBS",
),
"uk": (
"За скасованим бронюванням досі закріплений номер",
"Бронювання не підтверджено",
"Відповідність PMS не перевірено",
"Повторний код бронювання каналу",
"Повторний ідентифікатор PMS",
"Номер не призначено",
"Номер не відповідає вимогам бронювання",
"Перевірку прибирання не підтверджено",
"Перетин призначень або блокувань номерів",
"Потрібна перевірка особи уповноваженим працівником",
"Стан оплати потребує перевірки працівником",
"Заїзд запланований не на сьогодні",
"Рецепція не підтвердила прибуття гостя",
"Стандартний час поселення ще не настав",
"Попередній виїзд і звільнення номера не підтверджено",
"Бронювання вже позначено як поточне проживання",
"Особливий запит потребує перевірки працівником",
"Запитана зручність номера недоступна",
"Суперечливі побажання щодо ліжок",
"Завдання техобслуговування досі відкрите",
"Завдання прибирання досі відкрите",
"Подію каналу потрібно звірити",
"Код бронювання каналу не збігається",
"Стани каналу та бронювання суперечать один одному",
"Основні правила потребують додаткової перевірки",
"Попереднє проживання потребує перевірки",
"Номер no-show лишається зайнятим, доки працівник його не звільнить",
"Запис PMS не підтверджено; це не повідомлення KBS",
),
}
SUPPORTED = tuple(_REASONS)
RTL = frozenset({"he", "ar"})
_NAMES = ("blocked", "review_ready", "other", "source_notice", "staff_action", "no_live_write")
_LOCALE_RE = re.compile(r"^[a-zA-Z]{2,3}(?:[-_][A-Za-z0-9]{2,8}){0,3}$")

if (set(_REASONS) != set(_UI) or
        any(len(labels) != len(CODES) or not all(isinstance(s, str) and s.strip() for s in labels)
            for labels in _REASONS.values()) or
        any(len(items) != len(_NAMES) or not all(isinstance(s, str) and s.strip() for s in items)
            for items in _UI.values())):
    raise RuntimeError("An incomplete or empty locale catalog was detected")


class LocalizationError(ValueError):
    """Invalid or mismatched source; user data is never echoed."""


def resolve_locale(requested: str) -> dict:
    """BCP-47-like language resolution, with explicit English fallback status."""
    if not isinstance(requested, str) or len(requested) > 36 or _LOCALE_RE.fullmatch(requested) is None:
        raise LocalizationError("Invalid locale identifier")
    base = requested.replace("_", "-").split("-")[0].lower()
    resolved = base if base in _REASONS else "en"
    return {
        "locale": resolved,
        "direction": "rtl" if resolved in RTL else "ltr",
        "translation_status": "CATALOG_DRAFT_UNREVIEWED" if resolved == base
                              else "FALLBACK_EN_UNSUPPORTED_LOCALE",
    }


def localize_code(code: str, requested_locale: str) -> dict:
    """Translate one known reason code without changing the rule code."""
    if not isinstance(code, str) or code not in BLOCKER_CODES:
        raise LocalizationError("Unsupported rule reason")
    meta = resolve_locale(requested_locale)
    return {**meta, "reason_code": code, "text": _REASONS[meta["locale"]][CODES.index(code)]}


def localized_pre_review(snapshot: dict, report: dict, requested_locale: str) -> dict:
    """Safely present a rule report in ten languages; no personal identifiers.

    The source is re-evaluated to avoid trusting forged/unrelated readiness.
    A match proves in-process consistency, not live PMS freshness or identity.
    """
    meta = resolve_locale(requested_locale)
    try:
        fresh = evaluate(snapshot)
    except (SnapshotError, TypeError, ValueError, RecursionError, OverflowError):
        raise LocalizationError("Invalid minimized review source") from None
    if not isinstance(report, dict) or fresh != report or fresh.get("mode") != "DRY_RUN_ONLY":
        raise LocalizationError("Unverified or stale rule report")
    labels = dict(zip(_NAMES, _UI[meta["locale"]]))
    results = []
    for row in fresh["arrivals"]:
        reasons = row["blockers"]
        if (set(reasons) - BLOCKER_CODES or row["status"] not in
                {"blocked", "review_ready", "other"} or row.get("human_approval_required") is not True):
            raise LocalizationError("Unsafe rule status")
        results.append({
            "task_id": row["task_id"],
            "status_code": row["status"],
            "status_text": labels[row["status"]],
            "reason_codes": list(reasons),
            "reason_texts": [_REASONS[meta["locale"]][CODES.index(code)] for code in reasons],
            "staff_action": labels["staff_action"],
        })
    return {
        **meta,
        "schema": "konaklamaflow.localized-pre-review.v1",
        "mode": "NO_EXECUTION_READ_ONLY",
        "source_validity": "UNVERIFIED_MINIMIZED_SNAPSHOT",
        "report_snapshot_sha256": fresh["snapshot_sha256"],
        "source_notice": labels["source_notice"],
        "no_live_write": labels["no_live_write"],
        "results": results,
    }
