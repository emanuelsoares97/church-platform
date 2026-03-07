
# SNT Almada — Sistema de Inscrições

Sistema web de gestão de eventos e inscrições desenvolvido em Django para a igreja SNT Almada.

O projeto permite:

- Publicação de eventos
- Inscrições públicas com múltiplos participantes
- Gestão interna de pagamentos
- Check-in individual por participante
- Dashboard com KPIs
- Interface totalmente responsiva (mobile-first)

---

## Tecnologias

- Python
- Django
- SQLite (atualmente)
- HTML + CSS custom
- JavaScript (vanilla)
- Server-rendered architecture

## Estrutura do Projeto

```
db.sqlite3
LICENSE
manage.py
README.md
requirements.txt
events/
	__init__.py
	admin.py
	apps.py
	forms.py
	management_urls.py
	management_views.py
	models.py
	permissions.py
	tests.py
	urls.py
	views.py
	__pycache__/
	migrations/
		__init__.py
		0001_initial.py
		0002_participant_checked_in_at.py
		0003_registration_public_id.py
		0004_alter_registration_public_id.py
		0005_participant_is_paid_participant_paid_at_and_more.py
		0006_alter_participant_ticket_code.py
		__pycache__/
	services/
		__init__.py
		emails.py
		__pycache__/
media/
	events/
snt_almada/
	__init__.py
	asgi.py
	settings.py
	urls.py
	wsgi.py
	__pycache__/
static/
	css/
		event_detail.css
		event_list.css
		global.css
		login.css
		management_v2.css
		qr_scanner.css
	img/
	js/
		event_detail.js
		navbar.js
		qr_scanner.js
templates/
	base.html
	auth/
		login.html
	emails/
		registration_ticket_pc.html
		registration_ticket.html
	events/
		event_detail.html
		event_list.html
		registration_success.html
	management/
		base_management.html
		event_registrations.html
		home.html
		registration_group.html
		scan.html
		ticket_lookup.html
tmp_emails/
	20260303-223539-1851096388496.eml
	20260303-224824-2281735198544.eml
	20260303-225603-2281733695824.eml
	20260307-110000-1943018680240.eml
	20260307-114115-2430184388064.eml
```

## Modelos Principais

### Event
- title
- slug
- description
- date
- location
- price
- is_active
- banner_image

### Registration
- event (FK)
- buyer_name
- buyer_email
- phone
- ticket_qty
- is_paid
- payment_method
- created_at

### Participant
- registration (FK)
- full_name
- checked_in

---

## Área Pública

Rotas:

- `/eventos/` → Lista de eventos ativos
- `/evento/<slug>/` → Página do evento + formulário

Funcionalidades:

- Inscrição com múltiplos participantes
- Validação dinâmica do número de nomes
- Cálculo automático do total
- Eventos gratuitos tratados automaticamente
- Design moderno e responsivo

---

## Painel de Gestão Interno

Protegio por login + permissões personalizadas.

Funcionalidades:

- Dashboard com lista de eventos
- KPIs compactos:
  - INS (Inscrições)
  - PAG (Pagas)
  - PART (Participantes)
  - CHK (Check-ins)
- Filtros por:
  - Nome/email
  - Pago / Não pago
  - Check-in completo / pendente
- Paginação
- Toggle de pagamento
- Check-in por participante (bloqueado se não pago)

---

## Regras de Negócio

- Uma inscrição pode ter vários participantes
- Pagamento é por inscrição
- Check-in é individual por participante
- Não é permitido check-in se pagamento não estiver confirmado
- Eventos gratuitos são automaticamente marcados como pagos

---

## Responsividade

- Navbar com menu hamburger
- KPIs compactos no mobile (4 colunas)
- Tabela responsiva
- Layout mobile-first

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

