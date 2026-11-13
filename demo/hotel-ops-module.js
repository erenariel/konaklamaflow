/* KonaklamaFlow hotel-operations v0.5: real project UI modules, synthetic only.
 * Numerical reports are Python-generated. The browser may filter/show but does
 * NOT recompute accounting, approve check-in, post payments or store identity.
 * Loaded inline into the existing single-file workbench by generator.
 */
'use strict';
const opsState={
  lang:'tr',selectedReport:'active_folios',selectedFolio:'FOL-001',
  selectedReservation:'KFD-2026-0002',selectedGuest:'GUEST_DEMO_001',
  reportFrom:'',reportTo:'',reportAgency:'',formOpen:false,roomCount:1,drafts:[],
  formMessage:'',country:'TR',guestTab:'identity'
};
const opsDict={
tr:{newBooking:'Yeni rezervasyon',reservation:'Rezervasyon',guest:'Misafirler',folios:'Aktif folyolar',agencies:'Acente alacakları',reports:'Raporlar',fx:'Kur ve fatura',block:'Blokajlar',assets:'Oda demirbaşları',room:'Oda',agency:'Acente',details:'Detaylar',status:'Durum',total:'Toplam',payments:'Ödemeler',balance:'Bakiye',date:'Tarih',open:'Aç',safe:'Kurgusal kayıtlar · canlı işlem yok',needs:'Gerçek veri kaynağı veya yetkili muhasebe altyapısı eksik; sahte rapor üretmiyoruz.',personal:'KVKK / GDPR: Gerçek kimlik, pasaport, TC, iletişim ve adres verisi bu demoda toplanmaz.',draft:'Bu rezervasyon yalnızca geçici taslaktır. PMS, OTA, folyo ve KBS işlemi gerçekleşmedi.',source:'Demo kurudur; gerçek güncel döviz kuru, e-fatura veya muhasebe fişi değildir.',filter:'Filtrele',clear:'Temizle',dateFrom:'Başlangıç',dateTo:'Bitiş',noData:'Filtreye uygun kurgusal kayıt yok',night:'Gecelik fiyat',addRoom:'Oda ekle',preview:'Taslak kontrolü',notes:'Notlar / özel talepler',bank:'Banka havalesi'},
en:{newBooking:'New reservation',reservation:'Reservations',guest:'Guests',folios:'Open folios',agencies:'Agency receivables',reports:'Reports',fx:'FX and invoicing',block:'Room blocks',assets:'Room inventory',room:'Room',agency:'Agency',details:'Details',status:'Status',total:'Total',payments:'Payments',balance:'Balance',date:'Date',open:'Open',safe:'Fictional records · no live operations',needs:'Authorized accounting or source records are missing; this report will not invent data.',personal:'KVKK / GDPR: This demo never collects real IDs, passports, contact details or addresses.',draft:'Temporary draft only. No PMS, OTA, folio or KBS action occurred.',source:'Fictional rates; not live FX, official invoice or accounting ledger.',filter:'Filter',clear:'Clear',dateFrom:'From',dateTo:'To',noData:'No fictional records match',night:'Nightly rate',addRoom:'Add room',preview:'Review draft',notes:'Notes / special requests',bank:'Bank transfer'},
fr:{newBooking:'Nouvelle réservation',reservation:'Réservations',guest:'Clients',folios:'Folios ouverts',agencies:'Créances des agences',reports:'Rapports',fx:'Devises et factures',block:'Blocages',assets:'Inventaire des chambres',room:'Chambre',agency:'Agence',details:'Détails',status:'Statut',total:'Total',payments:'Paiements',balance:'Solde',date:'Date',open:'Ouvrir',safe:'Données fictives · aucune opération réelle',needs:'Données comptables autorisées manquantes ; aucun résultat inventé.',personal:'KVKK / RGPD : aucune donnée d’identité réelle n’est collectée.',draft:'Brouillon temporaire ; aucune opération PMS ou KBS.',source:'Taux fictifs, sans valeur fiscale.',filter:'Filtrer',clear:'Effacer',dateFrom:'Du',dateTo:'Au',noData:'Aucun résultat',night:'Tarif par nuit',addRoom:'Ajouter chambre',preview:'Examiner brouillon',notes:'Notes',bank:'Virement'},
el:{newBooking:'Νέα κράτηση',reservation:'Κρατήσεις',guest:'Επισκέπτες',folios:'Ανοιχτοί λογαριασμοί',agencies:'Οφειλές πρακτορείων',reports:'Αναφορές',fx:'Συνάλλαγμα / τιμολόγια',block:'Δεσμεύσεις',assets:'Εξοπλισμός δωματίων',room:'Δωμάτιο',agency:'Πρακτορείο',details:'Λεπτομέρειες',status:'Κατάσταση',total:'Σύνολο',payments:'Πληρωμές',balance:'Υπόλοιπο',date:'Ημερομηνία',open:'Άνοιγμα',safe:'Εικονικά στοιχεία · χωρίς πραγματικές ενέργειες',needs:'Λείπουν τα εξουσιοδοτημένα δεδομένα.',personal:'KVKK / GDPR: Δεν συλλέγονται πραγματικά στοιχεία ταυτότητας.',draft:'Μόνο προσωρινό προσχέδιο· καμία ενέργεια PMS/KBS.',source:'Εικονικές ισοτιμίες χωρίς φορολογική ισχύ.',filter:'Φίλτρο',clear:'Καθαρισμός',dateFrom:'Από',dateTo:'Έως',noData:'Δεν βρέθηκαν εγγραφές',night:'Τιμή ανά νύχτα',addRoom:'Προσθήκη δωματίου',preview:'Έλεγχος σχεδίου',notes:'Σημειώσεις',bank:'Τραπεζικό έμβασμα'},
he:{newBooking:'הזמנה חדשה',reservation:'הזמנות',guest:'אורחים',folios:'חשבונות פתוחים',agencies:'חובות סוכנויות',reports:'דוחות',fx:'מטבע וחשבוניות',block:'חסימות חדרים',assets:'ציוד חדר',room:'חדר',agency:'סוכנות',details:'פרטים',status:'סטטוס',total:'סך הכול',payments:'תשלומים',balance:'יתרה',date:'תאריך',open:'פתח',safe:'נתונים מדומים · ללא פעולה אמיתית',needs:'נתוני הנהלת חשבונות מאושרים אינם זמינים.',personal:'KVKK / GDPR: אין להזין פרטי זהות אמיתיים.',draft:'טיוטה זמנית בלבד; לא בוצעה פעולה ב-PMS.',source:'שערים מדומים, לא חשבונית רשמית.',filter:'סינון',clear:'ניקוי',dateFrom:'מ-',dateTo:'עד',noData:'אין תוצאות',night:'מחיר ללילה',addRoom:'הוסף חדר',preview:'בדוק טיוטה',notes:'הערות',bank:'העברה בנקאית'},
ar:{newBooking:'حجز جديد',reservation:'الحجوزات',guest:'الضيوف',folios:'الحسابات المفتوحة',agencies:'ذمم الوكالات',reports:'التقارير',fx:'العملات والفواتير',block:'حظر الغرف',assets:'تجهيزات الغرف',room:'الغرفة',agency:'الوكالة',details:'التفاصيل',status:'الحالة',total:'الإجمالي',payments:'المدفوعات',balance:'الرصيد',date:'التاريخ',open:'فتح',safe:'بيانات افتراضية · دون تنفيذ فعلي',needs:'البيانات المحاسبية المصرح بها غير متاحة.',personal:'KVKK / GDPR: لا تجمع بيانات هوية حقيقية.',draft:'مسودة مؤقتة فقط؛ لا عمليات PMS أو KBS.',source:'أسعار صرف تجريبية وليست فواتير رسمية.',filter:'تصفية',clear:'مسح',dateFrom:'من',dateTo:'إلى',noData:'لا توجد سجلات',night:'سعر الليلة',addRoom:'أضف غرفة',preview:'مراجعة المسودة',notes:'ملاحظات',bank:'تحويل بنكي'},
de:{newBooking:'Neue Reservierung',reservation:'Reservierungen',guest:'Gäste',folios:'Offene Folios',agencies:'Agenturforderungen',reports:'Berichte',fx:'Währungen / Rechnungen',block:'Zimmerblockierungen',assets:'Zimmerinventar',room:'Zimmer',agency:'Agentur',details:'Details',status:'Status',total:'Gesamt',payments:'Zahlungen',balance:'Saldo',date:'Datum',open:'Öffnen',safe:'Fiktive Daten · kein Echtbetrieb',needs:'Buchhaltungsquellen fehlen; kein erfundener Bericht.',personal:'KVKK / DSGVO: Keine echten Ausweisdaten eingeben.',draft:'Nur Entwurf. Keine PMS- oder KBS-Aktion.',source:'Fiktive Wechselkurse, keine offiziellen Rechnungen.',filter:'Filtern',clear:'Löschen',dateFrom:'Von',dateTo:'Bis',noData:'Keine Einträge',night:'Nachtpreis',addRoom:'Zimmer hinzufügen',preview:'Entwurf prüfen',notes:'Notizen',bank:'Überweisung'},
ru:{newBooking:'Новое бронирование',reservation:'Бронирования',guest:'Гости',folios:'Открытые фолио',agencies:'Дебиторка агентств',reports:'Отчёты',fx:'Курсы / счета',block:'Блокировки',assets:'Оснащение номеров',room:'Номер',agency:'Агентство',details:'Детали',status:'Статус',total:'Итого',payments:'Оплаты',balance:'Остаток',date:'Дата',open:'Открыть',safe:'Тестовые данные · никаких реальных операций',needs:'Нет авторизованных данных бухгалтерии.',personal:'KVKK / GDPR: Реальные паспортные данные не собираются.',draft:'Только временный черновик. PMS и KBS не обновлены.',source:'Условные курсы, не официальные счета.',filter:'Фильтр',clear:'Сброс',dateFrom:'С',dateTo:'По',noData:'Нет записей',night:'Цена за ночь',addRoom:'Добавить номер',preview:'Проверить черновик',notes:'Примечания',bank:'Банковский перевод'},
es:{newBooking:'Nueva reserva',reservation:'Reservas',guest:'Huéspedes',folios:'Folios abiertos',agencies:'Cuentas por cobrar',reports:'Informes',fx:'Divisas / facturas',block:'Bloqueos',assets:'Inventario de habitaciones',room:'Habitación',agency:'Agencia',details:'Detalles',status:'Estado',total:'Total',payments:'Pagos',balance:'Saldo',date:'Fecha',open:'Abrir',safe:'Datos ficticios · sin operaciones reales',needs:'Faltan fuentes contables autorizadas.',personal:'KVKK / RGPD: No se recopilan documentos reales.',draft:'Solo borrador temporal. Sin operación PMS/KBS.',source:'Tipos de cambio ficticios, sin validez fiscal.',filter:'Filtrar',clear:'Borrar',dateFrom:'Desde',dateTo:'Hasta',noData:'Sin resultados',night:'Tarifa nocturna',addRoom:'Añadir habitación',preview:'Revisar borrador',notes:'Notas',bank:'Transferencia bancaria'},
uk:{newBooking:'Нове бронювання',reservation:'Бронювання',guest:'Гості',folios:'Відкриті фоліо',agencies:'Борги агенцій',reports:'Звіти',fx:'Курси / рахунки',block:'Блокування',assets:'Оснащення номерів',room:'Номер',agency:'Агенція',details:'Деталі',status:'Стан',total:'Всього',payments:'Оплати',balance:'Баланс',date:'Дата',open:'Відкрити',safe:'Тестові дані · без реальних операцій',needs:'Немає уповноважених бухгалтерських даних.',personal:'KVKK / GDPR: Реальні паспортні дані не збираються.',draft:'Тільки тимчасова чернетка. PMS/KBS не змінено.',source:'Умовні курси, не офіційні рахунки.',filter:'Фільтр',clear:'Очистити',dateFrom:'Від',dateTo:'До',noData:'Немає записів',night:'Ціна за ніч',addRoom:'Додати номер',preview:'Перевірити чернетку',notes:'Примітки',bank:'Банківський переказ'}
};
const opsNavigation={
ops_reservations:'reservation',ops_guests:'guest',ops_folios:'folios',
ops_agencies:'agencies',ops_reports:'reports',ops_rates:'fx',
ops_blocks:'block',ops_inventory:'assets'
};
const opsHtml=s=>esc(String(s??''));
const opsT=key=>(opsDict[opsState.lang]||opsDict.en)[key]||opsDict.en[key]||key;
const opsMoney=(value,currency)=>new Intl.NumberFormat(opsState.lang,{minimumFractionDigits:2,maximumFractionDigits:2}).format(Number(value))+' '+currency;
const opsAgency=id=>HOTEL_OPS_DATA.agencies.find(a=>a.id===id);
const opsRes=id=>HOTEL_OPS_DATA.reservations.find(r=>r.id===id);
const opsFolio=id=>HOTEL_OPS_DATA.folios.find(f=>f.id===id);
const opsStatusBadge=(status)=>'<span class="ops-chip">'+opsHtml(status)+'</span>';
const opsTable=(headers,rows)=>'<div class="ops-table-scroll"><table class="ops-table"><thead><tr>'+
 headers.map(h=>'<th>'+opsHtml(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.join('')+
 '</tbody></table></div>';
const opsTr=(cells,action)=>'<tr'+(action?' data-op-open="'+opsHtml(action)+'" tabindex="0" role="button"':'')+'>'+
 cells.map(x=>'<td>'+x+'</td>').join('')+'</tr>';
const opsCard=(title,inner)=>'<section class="ops-card"><h3>'+opsHtml(title)+'</h3>'+inner+'</section>';
const opsNotice=()=>'<p class="ops-notice" role="status">'+opsHtml(opsT('safe'))+'</p>';
const opsCountryCodes='AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW'.split(' ');
const opsCountryOptions=()=>opsCountryCodes.map(code=>'<option value="'+code+'"'+(code===opsState.country?' selected':'')+'>'+code+'</option>').join('');
const opsSelect=(id,options,selected)=>'<select id="'+id+'">'+options.map(([value,label])=>
 '<option value="'+opsHtml(value)+'"'+(value===selected?' selected':'')+'>'+opsHtml(label)+'</option>').join('')+'</select>';
function opsReservations(){
 const items=HOTEL_OPS_DATA.reservations;
 const rows=items.map(r=>opsTr([
 '<code dir="ltr">'+opsHtml(r.id)+'</code>',opsHtml(r.name),
 opsHtml((opsAgency(r.agency_id)||{}).name),opsHtml(r.checkin)+' → '+opsHtml(r.checkout),
 opsHtml(r.rooms.length),opsHtml(r.board),opsStatusBadge(r.status)
 ],'res:'+r.id));
 const view=opsCard(opsT('reservation'),'<div class="ops-toolbar"><button type="button" class="primary" data-op-action="new-reservation">'+opsHtml(opsT('newBooking'))+'</button><span>'+opsHtml(items.length)+' · '+opsHtml(opsT('safe'))+'</span></div>'+
 opsTable(['#','Ad / grup',opsT('agency'),opsT('date'),opsT('room'),'BB / HB / RO',opsT('status')],rows));
 const selected=opsRes(opsState.selectedReservation);
 const detail=selected?opsCard(opsT('details'),'<div class="ops-grid2">'+[
 ['Rezervasyon no',selected.id],['OTA ref',selected.agency_ref],['Acente',selected.agency_id],
 ['Pansiyon',selected.board],['Ödeme tipi',selected.payment_type],['Komisyon',selected.commission_type],
 ['Opsiyon tarihi',selected.option_expiry||'—'],['Oda sayısı',selected.rooms.length],
 ['Giriş',selected.checkin],['Çıkış',selected.checkout],['Durum',selected.status],['Para birimi',selected.currency],
 ['Talep',selected.special_requests.join(', ')||'—'],['Not',selected.notes||'—']
 ].map(([k,v])=>'<div><small>'+opsHtml(k)+'</small><strong>'+opsHtml(v)+'</strong></div>').join('')+'</div>'+
 opsTable(['Oda','Kategori','Yetişkin','Çocuk','Günlük fiyat / tarih'],selected.rooms.map(part=>
 opsTr([opsHtml(part.room_id||'ATANMADI'),opsHtml(part.category),opsHtml(part.adults),opsHtml(part.children),
 part.nightly_rates.map(n=>opsHtml(n.date)+' '+opsMoney(n.amount,selected.currency)).join('<div class="ops-divider"></div>')]))):'';
 return '<div class="ops-stack">'+opsNotice()+view+detail+(opsState.formOpen?opsBookingForm():'')+'</div>';
}
function opsBookingForm(){
 const agencies=HOTEL_OPS_DATA.agencies.map(a=>[a.id,a.name]);
 const categories=[...new Set(HOTEL_OPS_DATA.rooms.map(r=>r.category))].sort().map(v=>[v,v]);
 const roomInputs=Array.from({length:opsState.roomCount},(_,i)=>
 '<fieldset class="ops-room-field"><legend>'+opsHtml(opsT('room'))+' '+(i+1)+'</legend><label>Kategori'+opsSelect('draftRoom'+i,categories,'standard')+'</label>'+
 '<label>Yetişkin<input type="number" name="adults'+i+'" min="1" max="20" value="2" required></label>'+
 '<label>Çocuk<input type="number" name="children'+i+'" min="0" max="12" value="0" required></label>'+
 '<label>Günlük fiyat<input type="text" value="Yalnız yetkili PMS / tarife kaynağı" disabled></label></fieldset>').join('');
 const fields=[
 ['Düzenleyen adı / grup adı','<input name="draftLabel" type="text" maxlength="70" placeholder="ÖRNEK GRUP" autocomplete="off">'],
 ['Giriş','<input name="checkin" type="date" required value="2026-11-18">'],
 ['Çıkış','<input name="checkout" type="date" required value="2026-11-21">'],
 ['Acente',opsSelect('draftAgency',agencies,'DIRECT')],
 ['OTA referans','<input name="agency_ref" type="text" maxlength="36" placeholder="DEMO_REF" autocomplete="off">'],
 ['Pansiyon',opsSelect('draftBoard',[['BB','BB · Kahvaltı dahil'],['HB','HB · Yarım pansiyon'],['RO','RO · Oda'],['FB','FB · Tam pansiyon']],'BB')],
 ['Tahsilat',opsSelect('draftPayment',[['self_payment','Misafir ödemesi'],['city_ledger','City Ledger · acente alacağı']],'self_payment')],
 ['Komisyon',opsSelect('draftCommission',[['none','Komisyonsuz'],['net','Net fiyat'],['commission','Komisyonlu']],'none')],
 ['Durum',opsSelect('draftStatus',[['confirmed','Onaylı taslak'],['option','Opsiyonel'],['waitlist','Waitlist']],'option')],
 ['Opsiyon tarihi','<input name="option_expiry" type="date">']
 ].map(([k,html])=>'<label>'+opsHtml(k)+html+'</label>').join('');
 return opsCard(opsT('newBooking')+' · STAFF_REVIEW_REQUIRED','<p class="ops-notice">'+opsHtml(opsT('draft'))+' '+opsHtml(opsT('personal'))+'</p>'+
 '<form id="opsDraftForm" autocomplete="off"><div class="ops-form-grid">'+fields+'</div><div class="ops-room-stack">'+roomInputs+'</div>'+
 '<div class="ops-toolbar"><button type="button" data-op-action="add-room">'+opsHtml(opsT('addRoom'))+'</button>'+
 '<button type="submit" class="primary">'+opsHtml(opsT('preview'))+'</button>'+
 '<button type="button" data-op-action="close-form">Kapat</button></div>'+
 '<p class="ops-note">Oda blokajı, kimlik kaydı, ödeme, özel istek, transfer, erken ödeme, folyo posting ve fatura ancak yetkili kaynakta insan onayıyla işlenir.</p></form>'+
 (opsState.formMessage?'<div class="ops-message" role="status">'+opsHtml(opsState.formMessage)+'</div>':''));
}
function opsGuests(){
 const rows=HOTEL_OPS_DATA.guests.map(g=>opsTr([opsHtml(g.id),opsHtml(g.surname),opsHtml(g.given_name),
 opsHtml(g.country),opsHtml(g.identity_type),'<span class="ops-chip">NOT_COLLECTED</span>'],'guest:'+g.id));
 const g=HOTEL_OPS_DATA.guests.find(x=>x.id===opsState.selectedGuest)||HOTEL_OPS_DATA.guests[0];
 const restricted=['Kimlik / Pasaport Numarası','TC Kimlik Numarası','Doğum yeri','Doğum tarihi','İkamet adresi','Telefon','E-posta'];
 const controls=restricted.map((label,i)=>'<label>'+opsHtml(label)+'<input type="'+(i===3?'date':'text')+'" readonly disabled placeholder="RESTRICTED · NO REAL DATA"></label>').join('');
 const identifiers=['customer_id','surname','given_name','identity_type','country','preferred_language','title','gender','identity_number','turkish_national_id','birth_place','date_of_birth','address','telephone','email'];
 return '<div class="ops-stack">'+opsNotice()+opsCard(opsT('guest'),opsTable(['ID','Soyad','Ad','Ülke','Kimlik türü','KVKK / GDPR'],rows))+
 opsCard(opsT('details')+' · '+g.id,'<p class="ops-notice">'+opsHtml(opsT('personal'))+'</p>'+
 '<div class="ops-grid2"><label>Ülke / Country<select id="opsGuestCountry">'+opsCountryOptions()+'</select></label>'+
 '<label>Kimlik tipi<select id="opsGuestDoc"><option value="passport">Pasaport</option><option value="eu_identity">AB Kimlik Kartı</option><option value="national_id">Nüfus Cüzdanı</option><option value="driving_licence">Ehliyet</option><option value="other">Diğer</option></select></label>'+
 '<label>Ad<input readonly value="'+opsHtml(g.given_name)+'"></label><label>Soyad<input readonly value="'+opsHtml(g.surname)+'"></label>'+
 '<label>Dil<select id="opsGuestLang">'+Object.keys(opsDict).map(x=>'<option value="'+x+'">'+x.toUpperCase()+'</option>').join('')+'</select></label>'+
 '<label>Unvan<select disabled><option>Mr / Ms / Mx / Unspecified</option></select></label>'+
 '<label>Cinsiyet<select disabled><option>Not collected in demo</option></select></label>'+
 '<label>TC alanı / Türkiye vatandaşı<input type="text" id="opsTCKN" disabled placeholder="Yetkili sistemde TR ise aktif"></label>'+
 controls+'</div><p class="ops-note">Ülke değiştirildiğinde TC alanının etkinleşme şartı görüntülenir; demoda gerçek kimlik girişi daima kapalıdır. Alanlar: '+opsHtml(identifiers.join(' · '))+'</p>'+
 '<div class="ops-message" id="opsGuestCountryInfo" role="status"></div>')+'</div>';
}
function opsFolios(){
 const rows=HOTEL_OPS_REPORT.folios.filter(x=>x.status==='open').map(f=>opsTr([
 '<code dir="ltr">'+opsHtml(f.folio_id)+'</code>',opsHtml(f.room_id||'—'),opsHtml(f.reservation_id),
 opsHtml(f.payer_type==='agency'?f.agency:'Misafir'),opsMoney(f.postings,f.currency),
 opsMoney(f.payments,f.currency),'<strong>'+opsMoney(f.balance,f.currency)+'</strong>'
 ],'folio:'+f.folio_id));
 const f=HOTEL_OPS_REPORT.folios.find(x=>x.folio_id===opsState.selectedFolio)||HOTEL_OPS_REPORT.folios[0];
 const raw=opsFolio(f.folio_id);
 const postings=opsTable(['Tarih','Posting','Açıklama','Tutar'],raw.postings.map(p=>opsTr([
 opsHtml(p.date),'<code>'+opsHtml(p.kind)+'</code>',opsHtml(p.description),opsMoney(p.amount,f.currency)])));
 const payments=opsTable(['Tarih','Yöntem','Referans','Tutar'],raw.payments.map(p=>opsTr([
 opsHtml(p.date),opsHtml(p.method),opsHtml(p.reference),opsMoney(p.amount,f.currency)])));
 return '<div class="ops-stack">'+opsNotice()+opsCard(opsT('folios'),opsTable(['Folyo','Oda','Rezervasyon','Cari hesap',opsT('total'),opsT('payments'),opsT('balance')],rows))+
 opsCard('FOLYO · '+f.folio_id,'<div class="ops-grid2">'+[
 ['Şirket ticari unvanı',f.agency_legal_name||'Misafir · bireysel'],['Alacaklı türü',f.payer_type],
 ['Acente / City Ledger',f.agency||'—'],['Vade',f.due_date||'—'],
 ['Fatura durumu',f.invoice_status],['Fatura bölgesi',raw.invoice_region],
 ['Para birimi',f.currency],['Folyo açıklaması',f.folio_note],
 ['Ödenen',opsMoney(f.payments,f.currency)],['Kalan alacak',opsMoney(f.balance,f.currency)]
 ].map(([k,v])=>'<div><small>'+opsHtml(k)+'</small><strong>'+opsHtml(v)+'</strong></div>').join('')+'</div>'+
 '<h4>Posting / Folyo hareketleri</h4>'+postings+
 '<h4>Ödeme hareketleri</h4>'+payments+
 '<p class="ops-notice">City Ledger bir tahsilat yöntemi değildir; ödenmemiş acente alacağını ayrı takip eder. e-Fatura, mali belge ve kur farkı hesaplamaları bu demoda uygulanmaz.</p>')+'</div>';
}
function opsAgencyLedger(){
 const rows=HOTEL_OPS_REPORT.city_ledger.map(f=>opsTr([
 opsHtml(f.agency),opsHtml(f.agency_legal_name),opsHtml(f.reservation_id),opsHtml(f.folio_id),
 opsHtml(f.due_date),opsMoney(f.postings,f.currency),opsMoney(f.payments,f.currency),
 '<strong>'+opsMoney(f.balance,f.currency)+'</strong>'
 ],'folio:'+f.folio_id));
 return '<div class="ops-stack">'+opsNotice()+opsCard(opsT('agencies'),opsTable([
 opsT('agency'),'Ticari unvan',opsT('reservation'),'Folyo','Vade',opsT('total'),
 opsT('payments'),opsT('balance')],rows))+
 '<div class="ops-note">Acenteye ait şehir hesabı / City Ledger, tahsil edilmiş para değildir. Gerçek banka, acente ve mutabakat bilgileri bağlı değildir.</div></div>';
}
function opsRates(){
 const rates=HOTEL_OPS_DATA.fx_rates;
 const rows=rates.map(r=>opsTr([opsHtml(r.currency),opsHtml(r.to),opsHtml(r.rate),
 opsHtml(r.as_of),'FICTIONAL_DEMO_RATE']));
 const rNames=['TRY','EUR','USD','GBP','RUB','UAH','ILS','SAR','AED','CHF'];
 return '<div class="ops-stack">'+opsNotice()+opsCard(opsT('fx'),'<p class="ops-notice">'+opsHtml(opsT('source'))+'</p>'+
 opsTable(['Para birimi','Hedef','Örnek kur','Tarih','Kaynak'],rows)+
 '<p class="ops-note">ISO 4217 örnek seçimleri: '+opsHtml(rNames.join(' · '))+
 '. Diğer para birimleri için güncel, yetkili tarihli kur kaynağı gereklidir. Ülke dili tek başına fatura para birimini belirlemez.</p>')+
 opsCard('Fatura ve Muhasebe Uyum Kapıları','<div class="ops-grid2">'+[
 ['e-Fatura','NOT_CONFIGURED'],['e-Arşiv','NOT_CONFIGURED'],['Vergi / KDV','LEGAL_CONFIGURATION_REQUIRED'],
 ['Cari / hesap planı','NOT_CONFIGURED'],['Fatura posting','READ_ONLY_SAMPLE'],['Mali mizan','ACCOUNTING_SOURCE_REQUIRED'],
 ['Kur farkı','RATE_SOURCE_AND_POLICY_REQUIRED'],['Fatura iptal / iade','STAFF_APPROVAL_REQUIRED']
 ].map(([a,b])=>'<div><small>'+opsHtml(a)+'</small><strong>'+opsHtml(b)+'</strong></div>').join('')+'</div>')+'</div>';
}
function opsBlocks(){
 const rooms=HOTEL_OPS_DATA.rooms;
 return '<div class="ops-stack">'+opsNotice()+opsCard(opsT('block'),opsTable([
 opsT('room'),'Kategori','Kapasite','Yatak','Kat','Hazırlık','Teknik blokaj'],
 rooms.map(r=>opsTr([opsHtml(r.id),opsHtml(r.category),opsHtml(r.capacity),
 opsHtml(r.bed),opsHtml(r.floor),opsStatusBadge(r.housekeeping),
 r.blocked?opsStatusBadge('BLOCKED'):'—'])))+
 '<p class="ops-note">Mevcut 10 modüllü oda planı ayrıca kalır. Yeni rezervasyon taslakları oda müsaitliğini resmî olarak değiştirmez.</p></div>';
}
function opsAssets(){
 const rows=HOTEL_OPS_DATA.rooms.map(r=>opsTr([opsHtml(r.id),opsHtml(r.category),
 opsHtml(r.assets.join(', ')||'—'),opsHtml(r.housekeeping),'—']));
 return '<div class="ops-stack">'+opsNotice()+opsCard(opsT('assets'),opsTable([
 opsT('room'),'Kategori','Demirbaş (kurgusal)','Durum','Bakım tarihi'],rows))+'</div>';
}
function opsReports(){
 const reports=HOTEL_OPS_REPORT.reports;
 const catalog=HOTEL_OPS_DATA.report_catalog;
 const options=catalog.map(r=>[r.id,r.label+(r.status==='implemented'?'':' · ◌ Yetkili veri gerekli')]);
 const selected=reports[opsState.selectedReport]||reports.active_folios;
 const dateFilter=value=>{if(!opsState.reportFrom&&!opsState.reportTo)return true;
   const d=value.date||value.checkin||value.due_date||value.month||null;
   if(!d)return true;
   return (!opsState.reportFrom||d>=opsState.reportFrom.slice(0,d.length))&&
     (!opsState.reportTo||d<=opsState.reportTo.slice(0,d.length));
 };
 const rows=selected.rows.filter(row=>dateFilter(row)&&
   (!opsState.reportAgency||String(row.agency||row.agency_id||'').includes(opsState.reportAgency)));
 const keys=[...new Set(rows.flatMap(r=>Object.keys(r)))].slice(0,14);
 const view=selected.status==='implemented'
  ?(rows.length?opsTable(keys,rows.slice(0,200).map(r=>opsTr(keys.map(k=>opsHtml(
       typeof r[k]==='object'?JSON.stringify(r[k]):r[k]??'—'))))):'<p>'+opsHtml(opsT('noData'))+'</p>')
  :'<p class="ops-notice">'+opsHtml(opsT('needs'))+'</p>';
 return '<div class="ops-stack">'+opsNotice()+opsCard(opsT('reports'),'<div class="ops-report-filters">'+
 '<label>Rapor'+opsSelect('opsReportType',options,selected.id)+'</label>'+
 '<label>'+opsHtml(opsT('dateFrom'))+'<input type="date" id="opsDateFrom" value="'+opsHtml(opsState.reportFrom)+'"></label>'+
 '<label>'+opsHtml(opsT('dateTo'))+'<input type="date" id="opsDateTo" value="'+opsHtml(opsState.reportTo)+'"></label>'+
 '<label>'+opsHtml(opsT('agency'))+
 opsSelect('opsReportAgency',[['','Tümü'],...HOTEL_OPS_DATA.agencies.map(a=>[a.id,a.name])],opsState.reportAgency)+
 '</label></div><div class="ops-toolbar"><button type="button" data-op-action="apply-report">'+opsHtml(opsT('filter'))+'</button>'+
 '<button type="button" data-op-action="clear-report">'+opsHtml(opsT('clear'))+'</button>'+
 '<span>'+catalog.length+' rapor · '+catalog.filter(x=>x.status==='implemented').length+' read-only veri · '+(catalog.length-catalog.filter(x=>x.status==='implemented').length)+' entegrasyon gerektiriyor</span></div>'+
 '<div class="ops-report-result"><h4>'+opsHtml(selected.label)+' · '+opsHtml(selected.status)+'</h4>'+view+'</div>'+
 '<p class="ops-note">Gelir değerleri posting tarihlerine dayanır. Gerçek e-fatura, vergisel mizan, gider defteri veya fiş üretimi yapılmaz. Farklı para birimleri tek tutara toplanmaz.</p>')+'</div>';
}
window.opsView=function(page){
 const t=opsNavigation[page];if(!t)return '';
 const b={reservation:opsReservations,guest:opsGuests,folios:opsFolios,agencies:opsAgencyLedger,
 reports:opsReports,fx:opsRates,block:opsBlocks,assets:opsAssets};
 return '<section class="ops-view" id="opsView" lang="'+opsHtml(opsState.lang)+'" dir="'+(['ar','he'].includes(opsState.lang)?'rtl':'ltr')+'">'+
 (b[t]||(()=>''))()+'</section>';
};
function opsSyncLocale(lang){
 if(!Object.hasOwn(opsDict,lang))return;
 opsState.lang=lang;
 const e=document.getElementById('v04Locale');
 if(e){e.value=lang;e.dispatchEvent(new Event('change'));}
 const global=document.getElementById('globalLanguage');if(global)global.value=lang;
 for(const item of PAGE_LIST){const key=opsNavigation[item[0]];if(key)item[2]=opsT(key);}
 const top=PAGE_LIST.find(x=>x[0]===page);if(top&&opsNavigation[page]){
   top[3]=opsT(opsNavigation[page]);top[4]=opsT('safe');
 }
 render();
}
(function setupHotelOps(){
 const root=document.getElementById('content'),language=document.getElementById('globalLanguage');
 if(!root||!language)return;
 language.addEventListener('change',()=>opsSyncLocale(language.value));
 language.setAttribute('aria-label','🌐 Dil / Language');
 root.addEventListener('click',event=>{
   const action=event.target.closest('[data-op-action]')?.dataset.opAction;
   const row=event.target.closest('[data-op-open]')?.dataset.opOpen;
   if(row){const [kind,id]=row.split(':');
     if(kind==='folio'){opsState.selectedFolio=id;navTo('ops_folios')}
     else if(kind==='guest'){opsState.selectedGuest=id;render()}
     else if(kind==='res'){opsState.selectedReservation=id;render()}
     return;
   }
   if(!action)return;
   if(action==='new-reservation'){opsState.formOpen=true;opsState.formMessage='';render()}
   else if(action==='close-form'){opsState.formOpen=false;render()}
   else if(action==='add-room'){if(opsState.roomCount<12){opsState.roomCount++;render()}}
   else if(action==='apply-report'){
     opsState.selectedReport=document.getElementById('opsReportType').value;
     opsState.reportFrom=document.getElementById('opsDateFrom').value;
     opsState.reportTo=document.getElementById('opsDateTo').value;
     opsState.reportAgency=document.getElementById('opsReportAgency').value;render();
   }else if(action==='clear-report'){opsState.reportFrom='';opsState.reportTo='';opsState.reportAgency='';render();}
 });
 root.addEventListener('keydown',event=>{const row=event.target.closest('[data-op-open]');
   if(row&&(event.key==='Enter'||event.key===' ')){event.preventDefault();row.click();}
 });
 root.addEventListener('change',event=>{
   if(event.target.id==='opsGuestCountry'){
      opsState.country=event.target.value;
      const n=document.getElementById('opsGuestCountryInfo');
      if(n)n.textContent=opsState.country==='TR'?'TR: TC kimlik alanı yetkili üretim sisteminde aktive edilir. Demo girişe kapalı.':
       'TR dışı: TC kimlik alanı aktif değildir. Pasaport/ulusal kimlik bilgileri yalnız yetkili sistemde girilir.';
   }
 });
 root.addEventListener('submit',event=>{
   if(event.target.id!=='opsDraftForm')return;
   event.preventDefault();
   const form=event.target;
   const parseDate=name=>form.elements.namedItem(name)?.value||'';
   const a=parseDate('checkin'),b=parseDate('checkout');
   let reason='';
   if(!/^\d{4}-\d{2}-\d{2}$/.test(a)||!/^\d{4}-\d{2}-\d{2}$/.test(b)||b<=a)reason='Tarihler geçerli olmalı.';
   let total=0;for(let i=0;i<opsState.roomCount;i++){
      const category=document.getElementById('draftRoom'+i)?.value;
      const adults=Number(parseDate('adults'+i));
      const children=Number(parseDate('children'+i));
      const limits=HOTEL_OPS_DATA.rooms.filter(r=>r.category===category).map(r=>r.capacity);
      const max=Math.max(0,...limits);
      total+=adults+children;
      if(!Number.isInteger(adults)||!Number.isInteger(children)||adults<1||children<0||adults+children>max){
        reason='Kişi sayısı seçilen oda kategorisinin örnek kapasitesine uygun değil.';
      }
   }
   if(reason){opsState.formMessage=reason;render();return;}
   const num=HOTEL_OPS_DATA.reservations.length+opsState.drafts.length+1;
   const id='KFD-'+a.slice(0,4)+'-'+String(num).padStart(4,'0');
   // Only non-personal summary persists in this browser tab's RAM.
   opsState.drafts.push({id,rooms:opsState.roomCount,persons:total});
   opsState.formMessage=id+' · '+opsT('draft')+' ('+opsState.roomCount+' oda · '+total+' kişi)';
   render();
 });
 const originalReset=document.getElementById('resetButton');
 originalReset?.addEventListener('click',()=>{opsState.drafts=[];opsState.formOpen=false;opsState.roomCount=1;
 opsState.formMessage='';});
 opsSyncLocale('tr');
})();
