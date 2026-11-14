/* Aurora timeline v1: presentation filters over canonical source, no writes. */
'use strict';
const auroraTimelineFilterState={floor:'all',category:'all',channel:'all',status:'all'};
const auroraTimelineTranslations={
 tr:{title:'Rezervasyon zaman çizelgesi',floor:'Kat',category:'Oda tipi',channel:'Kanal',status:'Rezervasyon durumu',all:'Tümü',reset:'Filtreleri sıfırla',shown:'Gösterilen oda',bookings:'Görüntülenen rezervasyon',noRecords:'Bu tarih aralığında eşleşen rezervasyon yok',fictional:'Kurgusal kaynak · canlı müsaitlik değil',confirmed:'Onaylı',cancelled:'İptal',pending:'Bekliyor',no_show:'Gelmedi',in_house:'Konaklıyor',checked_out:'Çıkış',dates:'Görüntülenen tarih'},
 en:{title:'Reservation timeline',floor:'Floor',category:'Room category',channel:'Channel',status:'Booking status',all:'All',reset:'Clear filters',shown:'Rooms shown',bookings:'Bookings shown',noRecords:'No matching bookings in this date range',fictional:'Fictional source · not live availability',confirmed:'Confirmed',cancelled:'Cancelled',pending:'Pending',no_show:'No-show',in_house:'In house',checked_out:'Checked out',dates:'Visible dates'},
 fr:{title:'Calendrier des réservations',floor:'Étage',category:'Catégorie',channel:'Canal',status:'Statut',all:'Tous',reset:'Effacer les filtres',shown:'Chambres visibles',bookings:'Réservations visibles',noRecords:'Aucune réservation correspondante sur ces dates',fictional:'Source fictive · disponibilités non réelles',confirmed:'Confirmée',cancelled:'Annulée',pending:'En attente',no_show:'Non-présentation',in_house:'En séjour',checked_out:'Départ',dates:'Dates visibles'},
 de:{title:'Reservierungszeitplan',floor:'Etage',category:'Zimmerkategorie',channel:'Kanal',status:'Buchungsstatus',all:'Alle',reset:'Filter löschen',shown:'Sichtbare Zimmer',bookings:'Sichtbare Buchungen',noRecords:'Keine passenden Buchungen in diesem Zeitraum',fictional:'Fiktive Daten · keine Live-Verfügbarkeit',confirmed:'Bestätigt',cancelled:'Storniert',pending:'Ausstehend',no_show:'No-Show',in_house:'Im Haus',checked_out:'Abgereist',dates:'Zeitraum'},
 el:{title:'Χρονολόγιο κρατήσεων',floor:'Όροφος',category:'Κατηγορία',channel:'Κανάλι',status:'Κατάσταση',all:'Όλα',reset:'Εκκαθάριση φίλτρων',shown:'Ορατά δωμάτια',bookings:'Ορατές κρατήσεις',noRecords:'Δεν υπάρχουν αντίστοιχες κρατήσεις',fictional:'Εικονική πηγή · όχι πραγματική διαθεσιμότητα',confirmed:'Επιβεβαιωμένη',cancelled:'Ακυρώθηκε',pending:'Εκκρεμεί',no_show:'Μη άφιξη',in_house:'Διαμένει',checked_out:'Αναχώρησε',dates:'Ορατές ημερομηνίες'},
 he:{title:'ציר זמן להזמנות',floor:'קומה',category:'סוג חדר',channel:'ערוץ',status:'סטטוס הזמנה',all:'הכול',reset:'ניקוי מסננים',shown:'חדרים מוצגים',bookings:'הזמנות מוצגות',noRecords:'אין הזמנות תואמות בטווח התאריכים',fictional:'מקור מדומה · לא זמינות בזמן אמת',confirmed:'מאושרת',cancelled:'בוטלה',pending:'ממתינה',no_show:'לא הגיע',in_house:'שוהה',checked_out:'עזב',dates:'תאריכים מוצגים'},
 ar:{title:'الجدول الزمني للحجوزات',floor:'الطابق',category:'فئة الغرفة',channel:'القناة',status:'حالة الحجز',all:'الكل',reset:'مسح الفلاتر',shown:'الغرف المعروضة',bookings:'الحجوزات المعروضة',noRecords:'لا توجد حجوزات مطابقة في الفترة',fictional:'بيانات خيالية · ليست إتاحة مباشرة',confirmed:'مؤكد',cancelled:'ملغى',pending:'معلق',no_show:'لم يصل',in_house:'مقيم',checked_out:'غادر',dates:'التواريخ المعروضة'},
 ru:{title:'Лента бронирований',floor:'Этаж',category:'Тип номера',channel:'Канал',status:'Статус брони',all:'Все',reset:'Сбросить фильтры',shown:'Номеров показано',bookings:'Бронирований показано',noRecords:'Нет подходящих бронирований за этот период',fictional:'Вымышленные данные · не актуальная доступность',confirmed:'Подтверждено',cancelled:'Отменено',pending:'Ожидание',no_show:'Не заехал',in_house:'Проживает',checked_out:'Выехал',dates:'Показаны даты'},
 es:{title:'Calendario de reservas',floor:'Planta',category:'Categoría',channel:'Canal',status:'Estado',all:'Todos',reset:'Borrar filtros',shown:'Habitaciones visibles',bookings:'Reservas visibles',noRecords:'No hay reservas coincidentes en estas fechas',fictional:'Fuente ficticia · disponibilidad no actual',confirmed:'Confirmada',cancelled:'Cancelada',pending:'Pendiente',no_show:'No presentado',in_house:'Alojado',checked_out:'Salió',dates:'Fechas visibles'},
 uk:{title:'Часова шкала бронювань',floor:'Поверх',category:'Категорія',channel:'Канал',status:'Статус',all:'Усі',reset:'Очистити фільтри',shown:'Показано номерів',bookings:'Показано бронювань',noRecords:'Немає відповідних бронювань у цьому періоді',fictional:'Вигадані дані · не актуальна наявність',confirmed:'Підтверджено',cancelled:'Скасовано',pending:'Очікує',no_show:'Не прибув',in_house:'Проживає',checked_out:'Виїхав',dates:'Показані дати'}
};
function auroraTimelineCopy(){return auroraTimelineTranslations[auroraRoomLocale()]||auroraTimelineTranslations.en;}
function auroraTimelineCanonical(id){
 if(typeof CANONICAL_DATA!=='object'||!CANONICAL_DATA||typeof CANONICAL_LINKS!=='object')return null;
 const parent=window.canonicalReservationId?.(id);return parent?CANONICAL_DATA.reservations.find(row=>row.id===parent)||null:null;
}
function auroraTimelineSelect(id,key,values,current){
 const text=auroraTimelineCopy();return '<label class="aurora-timeline-filter" for="'+id+'">'+esc(text[key])+'<select id="'+id+'">'+values.map(([val,label])=>'<option value="'+esc(val)+'"'+(val===current?' selected':'')+'>'+esc(label)+'</option>').join('')+'</select></label>';
}
function auroraTimelineToolbar(){
 const source=auroraRoomSource(),text=auroraTimelineCopy();
 if(!source)return '';
 const reservations=typeof CANONICAL_DATA==='object'?CANONICAL_DATA.reservations:[];
 const floorValues=[...new Set(source.rooms.map(row=>String(row.floor)))].sort((a,b)=>Number(a)-Number(b));
 const categories=[...new Set(source.rooms.map(row=>row.category))].sort();
 const channels=[...new Set(reservations.map(row=>row.source_ref.provider))].sort();
 const statuses=[...new Set(reservations.map(row=>row.status))].sort();
 const options=(values,translate=false)=>[['all',text.all],...values.map(val=>[val,translate?(text[val]||val):val])];
 const dates=timelineDates(),range=auroraRoomDate(dates[0])+' — '+auroraRoomDate(dates[6]);
 return '<section id="auroraTimelineFilters" class="aurora-timeline-tools" aria-labelledby="auroraTimelineTitle" data-i18n-skip data-source-state="synthetic_snapshot">'+
  '<div class="aurora-timeline-heading"><div><h2 id="auroraTimelineTitle">'+esc(text.title)+'</h2><p>'+esc(text.fictional)+'</p></div><span class="aurora-timeline-range" aria-label="'+esc(text.dates)+'">'+esc(range)+'</span></div>'+
  '<div class="aurora-timeline-grid">'+
   auroraTimelineSelect('auroraTimelineFloor','floor',options(floorValues.map(val=>val)),auroraTimelineFilterState.floor)+
   auroraTimelineSelect('auroraTimelineCategory','category',options(categories),auroraTimelineFilterState.category)+
   auroraTimelineSelect('auroraTimelineChannel','channel',options(channels),auroraTimelineFilterState.channel)+
   auroraTimelineSelect('auroraTimelineStatus','status',options(statuses,true),auroraTimelineFilterState.status)+
   '<button id="auroraTimelineReset" type="button" class="secondary">'+esc(text.reset)+'</button></div>'+
  '<p id="auroraTimelineSummary" class="aurora-timeline-summary" aria-live="polite" role="status"></p>'+
  '</section>';
}
const auroraPreviousTimelineView=timelineView;
timelineView=function(compact=false){
 const visual=auroraPreviousTimelineView(compact);
 return compact?visual:auroraTimelineToolbar()+visual;
};
function auroraApplyTimelineFilters(){
 const toolbar=document.getElementById('auroraTimelineFilters');
 if(!toolbar)return;
 const source=auroraRoomSource(),text=auroraTimelineCopy(),rows=[...document.querySelectorAll('.rack-panel .rack-row')];
 if(!source)return;
 const rooms=new Map(source.rooms.map(room=>[room.id,room]));
 const channelRestricted=auroraTimelineFilterState.channel!=='all'||auroraTimelineFilterState.status!=='all';
 let visibleRows=0,visibleBars=0;
 for(const row of rows){
  const room=rooms.get(row.dataset.rackRoom);
  const roomMatch=!!room&&(auroraTimelineFilterState.floor==='all'||String(room.floor)===auroraTimelineFilterState.floor)
   &&(auroraTimelineFilterState.category==='all'||room.category===auroraTimelineFilterState.category);
  let matchingBars=0;
  for(const bar of row.querySelectorAll('.stay-bar[data-booking]')){
   const booking=auroraTimelineCanonical(bar.dataset.booking);
   const match=!!booking&&(auroraTimelineFilterState.channel==='all'||booking.source_ref.provider===auroraTimelineFilterState.channel)
    &&(auroraTimelineFilterState.status==='all'||booking.status===auroraTimelineFilterState.status);
   bar.style.display=match?'':'none';
   bar.dataset.timelineStatus=booking?.status||'source_not_connected';
   bar.dataset.timelineChannel=booking?.source_ref.provider||'source_not_connected';
   if(match)matchingBars++;
  }
  const visible=roomMatch&&(!channelRestricted||matchingBars>0);
  row.style.display=visible?'':'none';
  row.setAttribute('aria-hidden',String(!visible));
  if(visible){visibleRows++;visibleBars+=matchingBars;}
 }
 const summary=document.getElementById('auroraTimelineSummary');
 if(summary)summary.textContent=text.shown+': '+visibleRows+' / '+source.rooms.length+' · '+text.bookings+': '+visibleBars+
  (channelRestricted&&visibleBars===0?' · '+text.noRecords:'');
}
const auroraPreviousRender=render;
render=function(){auroraPreviousRender();auroraApplyTimelineFilters();};
const auroraTimelineIds={auroraTimelineFloor:'floor',auroraTimelineCategory:'category',auroraTimelineChannel:'channel',auroraTimelineStatus:'status'};
document.getElementById('content').addEventListener('change',event=>{
 const key=auroraTimelineIds[event.target.id];
 if(!key)return;
 auroraTimelineFilterState[key]=event.target.value;auroraApplyTimelineFilters();
});
document.getElementById('content').addEventListener('click',event=>{
 if(event.target.id!=='auroraTimelineReset')return;
 Object.assign(auroraTimelineFilterState,{floor:'all',category:'all',channel:'all',status:'all'});
 for(const id of Object.keys(auroraTimelineIds)){
  const select=document.getElementById(id);if(select)select.value='all';
 }
 auroraApplyTimelineFilters();
});
document.getElementById('resetButton').addEventListener('click',()=>{
 Object.assign(auroraTimelineFilterState,{floor:'all',category:'all',channel:'all',status:'all'});
},true);
