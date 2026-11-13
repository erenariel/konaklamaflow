/* KonaklamaFlow v0.5.1 full-page locale coordination.
 * No external translation services, private text sent nowhere.
 * Display strings only; never change report, folio or approval logic.
 */
'use strict';
const fullUiLocales=['tr','en','fr','el','he','ar','de','ru','es','uk'];
const fullUiMenu={
tr:['Genel Bakış','Gelişler ve Check-in','OTA & Kanal Yönetimi','Oda Planı','Housekeeping','Misafir Deneyimi','Görev Merkezi','Gelir ve Dağıtım','AI Karar Merkezi','Entegrasyonlar','Rezervasyonlar','Misafirler','Aktif Folyolar','Acente Alacakları','Rapor Merkezi','Kurlar ve Fatura','Blokajlar','Demirbaşlar'],
en:['Overview','Arrivals & Check-in','OTA & Channels','Room Plan','Housekeeping','Guest Experience','Task Center','Revenue & Distribution','AI Decision Center','Integrations','Reservations','Guests','Open Folios','Agency Receivables','Report Center','FX & Invoicing','Room Blocks','Room Assets'],
fr:['Vue d’ensemble','Arrivées et check-in','OTA et canaux','Plan des chambres','Entretien ménager','Expérience client','Centre des tâches','Revenus et distribution','Centre de décision IA','Intégrations','Réservations','Clients','Folios ouverts','Créances des agences','Centre des rapports','Devises et factures','Blocages des chambres','Équipements des chambres'],
el:['Επισκόπηση','Αφίξεις και check-in','OTA και κανάλια','Πλάνο δωματίων','Καθαριότητα','Εμπειρία επισκέπτη','Κέντρο εργασιών','Έσοδα και διανομή','Κέντρο αποφάσεων AI','Διασυνδέσεις','Κρατήσεις','Επισκέπτες','Ανοιχτοί λογαριασμοί','Οφειλές πρακτορείων','Κέντρο αναφορών','Συνάλλαγμα και τιμολόγηση','Δεσμεύσεις δωματίων','Εξοπλισμός δωματίων'],
he:['סקירה כללית','הגעות וצ׳ק-אין','OTA וערוצי מכירה','תוכנית חדרים','משק בית','חוויית אורח','מרכז משימות','הכנסות והפצה','מרכז החלטות AI','ממשקים','הזמנות','אורחים','חשבונות פתוחים','חובות סוכנויות','מרכז דוחות','מטבע וחשבוניות','חסימות חדרים','ציוד חדרים'],
ar:['نظرة عامة','الوصول وتسجيل الدخول','وكالات الإنترنت والقنوات','مخطط الغرف','التدبير المنزلي','تجربة الضيف','مركز المهام','الإيرادات والتوزيع','مركز قرارات AI','التكاملات','الحجوزات','الضيوف','الحسابات المفتوحة','مستحقات الوكالات','مركز التقارير','العملات والفواتير','حظر الغرف','تجهيزات الغرف'],
de:['Übersicht','Anreisen und Check-in','OTA und Kanäle','Zimmerplan','Housekeeping','Gästeerlebnis','Aufgabenzentrale','Umsatz und Vertrieb','KI-Entscheidungszentrum','Integrationen','Reservierungen','Gäste','Offene Folios','Agenturforderungen','Berichtszentrale','Wechselkurse und Rechnungen','Zimmerblockierungen','Zimmerausstattung'],
ru:['Обзор','Заезды и регистрация','OTA и каналы','План номеров','Уборка','Гостевой сервис','Центр задач','Доходы и каналы','Центр решений ИИ','Интеграции','Бронирования','Гости','Открытые фолио','Долги агентств','Центр отчётов','Валюты и счета','Блокировки номеров','Оснащение номеров'],
es:['Resumen','Llegadas y check-in','OTA y canales','Plan de habitaciones','Limpieza','Experiencia del huésped','Centro de tareas','Ingresos y distribución','Centro de decisiones de IA','Integraciones','Reservas','Huéspedes','Folios abiertos','Cuentas por cobrar de agencias','Centro de informes','Divisas y facturación','Bloqueos de habitaciones','Equipamiento de habitaciones'],
uk:['Огляд','Прибуття та реєстрація','OTA та канали','План номерів','Прибирання','Гостьовий сервіс','Центр завдань','Доходи й дистрибуція','Центр рішень ШІ','Інтеграції','Бронювання','Гості','Відкриті фоліо','Борги агенцій','Центр звітів','Валюти й рахунки','Блокування номерів','Оснащення номерів']
};
const fullUiNotes={
tr:'Kurgusal veriler · Salt okunur ön inceleme · Nihai işlemler yetkili personelde',
en:'Fictional data · Read-only pre-review · Final actions require authorized staff',
fr:'Données fictives · Pré-examen en lecture seule · Actions réservées au personnel habilité',
el:'Εικονικά δεδομένα · Προέλεγχος μόνο για ανάγνωση · Τελικές ενέργειες από εξουσιοδοτημένο προσωπικό',
he:'נתונים מדומים · בדיקה ראשונית לקריאה בלבד · אישור סופי בידי צוות מורשה',
ar:'بيانات افتراضية · مراجعة أولية للقراءة فقط · الإجراءات النهائية للموظفين المخولين',
de:'Fiktive Daten · Vorprüfung im Lesemodus · Freigabe nur durch befugtes Personal',
ru:'Тестовые данные · Предварительная проверка без записи · Итоговые действия только уполномоченным сотрудником',
es:'Datos ficticios · Revisión preliminar de solo lectura · Acciones finales por personal autorizado',
uk:'Тестові дані · Попередня перевірка без запису · Остаточні дії лише уповноваженого персоналу'
};
const fullUiMarker={
tr:'Taslak çeviriler · gerçek kişisel veri yok',
en:'Draft translations · no real personal data',
fr:'Traductions provisoires · aucune donnée personnelle réelle',
el:'Πρόχειρες μεταφράσεις · χωρίς πραγματικά προσωπικά δεδομένα',
he:'תרגומים בטיוטה · ללא מידע אישי אמיתי',
ar:'ترجمات أولية · دون بيانات شخصية حقيقية',
de:'Übersetzungsentwürfe · keine echten personenbezogenen Daten',
ru:'Черновые переводы · без реальных персональных данных',
es:'Traducciones provisionales · sin datos personales reales',
uk:'Чернетки перекладів · без справжніх персональних даних'
};
const fullUiPhrases={};
for(const code of fullUiLocales)fullUiPhrases[code]=new Map();
const fullUiFallbacks={};
function fullUiRows(rows){
 for(const row of rows){
   if(row.length!==10)throw new Error('Incomplete locale row');
   const [key,...phrases]=row;
   if(!key||phrases.some(p=>typeof p!=='string'||!p.trim()))throw new Error('Invalid locale entry');
   fullUiPhrases.tr.set(key,key);
   for(let i=1;i<10;i++)fullUiPhrases[fullUiLocales[i]].set(key,phrases[i-1]);
 }
}
function fullUiEnglishRows(rows){
 for(const [tr,en] of rows){
   if(!tr||!en)throw new Error('Incomplete fallback');
   if(!fullUiPhrases.en.has(tr))fullUiPhrases.en.set(tr,en);
 }
}
const fullUiSourceText=new WeakMap();
function fullUiTranslation(source,lang){
 const exact=fullUiPhrases[lang].get(source);
 if(exact)return exact;
 const english=fullUiPhrases.en.get(source);
 if(lang!=='tr'&&english){fullUiFallbacks[lang]=(fullUiFallbacks[lang]||0)+1;return english;}
 return source;
}
function fullUiTranslateTree(){
 const lang=(typeof opsState!=='undefined'&&fullUiLocales.includes(opsState.lang))?opsState.lang:'tr';
 fullUiFallbacks[lang]=0;
 const selector='body';
 const root=document.querySelector(selector);
 if(!root)return;
 const iter=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
 const nodes=[];
 for(let n=iter.nextNode();n;n=iter.nextNode()){
   if(!n.nodeValue||!n.nodeValue.trim())continue;
   const parent=n.parentElement;
   if(!parent||parent.closest('script,style,pre,code,svg,[data-i18n-skip],.v04-reasons,.v04-evidence'))continue;
   nodes.push(n);
 }
 for(const node of nodes){
    if(!fullUiSourceText.has(node))fullUiSourceText.set(node,node.nodeValue);
    const src=fullUiSourceText.get(node);
    const left=src.match(/^\s*/)[0],right=src.match(/\s*$/)[0],body=src.trim();
    const translated=fullUiTranslation(body,lang);
    node.nodeValue=left+translated+right;
 }
 for(const el of root.querySelectorAll('input[placeholder],textarea[placeholder],button[title],[aria-label]')){
   if(el.closest('.v04-panel'))continue;
   for(const attr of ['placeholder','title','aria-label']){
     if(!el.hasAttribute(attr))continue;
     const name='fullUiOriginal'+attr.charAt(0).toUpperCase()+attr.slice(1);
     if(!el.dataset[name])el.dataset[name]=el.getAttribute(attr);
     const original=el.dataset[name];
     const translated=fullUiTranslation(original,lang);
     if(translated!==original||lang==='tr')el.setAttribute(attr,translated);
   }
 }
 const marker=document.getElementById('fullUiTranslationMarker');
 if(marker){marker.textContent=fullUiMarker[lang];marker.lang=lang;}
 const dateEl=document.querySelector('.top-actions .date');
 if(dateEl){dateEl.textContent=new Intl.DateTimeFormat(lang,{weekday:'long',day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date('2026-11-12T12:00:00Z'));}
}
function fullUiSetMetadata(lang){
 if(!fullUiLocales.includes(lang))return;
 document.documentElement.lang=lang;
 document.documentElement.dir=(lang==='ar'||lang==='he')?'rtl':'ltr';
 const labels=fullUiMenu[lang];
 if(labels.length!==PAGE_LIST.length)throw new Error('Navigation/catalog mismatch');
 PAGE_LIST.forEach((row,index)=>{row[2]=labels[index];row[3]=labels[index];row[4]=fullUiNotes[lang]});
}
window.applyFullLocale=fullUiTranslateTree;
window.localizePageMetadata=fullUiSetMetadata;
