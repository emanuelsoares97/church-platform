# Church Platform

Sistema web desenvolvido em Django para apoiar a gestão da igreja, com foco em eventos, inscrições e área interna de gestão.

Este projeto foi pensado para resolver necessidades reais da igreja e, ao mesmo tempo, servir como base sólida de estudo e evolução em Django. A ideia não foi fazer apenas “mais um CRUD”, mas sim construir algo organizado, reutilizável e próximo de um cenário real.

## O que o projeto faz

Atualmente, o projeto já inclui funcionalidades como:

- criação e publicação de eventos
- página pública de eventos
- inscrições públicas
- suporte para múltiplos participantes na mesma inscrição
- gestão interna das inscrições
- controlo de pagamento
- check-in por participante
- dashboard de gestão com indicadores e filtros
- interface responsiva
- envio de e-mails de confirmação

## Tecnologias utilizadas

- Python
- Django 5.2
- SQLite
- HTML
- CSS
- JavaScript
- Django Templates
- Resend para envio de e-mails

## Estrutura do projeto

A estrutura está organizada desta forma:

```text
church-platform/
├── church_platform/         # configuração principal do projeto Django
├── core/                    # app base / páginas gerais
├── events/                  # app principal de eventos, inscrições e gestão relacionada
├── gallery/                 # app da galeria
├── management/              # área de gestão e organização interna
├── static/                  # ficheiros estáticos globais
├── templates/               # templates globais
├── manage.py
├── requirements.txt
├── README.md
├── .gitignore
└── LICENSE
```

### Resumo das principais pastas

#### `church_platform/`
Aqui fica a configuração principal do projeto Django, incluindo ficheiros como:

- `settings.py`
- `urls.py`
- `wsgi.py`
- `asgi.py`

É basicamente o centro da configuração global da aplicação.

#### `core/`
App usada para páginas mais gerais do projeto. É o sítio ideal para colocar partes institucionais, páginas base ou funcionalidades mais transversais que não pertencem diretamente a eventos ou galeria.

#### `events/`
É a app mais importante do projeto neste momento. Aqui está a lógica principal ligada a:

- eventos
- inscrições
- participantes
- pagamentos
- check-in
- views públicas
- views internas de gestão
- formulários
- permissões
- serviços de e-mail
- testes

Uma estrutura possível dentro desta app passa por ficheiros como:

```text
events/
├── admin.py
├── apps.py
├── forms.py
├── management_urls.py
├── management_views.py
├── models.py
├── permissions.py
├── urls.py
├── views.py
├── migrations/
├── services/
│   └── emails.py
└── tests/
```

#### `gallery/`
App dedicada à galeria. Serve para separar melhor a lógica de media e evitar misturar tudo dentro da app de eventos.

#### `management/`
Esta pasta/app representa a área de gestão. Faz sentido existir separada porque a gestão não vai ficar limitada apenas a eventos. No futuro pode incluir outras áreas como conteúdos, media, equipas, relatórios ou outras ferramentas internas.

#### `static/`
Aqui ficam os ficheiros estáticos globais do projeto, como:

- CSS
- JavaScript
- imagens
- ícones

É a pasta usada para centralizar o frontend partilhado entre várias páginas.

#### `templates/`
Contém os templates globais do Django. Normalmente é aqui que ficam:

- `base.html`
- includes reutilizáveis
- páginas partilhadas entre apps

## Organização do projeto

A ideia da estrutura foi separar bem as responsabilidades.

Em vez de colocar tudo numa única app, o projeto está dividido por áreas com funções diferentes. Isso ajuda bastante em manutenção, crescimento e clareza do código.

De forma resumida:

- `core` trata da base e páginas gerais
- `events` trata da lógica de eventos e inscrições
- `gallery` trata da galeria
- `management` prepara a área interna de gestão
- `templates` e `static` centralizam a parte visual global
- `church_platform` guarda a configuração do projeto

## Funcionalidades já pensadas na lógica do sistema

Algumas regras de negócio já fazem parte da ideia do projeto e ajudam a aproximá-lo de um caso real:

- uma inscrição pode ter vários participantes
- o controlo de pagamento está ligado à inscrição
- o check-in é feito por participante
- eventos gratuitos podem ser tratados de forma diferente dos pagos
- a área interna de gestão é separada da parte pública
- o projeto está preparado para crescer para mais áreas internas além dos eventos

## Como correr o projeto localmente

### 1. Criar e ativar ambiente virtual

No Windows PowerShell:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Aplicar migrações

```bash
python manage.py migrate
```

### 4. Recolher ficheiros estáticos

```bash
python manage.py collectstatic --noinput
```

### 5. Iniciar o servidor

```bash
python manage.py runserver
```

Depois disso, o projeto fica disponível em:

```text
http://127.0.0.1:8000/
```

## Variáveis de ambiente

Para algumas funcionalidades, especialmente envio de e-mails, é importante configurar variáveis de ambiente no projeto.

Exemplo:

```env
RESEND_API_KEY=sua_chave_aqui
DEFAULT_FROM_EMAIL=seu_email_aqui
```

## Testes

Para correr os testes:

```bash
python manage.py test
```

Os testes servem para validar a lógica principal da aplicação e reduzir o risco de quebrar funcionalidades ao longo da evolução do projeto.

## Objetivo deste projeto

Este projeto foi criado com dois objetivos principais:

1. resolver uma necessidade real da igreja
2. servir como projeto sério de aprendizagem e evolução em Django

Mais do que apenas praticar o framework, a ideia aqui é trabalhar estrutura, organização, regras de negócio, separação de responsabilidades e construção de uma base que faça sentido crescer.

## Estado atual

O projeto já tem uma base sólida e funcional, mas continua em evolução.

Ainda há espaço para melhorar áreas como:

- permissões e grupos
- dashboard de gestão
- relatórios
- exportação de dados
- melhoria da organização interna de algumas áreas
- futura expansão da área de gestão para outras funcionalidades além dos eventos

## Nota final

Este não é um projeto feito apenas para demonstração visual. É um projeto construído para uso real, com preocupação em organização, manutenção e crescimento.

Ao longo do desenvolvimento, o foco tem sido construir de forma limpa, profissional e com lógica de negócio que faça sentido no mundo real.
