# FoundLab Backend

Bem-vindo ao repositório do FoundLab Backend!

Este projeto é a espinha dorsal da FoundLab, uma infraestrutura de reputação digital que conecta TradFi (Finanças Tradicionais) e Web3. Desenvolvido com FastAPI e MongoDB, ele oferece uma suíte modular de ferramentas para avaliação de reputação, detecção de fraude, compliance e muito mais.

## Módulos Principais

*   **ScoreLab**: Calcula o `P(x)` (probabilidade de reputação) com base em diversas flags e metadados.
*   **DFC (Dynamic Flag Engine)**: Gerencia e aplica flags dinâmicas, permitindo a definição de regras flexíveis para categorizar entidades.
*   **Sherlock**: Um validador reputacional que integra com provedores externos (simulados para esta POC, como Chainalysis) para consultas de compliance.
*   **SigilMesh**: Cria metadados para NFTs de reputação, incorporando scores e atributos relevantes.
*   **Sentinela**: Um sistema de trigger de risco que dispara alertas com base em scores e regras pré-definidas.
*   **GasMonitor**: Analisa padrões de consumo de gás para detecção de anomalias e potencial fraude.

## Tecnologias Utilizadas

*   **Framework Web**: FastAPI
*   **Banco de Dados**: MongoDB (com Motor para operações assíncronas)
*   **Gerenciamento de Dependências**: Poetry
*   **Containerização**: Docker, Docker Compose
*   **Testes**: Pytest, Pytest-Asyncio, PyMongo-InMemory
*   **CI/CD**: GitHub Actions
*   **Linting/Formating**: Ruff

## Como Rodar o Projeto

### Pré-requisitos

*   Python 3.11 ou superior
*   Poetry (instale com `pip install poetry`)
*   Docker e Docker Compose

### 1. Configuração do Ambiente

Clone o repositório:

```bash
git clone https://github.com/irelia0nerf/DEP.gitfoundlab_backend
cd foundlab_backend
```

Configure o ambiente virtual e as dependências:

```bash
make setup
```

Isso instalará as dependências usando Poetry e criará um arquivo `.env` a partir do `.env.example`. Você pode editar o `.env` para alterar a URL do MongoDB, por exemplo.

### 2. Executando Localmente (Sem Docker)

Certifique-se de ter uma instância do MongoDB rodando localmente (na porta 27017, ou ajuste no `.env`). Se não tiver, pode iniciar uma com Docker:

```bash
docker run --rm --name mongo_local -p 27017:27017 -d mongo:latest
```

Então, inicie a aplicação FastAPI:

```bash
make run
```

A API estará disponível em `http://localhost:8000`.

### 3. Executando com Docker Compose

Esta é a maneira recomendada para desenvolvimento e deploy, pois inclui o MongoDB.

```bash
make run_docker
```

Isso construirá as imagens Docker (se necessário) e iniciará os contêineres para a API e o MongoDB.

A API estará disponível em `http://localhost:8000`.
Para parar os contêineres:

```bash
make stop_docker
```

### 4. Acessando a Documentação da API

Uma vez que a API esteja rodando, você pode acessar a documentação interativa:

*   **Swagger UI**: `http://localhost:8000/docs`
*   **ReDoc**: `http://localhost:8000/redoc`

## Endpoints Principais

A API é dividida em módulos com rotas específicas:

*   **Monitoramento**:
    *   `GET /health`: Verifica a saúde da aplicação.
    *   `GET /version`: Retorna a versão da aplicação.

*   **ScoreLab (`/scores`)**:
    *   `POST /scores`: Calcula e armazena um novo score de reputação.
    *   `GET /scores/{score_id}`: Recupera um score pelo ID.
    *   `GET /scores/entity/{entity_id}`: Recupera todos os scores para uma entidade.

*   **DFC (`/flags`)**:
    *   `POST /flags/definitions`: Cria uma nova definição de flag.
    *   `GET /flags/definitions`: Recupera todas as definições de flags.
    *   `GET /flags/definitions/{flag_name}`: Recupera uma definição de flag por nome.
    *   `PUT /flags/definitions/{flag_name}`: Atualiza uma definição de flag.
    *   `DELETE /flags/definitions/{flag_name}`: Deleta uma definição de flag.
    *   `POST /flags/apply`: Aplica flags dinâmicas a uma entidade com base em metadados.

*   **Sherlock (`/sherlock`)**:
    *   `POST /sherlock/validate`: Realiza validação reputacional de uma entidade (com provedores mockados).
    *   `GET /sherlock/{entity_id}`: Recupera resultados de validação histórica para uma entidade.

*   **SigilMesh (`/nft`)**:
    *   `POST /nft/metadata`: Gera metadados para NFTs de reputação com base em um score.

*   **Sentinela (`/sentinela`)**:
    *   `POST /sentinela/triggers`: Cria novas regras de trigger de risco.
    *   `GET /sentinela/triggers`: Recupera todas as regras de trigger de risco.
    *   `GET /sentinela/triggers/{trigger_name}`: Recupera uma regra de trigger por nome.
    *   `PUT /sentinela/triggers/{trigger_name}`: Atualiza uma regra de trigger.
    *   `DELETE /sentinela/triggers/{trigger_name}`: Deleta uma regra de trigger.
    *   `POST /sentinela/assess`: Avalia o risco de uma entidade com base em score e flags.

*   **GasMonitor (`/gasmonitor`)**:
    *   `POST /gasmonitor/ingest`: Ingesta um novo registro de consumo de gás.
    *   `GET /gasmonitor/records/{entity_id}`: Recupera registros de consumo de gás para uma entidade.
    *   `POST /gasmonitor/analyze/{entity_id}`: Analisa padrões de consumo de gás para detecção de anomalias (lógica simplificada).

## Testes

Os testes são escritos com `pytest` e `pytest-asyncio`, utilizando um MongoDB in-memory (`pymongo-inmemory`) para garantir isolamento e velocidade.

Para rodar os testes e verificar a cobertura:

```bash
make coverage
```

A cobertura deve ser `>= 90%`.

## CI/CD com GitHub Actions

O arquivo `.github/workflows/ci_cd.yml` configura um pipeline de CI/CD que:

1.  Faz Checkout do código.
2.  Configura o Python 3.11.
3.  Instala as dependências com Poetry.
4.  Executa o linter (`ruff`).
5.  Executa os testes (`pytest`) com relatório de cobertura.
6.  Faz upload do relatório de cobertura para o Codecov.
7.  Constrói a imagem Docker (dry run).

## Contribuições

Este projeto foi desenvolvido como uma primeira versão funcional. Contribuições, sugestões ou melhorias são bem-vindas!