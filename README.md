# RepoBlueprint AI

**Arkkitehtuurimoottori** — Välitön, todisteisiin pohjautuva, suoritettava ymmärrys arkkitehtuurista.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-green.svg)

RepoBlueprint AI muuttaa minkä tahansa repositorion kattavaksi arkkitehtuurimalliksi. Se yhdistää AST-pohjaisen jäsennyksen (Tree-sitter) paikallisiin kielimalleihin (Ollama) luodakseen interaktiivisia kaavioita, arkkitehtuurisia oivalluksia ja vertailuja commitien välillä.

## 🌟 Uutta v3.0:ssa: Premium UI/UX & Suomenkielinen Tuki

-   **💎 Miljardin Dollarin Estetiikka**: Täydellinen uudistus modernien SaaS-standardien mukaisesti (Linear, Vercel, Stripe -tyyli).
-   **🇫🇮 Täysin Suomennettu**: Käyttöliittymä on lokalisoitu kokonaan suomeksi.
-   **🎨 Kattava Design System**: Yhtenäinen typografia, välimatkat ja väripaletit ammattimaisen ilmeen takaamiseksi.
-   **✨ Glassmorphism & Animaatiot**: Sulavat interaktiot, lasimaiset kortit ja hienostuneet mikroanimaatiot Framer Motionilla.
-   **📱 Vankka Responsiivisuus**: Grid-pohjaiset asettelut varmistavat täydellisen toimivuuden kaikilla laitteilla ilman sisällön pakkautumista.

## 🚀 Tärkeimmät Ominaisuudet

-   **🧠 Arkkitehtuurin Tietämysverkko (AKG)**: Kartoi komponentit, riippuvuudet ja kerrokset todisteisiin ankkuroiden.
-   **🔍 Luonnollisen Kielen Kyselyt**: Kysy kysymyksiä kuten "Missä autentikaatiologiikka sijaitsee?" tai "Mitä riippuvuuksia User-palvelulla on?".
-   **🔄 Blueprint Diff**: Vertaa arkkitehtuuria haarojen tai commitien välillä havaitaksesi rikkovat muutokset.
-   **📊 Interaktiiviset Kaaviot**: Automaattisesti generoidut C4 Context, Container ja Component -kaaviot (Mermaid.js).
-   **📑 Monimuotoinen Vienti**: Erikoisraportit Markdown-, HTML- (offline) ja JSON-muodoissa.
-   **🔐 100% Paikallinen Yksityisyys**: Toimii kokonaan omalla koneellasi Ollaman avulla. Lähdekoodisi ei koskaan poistu ympäristöstäsi.

## 🛠️ Tekninen Pino

-   **Backend**: Python 3.11, FastAPI, NetworkX, GitPython, Tree-sitter
-   **Frontend**: Next.js 15, TypeScript, Tailwind CSS, Shadcn/UI, Framer Motion
-   **AI/ML**: Ollama (Qwen2.5-Coder / Llama 3), LangChain
-   **Infrastructure**: Docker, Docker Compose

## 🏁 Pika-aloitus

### Esivaatimukset

-   [Docker & Docker Compose](https://www.docker.com/products/docker-desktop/)
-   [Ollama](https://ollama.com/) käynnissä paikallisesti (oletus: `http://localhost:11434`)

### Aja Dockerilla

```bash
# 1. Kloonaa repositorio
git clone https://github.com/harleysederholm-alt/BluePrint.git
cd BluePrint

# 2. Käynnistä sovellus
docker-compose up --build
```

Avaa sovellus:
-   **Frontend**: [http://localhost:3000](http://localhost:3000)
-   **Backend API**: [http://localhost:8000/docs](http://localhost:8000/docs)

### Manuaalinen Asennus (Kehitys)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # tai `venv\Scripts\activate` Windowsilla
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## 📖 Käyttöoppaat

### Repositorion Analysointi
1.  Syötä GitHub/GitLab URL etusivulla.
2.  Valitse kohdeyleisöprofiili (Insinööri, Johtaja, Arkkitehti).
3.  Seuraa reaaliaikaista analyysia, kun agentit jäsentävät koodia ja rakentavat graafia.

### Graafin Kysely
Käytä **Kysely (Query)** -välilehteä esittääksesi kysymyksiä:
-   *"Etsi kaikki kontrollerit maksu-moduulista"*
-   *"Näytä kehäriippuvuudet"*
-   *"Analysoi DataLayerin monimutkaisuus"*

### Raporttien Vienti
Klikkaa **Vie (Export)** -painiketta ladataksesi:
-   `Analysis.md` - Kattava arkkitehtuuriraportti.
-   `Analysis.html` - Itsenäinen offline-raportti interaktiivisilla kaavioilla.

## 🧪 Testaus

```bash
# Backend testit
cd backend && pytest

# Frontend tyyppitarkistus
cd frontend && npx tsc --noEmit
```

## 📄 Lisenssi

MIT © 2026 RepoBlueprint AI
