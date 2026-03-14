
# Church Platform 

Sistema web de gestão de eventos e inscrições desenvolvido em Django para a igreja .

O projeto permite:

- Publicação de eventos
- Inscrições públicas com múltiplos participantes
- Gestão interna de pagamentos
- Check-in individual por participante (mobile + leitor QR)
- Dashboard com KPIs e filtros avançados
- Interface totalmente responsiva (mobile-first)

---

## Tecnologias

- Python (Django 5.2)
- SQLite (local / dev)
- HTML/CSS custom
- JavaScript (vanilla) com AJAX para interações mais fluídas
- Server-rendered architecture (templates)

---

## Setup & Execução

### 1) Criar e ativar ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Instalar dependências

```powershell
pip install -r requirements.txt
```

### 3) Criar banco de dados e migrar

```powershell
python manage.py migrate
```

### 4) Coletar static (importante para testes + deploy)

```powershell
python manage.py collectstatic --noinput
```

### 5) Rodar servidor local

```powershell
python manage.py runserver
```

---

## Estrutura Principal (resumo)

- `events/` → app principal (models, views, forms, templates, gestão interna)
- `templates/` → templates Django
- `static/` → estilos e scripts (inclui `static/js/management_ajax.js` para AJAX no painel de gestão)
- `events/services/emails.py` → envio de e-mails via Resend
- `events/tests/` → cobertura completa de modelos, views e serviços

---

## O que existe de novo / o que vale destacar

###  AJAX no painel de gestão
- Toggles de pagamento (`toggle-participant-paid`) e check-in (`toggle-participant-checkin`) funcionam via AJAX;
- Evita reloads e mantém a interface fluida;
- Tem mensagens de sucesso/erro exibidas diretamente na página.

### Testes automatizados
- Cobertura completa para:
  - validação das views públicas
  - lógica de check-in / pagamento
  - envio de e-mail via Resend (mockado nos testes)
- Para rodar:
  ```powershell
  python manage.py test
  ```

### Segurança e regras de negócio aplicadas
- Check-in bloqueado se participante não estiver pago.
- Registro de pagamento feito por inscrição (todos os participantes são pagos juntos).
- Eventos grátis marcam automaticamente inscrição + participantes como pagos.

---

## Como contribuir / rodar em produção

1. Atualizar `requirements.txt` se adicionar libs
2. Executar `python manage.py migrate` no deploy
3. Executar `python manage.py collectstatic --noinput`
4. Garantir variáveis de ambiente (principalmente `RESEND_API_KEY` e `DEFAULT_FROM_EMAIL`)

---

## Observações

- A aplicação usa o Resend para envio de e-mails (configurado em `settings.py`). Sem `RESEND_API_KEY` o envio falha intencionalmente.
- Em dev, o `tmp_emails/` guarda alguns exemplos de `.eml` gerados em testes/execuções.

---

## Testes

Todos os testes são executados com:

```powershell
python manage.py test
```

Eles cobrem:

- Modelos (`events.tests.test_models`)
- Views públicas e internas (`events.tests.test_views`)
- Serviço de e-mail (`events.tests.test_emails`)

---

Boa sorte no deploy! Se quiser posso também gerar um checklist de deploy com variáveis de ambiente e configurações específicas de infra.
**Cobertura atual: 73%**

- models.py: 94%
- permissions.py: 100%
- forms.py: 100%
- urls.py: 100%
- admin.py: 83%
- views.py: 56%
- management_views.py: 48%
- emails.py: 85%

Total de 37 testes, todos passando.

---

## Estado Atual

- Arquitetura server-rendered (POST + redirect)
- Ações de pagamento e check-in recarregam a página completa
- Estrutura pronta para evoluir para AJAX se necessário

---

## Objetivo do Projeto

Este projeto foi desenvolvido como:

- Ferramenta real para igreja
- Exercício de arquitetura Django tradicional
- Base para possível evolução futura (SaaS)

---

