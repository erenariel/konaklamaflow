/* Decision evidence trail: presentation of Python-precomputed, fictional facts.
 * It is NOT the #53 hash-chain audit log and never records staff events.
 * No fetch, writes, storage, approval, generated decisions or live AI. */
(function mountDecisionEvidenceTrail(){
 'use strict';
 const panel=document.getElementById('v04Global');
 const select=document.getElementById('v04Booking');
 const language=document.getElementById('v04Locale');
 const state=document.getElementById('v04State');
 const footer=document.getElementById('v04Footer');
 if(!panel||!select||!language||!state||!footer)return;
 const COPY={
  tr:['Karar kanıt yolu','Kurgusal Python raporu · Salt okunur · Gerçek audit kaydı değildir','Kaynak → Kural → Kanıt → İnsan incelemesi','Örnek kaynak','Kural kararı','Kanıt alanları','Personel sınırı','Kaynak veya karar tutarsız; iz gösterilmiyor.','Henüz gerçek onay ya da işlem yapılmadı.','Kaynak zamanı/doğruluğu bağımsız doğrulanmadı.','Kayıt bulunamadı','Gerekçe yok; bu durum gerçek check-in izni vermez.'],
  en:['Decision evidence trail','Fictional Python report · Read-only · Not an actual audit log','Source → Rule → Evidence → Human review','Sample source','Rule decision','Evidence fields','Staff boundary','Source or decision inconsistent; trail hidden.','No real approval or operation occurred.','Source time and validity not independently verified.','No matching record','No reason codes; this is not check-in authorization.'],
  fr:['Parcours des preuves','Rapport Python fictif · Lecture seule · Pas un journal d’audit réel','Source → Règles → Preuves → Examen humain','Source fictive','Décision des règles','Champs de preuve','Contrôle humain','Source ou décision incohérente ; parcours masqué.','Aucune validation ou opération réelle.','Source non vérifiée indépendamment.','Aucune trace','Aucun code ; cela n’autorise pas l’arrivée.'],
  de:['Entscheidungsnachweis','Fiktiver Python-Bericht · Nur Lesen · Kein echtes Auditprotokoll','Quelle → Regeln → Belege → Mensch','Beispielquelle','Regelergebnis','Belegfelder','Personalprüfung','Quelle oder Entscheidung unklar; Anzeige gesperrt.','Keine echte Freigabe oder Aktion.','Quelle unabhängig nicht geprüft.','Kein Eintrag','Keine Codes; keine Check-in-Freigabe.'],
  el:['Ίχνος τεκμηρίωσης','Εικονική αναφορά Python · Μόνο ανάγνωση · Όχι πραγματικός έλεγχος','Πηγή → Κανόνες → Στοιχεία → Προσωπικό','Εικονική πηγή','Απόφαση κανόνων','Πεδία στοιχείων','Ανθρώπινος έλεγχος','Ασυνεπής πηγή ή απόφαση· το ίχνος κρύφτηκε.','Δεν έγινε πραγματική έγκριση ή ενέργεια.','Μη επαληθευμένη πηγή.','Δεν υπάρχει καταχώριση','Χωρίς αιτιολογίες· όχι άδεια check-in.'],
  he:['מסלול ראיות להחלטה','דוח Python מדומה · לקריאה בלבד · לא יומן ביקורת אמיתי','מקור ← כללים ← ראיות ← צוות','מקור לדוגמה','החלטת הכללים','שדות ראיות','בדיקת צוות','המקור או ההחלטה אינם תואמים; המסלול מוסתר.','לא בוצעו אישור או פעולה אמיתיים.','המקור לא אומת באופן עצמאי.','לא נמצאה רשומה','אין סיבות; אין הרשאת צ׳ק-אין.'],
  ar:['مسار أدلة القرار','تقرير Python افتراضي · للقراءة فقط · ليس سجل تدقيق حقيقي','المصدر ← القواعد ← الأدلة ← الموظف','مصدر تجريبي','قرار القواعد','حقول الأدلة','مراجعة بشرية','تعارض في المصدر أو القرار؛ تم إخفاء المسار.','لم تحدث موافقة أو عملية حقيقية.','المصدر غير موثق بشكل مستقل.','لا يوجد سجل','لا أسباب؛ لا يسمح بتسجيل الوصول.'],
  es:['Rastro de evidencias','Informe Python ficticio · Solo lectura · No es auditoría real','Fuente → Reglas → Pruebas → Personal','Fuente ficticia','Decisión de reglas','Campos de prueba','Revisión humana','Fuente o decisión incoherente; rastro oculto.','No hubo aprobación ni operación real.','Fuente sin verificación independiente.','Sin registro','Sin códigos; no autoriza el check-in.'],
  ru:['След принятия решения','Вымышленный отчёт Python · Только чтение · Не журнал аудита','Источник → Правила → Доказательства → Сотрудник','Тестовый источник','Решение правил','Поля доказательств','Контроль сотрудника','Источник или решение не совпадают; данные скрыты.','Реального одобрения или операции не было.','Источник не проверен независимо.','Запись отсутствует','Кодов нет; не разрешает заселение.'],
  uk:['Шлях доказів рішення','Вигаданий звіт Python · Лише читання · Не журнал аудиту','Джерело → Правила → Докази → Персонал','Джерело прикладу','Рішення правил','Поля доказів','Контроль персоналу','Дані або рішення не узгоджені; шлях приховано.','Реального схвалення чи дії не було.','Джерело не перевірено незалежно.','Запис відсутній','Без кодів; це не дозвіл на заселення.']
 };
 const root=document.createElement('section');
 root.className='kf-decision-evidence';
 root.id='kfDecisionEvidence';
 root.setAttribute('aria-labelledby','kfDecisionEvidenceTitle');
 const head=document.createElement('div');
 head.className='kf-decision-evidence-head';
 const heading=document.createElement('h3');
 heading.id='kfDecisionEvidenceTitle';
 const sub=document.createElement('p');
 sub.id='kfDecisionEvidenceNote';
 head.append(heading,sub);
 const status=document.createElement('p');
 status.id='kfDecisionEvidenceStatus';
 status.setAttribute('role','status');
 status.setAttribute('aria-live','polite');
 const path=document.createElement('ol');
 path.className='kf-decision-evidence-path';
 path.id='kfDecisionEvidencePath';
 root.append(head,status,path);
 panel.insertBefore(root,footer);

 function textNode(parent,tag,value,klass){
  const el=document.createElement(tag);
  if(klass)el.className=klass;
  el.textContent=String(value);
  parent.append(el);
  return el;
 }
 function entry(label,items,kind){
  const li=document.createElement('li');
  li.className='kf-decision-evidence-step';
  li.dataset.traceStep=kind;
  textNode(li,'strong',label,'kf-decision-step-title');
  const list=document.createElement('div');
  list.className='kf-decision-step-values';
  for(const [value,code] of items){
   const node=textNode(list,code?'code':'span',value,code?'kf-decision-code':'kf-decision-text');
   if(code)node.dir='ltr';
  }
  li.append(list);
  path.append(li);
 }
 function render(){
  const copy=COPY[language.value]||COPY.en;
  heading.textContent=copy[0];
  sub.textContent=copy[1];
  path.replaceChildren();
  const report=typeof INITIAL_EVALUATION!=='undefined'?INITIAL_EVALUATION:null;
  const catalog=typeof V04_CATALOG!=='undefined'?V04_CATALOG:null;
  const row=report?.arrivals?.find(item=>item.task_id===select.value);
  const codes=row?.blockers;
  const valid=typeof reportStale==='boolean'&&!reportStale
    &&report?.mode==='DRY_RUN_ONLY'
    &&typeof report.snapshot_sha256==='string'
    &&/^[a-f0-9]{64}$/.test(report.snapshot_sha256)
    &&catalog?.sourceSha===report.snapshot_sha256
    &&Array.isArray(catalog.codes)
    &&typeof row?.task_id==='string'&&/^[a-f0-9]{24}$/.test(row.task_id)
    &&row.human_approval_required===true
    &&Array.isArray(codes)&&new Set(codes).size===codes.length
    &&codes.every(code=>typeof code==='string'
      &&catalog.codes.includes(code)
      &&Array.isArray(catalog.evidence?.[code])
      &&catalog.evidence[code].every(field=>typeof field==='string'
        &&/^[a-zA-Z][\w.\[\]]{0,90}$/.test(field)))
    &&Array.isArray(report.arrivals)
    &&report.arrivals.every(item=>item.human_approval_required===true)
    &&row.status===(codes.length?'blocked':'review_ready');
  root.dataset.sourceState=valid?'source_bound':'unverified';
  status.textContent=valid?copy[2]:copy[7];
  if(!valid)return;
  const evidence=[...new Set(codes.flatMap(code=>catalog.evidence[code]))];
  entry(copy[3],[
   ['SHA-256: '+report.snapshot_sha256.slice(0,16)+'…',true],
   [copy[9],false]
  ],'source');
  entry(copy[4],[
   ['task '+row.task_id.slice(0,12)+'…',true],
   ...(codes.length?codes.map(code=>[code,true]):[[copy[11],false]])
  ],'rules');
  entry(copy[5],evidence.length?evidence.map(f=>[f,true]):[[copy[10],false]],'evidence');
  entry(copy[6],[[copy[8],false]],'staff');
 }
 select.addEventListener('change',render);
 language.addEventListener('change',render);
 const observedState=new MutationObserver(render);
 observedState.observe(state,{childList:true,characterData:true,subtree:true});
 observedState.observe(select,{attributes:true,attributeFilter:['disabled']});
 render();
})();
