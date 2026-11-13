/* Demo-only AI command center. All metrics are derived from the existing
 * fictional in-memory snapshot; this module never submits hotel changes. */
const DEMO_GUEST_NAMES=Object.freeze({
 KF1001:'Sofia Bennett',KF1002:'Mateo Costa',KF1003:'Emma Laurent',
 KF1004:'Daniel Reed',KF1005:'Isabella Moretti',KF1006:'Noah Fischer',
 KF1007:'Olivia Martin',KF1008:'Lukas Weber',KF1009:'Ava Wilson',
 KF1010:'Leo Novak',KF1011:'Maya Chen',KF1012:'Amelia Stone'
});
function demoGuestName(id){return DEMO_GUEST_NAMES[id]||'Örnek misafir';}
const COMMAND_LANG={
 tr:['AI Operasyon Merkezi','Örnek veri · Çevrimdışı','Kaynak → Kural motoru → AI açıklaması → Personel','Operasyonun merkezinde yapay zekâ','Senaryoyu oynat','Duraklat','İleri','Sıfırla','İncelenen rezervasyon','Mevcut adım','Kanıt ve güvenli karar','Kontrol personelde','Yedi günlük doluluk','Kanallara göre rezervasyon','Kurgusal 12 Kasım 2026 veri anlık görüntüsü','Gösterilen adımlar gerçek PMS işlemi değildir.','Başlamak için senaryoyu oynat.'],
 en:['AI Operations Center','Sample data · Offline','Source → Rule engine → AI explanation → Staff','AI at the center of operations','Play scenario','Pause','Next','Reset','Reservation in focus','Current step','Evidence and safe decision','Staff retains control','Seven-day occupancy','Bookings by channel','Fictional snapshot: 12 November 2026','No live PMS actions are performed.','Play a scenario to begin.'],
 fr:['Centre des opérations IA','Données fictives · Hors ligne','Source → Règles → Explication IA → Équipe','L’IA au cœur des opérations','Lancer le scénario','Pause','Suivant','Réinitialiser','Réservation ciblée','Étape actuelle','Preuves et décision sûre','Décision humaine','Occupation sur sept jours','Réservations par canal','Données fictives du 12 novembre 2026','Aucune action PMS réelle.','Lance le scénario.'],
 el:['Κέντρο λειτουργιών AI','Δοκιμαστικά δεδομένα · Offline','Πηγή → Κανόνες → AI → Προσωπικό','AI στο κέντρο λειτουργιών','Έναρξη σεναρίου','Παύση','Επόμενο','Επαναφορά','Κράτηση σε εξέταση','Τρέχον βήμα','Στοιχεία και ασφαλής απόφαση','Ανθρώπινος έλεγχος','Πληρότητα επτά ημερών','Κρατήσεις ανά κανάλι','Εικονικά δεδομένα 12 Νοεμβρίου 2026','Χωρίς πραγματικές ενέργειες PMS.','Ξεκίνησε το σενάριο.'],
 he:['מרכז תפעול AI','נתוני הדגמה · לא מקוון','מקור ← מנוע כללים ← הסבר AI ← צוות','AI במרכז התפעול','הפעל תרחיש','השהה','הבא','אפס','הזמנה נבדקת','שלב נוכחי','ראיות והחלטה בטוחה','הצוות מאשר','תפוסה לשבעה ימים','הזמנות לפי ערוץ','נתונים מדומים: 12 בנובמבר 2026','אין פעולות PMS אמיתיות.','הפעל תרחיש להתחלה.'],
 ar:['مركز عمليات الذكاء الاصطناعي','بيانات تجريبية · دون اتصال','المصدر ← القواعد ← شرح الذكاء الاصطناعي ← الموظف','الذكاء الاصطناعي في قلب العمليات','تشغيل السيناريو','إيقاف مؤقت','التالي','إعادة تعيين','الحجز قيد المراجعة','الخطوة الحالية','الأدلة والقرار الآمن','القرار للموظف','الإشغال خلال سبعة أيام','الحجوزات حسب القناة','بيانات افتراضية: 12 نوفمبر 2026','لا توجد عمليات فعلية على PMS.','شغّل السيناريو للبدء.'],
 de:['KI-Betriebszentrale','Beispieldaten · Offline','Quelle → Regeln → KI-Erklärung → Personal','KI im Mittelpunkt des Betriebs','Szenario starten','Pause','Weiter','Zurücksetzen','Buchung im Fokus','Aktueller Schritt','Nachweis und sichere Entscheidung','Personal entscheidet','Belegung über sieben Tage','Buchungen nach Kanal','Fiktiver Datenstand: 12. November 2026','Keine echten PMS-Aktionen.','Szenario starten.'],
 ru:['Центр операций ИИ','Тестовые данные · Офлайн','Источник → Правила → ИИ → Персонал','ИИ в центре работы','Запустить сценарий','Пауза','Далее','Сбросить','Выбранная бронь','Текущий этап','Доказательства и решение','Решение за персоналом','Загрузка за семь дней','Брони по каналам','Тестовые данные: 12 ноября 2026','Реальные действия PMS не выполняются.','Запустите сценарий.'],
 es:['Centro de operaciones IA','Datos ficticios · Sin conexión','Fuente → Reglas → Explicación IA → Personal','IA en el centro de las operaciones','Reproducir escenario','Pausar','Siguiente','Restablecer','Reserva seleccionada','Paso actual','Pruebas y decisión segura','Decisión humana','Ocupación de siete días','Reservas por canal','Datos ficticios: 12 de noviembre de 2026','No se ejecutan acciones PMS reales.','Inicia el escenario.'],
 uk:['Центр операцій ШІ','Тестові дані · Офлайн','Джерело → Правила → ШІ → Персонал','ШІ в центрі операцій','Запустити сценарій','Пауза','Далі','Скинути','Бронювання у фокусі','Поточний крок','Докази та безпечне рішення','Рішення за персоналом','Завантаженість за сім днів','Бронювання за каналом','Тестові дані: 12 листопада 2026','Реальні дії PMS не виконуються.','Запусти сценарій.']
};
function commandText(i){return (COMMAND_LANG[typeof opsState!=='undefined'?opsState.lang:'tr']||COMMAND_LANG.en)[i];}
function aiCommandCenter(){
 const story=currentStory(),step=storyStarted?story.steps[storyStep]:null;
 const booking=state.reservations.find(b=>b.id===story?.booking_id);
 const current=step?Math.min(storyStep+1,story.steps.length):0;
 const safeText=x=>esc(x||'');
 return `<section id="aiCommandCenter" class="ai-command" aria-label="${safeText(commandText(0))}">
 <div class="ai-command-top"><div><span class="ai-command-eyebrow">✦ ${safeText(commandText(0))}</span><h2>${safeText(commandText(3))}</h2><p>${safeText(commandText(2))}</p></div><span class="ai-command-badge">${safeText(commandText(1))}</span></div>
 <div class="ai-command-body"><div class="ai-command-main"><div class="ai-command-steps" aria-label="${safeText(commandText(5))}">${story.steps.map((s,i)=>`<span class="${storyStarted?(i<storyStep?'complete':i===storyStep?'active':''):''}" aria-label="${i+1} / ${story.steps.length}">${String(i+1).padStart(2,'0')}</span>`).join('')}</div>
 <div class="ai-command-caption">${safeText(commandText(9))} · ${current}/${story.steps.length}</div>
 <h3 aria-live="polite">${safeText(step?step.title:commandText(16))}</h3><p class="ai-command-description">${safeText(step?step.body:story.summary)}</p>
 <div class="ai-command-controls"><button id="commandPlay" class="primary" ${reportStale?'disabled':''}>${icon('play')} ${safeText(commandText(4))}</button><button id="commandPause" class="secondary" ${!storyPlaying?'disabled':''}>${safeText(commandText(5))}</button><button id="commandNext" class="secondary" ${reportStale?'disabled':''}>${safeText(commandText(6))}</button><button id="commandReset" class="ghost">${safeText(commandText(7))}</button></div><p class="ai-command-foot">${safeText(commandText(15))}</p></div>
 <div class="ai-command-focus"><span class="ai-command-caption">${safeText(commandText(8))} · ÖRNEK</span><h3>${safeText(demoGuestName(booking?.id))}</h3><p>${safeText(booking?.id)} · ${safeText(channelName[booking?.channel])}</p><dl><div><dt>Check-in</dt><dd>${safeText(booking?.arrival)}</dd></div><div><dt>Check-out</dt><dd>${safeText(booking?.departure)}</dd></div><div><dt>${safeText(commandText(10))}</dt><dd>${safeText(step?.evidence?.[0]?.value||story.final_status)}</dd></div></dl><span class="ai-command-human">${icon('shield')} ${safeText(commandText(11))}</span></div></div>
 </section>`;
}
function operationsSnapshotCharts(){
 const dates=timelineDates();const rooms=state.rooms.length||1;
 const booked=dates.map(day=>new Set(state.reservations.filter(b=>b.status!=='cancelled'&&b.room_id&&b.arrival<=day&&b.departure>day).map(b=>b.room_id)).size);
 const channels={};for(const b of state.reservations){if(b.status==='cancelled')continue;const n=channelName[b.channel]||b.channel;channels[n]=(channels[n]||0)+1;}
 const top=Object.entries(channels).sort((a,b)=>b[1]-a[1]).slice(0,5),max=Math.max(1,...top.map(c=>c[1]));
 return `<div id="opsSnapshotCharts" class="ai-charts"><section class="panel"><div class="panel-head"><div><h2>${esc(commandText(12))}</h2><p>${esc(commandText(14))} · ${rooms} demo oda</p></div></div><div class="ai-chart-bars" role="img" aria-label="${esc(commandText(12))}">${dates.map((day,i)=>`<div class="ai-chart-column" title="${esc(day)}: ${booked[i]}/${rooms}"><span>${booked[i]}</span><div class="ai-chart-track"><i style="height:${100*booked[i]/rooms}%"></i></div><small>${esc(day.slice(5))}</small></div>`).join('')}</div></section><section class="panel"><div class="panel-head"><div><h2>${esc(commandText(13))}</h2><p>${esc(commandText(14))} · ${state.reservations.length} kayıt</p></div></div><div class="ai-chart-channel">${top.map(([name,count])=>`<div><span>${esc(name)}</span><div class="ai-chart-track-horizontal"><i style="width:${100*count/max}%"></i></div><strong>${count}</strong></div>`).join('')}</div></section></div>`;
}
