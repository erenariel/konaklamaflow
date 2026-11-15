"use strict";
/* Fictional, precomputed Python proposals. This UI never runs the solver or writes data. */
(() => {
  const data = window.ALLOCATION_SCENARIOS;
  if (!Array.isArray(data) || data.length === 0) return;
  const $ = (id) => document.getElementById(id);
  const select = $("scenario");
  const rooms = $("rooms");
  const stays = $("stays");
  const holds = $("holds");
  const outcome = $("outcome");
  const explanation = $("explanation");
  const calculate = $("calculate");
  const why = $("explain");
  const reset = $("reset");
  const prompt = $("prompt");
  const current = () => data.find((entry) => entry.id === select.value);
  const labels = {
    twin: "Twin / iki ayrı yatak", double: "Double / çift kişilik",
    single: "Single", flex: "Esnek", none: "Özel yatak talebi yok",
    proposed: "Öneri oluşturuldu", no_solution: "Uygun ortak çözüm bulunamadı",
    manual_review_required: "Personel incelemesi gerekli",
    inspected: "Kontrol edilmiş", clean: "Temiz", dirty: "Temizlik bekliyor",
    out_of_order: "Bakım dışı", out_of_service: "Hizmet dışı",
    verified_vacant: "Örnek veride doğrulanmış boş", unknown: "Bilinmiyor",
    occupied: "Dolu",
  };
  const reasons = {
    ALL_CONSTRAINTS_SATISFIED_IN_FICTIONAL_SNAPSHOT: "Kurgusal veri setindeki bütün zorunlu kısıtları karşılayan ortak bir öneri bulundu.",
    NO_FEASIBLE_PROPOSAL: "Seçilen tarihler, oda kategorisi, yatak, kapasite, bakım veya çakışma kısıtları nedeniyle bütün rezervasyonlara birlikte uygun oda bulunamadı.",
    ROOM_READINESS_UNVERIFIED: "İlgili odanın fiziksel doluluk veya hazırlık bilgisi doğrulanmamış. Otomatik uygun kabul edilmiyor.",
    HELD_ROOM_RELEASE_NOT_VERIFIED: "İptal/no-show gibi bir durum, oda blokajını kendiliğinden kaldırmaz. Manuel serbest bırakma doğrulanmalı.",
    SEARCH_LIMIT_REACHED: "Hesaplama sınırı aşıldı; kısmi plan gösterilmez.",
  };
  function el(tag, css, content) {
    const node = document.createElement(tag);
    if (css) node.className = css;
    if (content !== undefined) node.textContent = String(content);
    return node;
  }
  function field(label, value) {
    const cell = el("div", "field");
    cell.append(el("dt", "", label), el("dd", "", value));
    return cell;
  }
  function card(title, subtitle, cells, css) {
    const node = el("article", "tile " + (css || ""));
    node.append(el("h3", "", title), el("p", "sub", subtitle));
    const dl = el("dl", "fields");
    for (const [label, value] of cells) dl.append(field(label, value));
    node.append(dl);
    return node;
  }
  function describe(scenario) {
    const src = scenario.source;
    $("scenario-description").textContent = scenario.description;
    $("case-count").textContent = src.stays.length + " konaklama · " + src.rooms.length + " oda";
    rooms.replaceChildren();
    stays.replaceChildren();
    holds.replaceChildren();
    for (const room of src.rooms) {
      const blocked = room.maintenance.length > 0 ? " · bakım aralığı mevcut" : "";
      rooms.append(card(room.id, labels[room.bed] || room.bed,
        [["Kategori", room.category], ["Kapasite", room.capacity + " kişi"],
         ["Oda kontrolü", labels[room.readiness] || room.readiness],
         ["Doluluk sinyali", labels[room.occupancy] || room.occupancy],
         ["Bakım", room.maintenance.length ? "Var" + blocked : "Yok"]], "room"));
    }
    for (const stay of src.stays) {
      stays.append(card(stay.id, stay.arrival + " → " + stay.departure,
        [["Kategori", stay.category], ["Kişi", stay.persons],
         ["Yatak talebi", labels[stay.bed_request] || stay.bed_request]], "stay"));
    }
    if (src.holds.length) {
      for (const hold of src.holds) {
        holds.append(card(hold.id, "Önceden belirtilmiş oda blokajı",
          [["Oda", hold.room_id], ["Durum", hold.status],
           ["Serbest bırakma", hold.release_confirmed ? "Doğrulandı" : "Doğrulanmadı"]], "hold"));
      }
    } else {
      holds.append(el("p", "empty", "Bu örnekte ek oda blokajı yok."));
    }
    outcome.hidden = true;
    explanation.hidden = true;
    why.hidden = true;
    why.setAttribute("aria-expanded", "false");
    why.textContent = "Kararın nedenlerini göster";
    prompt.textContent = "Kurgusal sonucu görüntülemek için “Önerileri göster” düğmesine bas.";
  }
  function show() {
    const entry = current();
    if (!entry) return;
    const report = entry.report;
    const status = $("status");
    status.textContent = labels[report.status] || report.status;
    status.className = "status " + report.status;
    $("searched").textContent = "İncelenen adaylar: " + report.search.candidate_rooms
      + " oda · " + report.search.requested_stays + " konaklama · "
      + report.search.states_explored + " arama adımı";
    const results = $("proposal-list");
    results.replaceChildren();
    if (report.status === "proposed" && report.proposals.length) {
      for (const p of report.proposals) {
        const stay = entry.source.stays.find((s) => s.id === p.stay_id);
        const room = entry.source.rooms.find((r) => r.id === p.room_id);
        results.append(card(p.stay_id + " → " + p.room_id, "Personel onayına sunulan kurgusal öneri",
          [["Yatak", labels[room.bed] || room.bed], ["Talep", labels[stay.bed_request] || stay.bed_request],
           ["Durum", "Oda gerçekten atanmadı"]], "proposal"));
      }
    } else {
      results.append(el("p", "empty warning", "Bu senaryoda otomatik oda önerisi yok. Personel kontrolü gerekli."));
    }
    const codeList = $("reason-codes");
    codeList.replaceChildren();
    for (const reason of report.reason_codes) {
      const line = el("li", "");
      line.append(el("code", "", reason), el("p", "", reasons[reason] || "Ayrıntılı manuel inceleme gerekir."));
      codeList.append(line);
    }
    $("status-message").textContent = report.status === "proposed"
      ? "Öneriler algoritmadan önceden hesaplandı; gerçek işlem yapılmadı."
      : "Güvenli kapanış: eksik/çakışan kanıtta kısmi veya doğrulanmamış öneri yok.";
    outcome.hidden = false;
    explanation.hidden = true;
    why.hidden = false;
    why.setAttribute("aria-expanded", "false");
    why.textContent = "Kararın nedenlerini göster";
    prompt.textContent = "Bu sonuç Python'dan önceden üretildi; tarayıcıda yeni oda tahsisi hesaplanmadı.";
  }
  select.addEventListener("change", () => describe(current()));
  calculate.addEventListener("click", show);
  why.addEventListener("click", () => {
    const open = explanation.hidden;
    explanation.hidden = !open;
    why.setAttribute("aria-expanded", String(open));
    why.textContent = open ? "Gerekçeleri gizle" : "Kararın nedenlerini göster";
  });
  reset.addEventListener("click", () => {
    select.selectedIndex = 0;
    describe(data[0]);
    select.focus();
  });
  describe(data[0]);
})();
