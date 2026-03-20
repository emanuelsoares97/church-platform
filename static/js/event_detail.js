(() => {
  const root = document.querySelector(".wrap");
  if (!root) return;

  // Banner dinâmico por evento
  const bannerUrl = root.dataset.bannerUrl;
  if (bannerUrl) {
    document.documentElement.style.setProperty("--event-bg", `url("${bannerUrl}")`);
  }

  // Preço do evento
  const priceRaw = root.dataset.price || "0";
  const PRICE = parseFloat(String(priceRaw).replace(",", ".")) || 0;

  const form = document.getElementById("regForm");
  const submitBtn = document.getElementById("submitBtn");
  const buyerEl = document.getElementById("id_buyer_name");

  const qtyEl = document.getElementById("id_ticket_qty");
  const totalEl = document.getElementById("total");
  const minus = document.getElementById("minus");
  const plus = document.getElementById("plus");
  const participantsEl = document.getElementById("participants");

  const mbwayBox = document.getElementById("mbwayBox");
  const localBox = document.getElementById("localBox");

  // Caixa de erro inline
  const formError = document.getElementById("formError");

  function showError(msg) {
    if (!formError) return;
    formError.textContent = msg;
    formError.classList.add("show");
  }

  function clearError() {
    if (!formError) return;
    formError.textContent = "";
    formError.classList.remove("show");
  }

  // Valores anteriores vindos do backend
  const prevEl = document.getElementById("participant-values");
  let prevValues = [];

  if (prevEl) {
    try {
      prevValues = JSON.parse(prevEl.textContent || "[]");
    } catch (e) {
      prevValues = [];
    }
  }

  function clampQty(n) {
    if (Number.isNaN(n)) return 1;
    return Math.min(20, Math.max(1, n));
  }

  function formatEUR(value) {
    return value.toFixed(2).replace(".", ",") + "€";
  }

  function updateTotal() {
    if (!qtyEl) return;

    const qty = clampQty(parseInt(qtyEl.value || "1", 10));

    // Em eventos gratuitos, o bloco do total pode nem existir
    if (!totalEl) return;

    totalEl.textContent = formatEUR(PRICE * qty);
  }

  function readCurrentParticipantNames() {
    return Array.from(document.querySelectorAll('input[name="participant_name"]'))
      .map((input) => input.value);
  }

  function renderParticipants() {
    if (!participantsEl || !qtyEl) return;

    const qty = clampQty(parseInt(qtyEl.value || "1", 10));
    const currentValues = readCurrentParticipantNames();

    participantsEl.innerHTML = "";

    for (let i = 1; i <= qty; i++) {
      const wrap = document.createElement("div");
      wrap.className = "field";

      const label = document.createElement("label");
      label.textContent = `Participante ${i}`;
      label.setAttribute("for", `participant_name_${i}`);

      const input = document.createElement("input");
      input.type = "text";
      input.name = "participant_name";
      input.id = `participant_name_${i}`;
      input.required = true;
      input.placeholder = `Nome do participante ${i}`;

      const fromPrev = prevValues[i - 1];
      const fromCurrent = currentValues[i - 1];
      input.value = (fromPrev ?? fromCurrent ?? "").toString();

      input.addEventListener("input", clearError);

      wrap.appendChild(label);
      wrap.appendChild(input);
      participantsEl.appendChild(wrap);
    }

    // Auto-preencher participante 1 com nome do comprador
    const first = document.querySelector('input[name="participant_name"]');
    if (first && buyerEl && !first.value.trim() && buyerEl.value.trim()) {
      first.value = buyerEl.value.trim();
    }
  }

  function setQty(n) {
    if (!qtyEl) return;

    const v = clampQty(n);
    qtyEl.value = v;
    updateTotal();
    renderParticipants();
  }

  function showPaymentBox(value) {
    // Em eventos gratuitos estas boxes podem não existir
    if (!mbwayBox || !localBox) return;

    if (value === "MBWAY") {
      mbwayBox.style.display = "block";
      localBox.style.display = "none";
    } else {
      mbwayBox.style.display = "none";
      localBox.style.display = "block";
    }
  }

  // + / -
  minus?.addEventListener("click", () => {
    clearError();
    setQty(parseInt(qtyEl?.value || "1", 10) - 1);
  });

  plus?.addEventListener("click", () => {
    clearError();
    setQty(parseInt(qtyEl?.value || "1", 10) + 1);
  });

  // Qty manual
  qtyEl?.addEventListener("input", () => {
    clearError();
    setQty(parseInt(qtyEl.value || "1", 10));
  });

  // Toggle pagamento
  document.querySelectorAll('input[name="payment_method"]').forEach((radio) => {
    radio.addEventListener("change", (e) => {
      clearError();
      showPaymentBox(e.target.value);
    });
  });

  // Reset
  document.getElementById("resetBtn")?.addEventListener("click", () => {
    setTimeout(() => {
      prevValues = [];
      clearError();
      setQty(1);

      const selected = document.querySelector('input[name="payment_method"]:checked');
      if (selected || (mbwayBox && localBox)) {
        showPaymentBox(selected ? selected.value : "MBWAY");
      }
    }, 0);
  });

  // Auto atualizar participante 1 com buyer_name
  buyerEl?.addEventListener("input", () => {
    clearError();
    const first = document.querySelector('input[name="participant_name"]');
    if (first && !first.value.trim()) {
      first.value = buyerEl.value;
    }
  });

  // Validar submit
  form?.addEventListener("submit", (e) => {
    clearError();

    const qty = clampQty(parseInt(qtyEl?.value || "1", 10));
    const inputs = Array.from(document.querySelectorAll('input[name="participant_name"]'));
    const filled = inputs.filter((input) => input.value.trim().length > 0).length;

    if (filled !== qty) {
      e.preventDefault();
      showError(`Preenche exatamente ${qty} nome(s) de participante.`);
      inputs.find((input) => !input.value.trim())?.focus();
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.style.opacity = "0.75";
      submitBtn.textContent = "A enviar...";
    }
  });

  // Init
  setQty(parseInt(qtyEl?.value || "1", 10));

  const selected = document.querySelector('input[name="payment_method"]:checked');
  if (selected || (mbwayBox && localBox)) {
    showPaymentBox(selected ? selected.value : "MBWAY");
  }
})();