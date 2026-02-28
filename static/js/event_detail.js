(() => {
  const root = document.querySelector(".wrap");
  if (!root) return;

  const bannerUrl = root.dataset.bannerUrl;
if (bannerUrl) {
  document.documentElement.style.setProperty("--event-bg", `url("${bannerUrl}")`);
}

  const priceRaw = root.dataset.price || "0";
  const PRICE = parseFloat(String(priceRaw).replace(",", "."));

  const qtyEl = document.getElementById("id_ticket_qty");
  const totalEl = document.getElementById("total");
  const minus = document.getElementById("minus");
  const plus = document.getElementById("plus");
  const participantsEl = document.getElementById("participants");

  const mbwayBox = document.getElementById("mbwayBox");
  const localBox = document.getElementById("localBox");

  function clampQty(n) {
    if (Number.isNaN(n)) return 1;
    return Math.min(20, Math.max(1, n));
  }

  function formatEUR(value) {
    // pt-PT: vírgula decimal
    return value.toFixed(2).replace(".", ",") + "€";
  }

  function updateTotal() {
    const qty = clampQty(parseInt(qtyEl.value || "1", 10));
    totalEl.textContent = formatEUR(PRICE * qty);
  }

  function renderParticipants() {
    const qty = clampQty(parseInt(qtyEl.value || "1", 10));
    participantsEl.innerHTML = "";

    for (let i = 1; i <= qty; i++) {
      const wrap = document.createElement("div");
      wrap.className = "field";

      const label = document.createElement("label");
      label.textContent = `Participante ${i}`;

      const input = document.createElement("input");
      input.type = "text";
      input.name = "participant_name";
      input.required = true;
      input.placeholder = `Nome do participante ${i}`;

      wrap.appendChild(label);
      wrap.appendChild(input);
      participantsEl.appendChild(wrap);
    }
  }

  function setQty(n) {
    const v = clampQty(n);
    qtyEl.value = v;
    updateTotal();
    renderParticipants();
  }

  function showPaymentBox(value) {
    // Django envia "MBWAY" ou "LOCAL"
    if (value === "MBWAY") {
      mbwayBox.style.display = "block";
      localBox.style.display = "none";
    } else {
      mbwayBox.style.display = "none";
      localBox.style.display = "block";
    }
  }

  // Events
  minus?.addEventListener("click", () => setQty(parseInt(qtyEl.value, 10) - 1));
  plus?.addEventListener("click", () => setQty(parseInt(qtyEl.value, 10) + 1));
  qtyEl?.addEventListener("input", () => setQty(parseInt(qtyEl.value, 10)));

  document.querySelectorAll('input[name="payment_method"]').forEach(r => {
    r.addEventListener("change", (e) => showPaymentBox(e.target.value));
  });

  document.getElementById("resetBtn")?.addEventListener("click", () => {
    setTimeout(() => {
      setQty(1);
      const selected = document.querySelector('input[name="payment_method"]:checked');
      showPaymentBox(selected ? selected.value : "MBWAY");
    }, 0);
  });

  // Init
  setQty(parseInt(qtyEl?.value || "1", 10));
  const selected = document.querySelector('input[name="payment_method"]:checked');
  showPaymentBox(selected ? selected.value : "MBWAY");
})();