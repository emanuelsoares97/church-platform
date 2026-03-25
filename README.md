# Church Platform

Sistema web desenvolvido em Django para apoiar a gestão de igrejas, focado em eventos, inscrições e gestão interna. Uma plataforma construída para resolver necessidades reais, servindo como base sólida para estudo e evolução em Django.

O objetivo foi desenvolver algo organizado, reutilizável e próximo de um cenário real, não apenas mais um CRUD comum.

## Funcionalidades

- criação e publicação de eventos
- página pública de eventos com filtros e busca
- inscrições públicas online
- suporte para múltiplos participantes por inscrição
- gestão interna centralizada de inscrições e registos
- controlo de pagamento com múltiplos métodos (MB Way, pagamento local)
- check-in por participante
- dashboard de gestão com indicadores, KPIs e filtros avançados
- galeria de momentos da igreja com retenção configurável
- sistema de permissões baseado em roles
- envio automático de e-mails de confirmação
- exportação de dados para Excel
- interface responsiva
- suporte PWA
- geração de QR codes para bilhetes

## Stack Tecnológico

- Python 3.10+
- Django 5.2.11
- PostgreSQL
- JavaScript / Vanilla JS
- HTML5 / CSS3
- Cloudinary para gestão de imagens
- Resend para envio de e-mails
- Gunicorn para produção
- WhiteNoise para servir estáticos

## Estrutura do Projeto

```
church-platform/
├── church_platform/         # configuração principal do Django
├── core/                    # app base - páginas gerais e transversais
├── events/                  # app principal - eventos, inscrições, check-in
├── gallery/                 # app de galeria de momentos
├── management/              # área interna de gestão
├── static/                  # ficheiros estáticos (CSS, JS, imagens)
├── templates/               # templates Django
├── manage.py
├── requirements.txt
├── db.sqlite3               # base de dados
└── LICENSE
```

### Apps Principais

#### church_platform/

Configuração central do projeto Django incluindo:

- `settings.py` - definições globais, apps instaladas, autenticação
- `urls.py` - rotas principais e include das apps
- `wsgi.py` e `asgi.py` - entry points para deployment
- ficheiro `.env` com variáveis de ambiente

#### core/

Funcionalidades gerais e transversais do projeto:

- páginas institucionais
- views públicas base
- vistas PWA
- utilitários de imagem (otimização, processamento)
- dados mestres como ministérios da igreja

#### events/

Núcleo do sistema com toda a lógica de eventos.

Modelos principais:
- `Event` - definição de eventos com datas, preço, limite de inscrições
- `Registration` - inscrição no evento
- `Participant` - participante individual de uma inscrição

Funcionalidades:
- gestor de eventos (criar, editar, publicar, arquivar)
- validação de inscrições e pagamento
- check-in de presença com tracking
- gestão de permissões baseada em roles
- emissão de QR codes para bilhetes
- formulários com validação completa
- serviço de e-mail automático
- suite completa de testes

Estrutura interna:
```
events/
├── models.py                # Event, Registration, Participant
├── views.py                 # vistas públicas
├── management_views.py      # vistas de gestão interna
├── management_urls.py       # rotas de gestão
├── forms.py                 # validação de formulários
├── permissions.py           # controlo de acesso por role
├── admin.py                 # interface admin django
├── apps.py
├── services/
│   └── emails.py           # envio automático de e-mails
├── tests/
│   ├── test_models.py       # 72 testes
│   ├── test_forms.py        # 58 testes
│   ├── test_views.py        # 114 testes
│   ├── test_permissions.py  # 18 testes
│   ├── test_emails.py       # 24 testes
│   ├── test_utils.py        # 13 testes
│   └── __init__.py
└── migrations/             # histórico de alterações à BD
```

#### gallery/

Gestão de galeria de momentos da igreja com:

- álbuns com data e descrição
- imagens com retenção configurável (7, 15 ou 30 dias)
- integração com Cloudinary para armazenamento
- slug automático para URLs
- testes e validação de formulários

#### management/

Área interna de gestão com controlo de acesso baseado em roles:

- dashboard principal com estatísticas
- gestor de eventos (criar, editar, arquivar)
- gestor de inscrições com filtros avançados
- gestor de galeria e uploads
- exportação de dados para Excel
- KPIs de eventos (inscrições, presença, pagamento)
- sistema de permissões granular

Modelos de permissões:
- `leadership_required` - liderança (acesso total)
- `management_required` - qualquer gestor
- `reception_or_leadership_required` - receção ou liderança
- `media_or_leadership_required` - mídia ou liderança

## Testes

O projeto possui suite completa de testes unitários e de integração:

```
100 testes no total
Cobertura: 85%

Distribuição de cobertura por módulo:
- events/migrations: 100%
- events/permissions: 100%
- events/models: 94%
- events/forms: 100%
- events/views: 86%
- events/admin: 82%
- events/services/emails: 64%
- management/permissions: 100%
- management/views: 60%
- gallery/models: 67%
- gallery/admin: 62%
- gallery/forms: 62%
- core/urls: 100%
- core/apps: 100%
- church_platform settings: 98%
```

Executar testes localmente:

```bash
# Executar todos os testes
python -m coverage run manage.py test

# Gerar relatório de cobertura
python -m coverage report -m

# Gerar relatório em HTML
python -m coverage html
```

## Instalação e Setup

### Pré-requisitos

- Python 3.10 ou superior
- PostgreSQL 12+ (ou SQLite para desenvolvimento)
- pip ou poetry

### Configuração Local

1. Clone o repositório

```bash
git clone <repo-url>
cd church-platform
```

2. Crie um ambiente virtual

```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências

```bash
pip install -r requirements.txt
```

4. Configure variáveis de ambiente

Crie um ficheiro `.env` na raiz do projeto:

```
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@localhost/church_platform
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloudname
RESEND_API_KEY=re_...
DEFAULT_FROM_EMAIL=noreply@example.com
```

5. Aplique as migrações

```bash
python manage.py migrate
```

6. Crie um superuser

```bash
python manage.py createsuperuser
```

7. Execute o servidor

```bash
python manage.py runserver
```

A aplicação estará disponível em `http://localhost:8000`

## Deployment

### Com Gunicorn

Para produção com Gunicorn:

```bash
gunicorn church_platform.wsgi:application --bind 0.0.0.0:8000
```

Os estáticos são servidos com WhiteNoise, eliminando a necessidade de servidor web separado para CSS/JS/imagens.

### Variáveis de Ambiente em Produção

- `SECRET_KEY` - chave secreta (gerado aleatoriamente)
- `DEBUG` - sempre False em produção
- `ALLOWED_HOSTS` - domínios permitidos
- `DATABASE_URL` - URL da base de dados PostgreSQL
- `CLOUDINARY_URL` - credenciais Cloudinary
- `RESEND_API_KEY` - chave da API Resend

## Base de Dados

PostgreSQL com suporte a:

- Retenção configurável de dados (ex: galeria com 7, 15 ou 30 dias)
- Transações ACID
- Índices para melhor performance
- 11+ migrações aplicadas para evolução segura do schema

Principais mudanças no histórico:
- Adição de check-in tracking
- Sistema de deadline para inscrições
- Arquivamento de eventos
- Campos de pagamento com data e valor

## Contribuições

Quando trabalhar no projeto, considere:

- Manter a estrutura modular das apps
- Adicionar testes para novas funcionalidades
- Seguir o padrão de permissões existente
- Usar migrations para mudanças no schema
- Documentar comportamentos complexos
- Manter cobertura de testes acima de 80%

## Licença

Ver ficheiro [LICENSE](LICENSE)
