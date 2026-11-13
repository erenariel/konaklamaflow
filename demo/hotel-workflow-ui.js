/* KonaklamaFlow illustrated hotel workflows + staff ID panel.
 * Proprietary vendor UI not copied. No auth token, PII, network, writes or storage.
 */
'use strict';
const wfOperators=[
 {id:'DEMO-REC-001',login:'sample.reception',name:'Sample Reception',dept:'Front Office',role:'reception'},
 {id:'DEMO-HK-002',login:'sample.housekeeping',name:'Sample Housekeeping',dept:'Housekeeping',role:'housekeeping'},
 {id:'DEMO-FIN-003',login:'sample.finance',name:'Sample Finance',dept:'Accounting',role:'finance'},
 {id:'DEMO-MGR-004',login:'sample.manager',name:'Sample Manager',dept:'Management',role:'manager'},
 {id:'DEMO-AUD-005',login:'sample.auditor',name:'Sample Auditor',dept:'Audit',role:'auditor'}
];
const wfVendors=[
 ['ElektraWeb','https://yardim.elektraweb.com/detayli-anlatim/onburo-kontrol-paneli'],
 ['Sistem Otel','https://sistemotel.gitbook.io/sistem-otel-kullanim-klavuzu'],
 ['Sedna','https://kod.com.tr/Product/SednaHotel']
];
const wfDefinitions=[
 ['reservation_intake','Rezervasyon ve grup taslağı','channel_reference,arrival_departure,room_capacity,staff_review','reception,manager','STAFF_REVIEW'],
 ['room_blocking','Oda planı ve blokaj','overlap_check,maintenance,housekeeping,category_match','reception,housekeeping,manager','STAFF_REVIEW'],
 ['arrival_preflight','Giriş hazırlığı','identity_review,room_readiness,folio_review,arrival_time','reception,manager','STAFF_REVIEW'],
 ['checkout_preflight','Çıkış ve bakiye','departure,folio_balance,agency_receivable,invoice_review','reception,finance,manager','STAFF_REVIEW'],
 ['folio_postings','Folyo ve posting','posting_types,payment_separation,currency,reconciliation','finance,manager','STAFF_REVIEW'],
 ['agency_credit','Acente ve City Ledger','legal_entity,credit_terms,invoice_policy,aging','finance,manager','STAFF_REVIEW'],
 ['night_audit','Gün sonu ve audit','arrivals,departures,zero_rate,trial_balance,audit_lock','finance,manager','MISSING_TRUSTED_SOURCE'],
 ['housekeeping','Kat hizmetleri ve teknik bakım','room_cleanliness,work_orders,stock,supervisor_check','housekeeping,manager','STAFF_REVIEW'],
 ['rate_contracts','Fiyat, kontenjan ve allotment','agency_rates,release_day,stop_sale,room_nights','reception,manager','MISSING_TRUSTED_SOURCE'],
 ['guest_profile','Misafir profili ve KVKK/GDPR','identity_minimization,purpose,retention,role_scope','reception,manager','AUTHORIZATION_REQUIRED'],
 ['invoicing','Fatura ve mali uyum','invoice_region,tax_rules,exchange_source,fiscal_authority','finance,manager','MISSING_TRUSTED_SOURCE'],
 ['analytics','Doluluk, bütçe ve performans','room_nights,rate_plan,agency_segments,budget','finance,manager,auditor','STAFF_REVIEW'],
 ['handover','Personel devri ve görevler','task_owner,source_revision,shift_handover,audit_trace','reception,housekeeping,finance,manager','STAFF_REVIEW'],
 ['external_integrations','PMS, OTA, KBS entegrasyon sınırı','api_permissions,least_privilege,sandbox,human_approval','manager,auditor','AUTHORIZATION_REQUIRED']
].map(([id,name,checks,roles,status])=>({id,name,checks:checks.split(','),roles:roles.split(','),status}));
const wfState={operator:'DEMO-REC-001',selected:'reservation_intake',log:[],status:'not_started',scenario:'room_block',stage:0,timer:null,playing:false};
const wfRoleText={
tr:{title:'Personel & Oturum',workflows:'İş akışları',person:'Aktif demo personeli',login:'Giriş kimliği',staff:'Personel ID',role:'Görev',scopes:'Görüntüleme yetkisi',session:'Oturum durumu',notAuth:'Bu gerçek giriş veya kimlik doğrulaması değildir',action:'Kontrolleri göster',verify:'Kaynağı doğrula',decision:'İnsan onayı gerekli',source:'Sağlayıcı entegrasyonları',off:'Bağlı değil',scenario:'Operasyon simülasyonu',play:'Tüm senaryoları oynat',pause:'Durdur',next:'Sonraki adım',locked:'Üretim işlemi devre dışı',log:'Oturum içi işlem izi',noLog:'Henüz demo kaydı yok',status:'Durum',none:'Veri kaynağı bağlı değil',result:'Kural gerekçesi',nextStep:'Güvenli sonraki adım',demo:'Yalnızca kurgusal personel ve rezervasyonlar',type:'İş akışı',roleMissing:'Bu rolün görüntüleme izni yok',approved:'Check-in onayı değildir'},
en:{title:'Staff & Session',workflows:'Workflows',person:'Active demo staff',login:'Login ID',staff:'Staff ID',role:'Role',scopes:'View permissions',session:'Session status',notAuth:'This is not real authentication or sign-in',action:'Show checks',verify:'Verify source',decision:'Human approval required',source:'Provider integrations',off:'Not connected',scenario:'Operations simulation',play:'Play all scenarios',pause:'Stop',next:'Next step',locked:'Production actions disabled',log:'In-session action trace',noLog:'No demo action yet',status:'Status',none:'No live source connected',result:'Rule reason',nextStep:'Next safe step',demo:'Fictional staff and bookings only',type:'Workflow',roleMissing:'This role cannot view that workflow',approved:'Not a check-in approval'}
};
function wfT(key){return (wfRoleText[typeof opsState==='object'?opsState.lang:'tr']||wfRoleText.en)[key]||wfRoleText.en[key]||key;}
function wfOperator(){return wfOperators.find(p=>p.id===wfState.operator)||wfOperators[0];}
function wfAllowed(flow){return flow.roles.includes(wfOperator().role);}
function wfRenderProfile(){
 const u=wfOperator();
 const capabilities={reception:['room_read','booking_read','guest_safe_read','folio_safe_read','request_draft'],housekeeping:['room_read','hk_read','maintenance_read','request_draft'],finance:['folio_safe_read','ledger_read','reports_read','request_draft'],manager:['room_read','booking_read','guest_safe_read','folio_safe_read','hk_read','ledger_read','reports_read','review_requests','request_draft'],auditor:['room_read','booking_read','folio_safe_read','ledger_read','reports_read','audit_read']};
 const opts=wfOperators.map(x=>'<option value="'+x.id+'"'+(u.id===x.id?' selected':'')+'>'+x.id+' · '+x.dept+'</option>').join('');
 return '<div class="wf-grid"><section class="ops-card"><h3>'+wfT('title')+'</h3><p class="ops-notice">'+wfT('notAuth')+'</p><label>'+wfT('person')+'<select id="wfOperator">'+opts+'</select></label>'+
 '<div class="ops-grid2">'+[['ID',u.id],[wfT('login'),u.login],[wfT('role'),u.role],[wfT('session'),'SYNTHETIC_OFFLINE'],['Department',u.dept],['Tenant','SAMPLE_HOTEL_01']].map(([key,val])=>'<div><small>'+key+'</small><strong>'+val+'</strong></div>').join('')+'</div>'+
 '<h4>'+wfT('scopes')+'</h4><div class="wf-chips">'+capabilities[u.role].map(x=>'<code>'+x+'</code>').join('')+'</div>'+
 '<p class="ops-notice">'+wfT('locked')+' · MFA / RBAC / audit-log backend NOT CONNECTED</p></section>'+
 '<section class="ops-card"><h3>'+wfT('log')+'</h3><div id="wfAuditLog" aria-live="polite">'+(wfState.log.length?wfState.log.slice(-12).reverse().map((entry,i)=>'<p class="wf-event"><b>'+String(i+1)+'. </b>'+entry+'</p>').join(''):'<p>'+wfT('noLog')+'</p>')+'</div><p class="ops-note">Her işlem geçici tarayıcı belleğindedir. Gerçek kullanıcı oturumu, kalıcı audit veya yetki sağlamaz.</p></section></div>';
}
const wfScenarios=[
 {id:'room_block',name:'Oda çakışması',steps:['Rezervasyon ve oda tarihleri kontrol edilir','Çakışan tahsis engeli bulundu','Kat hizmetleri ve bakım durumu yeniden kontrol edilir','Oda değiştirme önerisi yalnız taslak olarak sunulur','Yetkili resepsiyon personeline inceleme devredilir'],why:'ROOM_CONFLICT · NO_ASSIGNED_ROOM',next:'Uygun oda ve tarihleri gerçek PMS içinde insan doğrular'},
 {id:'payment',name:'Ödeme / folyo uyarısı',steps:['Folyo posting toplamları okunur','Tahsilat, City Ledger alacağından ayrılır','Eksik bakiye veya yanlış para birimi kontrol edilir','İptal/iade işlemi yetkisi gösterilmez','Yetkili finans personelinden mutabakat istenir'],why:'PAYMENT_REVIEW · FOLIO_BALANCE',next:'Banka ve folyo bakiyesi gerçek kaynaktan doğrulanır'},
 {id:'identity',name:'Kimlik ve giriş kontrolü',steps:['Giriş tarihi doğrulanır','Kişi sayısı ve kapasite incelenir','Kimlik verisi yalnız yetkili sistemde doğrulanmalıdır','Check-in/KBS eylemi kasten engellenir','Personel inceleme sonucunu kaynağa işler'],why:'IDENTITY_STAFF_REVIEW · GUEST_NOT_ARRIVED',next:'Gerekli kimlik kontrolü yetkili kişi tarafından yapılır'},
 {id:'channel',name:'OTA kaynak uyuşmazlığı',steps:['Kanal referansı okunur','PMS rezervasyon eşleşmesi kontrol edilir','Çift referans veya iptal farkı tespit edilir','Düzeltme talebi onay için hazırlanır','Entegrasyon izni yoksa hiçbir kaynak değiştirilmez'],why:'CHANNEL_REFERENCE_MISMATCH · CHANNEL_STATUS_CONFLICT',next:'OTA ve PMS sistemlerinde ayrı ayrı teyit alınır'},
 {id:'maintenance',name:'Bakım ve oda hazırlığı',steps:['Oda temizliği durumu incelenir','Açık teknik iş emri tespit edilir','Oda bloke veya kirli ise girişe hazır değildir','Kat amiri ve teknik servis kontrolü istenir','Onay verilene kadar oda önerilmez'],why:'MAINTENANCE_TASK_OPEN · HOUSEKEEPING_NOT_INSPECTED',next:'Temizlik ve teknik onay gerçek PMS kaynağına işlenmelidir'}
];
function wfStop(){if(wfState.timer!==null)clearTimeout(wfState.timer);wfState.timer=null;wfState.playing=false;}
function wfRecord(message){wfState.log.push(message);if(wfState.log.length>25)wfState.log.shift();}
function wfStage(){
 const sc=wfScenarios.find(x=>x.id===wfState.scenario)||wfScenarios[0];
 const i=Math.max(0,Math.min(sc.steps.length-1,wfState.stage));
 return '<div class="wf-story"><div class="ops-grid2"><div><small>'+wfT('status')+'</small><strong>'+sc.name+' · '+(i+1)+'/'+sc.steps.length+'</strong></div><div><small>'+wfT('result')+'</small><strong>'+sc.why+'</strong></div></div>'+
 '<ol class="wf-steps">'+sc.steps.map((x,k)=>'<li class="'+(k===i?'wf-active':'')+'">'+x+'</li>').join('')+'</ol>'+
 '<p class="ops-notice">'+wfT('nextStep')+': '+sc.next+' · '+wfT('decision')+'</p></div>';
}
function wfView(pageId){
 if(pageId==='ops_staff')return '<section class="ops-view" id="wfView" lang="'+opsState.lang+'" dir="'+(['ar','he'].includes(opsState.lang)?'rtl':'ltr')+'">'+wfRenderProfile()+'</section>';
 if(pageId!=='ops_workflows')return '';
 const flow=wfDefinitions.find(f=>f.id===wfState.selected)||wfDefinitions[0];
 const options=wfDefinitions.map(x=>'<option value="'+x.id+'"'+(x.id===wfState.selected?' selected':'')+'>'+x.name+'</option>').join('');
 const allowed=wfAllowed(flow);
 const checks=flow.checks.map(c=>'<li><code dir="ltr">'+c+'</code></li>').join('');
 return '<section class="ops-view" id="wfView" lang="'+opsState.lang+'" dir="'+(['ar','he'].includes(opsState.lang)?'rtl':'ltr')+'"><div class="ops-stack">'+
 '<p class="ops-notice">'+wfT('demo')+' · '+wfT('notAuth')+' · '+wfT('locked')+'</p>'+
 '<div class="wf-grid"><section class="ops-card"><h3>'+wfT('workflows')+'</h3><label>'+wfT('type')+'<select id="wfFlow">'+options+'</select></label>'+
 '<div class="ops-grid2"><div><small>Workflow ID</small><strong>'+flow.id+'</strong></div><div><small>'+wfT('status')+'</small><strong>'+flow.status+'</strong></div></div>'+
 '<h4>AI-1 → PYTHON RULES → AI-2 → HUMAN</h4><ol>'+checks+'</ol>'+
 '<p class="ops-note">'+(allowed?wfT('decision'):wfT('roleMissing'))+'</p>'+
 '<button class="primary" type="button" id="wfPreview"'+(allowed?'':' disabled')+'>'+wfT('action')+'</button>'+
 '<div id="wfPreviewResult" role="status">'+wfT('none')+'</div></section>'+
 '<section class="ops-card"><h3>'+wfT('source')+'</h3>'+
 wfVendors.map(([name,url])=>'<div class="wf-vendor"><b>'+name+'</b> <span>'+wfT('off')+'</span> <small>NOT_CONNECTED · READ_ONLY</small></div>').join('')+
 '<p class="ops-note">Kaynak kılavuzları: ElektraWeb / Sistem Otel / Sedna. Sağlayıcı kimliği, erişim izni, audit ve veri minimizasyonu olmadan bağlanılmaz.</p></section></div>'+
 '<section class="ops-card"><h3>'+wfT('scenario')+'</h3><div class="ops-toolbar"><select id="wfScenario" aria-label="'+wfT('scenario')+'">'+
 wfScenarios.map(x=>'<option value="'+x.id+'"'+(x.id===wfState.scenario?' selected':'')+'>'+x.name+'</option>').join('')+'</select>'+
 '<button class="primary" id="wfPlay" type="button">'+(wfState.playing?wfT('pause'):wfT('play'))+'</button>'+
 '<button id="wfNext" type="button">'+wfT('next')+'</button>'+
 '<span>'+wfT('locked')+'</span></div>'+wfStage()+'</section></div></section>';
}
window.workflowView=wfView;
window.workflowProfileState=wfState;
(function wfBoot(){
 const root=document.getElementById('content');
 if(!root)return;
 root.addEventListener('change',event=>{
  if(event.target.id==='wfOperator'){wfStop();if(!wfOperators.some(x=>x.id===event.target.value))return;wfState.operator=event.target.value;wfRecord('DEMO ROLE SWITCH → '+wfState.operator);render();}
  if(event.target.id==='wfFlow'){wfState.selected=event.target.value;render();}
  if(event.target.id==='wfScenario'){wfStop();wfState.scenario=event.target.value;wfState.stage=0;render();}
 });
 root.addEventListener('click',event=>{
  const id=event.target.id;
  if(id==='wfPreview'){
   const flow=wfDefinitions.find(x=>x.id===wfState.selected);
   if(!flow||!wfAllowed(flow))return;
   wfRecord(wfOperator().id+' → '+flow.id+' / READ_ONLY_PREVIEW');
   const result=document.getElementById('wfPreviewResult');
   if(result)result.textContent=flow.status+' · '+flow.checks.join(' → ')+' · HUMAN_APPROVAL_REQUIRED · NO_LIVE_EXECUTION';
  }
  if(id==='wfNext'){wfStop();const sc=wfScenarios.find(x=>x.id===wfState.scenario);wfState.stage=(wfState.stage+1)%sc.steps.length;render();}
  if(id==='wfPlay'){
   if(wfState.playing){wfStop();render();return;}
   if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){wfState.stage=(wfState.stage+1)%5;render();return;}
   wfState.playing=true;render();
   wfState.timer=setTimeout(function tick(){
      if(!wfState.playing)return;
      wfState.stage++;
      const current=wfScenarios.find(x=>x.id===wfState.scenario);
      if(wfState.stage>=current.steps.length){
        const idx=wfScenarios.findIndex(x=>x.id===wfState.scenario);
        if(idx===wfScenarios.length-1){wfStop();wfState.stage=current.steps.length-1;wfRecord('SCENARIOS COMPLETE · NOTHING EXECUTED');render();return;}
        wfState.scenario=wfScenarios[idx+1].id;wfState.stage=0;
      }
      render();wfState.timer=setTimeout(tick,1700);
   },1700);
  }
 });
 const reset=document.getElementById('resetButton');
 reset?.addEventListener('click',()=>{wfStop();wfState.operator='DEMO-REC-001';wfState.stage=0;wfState.scenario='room_block';wfState.log=[];});
})();
