/* Aurora graphical room plan: display precomputed Python facts, never allocate. */
'use strict';
const auroraRoomFilters={floor:'all',category:'all',state:'all',search:''};
const auroraStateSymbols={occupied:'●',vacant_unverified:'○',expected_arrival:'↘',expected_departure:'↗',blocked:'⊘',out_of_order:'◇',out_of_service:'◇',conflict:'!'};
function auroraRoomLocale(){return typeof opsState!=='undefined'?opsState.lang:'tr';}
function auroraRoomText(key){return AURORA_ROOM_TEXT[auroraRoomLocale()]?.[key]||AURORA_ROOM_TEXT.en[key]||key;}
function auroraRoomNumber(value){return new Intl.NumberFormat(auroraRoomLocale()).format(value);}
function auroraRoomDate(value){return new Intl.DateTimeFormat(auroraRoomLocale(),{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(value+'T12:00:00Z'));}
function auroraRoomCategory(value){return auroraRoomText('category_'+value);}
function auroraRoomSource(){
 if(typeof AURORA_ROOM_GRAPH!=='object'||!AURORA_ROOM_GRAPH||typeof CANONICAL_LINKS!=='object')return null;
 return AURORA_ROOM_GRAPH.schema_version==='aurora-room-graph.v1'&&AURORA_ROOM_GRAPH.canonical_sha256===CANONICAL_LINKS.canonical_sha256&&AURORA_ROOM_GRAPH.as_of===CANONICAL_LINKS.as_of&&Array.isArray(AURORA_ROOM_GRAPH.rooms)?AURORA_ROOM_GRAPH:null;
}
function auroraVisibleRooms(){
 const source=auroraRoomSource();if(!source)return[];
 const query=auroraRoomFilters.search.trim().toLocaleLowerCase(auroraRoomLocale());
 return source.rooms.filter(room=>(auroraRoomFilters.floor==='all'||String(room.floor)===auroraRoomFilters.floor)
  &&(auroraRoomFilters.category==='all'||room.category===auroraRoomFilters.category)
  &&(auroraRoomFilters.state==='all'||room.state_codes.includes(auroraRoomFilters.state))
  &&(!query||[room.id,...room.reservation_ids,...room.guest_labels].join(' ').toLocaleLowerCase(auroraRoomLocale()).includes(query)));
}
function auroraRoomAxes(room){
 const clean=room.housekeeping_cleanliness||'unknown';
 return '<span class="aurora-axis-stack">'+[
  ['occupancy',auroraRoomText('occupancy'),auroraRoomText(room.occupancy_state==='occupied'?'occupied':'unknown')],
  ['housekeeping',auroraRoomText('housekeeping'),auroraRoomText(clean)],
  ['allocation',auroraRoomText('allocation'),auroraRoomText(room.assignment_state)]
 ].map(([axis,label,value])=>'<span class="aurora-axis" data-axis="'+axis+'"><span>'+esc(label)+'</span><b>'+esc(value)+'</b></span>').join('')+'</span>';
}
function auroraRoomCard(room){
 const evidence=new Set(storyRoomIds()).has(room.id);
 const codes=room.state_codes.map(code=>'<span class="aurora-room-status" data-state="'+esc(code)+'"><i aria-hidden="true">'+esc(auroraStateSymbols[code]||'·')+'</i>'+esc(auroraRoomText(code))+'</span>').join('')+
  (room.review_status==='blocked'?'<span class="aurora-room-status" data-state="review_required"><i aria-hidden="true">!</i>'+esc(auroraRoomText('review_required'))+'</span>':'');
 const label=auroraRoomText('room')+' '+room.id+' · '+auroraRoomText('selectRoom');
 return '<button type="button" class="room aurora-room-card" data-room="'+esc(room.id)+'" data-occupancy="'+esc(room.occupancy_state)+'" data-housekeeping="'+esc(room.housekeeping)+'" data-assignment="'+esc(room.assignment_state)+'" data-state-codes="'+esc(JSON.stringify(room.state_codes))+'" data-ai-evidence="'+String(evidence)+'" aria-pressed="'+String(detail===room.id)+'" aria-label="'+esc(label)+'">'+
  '<span class="aurora-card-top"><span><strong><bdi>'+esc(room.id)+'</bdi></strong><small>'+esc(auroraRoomCategory(room.category))+' · '+esc(auroraRoomText('bed_'+room.bed))+'</small></span><span class="aurora-room-capacity">'+esc(auroraRoomText('capacity'))+' <b>'+esc(auroraRoomNumber(room.capacity))+'</b><br>'+esc(auroraRoomText('people'))+' '+esc(auroraRoomNumber(room.assigned_people))+'</span></span>'+
  auroraRoomAxes(room)+'<span class="aurora-room-statuses" aria-label="'+esc(auroraRoomText('operationalStates'))+'">'+codes+'</span>'+
  '<span class="aurora-room-guest"><b>'+(room.reservation_ids.length?room.reservation_ids.map(id=>'<bdi>'+esc(id)+'</bdi>').join(' · '):esc(auroraRoomText('none')))+'</b>'+esc(room.guest_labels.slice(0,2).join(' · '))+'</span>'+
  '<span class="aurora-room-foot"><span>'+esc(auroraRoomText('details'))+' ↗</span><span>'+esc(auroraRoomText('evidence'))+' '+esc(auroraRoomNumber(room.reason_codes.length))+'</span></span></button>';
}
function auroraRoomGroups(){
 const rooms=auroraVisibleRooms();if(!rooms.length)return '<div class="aurora-room-empty">'+esc(auroraRoomText('empty'))+'</div>';
 const floors=[...new Set(rooms.map(room=>room.floor))].sort((a,b)=>a-b);
 return floors.map(floor=>{const rows=rooms.filter(room=>room.floor===floor);return '<section class="aurora-floor" data-floor="'+esc(floor)+'"><h3>'+esc(auroraRoomText('floor'))+' '+esc(auroraRoomNumber(floor))+' <small>'+esc(auroraRoomNumber(rows.length))+' '+esc(auroraRoomText('rooms'))+'</small></h3><div class="aurora-room-grid">'+rows.map(auroraRoomCard).join('')+'</div></section>';}).join('');
}
function auroraRoomPlanView(){
 const source=auroraRoomSource(),stale=typeof reportStale!=='undefined'&&reportStale;
 const state=source?(stale?'stale':'synthetic_snapshot'):'source_not_connected';
 const symbol='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true"><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(-35 12 12)"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="1"/></svg>';
 let html='<section id="auroraRoomPlan" class="aurora-room-plan" data-i18n-skip data-source-state="'+state+'" aria-labelledby="auroraRoomTitle"><header class="aurora-room-hero"><div class="aurora-room-heading"><div class="aurora-room-kicker">'+symbol+'AURORA / '+esc(auroraRoomText('room'))+'</div><h2 id="auroraRoomTitle">'+esc(auroraRoomText('title'))+'</h2><p>'+esc(auroraRoomText('subtitle'))+'</p></div><span class="aurora-source-chip"><i aria-hidden="true"></i>'+esc(auroraRoomText('fictional'))+'</span></header>';
 html+='<div class="aurora-room-boundary" data-stale="'+String(stale)+'" role="status">'+esc(auroraRoomText(!source?'sourceMissing':stale?'stale':'physicalUnknown'))+'<br>'+esc(auroraRoomText('readOnly'))+' · <code>'+state+'</code></div>';
 if(!source)return html+'<p class="aurora-room-empty">'+esc(auroraRoomText('sourceMissing'))+'</p></section>';
 const select=(id,key,values,current)=>'<label class="aurora-filter" for="'+id+'">'+esc(auroraRoomText(key))+'<select id="'+id+'" aria-controls="auroraRoomGroups">'+values.map(([value,label])=>'<option value="'+esc(value)+'"'+(current===value?' selected':'')+'>'+esc(label)+'</option>').join('')+'</select></label>';
 const floors=[...new Set(source.rooms.map(room=>room.floor))].sort((a,b)=>a-b);
 const categories=[...new Set(source.rooms.map(room=>room.category))];
 const states=['occupied','vacant_unverified','expected_arrival','expected_departure','blocked','out_of_order','out_of_service','conflict'];
 html+='<div class="aurora-room-toolbar" role="group" aria-label="'+esc(auroraRoomText('filters'))+'">'+
  select('auroraFloorFilter','floor',[['all',auroraRoomText('allFloors')],...floors.map(floor=>[String(floor),auroraRoomText('floor')+' '+auroraRoomNumber(floor)])],auroraRoomFilters.floor)+
  select('auroraCategoryFilter','category',[['all',auroraRoomText('allCategories')],...categories.map(category=>[category,auroraRoomCategory(category)])],auroraRoomFilters.category)+
  select('auroraStateFilter','operationalStates',[['all',auroraRoomText('allStates')],...states.map(state=>[state,auroraRoomText(state)])],auroraRoomFilters.state)+
  '<label class="aurora-filter search" for="auroraRoomSearch">'+esc(auroraRoomText('search'))+'<input id="auroraRoomSearch" type="search" autocomplete="off" value="'+esc(auroraRoomFilters.search)+'" placeholder="'+esc(auroraRoomText('searchPlaceholder'))+'" aria-controls="auroraRoomGroups"></label><button type="button" class="secondary" id="auroraResetFilters">'+esc(auroraRoomText('resetFilters'))+'</button></div>';
 html+='<div class="aurora-room-stats"><span id="auroraRoomCount" role="status" aria-live="polite">'+esc(auroraRoomText('shown'))+' <strong>'+esc(auroraRoomNumber(auroraVisibleRooms().length))+' / '+esc(auroraRoomNumber(source.rooms.length))+'</strong> '+esc(auroraRoomText('rooms'))+'</span><span>'+esc(auroraRoomText('sourceLabel'))+' · <bdi title="'+esc(source.as_of)+'">'+esc(auroraRoomDate(source.as_of))+'</bdi></span></div><div id="auroraRoomGroups">'+auroraRoomGroups()+'</div></section>';
 return html;
}
// Extend the current room route, retaining its established timeline and drawers.
roomView=function(){return auroraRoomPlanView()+timelineView(false);};
function auroraRefreshRooms(){
 const groups=document.getElementById('auroraRoomGroups');if(!groups)return;
 groups.innerHTML=auroraRoomGroups();
 groups.querySelectorAll('.aurora-room-card').forEach(button=>button.addEventListener('click',()=>showRoom(button.dataset.room)));
 const count=document.getElementById('auroraRoomCount'),source=auroraRoomSource();
 if(count&&source)count.innerHTML=esc(auroraRoomText('shown'))+' <strong>'+esc(auroraRoomNumber(auroraVisibleRooms().length))+' / '+esc(auroraRoomNumber(source.rooms.length))+'</strong> '+esc(auroraRoomText('rooms'));
}
document.getElementById('content').addEventListener('input',event=>{
 if(event.target.id==='auroraRoomSearch'){auroraRoomFilters.search=event.target.value;auroraRefreshRooms();}
});
document.getElementById('content').addEventListener('change',event=>{
 const key={auroraFloorFilter:'floor',auroraCategoryFilter:'category',auroraStateFilter:'state'}[event.target.id];
 if(key){auroraRoomFilters[key]=event.target.value;auroraRefreshRooms();}
});
document.getElementById('content').addEventListener('click',event=>{
 if(event.target.closest('#auroraResetFilters')){
  Object.assign(auroraRoomFilters,{floor:'all',category:'all',state:'all',search:''});
  for(const id of ['auroraFloorFilter','auroraCategoryFilter','auroraStateFilter'])document.getElementById(id).value='all';
  document.getElementById('auroraRoomSearch').value='';auroraRefreshRooms();
 }
});
document.getElementById('resetButton').addEventListener('click',()=>{
 Object.assign(auroraRoomFilters,{floor:'all',category:'all',state:'all',search:''});
},true);
const auroraOriginalCloseDetail=closeDetail;
closeDetail=function(){
 auroraOriginalCloseDetail();
 document.querySelectorAll('.aurora-room-card[aria-pressed="true"]').forEach(card=>card.setAttribute('aria-pressed','false'));
};
const auroraOriginalShowRoom=showRoom;
showRoom=function(id){
 auroraOriginalShowRoom(id);
 const source=auroraRoomSource(),room=source?.rooms.find(room=>room.id===id);if(!room)return;
 const drawer=document.getElementById('drawer');if(!drawer||!document.getElementById('backdrop').classList.contains('open'))return;
 // The historical drawer classified every non-inspected/non-dirty value as
 // technical closure. Clean/in-progress are cleaning states, not closures.
 if(['clean','in_progress'].includes(room.housekeeping)){
  const cleaning=drawer.querySelector(':scope > p[style]');
  if(cleaning){cleaning.textContent=auroraRoomText(room.housekeeping);cleaning.dataset.auroraCleaningStatus=room.housekeeping;}
 }
 const panel=document.createElement('section');panel.className='aurora-room-detail';panel.dataset.auroraRoomDetail=id;panel.setAttribute('data-i18n-skip','');
 panel.innerHTML='<strong>'+esc(auroraRoomText('sourceLabel'))+' · '+esc(auroraRoomDate(source.as_of))+'</strong>'+auroraRoomAxes(room)+'<p>'+esc(auroraRoomText(reportStale?'stale':'readOnly'))+'</p>';
 drawer.querySelector('h2')?.after(panel);
 document.querySelectorAll('.aurora-room-card').forEach(card=>card.setAttribute('aria-pressed',String(card.dataset.room===id)));
};
