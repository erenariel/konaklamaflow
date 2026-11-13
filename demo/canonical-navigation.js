/* Explicit FK navigation over the generated canonical snapshot. No writes. */
'use strict';
window.canonicalFocusReservation = null;
const canonicalNavLabels = {
 tr:['Ortak rezervasyon kaydı','Oda planı','Rezervasyon detayları','İlgili folyo','Kaynak rapor','Finans kaydı yok · not_applicable','Oda konaklamaları','Misafir','Salt okunur kurgusal kaynak'],
 en:['Shared reservation record','Room plan','Reservation details','Related folio','Source report','No financial record · not_applicable','Room stays','Guest','Read-only fictional source'],
 fr:['Réservation commune','Plan des chambres','Détails de réservation','Folio associé','Rapport source','Aucun enregistrement financier · not_applicable','Séjours par chambre','Client','Source fictive en lecture seule'],
 el:['Κοινή κράτηση','Πλάνο δωματίων','Στοιχεία κράτησης','Σχετικός λογαριασμός','Αναφορά πηγής','Χωρίς οικονομική εγγραφή · not_applicable','Διαμονές δωματίων','Επισκέπτης','Εικονική πηγή μόνο για ανάγνωση'],
 he:['רשומת הזמנה משותפת','תוכנית חדרים','פרטי הזמנה','חשבון קשור','דוח מקור','אין רישום כספי · not_applicable','שהיות בחדרים','אורח','מקור מדומה לקריאה בלבד'],
 ar:['سجل الحجز المشترك','مخطط الغرف','تفاصيل الحجز','الحساب المرتبط','تقرير المصدر','لا سجل مالي · not_applicable','إقامات الغرف','ضيف','مصدر افتراضي للقراءة فقط'],
 de:['Gemeinsame Buchung','Zimmerplan','Buchungsdetails','Zugehöriges Folio','Quellbericht','Kein Finanzdatensatz · not_applicable','Zimmeraufenthalte','Gast','Fiktive Quelle, nur lesbar'],
 ru:['Общая запись брони','План номеров','Данные брони','Связанный счёт','Исходный отчёт','Нет финансовой записи · not_applicable','Проживание в номерах','Гость','Вымышленный источник, только чтение'],
 es:['Reserva compartida','Plano de habitaciones','Detalles de reserva','Folio relacionado','Informe de origen','Sin registro financiero · not_applicable','Estancias por habitación','Huésped','Fuente ficticia de solo lectura'],
 uk:['Спільний запис бронювання','План номерів','Дані бронювання','Пов’язаний рахунок','Звіт джерела','Немає фінансового запису · not_applicable','Проживання в номерах','Гість','Вигадане джерело, лише читання']
};
function canonicalCopy(){return canonicalNavLabels[typeof opsState!=='undefined'?opsState.lang:'tr']||canonicalNavLabels.en;}
function canonicalLink(id){return typeof CANONICAL_LINKS==='object'?CANONICAL_LINKS.reservations[id]:null;}
window.canonicalReservationId=function(id){
 if(typeof id!=='string'||typeof CANONICAL_LINKS!=='object')return null;
 return Object.hasOwn(CANONICAL_LINKS.reservations,id)?id:CANONICAL_LINKS.review_links[id]?.reservation_id||null;
};
function canonicalNavigationSection(id){
 const key=window.canonicalReservationId(id),link=key&&canonicalLink(key);if(!link)return null;
 const text=canonicalCopy(),section=document.createElement('section');
 section.className='canonical-links';section.dataset.canonicalReservationId=key;
 section.dataset.canonicalSourceState=reportStale?'stale':'synthetic_snapshot';
 const title=document.createElement('h3');title.textContent=text[0]+' · '+key;section.append(title);
 const boundary=document.createElement('p');boundary.className='section-note';
 boundary.textContent=text[8]+' · '+CANONICAL_LINKS.as_of;section.append(boundary);
 const buttons=document.createElement('div');buttons.className='actions';
 function add(label,action,folio){
  const button=document.createElement('button');button.type='button';button.className='secondary';
  button.textContent=label;button.dataset.canonicalAction=action;button.dataset.reservationId=key;
  if(folio)button.dataset.folioId=folio;buttons.append(button);
 }
 add(text[1],'room-plan');add(text[2],'reservation');
 for(const folio of link.folio_ids)add(text[3]+' · '+folio,'folio',folio);
 if(!link.folio_ids.length){const note=document.createElement('p');note.dataset.financeState='not_applicable';note.textContent=text[5];section.append(note);}
 add(text[4],'reports');section.append(buttons);
 const stays=document.createElement('p');stays.className='section-note';
 stays.textContent=text[6]+': '+link.room_stay_ids.join(', ');section.append(stays);
 return section;
}
const canonicalOriginalShowBooking=showBooking;
showBooking=function(id){
 canonicalOriginalShowBooking(id);
 const section=canonicalNavigationSection(id),drawer=document.getElementById('drawer');
 if(section&&drawer&&document.getElementById('backdrop').classList.contains('open')){
  const actions=drawer.querySelector('.actions');if(actions)actions.before(section);else drawer.append(section);
 }
};
const canonicalOriginalShowRoom=showRoom;
showRoom=function(id){
 canonicalOriginalShowRoom(id);
 const drawer=document.getElementById('drawer');if(!drawer)return;
 const parents=[...new Set(CANONICAL_DATA.room_stays.filter(stay=>stay.room_id===id).map(stay=>stay.reservation_id))];
 for(const parent of parents){const section=canonicalNavigationSection(parent);if(section)drawer.append(section);}
};
window.focusCanonicalRoomPlan=function(id){
 const key=window.canonicalReservationId(id);if(!key)return false;
 window.canonicalFocusReservation=key;navTo('rooms');
 const cases=Object.entries(CANONICAL_LINKS.review_links).filter(([,link])=>link.reservation_id===key).map(([caseId])=>caseId);
 const targets=[...document.querySelectorAll('.stay-bar[data-booking]')].filter(bar=>cases.includes(bar.dataset.booking));
 // Scroll to a real stay case; all of the parent's rooms stay highlighted.
 const target=targets[0];
 target?.scrollIntoView({block:'center',behavior:'instant'});target?.focus({preventScroll:true});return true;
};
window.openCanonicalReview=function(id){
 const key=window.canonicalReservationId(id);if(!key)return false;
 const cases=Object.entries(CANONICAL_LINKS.review_links).filter(([,link])=>link.reservation_id===key);
 closeDetail();
 if(cases.length===1){showBooking(cases[0][0]);return true;}
 // A multi-room booking is not silently represented by the first room.
 const text=canonicalCopy();
 openDrawer('<h2>'+esc(key)+'</h2><p class="section-note">'+esc(text[6])+' · '+esc(text[8])+'</p>'+
  cases.map(([engineId,link])=>'<button class="secondary" type="button" data-canonical-case="'+esc(engineId)+'">'+esc(link.room_stay_id)+'</button>').join(''));
 return true;
};
window.openCanonicalReservation=function(id,options={}){return window.opsFocusReservation?.(id,options)||false;};
document.addEventListener('click',event=>{
 const action=event.target.closest('[data-canonical-action]');
 if(action&&action.closest('.canonical-links')&&!action.closest('#opsView')){
  const id=action.dataset.reservationId;if(!canonicalLink(id))return;
  if(action.dataset.canonicalAction==='room-plan')window.focusCanonicalRoomPlan(id);
  else if(action.dataset.canonicalAction==='folio'){closeDetail();window.opsFocusFolio?.(action.dataset.folioId);}
  else {closeDetail();window.opsFocusReservation?.(id,{tab:action.dataset.canonicalAction==='reports'?'reports':'reservation'});}
 }
 const child=event.target.closest('[data-canonical-case]');if(child)showBooking(child.dataset.canonicalCase);
});
document.addEventListener('click',event=>{
 if(event.target.closest('#commandPlay,#commandNext,#commandReset,#startShowcase,#tourPlay,#tourNext,#tourReset,#resetButton'))window.canonicalFocusReservation=null;
},true);
document.addEventListener('change',event=>{if(event.target.id==='tourScenario')window.canonicalFocusReservation=null;},true);
