<div align="left">

<!-- <img src="assets/logo.png" alt="GathaAI Studio" width="800"> Se tiver uma logo, pode descomentar essa linha -->
<h1>GathaAI Studio</h1>

---
<p>
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white">
  <img src="https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge">
  <img src="https://img.shields.io/badge/Ollama-Local-000000?style=for-the-badge">
</p>

<img src="https://img.shields.io/github/stars/Rafael-MonteiroA/GathaAI-Studio?style=flat-square">
<img src="https://img.shields.io/github/forks/Rafael-MonteiroA/GathaAI-Studio?style=flat-square">
<img src="https://img.shields.io/github/license/Rafael-MonteiroA/GathaAI-Studio?style=flat-square">

---

# 📖 Sobre

O **GathaAI Studio** é a evolução web do GathaAI, um ambiente completo e moderno para interagir com inteligências artificiais. Ele possui uma arquitetura robusta separada em frontend e backend, oferecendo:

- 🎨 Interface escura e minimalista (preto/cinza)
- ⚡ Respostas em tempo real via Streaming (SSE)
- 💾 Persistência em banco de dados relacional
- 🔄 Gerenciamento rápido utilizando cache
- 🤖 Suporte a múltiplos provedores de IA (Ollama, Groq, OpenAI, OpenRouter)
- 🧠 Memory Engine com busca semântica via ChromaDB
- 🔐 Armazenamento criptografado de chaves de API (Fernet/AES)

---

# ✨ Funcionalidades

| Recurso | Descrição |
|----------|----------|
| 🖥️ Frontend Web | Interface moderna e responsiva construída com Next.js |
| ⚡ Backend Assíncrono | API extremamente veloz com FastAPI (Python) |
| 🧠 Memória Persistente | Histórico salvo via PostgreSQL + SQLAlchemy |
| 🚀 Cache e Estado | Otimização de performance utilizando Redis |
| 🤖 Multi-Provider | Ollama (local), Groq, OpenAI, OpenRouter — troque por conversa |
| 🧠 Memory Engine | Recall semântico de conversas passadas via ChromaDB |
| 🌊 Streaming (SSE) | Resposta visual contínua token a token, com exibição de "raciocínio" |
| ⚙️ Settings por Conversa | Model override, temperatura e system prompt customizável |
| 📤 Export | Exporte conversas em JSON ou Markdown |
| 🛡️ Rate Limiting | Proteção contra abuso via slowapi |
| 🔐 BYOK (Bring Your Own Key) | Adicione suas chaves de API na UI — armazenadas com criptografia |
| 🐳 Dockerizado | Configuração e deploy simplificados via Docker Compose |

---

# 🏗️ Arquitetura

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│  Next.js     │     │  Backend (FastAPI)                        │
│  Frontend    │────▶│                                          │
│  :3000       │ SSE │  ┌──────────┐  ┌──────────┐  ┌────────┐ │
└─────────────┘     │  │ Chat     │  │ Memory   │  │Settings│ │
                    │  │ Service  │  │ Engine   │  │  API   │ │
                    │  └────┬─────┘  └────┬─────┘  └────────┘ │
                    │       │             │                    │
                    │  ┌────▼─────────────▼────┐               │
                    │  │   Provider Factory     │               │
                    │  │  Ollama│Groq│OpenAI│OR │               │
                    │  └───────────────────────┘               │
                    └───────┬──────────┬───────────┬───────────┘
                            │          │           │
                    ┌───────▼──┐ ┌─────▼────┐ ┌───▼─────┐
                    │PostgreSQL│ │ ChromaDB │ │  Redis  │
                    │  :5432   │ │  :8100   │ │  :6379  │
                    └──────────┘ └──────────┘ └─────────┘
```

---

# 🚀 Instalação

## Pré-requisitos
- [Node.js](https://nodejs.org/) (v18+)
- [Docker e Docker Compose](https://www.docker.com/)
- [Ollama](https://ollama.com/) (para rodar a IA localmente)

## Clonar repositório

```bash
git clone https://github.com/Rafael-MonteiroA/GathaAI-Studio.git
cd GathaAI-Studio
```

## Configurar Variáveis de Ambiente

Copie o arquivo de exemplo e ajuste conforme necessário:

```bash
cp .env.example .env
```

> Para uso local de desenvolvimento, os valores padrão já funcionam sem alterações.

---

# 🤖 Modelo Local

Instale o Ollama em sua máquina:
https://ollama.com

Baixe o modelo recomendado do projeto:

```bash
ollama pull qwen3:8b
```

> Qualquer modelo do Ollama é suportado. Você pode trocar o modelo por conversa na interface.

---

# ▶️ Executando

## 1. Subindo o Backend (Banco de Dados, Redis, ChromaDB e API)

Com o Docker em execução na sua máquina, abra o terminal na pasta principal do projeto e rode:

```bash
docker compose up -d --build
```

Serviços que serão iniciados:
| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Backend (FastAPI) | `8000` | API principal |
| PostgreSQL | `5433` | Banco de dados |
| Redis | `6380` | Cache e rate limiting |
| ChromaDB | `8100` | Vector store (Memory Engine) |

## 2. Subindo o Frontend (Interface Web)

Abra outro terminal, navegue até a pasta do frontend e inicie a aplicação:

```bash
cd frontend
npm install
npm run dev
```
*(A interface web estará disponível no navegador em `http://localhost:3000`)*

## 3. Verificar saúde do sistema

```bash
curl http://localhost:8000/health
```

---

# 🔌 Provedores de IA Suportados

| Provider | Tipo | Configuração |
|----------|------|-------------|
| **Ollama** | Local (gratuito) | Funciona automaticamente — nenhuma chave necessária |
| **Groq** | Cloud (freemium) | Adicione sua API key via Settings na interface |
| **OpenAI** | Cloud (pago) | Adicione sua API key via Settings na interface |
| **OpenRouter** | Cloud (multi-modelo) | Adicione sua API key via Settings na interface |

> As chaves de API são armazenadas com criptografia AES (Fernet) no banco de dados. Nenhum dado é enviado para fora da sua máquina sem sua autorização explícita.

---

# 🔒 Segurança

✅ Chaves, senhas de banco e variáveis no arquivo `.env` (protegido e ignorado pelo Git).

✅ API keys de provedores criptografadas com Fernet (AES-128-CBC) antes de salvar no banco.

✅ Validação de segredos em produção — o sistema recusa iniciar com credenciais padrão em modo produção.

✅ Rate limiting em todos os endpoints (proteção contra abuso).

✅ Uso de Docker para isolamento do banco e serviços locais.

✅ Totalmente compatível com IA local (Ollama), sem envio de dados confidenciais para fora da sua máquina.

---

# 📦 Tecnologias Principais

**Backend:**
- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 + Asyncpg
- Alembic (Migrações)
- Redis
- ChromaDB (Vector Store)
- slowapi (Rate Limiting)
- cryptography (Fernet)

**Frontend:**
- Next.js 16 (React 19)
- Tailwind CSS v4
- Zustand (Gerenciador de Estado Global)
- Framer Motion (Animações)
- Lucide Icons (Ícones)
- shadcn/ui (Componentes base)

---

# 📁 Estrutura do Projeto

```
GathaAI-Studio/
├── backend/
│   ├── api/v1/            # Endpoints REST (conversations, settings, export, health)
│   ├── domain/            # Models SQLAlchemy (Conversation, Message, Settings, ProviderKey)
│   ├── infra/
│   │   ├── db/            # Database engine + migrations (Alembic)
│   │   ├── providers/     # Adapters LLM (Ollama, Groq, OpenAI, OpenRouter)
│   │   └── vector/        # ChromaDB client
│   ├── services/
│   │   ├── chat/          # Chat service + prompt builder
│   │   └── memory/        # Memory Engine (semantic recall)
│   ├── config.py          # Settings com validação de produção
│   └── main.py            # App FastAPI + lifespan
├── frontend/
│   └── src/
│       ├── app/           # Next.js pages + globals.css
│       ├── components/    # Chat, Layout, Settings, UI
│       ├── lib/           # API client functions
│       └── store/         # Zustand stores
├── docker/                # Dockerfiles
├── docker-compose.yml     # Orquestração de todos os serviços
├── .env.example           # Template de variáveis de ambiente
└── README.md
```

---
<div align="left">

## Created by Rafael Monteiro

</div>
