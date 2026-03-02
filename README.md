
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

## 🚀 Tecnologias

- Python
- Django
- SQLite (atualmente)
- HTML + CSS custom
- JavaScript (vanilla)
- Server-rendered architecture

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

