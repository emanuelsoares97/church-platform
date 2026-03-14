(function() {
  document.querySelectorAll('form[method="post"]').forEach(form => {
    form.addEventListener('submit', async function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      const button = this.querySelector('button');
      const originalText = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '⏳ A processar...';

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
          // Recarregar para atualizar a UI
          location.reload();
        } else {
          alert(data.error || 'Erro ao processar.');
          button.innerHTML = originalText;
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