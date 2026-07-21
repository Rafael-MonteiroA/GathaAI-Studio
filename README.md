<div align="left">

<!-- <img src="assets/logo.png" alt="GathaAI Studio" width="800"> Se tiver uma logo, pode descomentar essa linha -->
<h1>GathaAI Studio</h1>

---
<p>
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white">
  <img src="https://img.shields.io/badge/Ollama-Local-000000?style=for-the-badge">
</p>

<img src="https://img.shields.io/github/stars/Rafael-MonteiroA/GathaAI-Studio?style=flat-square">
<img src="https://img.shields.io/github/forks/Rafael-MonteiroA/GathaAI-Studio?style=flat-square">
<img src="https://img.shields.io/github/license/Rafael-MonteiroA/GathaAI-Studio?style=flat-square">

---

# 📖 Sobre

O **GathaAI Studio** é a evolução web do GathaAI, um ambiente completo e moderno para interagir com inteligências artificiais. Ele possui uma arquitetura robusta separada em frontend e backend, oferecendo:

- 🎨 Interface de usuário rica e moderna
- ⚡ Respostas em tempo real via Streaming (SSE)
- 💾 Persistência em banco de dados relacional
- 🔄 Gerenciamento rápido utilizando cache
- 🤖 Utilização fluida de modelos locais via Ollama

---

# ✨ Funcionalidades

| Recurso | Descrição |
|----------|----------|
| 🖥️ Frontend Web | Interface moderna e responsiva construída com Next.js |
| ⚡ Backend Assíncrono | API extremamente veloz com FastAPI (Python) |
| 🧠 Memória Persistente | Histórico salvo via PostgreSQL + SQLAlchemy |
| 🚀 Cache e Estado | Otimização de performance utilizando Redis |
| 🤖 IA Local | Integração nativa com Ollama |
| 🌊 Streaming (SSE) | Resposta visual contínua token a token, com exibição de "raciocínio" |
| 🐳 Dockerizado | Configuração e deploy simplificados via Docker Compose |

---

# 🚀 Instalação

## Pré-requisitos
- [Node.js](https://nodejs.org/)
- [Docker e Docker Compose](https://www.docker.com/)
- [Ollama](https://ollama.com/) (para rodar a IA localmente)

## Clonar repositório

```bash
git clone https://github.com/Rafael-MonteiroA/GathaAI-Studio.git
cd GathaAI-Studio
```

## Configurar Variáveis de Ambiente

Crie uma cópia do arquivo de exemplo para carregar as senhas e chaves padrão:

Copie o arquivo `.env.example` e renomeie a cópia exatamente para `.env` (na pasta principal do projeto).

---

# 🤖 Modelo Local

Instale o Ollama em sua máquina:
https://ollama.com

Baixe o modelo recomendado do projeto:

```bash
ollama pull qwen3:8b
```

---

# ▶️ Executando

## 1. Subindo o Backend (Banco de Dados, Redis e API)

Com o Docker em execução na sua máquina, abra o terminal na pasta principal do projeto e rode:

```bash
docker-compose up -d --build
```
*(O backend FastAPI ficará disponível em `http://localhost:8000`)*

## 2. Subindo o Frontend (Interface Web)

Abra outro terminal, navegue até a pasta do frontend e inicie a aplicação:

```bash
cd frontend
npm install
npm run dev
```
*(A interface web estará disponível no navegador em `http://localhost:3000`)*

---

# 🔒 Segurança

✅ Chaves, senhas de banco e variáveis no arquivo `.env` (protegido e ignorado pelo Git).

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

**Frontend:**
- Next.js (React)
- Tailwind CSS
- Zustand (Gerenciador de Estado Global)
- Lucide Icons (Ícones)

---
<div align="left">

## Created by Rafael Monteiro

</div>
