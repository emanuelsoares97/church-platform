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

function setButtonLoading(button) {
  if (!button) return;
  button.disabled = true;
  button.innerHTML = "⏳";
}

function restoreButton(button, originalText) {
  if (!button) return;
  button.disabled = false;
  button.innerHTML = originalText;
}

function applySuccessState(form, button, actionType, inputValue) {
  if (!button) return;

  if (inputValue) {
    const current = inputValue.value;

    if (current === "1") {
      if (actionType === "payment") {
        button.innerHTML = "💰";
      } else if (actionType === "checkin") {
        button.innerHTML = "✅";
      } else if (actionType === "payment-text") {
        button.innerHTML = "Remover pagamento";
      } else if (actionType === "checkin-text") {
        button.innerHTML = "Desfazer check-in";
      }

      inputValue.value = "0";
    } else {
      if (actionType === "payment" || actionType === "checkin") {
        button.innerHTML = "⬜";
      } else if (actionType === "payment-text") {
        button.innerHTML = "Confirmar pagamento";
      } else if (actionType === "checkin-text") {
        button.innerHTML = "Confirmar entrada";
      }

      inputValue.value = "1";
    }

    return;
  }

  if (actionType === "pay-all") {
    button.innerHTML = "💳 Pago";
  } else if (actionType === "checkin-all") {
    button.innerHTML = "✅ Feito";
  } else {
    button.innerHTML = "✔️";
  }
}

function updateRegistrationSummary(row) {
  if (!row) return;

  const participantRows = row.querySelectorAll(".participantRow");
  const total = participantRows.length;
  let paid = 0;
  let checked = 0;

  participantRows.forEach((participantRow) => {
    const paymentForm = participantRow.querySelector('form[data-action-type="payment"]');
    const checkinForm = participantRow.querySelector('form[data-action-type="checkin"]');

    if (paymentForm) {
      const paymentInput = paymentForm.querySelector('input[name="value"]');
      if (paymentInput && paymentInput.value === "0") {
        paid += 1;
      }
    }

    if (checkinForm) {
      const checkinInput = checkinForm.querySelector('input[name="value"]');
      if (checkinInput && checkinInput.value === "0") {
        checked += 1;
      }
    }
  });

  const paidBadge = row.querySelector('[data-registration-paid-badge]');
  const checkinBadge = row.querySelector('[data-registration-checkin-badge]');
  const payAllForm = row.querySelector('form[data-action-type="pay-all"]');
  const checkinAllForm = row.querySelector('form[data-action-type="checkin-all"]');

  if (paidBadge) {
    if (total > 0 && paid === total) {
      paidBadge.innerHTML = '<span class="dot"></span>Todos pagos';
    } else if (paid === 0) {
      paidBadge.innerHTML = '<span class="dot bad"></span>Não pago';
    } else {
      paidBadge.innerHTML = `<span class="dot warn"></span>${paid}/${total} pagos`;
    }
  }

  if (checkinBadge) {
    if (total > 0 && checked === total) {
      checkinBadge.innerHTML = '<span class="dot"></span>Check-in completo';
    } else if (checked === 0) {
      checkinBadge.innerHTML = '<span class="dot bad"></span>Sem check-in';
    } else {
      checkinBadge.innerHTML = `<span class="dot warn"></span>${checked}/${total} check-ins`;
    }
  }

  if (payAllForm) {
    payAllForm.style.display = total > 0 && paid !== total ? "" : "none";
  }

  if (checkinAllForm) {
    checkinAllForm.style.display = total > 0 && checked !== total ? "" : "none";
  }
}

function updateLookupStatus(participant) {
  const statusBig = document.querySelector("[data-lookup-status-big]");
  const paymentBadge = document.querySelector("[data-lookup-payment-badge]");
  const checkinBadge = document.querySelector("[data-lookup-checkin-badge]");
  const eventIsPaid = document.body.dataset.eventHasPrice === "1";

  if (statusBig) {
    if (participant.checked_in) {
      statusBig.className = "statusBig statusBig--ok";
      statusBig.innerHTML = "✅ Check-in já realizado";
    } else if (participant.is_paid) {
      statusBig.className = "statusBig statusBig--ok";
      statusBig.innerHTML = "✔ Participante pronto para entrar";
    } else if (eventIsPaid) {
      statusBig.className = "statusBig statusBig--bad";
      statusBig.innerHTML = "⚠ Pagamento pendente";
    } else {
      statusBig.className = "statusBig statusBig--neutral";
      statusBig.innerHTML = "🎟 Entrada gratuita";
    }
  }

  if (paymentBadge) {
    if (eventIsPaid) {
      if (participant.is_paid) {
        paymentBadge.className = "badge badge--ok";
        paymentBadge.innerHTML = "✔ Pagamento confirmado";
      } else {
        paymentBadge.className = "badge badge--warn";
        paymentBadge.innerHTML = "⚠ Pagamento pendente";
      }
    } else {
      paymentBadge.className = "badge";
      paymentBadge.innerHTML = "🎟 Evento gratuito";
    }
  }

  if (checkinBadge) {
    if (participant.checked_in) {
      checkinBadge.className = "badge badge--ok";
      checkinBadge.innerHTML = "✔ Check-in realizado";
    } else {
      checkinBadge.className = "badge badge--warn";
      checkinBadge.innerHTML = "⬜ Check-in por fazer";
    }
  }
}

function syncSiblingButtons(form, participant, actionType) {
  const participantRow = form.closest(".participantRow");
  if (participantRow) {
    const checkinForm = participantRow.querySelector('form[data-action-type="checkin"]');
    if (checkinForm) {
      const checkinButton = checkinForm.querySelector("button");
      const checkinInput = checkinForm.querySelector('input[name="value"]');

      if (checkinButton) {
        checkinButton.disabled = !participant.is_paid;
        if (!participant.is_paid && !participant.checked_in) {
          checkinButton.title = "Pagamento pendente";
        } else {
          checkinButton.removeAttribute("title");
        }
      }

      if (!participant.is_paid && checkinInput && participant.checked_in === false) {
        checkinInput.value = "1";
      }
    }

    const row = form.closest(".table__row");
    updateRegistrationSummary(row);
  }

  if (actionType === "payment-text") {
    const checkinForm = document.querySelector('form[data-action-type="checkin-text"]');
    if (checkinForm) {
      const checkinButton = checkinForm.querySelector("button");
      if (checkinButton) {
        checkinButton.disabled = !participant.is_paid;
        if (!participant.is_paid && !participant.checked_in) {
          checkinButton.title = "Pagamento pendente";
        } else {
          checkinButton.removeAttribute("title");
        }
      }
    }

    updateLookupStatus(participant);
  }

  if (actionType === "checkin-text") {
    updateLookupStatus(participant);
  }
}

function updateParticipantUiFromResponse(form, data, actionType) {
  const inputValue = form.querySelector('input[name="value"]');
  const button = form.querySelector("button");

  if (!data || !data.participant) return;

  const participant = data.participant;

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
  }

  if (actionType === "checkin" && button && inputValue) {
    button.innerHTML = participant.checked_in ? "✅" : "⬜";
    inputValue.value = participant.checked_in ? "0" : "1";
  }

  syncSiblingButtons(form, participant, actionType);
}

(function () {
  document.querySelectorAll("form.js-ajax-form").forEach((form) => {
    form.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const button = this.querySelector("button");
      const originalText = button ? button.innerHTML : "";
      const actionType = this.dataset.actionType || "";
      const inputValue = this.querySelector('input[name="value"]');

      setButtonLoading(button);

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
        } catch (jsonError) {
          throw new Error("Resposta inválida do servidor.");
        }

        if (!response.ok || !data.success) {
          alert(data.error || "Erro ao processar.");
          restoreButton(button, originalText);
          return;
        }

        updateKpis(data.kpis);

        if (data.participant) {
          updateParticipantUiFromResponse(this, data, actionType);
        } else {
          applySuccessState(this, button, actionType, inputValue);

          const row = this.closest(".table__row");
          if (row) {
            if (actionType === "pay-all") {
              row.querySelectorAll('form[data-action-type="payment"]').forEach((paymentForm) => {
                const paymentButton = paymentForm.querySelector("button");
                const paymentInput = paymentForm.querySelector('input[name="value"]');
                if (paymentButton) paymentButton.innerHTML = "💰";
                if (paymentInput) paymentInput.value = "0";
              });

              row.querySelectorAll('form[data-action-type="checkin"] button').forEach((checkinButton) => {
                checkinButton.disabled = false;
                checkinButton.removeAttribute("title");
              });
            }

            if (actionType === "checkin-all") {
              row.querySelectorAll('form[data-action-type="checkin"]').forEach((checkinForm) => {
                const checkinButton = checkinForm.querySelector("button");
                const checkinInput = checkinForm.querySelector('input[name="value"]');
                if (checkinButton) checkinButton.innerHTML = "✅";
                if (checkinInput) checkinInput.value = "0";
              });
            }

            updateRegistrationSummary(row);
          }
        }
      } catch (error) {
        alert(error.message || "Erro de rede.");
        restoreButton(button, originalText);
        return;
      } finally {
        if (button) {
          button.disabled = false;
        }
      }
    });
  });
})();