/* Aurora reservation timeline v1 — UI-only projection of canonical fictional stays.
 * No live availability, occupancy claim, booking write, or browser-side decision engine.
 * Status filters apply to a booking, not to physical room occupancy. */
'use strict';
const AURORA_TIMELINE_COPY={
 tr:{title:'Rezervasyon zaman çizelgesi',subtitle:'Kanonik oda konaklamaları · fiziksel doluluk doğrulanmadı',floor:'Kat',category:'Kategori',status:'Rezervasyon durumu',channel:'Kaynak',start:'Başlangıç',days:'Gün',all:'Tümü',search:'Oda veya rezervasyon ara',room:'Oda / kategori',noRooms:'Bu filtrelere uygun oda veya rezervasyon bulunamadı',source:'Kurgusal Python kaynağı · salt okunur',stale:'Kaynak görünümü eskidi. Yeniden doğrulama gerekli.',missing:'Kaynak doğrulanamıyor · source_not_connected',previous:'Önceki günler',next:'Sonraki günler',today:'Kaynak tarihine dön',confirmed:'Onaylı',pending:'Bekliyor',cancelled:'İptal',no_show:'Gelmedi',in_house:'Konaklıyor',blocked:'Teknik blokaj',maintenance:'Planlı bakım',checkout:'Çıkış günü oda gecesi değildir',notice:'Çizelgedeki tahsisler doğrulanmış fiziksel doluluk veya satılabilir oda göstergesi değildir.',visible:'Gösterilen oda',direct:'Direkt',agency:'Acente'},
 en:{title:'Reservation timeline',subtitle:'Canonical room stays · physical occupancy unverified',floor:'Floor',category:'Category',status:'Booking status',channel:'Channel',start:'Start date',days:'Days',all:'All',search:'Search room or booking',room:'Room / category',noRooms:'No rooms or bookings match the filters',source:'Fictional Python source · read-only',stale:'Source view is stale. Revalidation needed.',missing:'Source unavailable · source_not_connected',previous:'Previous days',next:'Next days',today:'Return to source date',confirmed:'Confirmed',pending:'Pending',cancelled:'Cancelled',no_show:'No-show',in_house:'In house',blocked:'Technical hold',maintenance:'Scheduled maintenance',checkout:'Checkout date is not an occupied night',notice:'Assignments do not establish physical occupancy or sellable inventory.',visible:'Rooms shown',direct:'Direct',agency:'Agency'},
 fr:{title:'Calendrier des réservations',subtitle:'Séjours fictifs · occupation physique non vérifiée',floor:'Étage',category:'Catégorie',status:'Statut',channel:'Canal',start:'Début',days:'Jours',all:'Tous',search:'Chercher une chambre ou réservation',room:'Chambre / catégorie',noRooms:'Aucun résultat',source:'Source Python fictive · lecture seule',stale:'Source périmée. Vérification nécessaire.',missing:'Source indisponible',previous:'Jours précédents',next:'Jours suivants',today:'Date de référence',confirmed:'Confirmée',pending:'En attente',cancelled:'Annulée',no_show:'Non-présentation',in_house:'Sur place',blocked:'Blocage technique',maintenance:'Entretien',checkout:'Départ non compté comme nuitée',notice:'Attribution ≠ occupation physique ou disponibilité.',visible:'Chambres',direct:'Direct',agency:'Agence'},
 de:{title:'Reservierungszeitplan',subtitle:'Fiktive Aufenthalte · Belegung nicht verifiziert',floor:'Etage',category:'Kategorie',status:'Buchungsstatus',channel:'Kanal',start:'Beginn',days:'Tage',all:'Alle',search:'Zimmer oder Buchung suchen',room:'Zimmer / Kategorie',noRooms:'Keine passenden Ergebnisse',source:'Fiktive Python-Quelle · schreibgeschützt',stale:'Quelldaten veraltet. Prüfung nötig.',missing:'Quelle nicht verfügbar',previous:'Frühere Tage',next:'Spätere Tage',today:'Quelldatum',confirmed:'Bestätigt',pending:'Ausstehend',cancelled:'Storniert',no_show:'Nicht erschienen',in_house:'Eingecheckt',blocked:'Technische Sperre',maintenance:'Wartung',checkout:'Abreisetag ist keine Übernachtung',notice:'Zuteilung ist keine bestätigte Belegung oder Verfügbarkeit.',visible:'Zimmer',direct:'Direkt',agency:'Agentur'},
 el:{title:'Χρονοδιάγραμμα κρατήσεων',subtitle:'Εικονικές διαμονές · μη επιβεβαιωμένη πληρότητα',floor:'Όροφος',category:'Κατηγορία',status:'Κατάσταση',channel:'Κανάλι',start:'Έναρξη',days:'Ημέρες',all:'Όλα',search:'Αναζήτηση δωματίου ή κράτησης',room:'Δωμάτιο / κατηγορία',noRooms:'Δεν υπάρχουν αποτελέσματα',source:'Εικονική πηγή Python · μόνο ανάγνωση',stale:'Τα δεδομένα είναι παλιά.',missing:'Μη διαθέσιμη πηγή',previous:'Προηγούμενες',next:'Επόμενες',today:'Ημερομηνία πηγής',confirmed:'Επιβεβαιωμένη',pending:'Εκκρεμεί',cancelled:'Ακυρώθηκε',no_show:'Δεν εμφανίστηκε',in_house:'Διαμένει',blocked:'Τεχνικός αποκλεισμός',maintenance:'Συντήρηση',checkout:'Η αναχώρηση δεν είναι διανυκτέρευση',notice:'Η ανάθεση δεν τεκμηριώνει πληρότητα ή διαθεσιμότητα.',visible:'Δωμάτια',direct:'Άμεσο',agency:'Πρακτορείο'},
 he:{title:'ציר זמן להזמנות',subtitle:'שהיות מדומות · תפוסה פיזית לא מאומתת',floor:'קומה',category:'קטגוריה',status:'מצב הזמנה',channel:'ערוץ',start:'תאריך התחלה',days:'ימים',all:'הכול',search:'חיפוש חדר או הזמנה',room:'חדר / קטגוריה',noRooms:'אין התאמות',source:'נתוני Python מדומים · קריאה בלבד',stale:'נתוני המקור התיישנו',missing:'המקור אינו זמין',previous:'ימים קודמים',next:'ימים הבאים',today:'חזרה לתאריך המקור',confirmed:'אושר',pending:'ממתין',cancelled:'בוטל',no_show:'לא הגיע',in_house:'שוהה',blocked:'חסימה טכנית',maintenance:'תחזוקה',checkout:'תאריך יציאה אינו לילה תפוס',notice:'הקצאה אינה מוכיחה תפוסה או זמינות.',visible:'חדרים',direct:'ישיר',agency:'סוכנות'},
 ar:{title:'الجدول الزمني للحجوزات',subtitle:'إقامات افتراضية · الإشغال الفعلي غير مؤكد',floor:'الطابق',category:'الفئة',status:'حالة الحجز',channel:'القناة',start:'البداية',days:'أيام',all:'الكل',search:'ابحث عن غرفة أو حجز',room:'الغرفة / الفئة',noRooms:'لا توجد نتائج',source:'مصدر Python افتراضي · للقراءة فقط',stale:'بيانات المصدر قديمة',missing:'المصدر غير متاح',previous:'الأيام السابقة',next:'الأيام التالية',today:'تاريخ المصدر',confirmed:'مؤكد',pending:'معلّق',cancelled:'ملغي',no_show:'لم يصل',in_house:'مقيم',blocked:'حظر تقني',maintenance:'صيانة',checkout:'يوم المغادرة ليس ليلة إقامة',notice:'التخصيص لا يثبت الإشغال أو توفر الغرف.',visible:'غرف',direct:'مباشر',agency:'وكالة'},
 ru:{title:'Календарь бронирований',subtitle:'Тестовые проживания · заселение не подтверждено',floor:'Этаж',category:'Категория',status:'Статус',channel:'Канал',start:'Начало',days:'Дней',all:'Все',search:'Найти номер или бронь',room:'Номер / категория',noRooms:'Нет результатов',source:'Тестовые данные Python · только чтение',stale:'Источник устарел',missing:'Источник недоступен',previous:'Ранее',next:'Позже',today:'Дата источника',confirmed:'Подтверждено',pending:'Ожидает',cancelled:'Отменено',no_show:'Не прибыл',in_house:'Проживает',blocked:'Тех. блокировка',maintenance:'Ремонт',checkout:'Выезд не считается ночью',notice:'Назначение не подтверждает занятость или доступность.',visible:'Номеров',direct:'Напрямую',agency:'Агентство'},
 es:{title:'Cronología de reservas',subtitle:'Estancias ficticias · ocupación física no verificada',floor:'Planta',category:'Categoría',status:'Estado',channel:'Canal',start:'Inicio',days:'Días',all:'Todas',search:'Buscar habitación o reserva',room:'Habitación / categoría',noRooms:'Sin resultados',source:'Fuente ficticia Python · solo lectura',stale:'Datos de origen antiguos',missing:'Fuente no disponible',previous:'Días anteriores',next:'Días siguientes',today:'Fecha de origen',confirmed:'Confirmada',pending:'Pendiente',cancelled:'Cancelada',no_show:'No presentado',in_house:'Alojado',blocked:'Bloqueo técnico',maintenance:'Mantenimiento',checkout:'La salida no cuenta como noche',notice:'La asignación no prueba ocupación física ni disponibilidad.',visible:'Habitaciones',direct:'Directo',agency:'Agencia'},
 uk:{title:'Календар бронювань',subtitle:'Вигадані проживання · заселення не підтверджено',floor:'Поверх',category:'Категорія',status:'Статус',channel:'Канал',start:'Початок',days:'Днів',all:'Усі',search:'Знайти номер чи бронювання',room:'Номер / категорія',noRooms:'Немає результатів',source:'Вигадане джерело Python · лише перегляд',stale:'Дані застаріли',missing:'Джерело недоступне',previous:'Раніше',next:'Далі',today:'Дата джерела',confirmed:'Підтверджено',pending:'Очікує',cancelled:'Скасовано',no_show:'Не прибув',in_house:'Проживає',blocked:'Технічне блокування',maintenance:'Техобслуговування',checkout:'Дата виїзду не є ночівлею',notice:'Призначення не підтверджує зайнятість чи доступність.',visible:'Номерів',direct:'Прямий',agency:'Агенція'}
};
const auroraTimelineFilters={start:null,days:7,floor:'all',category:'all',status:'all',channel:'all',query:''};
const auroraTimelineLocale=()=>typeof opsState!=='undefined'&&opsState.lang||'tr';
const auroraTimelineT=key=>(AURORA_TIMELINE_COPY[auroraTimelineLocale()]||AURORA_TIMELINE_COPY.en)[key]||AURORA_TIMELINE_COPY.en[key]||key;
const auroraTimelineEscape=value=>esc(String(value??''));
function auroraTimelineAddDays(iso,shift){
 const d=new Date(iso+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+shift);
 return d.toISOString().slice(0,10);
}
function auroraTimelineDates(){
 const first=auroraTimelineFilters.start||auroraTimelineAddDays(CANONICAL_LINKS.as_of,-1);
 return Array.from({length:auroraTimelineFilters.days},(_,i)=>auroraTimelineAddDays(first,timelineOffset+i));
}
function auroraTimelineWindow(start,end,dates){
 if(!start||!end||start>=end||start>dates[dates.length-1]||end<=dates[0])return null;
 const left=Math.max(0,dates.findIndex(date=>date>=start));
 const right=dates.filter(date=>date<end).length;
 return right>left?{left,width:right-left}:null;
}
function auroraTimelineStyle(range,days){
 return 'inset-inline-start:calc('+range.left+' * (100% / '+days+') + 3px);width:calc('+range.width+' * (100% / '+days+') - 6px)';
}
function auroraTimelineSource(){
 const graph=typeof auroraRoomSource==='function'?auroraRoomSource():null;
 if(!graph||typeof CANONICAL_DATA!=='object'||!CANONICAL_DATA)return null;
 if(!Array.isArray(CANONICAL_DATA.room_stays)||!Array.isArray(CANONICAL_DATA.reservations)||!Array.isArray(CANONICAL_DATA.room_blocks))return null;
 return graph;
}
function auroraTimelineBookingMap(){
 return new Map(CANONICAL_DATA.reservations.map(booking=>[booking.id,booking]));
}
function auroraTimelineCaseForStay(id){
 const cases=CANONICAL_LINKS.review_links||{};
 return Object.keys(cases).find(key=>cases[key].room_stay_id===id)||null;
}
function auroraTimelineFilterMarkup(graph){
 const t=auroraTimelineT,e=auroraTimelineEscape,f=auroraTimelineFilters;
 const floors=[...new Set(graph.rooms.map(room=>room.floor))].sort((a,b)=>a-b);
 const categories=[...new Set(graph.rooms.map(room=>room.category))].sort();
 const channels=[...new Set(CANONICAL_DATA.reservations.map(booking=>booking.source_ref.provider))].sort();
 const select=(id,key,options,current)=>'<label><span>'+e(t(key))+'</span><select id="'+id+'">'+options.map(([value,label])=>'<option value="'+e(value)+'"'+(current===value?' selected':'')+'>'+e(label)+'</option>').join('')+'</select></label>';
 const all=[[ 'all',t('all') ]];
 const statuses=[['confirmed',t('confirmed')],['pending',t('pending')],['cancelled',t('cancelled')],['no_show',t('no_show')],['in_house',t('in_house')]];
 return '<div class="aurora-timeline-filters" role="group" aria-label="'+e(t('title'))+'">'+
 select('auroraTimelineFloor','floor',[...all,...floors.map(x=>[String(x),String(x)])],f.floor)+
 select('auroraTimelineCategory','category',[...all,...categories.map(x=>[x,typeof auroraRoomCategory==='function'?auroraRoomCategory(x):x])],f.category)+
 select('auroraTimelineStatus','status',[...all,...statuses],f.status)+
 select('auroraTimelineChannel','channel',[...all,...channels.map(x=>[x,t(x)===x?x:t(x)])],f.channel)+
 '<label><span>'+e(t('start'))+'</span><input id="auroraTimelineStart" type="date" value="'+e(f.start||auroraTimelineAddDays(CANONICAL_LINKS.as_of,-1))+'"></label>'+
 select('auroraTimelineDays','days',[[7,'7'],[14,'14'],[21,'21']],String(f.days))+
 '<label class="aurora-timeline-search"><span>'+e(t('search'))+'</span><input id="auroraTimelineSearch" type="search" value="'+e(f.query)+'" placeholder="'+e(t('search'))+'"></label></div>';
}
function auroraTimelineViewV1(compact=false){
 const t=auroraTimelineT,e=auroraTimelineEscape,graph=auroraTimelineSource();
 const status=graph?(reportStale?'source_stale':'synthetic_snapshot'):'source_not_connected';
 if(!graph)return '<section class="panel rack-panel aurora-timeline" data-source-state="'+status+'"><p role="status">'+e(t('missing'))+'</p></section>';
 const dates=auroraTimelineDates(),f=auroraTimelineFilters,source=CANONICAL_DATA;
 const bookingMap=auroraTimelineBookingMap(),highlights=new Set(storyRoomIds());
 const rooms=graph.rooms.filter(room=>{
  if(!compact&&(f.floor!=='all'&&String(room.floor)!==f.floor||f.category!=='all'&&room.category!==f.category))return false;
  if(!compact&&f.query){
   const query=f.query.toLocaleLowerCase(auroraTimelineLocale());
   if(![room.id,...room.reservation_ids].join(' ').toLocaleLowerCase(auroraTimelineLocale()).includes(query))return false;
  }
  if(!compact&&(f.status!=='all'||f.channel!=='all')){
   return source.room_stays.some(stay=>stay.room_id===room.id&&!!auroraTimelineWindow(stay.arrival,stay.departure,dates)&&
    bookingMap.has(stay.reservation_id)&&
    (f.status==='all'||bookingMap.get(stay.reservation_id).status===f.status)&&
    (f.channel==='all'||bookingMap.get(stay.reservation_id).source_ref.provider===f.channel));
  }
  return true;
 });
 const selected=compact?rooms.filter(room=>['101','102','103','104','301','302','303','401'].includes(room.id)||highlights.has(room.id)).slice(0,9):rooms;
 const locale=auroraTimelineLocale(),dateFormat=new Intl.DateTimeFormat(locale,{weekday:'short',day:'numeric',month:'short',timeZone:'UTC'});
 const bars=(room)=>{
  const items=source.room_stays.filter(stay=>stay.room_id===room.id).map(stay=>({stay,booking:bookingMap.get(stay.reservation_id),range:auroraTimelineWindow(stay.arrival,stay.departure,dates)}))
    .filter(x=>x.booking&&x.range&&(compact||((f.status==='all'||x.booking.status===f.status)&&(f.channel==='all'||x.booking.source_ref.provider===f.channel))));
  return items.map(({stay,booking,range})=>{
   const caseId=auroraTimelineCaseForStay(stay.id);
   if(!caseId)return '';
   const inactive=['cancelled','no_show'].includes(booking.status);
   const label=[booking.id,t(booking.status),stay.arrival,stay.departure,booking.source_ref.provider,t('checkout')].join(' · ');
   return '<button class="stay-bar aurora-stay channel-'+e(booking.source_ref.provider)+' '+(inactive?'cancelled':'')+' '+(range.width<2?'stay-short':'')+'"'+
     ' style="'+auroraTimelineStyle(range,dates.length)+'" data-booking="'+e(caseId)+'" data-canonical-reservation="'+e(booking.id)+'" data-status="'+e(booking.status)+'" aria-label="'+e(label)+'" title="'+e(label)+'">'+
     '<strong>'+e(booking.id)+'</strong><span>'+e(t(booking.status))+' · '+e(booking.source_ref.provider)+'</span></button>';
  }).join('');
 };
 const blocks=room=>{
  const raw=source.room_blocks.filter(block=>block.room_id===room.id&&block.status==='active').map(block=>({start:block.start,end:block.end||auroraTimelineAddDays(dates[dates.length-1],1),label:t('blocked')}))
   .concat((source.rooms.find(x=>x.id===room.id)?.maintenance||[]).map(x=>({start:x.start,end:x.end,label:t('maintenance')})));
  return raw.map(entry=>{
   const range=auroraTimelineWindow(entry.start,entry.end,dates);
   return range?'<span class="aurora-date-block" style="'+auroraTimelineStyle(range,dates.length)+'" title="'+e(entry.label)+'">'+e(entry.label)+'</span>':'';
  }).join('');
 };
 const headers=dates.map(date=>'<div class="rack-day '+(date===CANONICAL_LINKS.as_of?'today':'')+'" role="columnheader" title="'+e(date)+'"><span>'+e(date)+'</span><b>'+e(dateFormat.format(new Date(date+'T12:00:00Z')))+'</b></div>').join('');
 const rows=selected.map(room=>{
  const graphStatus=room.state_codes.includes('out_of_order')||room.state_codes.includes('out_of_service')?'closed':room.housekeeping==='dirty'?'dirty':room.assignment_state==='assigned'?'held':'checked';
  const overlay=blocks(room);
  return '<div class="rack-row '+(overlay?'has-maintenance ':'')+(highlights.has(room.id)?'evidence-highlight':'')+'" role="row" data-rack-room="'+e(room.id)+'">'+
   '<button class="rack-name" role="rowheader" data-room="'+e(room.id)+'"><span class="room-state-dot '+graphStatus+'"></span><b>'+e(room.id)+'</b><small>'+e(typeof auroraRoomCategory==='function'?auroraRoomCategory(room.category):room.category)+'</small></button>'+
   '<div class="rack-track" role="cell"><div class="rack-cells">'+dates.map(d=>'<span class="'+(d===CANONICAL_LINKS.as_of?'today':'')+'"></span>').join('')+'</div>'+
   bars(room)+overlay+'</div></div>';
 }).join('');
 const toolbar='<div class="rack-tools"><button class="mini" type="button" data-timeline-shift="-7" aria-label="'+e(t('previous'))+'">‹</button>'+
  '<button class="mini" type="button" data-timeline-shift="0">'+e(t('today'))+'</button>'+
  '<button class="mini" type="button" data-timeline-shift="7" aria-label="'+e(t('next'))+'">›</button></div>';
 return '<section class="panel rack-panel aurora-timeline '+(compact?'compact':'')+'" data-source-state="'+status+'" data-days="'+dates.length+'" aria-label="'+e(t('title'))+'">'+
 '<div class="panel-head"><div><div class="panel-kicker">AURORA / TIMELINE · '+e(t('source'))+'</div><h2>'+e(t('title'))+' <span class="subtle-count">'+e(String(selected.length))+'</span></h2><p>'+e(t('subtitle'))+'</p></div>'+toolbar+'</div>'+
 (compact?'':auroraTimelineFilterMarkup(graph))+
 '<p class="aurora-timeline-disclaimer" role="status">'+e(reportStale?t('stale'):t('notice'))+'</p>'+
 '<div class="rack-scroll" tabindex="0" role="region" aria-label="'+e(t('title'))+'"><div class="rack" role="table" style="--aurora-days:'+dates.length+'"><div class="rack-header" role="row"><div class="rack-name" role="columnheader">'+e(t('room'))+'</div>'+headers+'</div>'+
 (selected.length?rows:'<p class="aurora-timeline-empty">'+e(t('noRooms'))+'</p>')+'</div></div>'+
 '<div class="rack-footer"><small>'+e(t('visible'))+': '+e(String(selected.length))+' · '+e(dates[0])+' – '+e(dates[dates.length-1])+' · '+e(t('checkout'))+'</small></div></section>';
}
timelineView=auroraTimelineViewV1;
document.getElementById('content').addEventListener('change',event=>{
 const map={auroraTimelineFloor:'floor',auroraTimelineCategory:'category',auroraTimelineStatus:'status',auroraTimelineChannel:'channel',auroraTimelineSearch:'query'};
 const id=event.target.id;
 if(Object.hasOwn(map,id))auroraTimelineFilters[map[id]]=event.target.value;
 else if(id==='auroraTimelineDays')auroraTimelineFilters.days=Number(event.target.value);
 else if(id==='auroraTimelineStart'){
  const start=event.target.value;
  if(!/^\d{4}-\d{2}-\d{2}$/.test(start))return;
  auroraTimelineFilters.start=start;timelineOffset=0;
 }else return;
 render();
});
document.getElementById('content').addEventListener('click',event=>{
 if(event.target.closest('[data-timeline-shift="0"]'))auroraTimelineFilters.start=null;
},true);
document.getElementById('resetButton').addEventListener('click',()=>{
 Object.assign(auroraTimelineFilters,{start:null,days:7,floor:'all',category:'all',status:'all',channel:'all',query:''});
},true);
