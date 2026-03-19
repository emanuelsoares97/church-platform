function updateKpis(kpis) {
  if (!kpis) return;

  const totalRegs = document.getElementById("kpi-total-regs");
  const totalPaid = document.getElementById("kpi-total-paid");
  const totalParticipants = document.getElementById("kpi-total-participants");
  const totalCheckins = document.getElementById("kpi-total-checkins");

  if (totalRegs) totalRegs.textContent = kpis.total_regs;
  if (totalPaid) totalPaid.textContent = kpis.total_paid_participants;
  if (totalParticipants) totalParticipants.textContent = kpis.total_participants;
  if (totalCheckins) totalCheckins.textContent = kpis.total_checkins;
}

function getParticipantRows(registrationRow) {
  if (!registrationRow) return [];
  return Array.from(registrationRow.querySelectorAll(".participantRow"));
}

function getRegistrationCounts(registrationRow) {
  const participantRows = getParticipantRows(registrationRow);
  const total = participantRows.length;

  let paid = 0;
  let checked = 0;

  participantRows.forEach((row) => {
    const paymentForm = row.querySelector('form[data-action-type="payment"]');
    const checkinForm = row.querySelector('form[data-action-type="checkin"]');

    if (paymentForm?.dataset.currentState === "paid") paid += 1;
    if (checkinForm?.dataset.currentState === "checked") checked += 1;
  });

  return { total, paid, checked };
}

function renderRegistrationBadges(registrationRow) {
  if (!registrationRow) return;

  const badgesContainer = registrationRow.querySelector(".registrationBadges");
  if (!badgesContainer) return;

  const { total, paid, checked } = getRegistrationCounts(registrationRow);

  let paymentBadge = "";
  if (paid === total) {
    paymentBadge = '<span class="badge"><span class="dot"></span>Todos pagos</span>';
  } else if (paid === 0) {
    paymentBadge = '<span class="badge"><span class="dot bad"></span>Não pago</span>';
  } else {
    paymentBadge = `<span class="badge"><span class="dot warn"></span>${paid}/${total} pagos</span>`;
  }

  let checkinBadge = "";
  if (checked === total) {
    checkinBadge = '<span class="badge"><span class="dot"></span>Check-in completo</span>';
  } else if (checked === 0) {
    checkinBadge = '<span class="badge"><span class="dot bad"></span>Sem check-in</span>';
  } else {
    checkinBadge = `<span class="badge"><span class="dot warn"></span>${checked}/${total} check-ins</span>`;
  }

  badgesContainer.innerHTML = paymentBadge + checkinBadge;
}

function renderRegistrationActions(registrationRow) {
  if (!registrationRow) return;

  const actionsCol = registrationRow.querySelector(".actionsCol");
  if (!actionsCol) return;

  const payAllForm = actionsCol.querySelector('form[data-action-type="pay-all"]');
  const checkinAllForm = actionsCol.querySelector('form[data-action-type="checkin-all"]');
  const { total, paid, checked } = getRegistrationCounts(registrationRow);

  if (payAllForm) {
    const payAllButton = payAllForm.querySelector("button");

    payAllForm.hidden = paid === total;

    if (payAllButton) {
      payAllButton.innerHTML = "💳 Pagar todos";
      payAllButton.disabled = false;
    }
  }

  if (checkinAllForm) {
    const checkinAllButton = checkinAllForm.querySelector("button");
    const shouldDisable = paid !== total && actionsCol.dataset.eventPricePositive === "1";

    checkinAllForm.hidden = checked === total;

    if (checkinAllButton) {
      checkinAllButton.innerHTML = "✅ Check-in todos";
      checkinAllButton.disabled = shouldDisable;
    }
  }
}
function refreshRegistrationUiFromDom(registrationRow) {
  if (!registrationRow) return;
  renderRegistrationBadges(registrationRow);
  renderRegistrationActions(registrationRow);
}

function updateLookupUi(data) {
  const participant = data?.participant;
  if (!participant) return;

  const statusBig = document.getElementById("lookup-status-big");
  const paymentBadge = document.getElementById("lookup-payment-badge");
  const checkinBadge = document.getElementById("lookup-checkin-badge");
  const paymentForm = document.querySelector('form[data-action-type="payment-text"]');
  const eventRequiresPayment = !!paymentForm;

  if (statusBig) {
    if (participant.checked_in) {
      statusBig.className = "statusBig statusBig--done";
      statusBig.innerHTML = "☑️ Check-in já realizado";
    } else if (participant.is_paid || !eventRequiresPayment) {
      statusBig.className = eventRequiresPayment
        ? "statusBig statusBig--ok"
        : "statusBig statusBig--neutral";
      statusBig.innerHTML = eventRequiresPayment
        ? "✔ Participante pronto para entrar"
        : "🎟 Entrada gratuita";
    } else {
      statusBig.className = "statusBig statusBig--bad";
      statusBig.innerHTML = "⚠ Pagamento pendente";
    }
  }

  if (paymentBadge && eventRequiresPayment) {
    paymentBadge.className = participant.is_paid ? "badge badge--ok" : "badge badge--warn";
    paymentBadge.innerHTML = participant.is_paid
      ? "✔ Pagamento confirmado"
      : "⚠ Pagamento pendente";
  }

  if (checkinBadge) {
    checkinBadge.className = participant.checked_in ? "badge badge--ok" : "badge badge--warn";
    checkinBadge.innerHTML = participant.checked_in
      ? "✔ Check-in realizado"
      : "⬜ Check-in por fazer";
  }

  const paymentTextForm = document.querySelector('form[data-action-type="payment-text"]');
  const checkinTextForm = document.querySelector('form[data-action-type="checkin-text"]');

  if (paymentTextForm) {
    const btn = paymentTextForm.querySelector("button");
    const value = paymentTextForm.querySelector('input[name="value"]');
    if (btn) btn.innerHTML = participant.is_paid ? "Remover pagamento" : "Confirmar pagamento";
    if (value) value.value = participant.is_paid ? "0" : "1";
  }

  if (checkinTextForm) {
    const btn = checkinTextForm.querySelector("button");
    const value = checkinTextForm.querySelector('input[name="value"]');
    if (btn) {
      btn.innerHTML = participant.checked_in ? "Desfazer check-in" : "Confirmar entrada";
      btn.disabled = eventRequiresPayment && !participant.is_paid;
    }
    if (value) value.value = participant.checked_in ? "0" : "1";
  }
}

function updateParticipantUiFromResponse(form, data, actionType) {
  const inputValue = form.querySelector('input[name="value"]');
  const button = form.querySelector("button");

  if (!data || !data.participant) return;

  const participant = data.participant;
  const participantRow = form.closest(".participantRow");
  const registrationRow = form.closest(".table__row");

  if (actionType === "payment-text" && button && inputValue) {
    button.innerHTML = participant.is_paid ? "Remover pagamento" : "Confirmar pagamento";
    inputValue.value = participant.is_paid ? "0" : "1";
  }

  if (actionType === "checkin-text" && button && inputValue) {
    button.innerHTML = participant.checked_in ? "Desfazer check-in" : "Confirmar entrada";
    inputValue.value = participant.checked_in ? "0" : "1";
  }

  if (actionType === "payment" && button && inputValue) {
    button.innerHTML = participant.is_paid ? "💰" : "⬜";
    inputValue.value = participant.is_paid ? "0" : "1";
    form.dataset.currentState = participant.is_paid ? "paid" : "unpaid";
  }

  if (actionType === "checkin" && button && inputValue) {
    button.innerHTML = participant.checked_in ? "✅" : "⬜";
    inputValue.value = participant.checked_in ? "0" : "1";
    form.dataset.currentState = participant.checked_in ? "checked" : "unchecked";
  }

  if (participantRow) {
    const paymentForm = participantRow.querySelector('form[data-action-type="payment"]');
    const checkinForm = participantRow.querySelector('form[data-action-type="checkin"]');
    const paymentButton = paymentForm?.querySelector("button");
    const paymentInput = paymentForm?.querySelector('input[name="value"]');
    const checkinButton = checkinForm?.querySelector("button");
    const checkinValue = checkinForm?.querySelector('input[name="value"]');

    if (paymentForm) {
      paymentForm.dataset.currentState = participant.is_paid ? "paid" : "unpaid";
      if (paymentButton) paymentButton.innerHTML = participant.is_paid ? "💰" : "⬜";
      if (paymentInput) paymentInput.value = participant.is_paid ? "0" : "1";
    }

    if (checkinForm) {
      checkinForm.dataset.currentState = participant.checked_in ? "checked" : "unchecked";
      if (checkinButton) {
        checkinButton.innerHTML = participant.checked_in ? "✅" : "⬜";
        checkinButton.disabled = !participant.is_paid;
      }
      if (checkinValue) {
        checkinValue.value = participant.checked_in ? "0" : "1";
      }
    }
  }

  if (registrationRow) {
    refreshRegistrationUiFromDom(registrationRow);
  }

  updateLookupUi(data);
}

function updateRegistrationUiAfterBulk(form, actionType) {
  const registrationRow = form.closest(".table__row");
  if (!registrationRow) return;

  const participantRows = getParticipantRows(registrationRow);

  participantRows.forEach((row) => {
    const paymentForm = row.querySelector('form[data-action-type="payment"]');
    const paymentButton = paymentForm?.querySelector("button");
    const paymentValue = paymentForm?.querySelector('input[name="value"]');

    const checkinForm = row.querySelector('form[data-action-type="checkin"]');
    const checkinButton = checkinForm?.querySelector("button");
    const checkinValue = checkinForm?.querySelector('input[name="value"]');

    if (actionType === "pay-all" && paymentForm) {
      paymentForm.dataset.currentState = "paid";
      if (paymentButton) paymentButton.innerHTML = "💰";
      if (paymentValue) paymentValue.value = "0";
      if (checkinButton) checkinButton.disabled = false;
    }

    if (actionType === "checkin-all" && checkinForm) {
      checkinForm.dataset.currentState = "checked";
      if (checkinButton) checkinButton.innerHTML = "✅";
      if (checkinValue) checkinValue.value = "0";
    }
  });

  refreshRegistrationUiFromDom(registrationRow);
}

(function () {
  document.querySelectorAll("form.js-ajax-form").forEach((form) => {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const button = this.querySelector("button");
      const originalText = button ? button.innerHTML : "";
      const actionType = this.dataset.actionType || "";

      if (button) {
        button.disabled = true;
        button.innerHTML = "⏳";
      }

      try {
        const response = await fetch(this.action, {
          method: "POST",
          body: formData,
          headers: {
            "X-CSRFToken": formData.get("csrfmiddlewaretoken"),
            "X-Requested-With": "XMLHttpRequest",
          },
        });

        let data = {};
        try {
          data = await response.json();
        } catch {
          throw new Error("Resposta inválida do servidor.");
        }

        if (!response.ok || !data.success) {
          alert(data.error || "Erro ao processar.");
          if (button) {
            button.innerHTML = originalText;
          }
          return;
        }

        updateKpis(data.kpis);

        if (data.participant) {
          updateParticipantUiFromResponse(this, data, actionType);
        } else {
          updateRegistrationUiAfterBulk(this, actionType);
        }
      } catch (error) {
        alert(error.message || "Erro de rede.");
        if (button) {
          button.innerHTML = originalText;
        }
      } finally {
        const registrationRow = this.closest(".table__row");

        if (button) {
          if (actionType === "pay-all" || actionType === "checkin-all") {
            if (!this.hidden) {
              button.disabled = false;
            }
          } else {
            button.disabled = false;
          }
        }

        if (registrationRow) {
          refreshRegistrationUiFromDom(registrationRow);
        }
      }
    });
  });

  document.querySelectorAll(".table__row").forEach((row) => {
    refreshRegistrationUiFromDom(row);
  });
})();