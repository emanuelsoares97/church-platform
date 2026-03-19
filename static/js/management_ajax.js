function updateKpis(kpis) {
  if (!kpis) return;

  const totalRegs = document.getElementById('kpi-total-regs');
  const totalPaid = document.getElementById('kpi-total-paid');
  const totalParticipants = document.getElementById('kpi-total-participants');
  const totalCheckins = document.getElementById('kpi-total-checkins');

  if (totalRegs) totalRegs.textContent = kpis.total_regs;
  if (totalPaid) totalPaid.textContent = kpis.total_paid_participants;
  if (totalParticipants) totalParticipants.textContent = kpis.total_participants;
  if (totalCheckins) totalCheckins.textContent = kpis.total_checkins;
}
(function () {
  document.querySelectorAll('form.js-ajax-form').forEach(form => {
    form.addEventListener('submit', async function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const button = this.querySelector('button');
      const originalText = button.innerHTML;

      button.disabled = true;
      button.innerHTML = '⏳';

      try {
        const response = await fetch(this.action, {
          method: 'POST',
          body: formData,
          headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            'X-Requested-With': 'XMLHttpRequest'
          }
        });

        const data = await response.json();

        if (data.success) {
          updateKpis(data.kpis);

          const inputValue = this.querySelector('input[name="value"]');

          if (inputValue) {
            const current = inputValue.value;

            if (current === "1") {
              button.innerHTML = button.innerHTML.includes('💰') || button.innerHTML.includes('⬜')
                ? '💰'
                : '✅';
              inputValue.value = "0";
            } else {
              button.innerHTML = '⬜';
              inputValue.value = "1";
            }
          } else {
            button.innerHTML = '✔️';
          }
        }

      } catch (error) {
        alert('Erro de rede.');
        button.innerHTML = originalText;
      } finally {
        button.disabled = false;
      }
    });
  });
})();