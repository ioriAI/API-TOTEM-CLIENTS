# NETRIS-IMAGO-API-TOTEM

![Imago Radiologia](https://imagoradiologia.com.br/wp-content/themes/imago/images/imago-logomarca-header-1.png)

Esta API permite automatizar o processo de consulta e obtenção de dados do sistema PACS Imago Radiologia, especificamente para a funcionalidade de Atendimentos Totem por Chegada.

## Índice

1. [Visão Geral](#visão-geral)
2. [Requisitos do Sistema](#requisitos-do-sistema)
3. [Instalação](#instalação)
4. [Configuração](#configuração)
5. [Usando a API](#usando-a-api)
6. [Integração com n8n](#integração-com-n8n)
7. [Resolução de Problemas](#resolução-de-problemas)
8. [Modo de Inspeção](#modo-de-inspeção)

## Visão Geral

Esta aplicação usa automação de navegador para:

1. Fazer login no sistema PACS Imago Radiologia
2. Navegar até a tela de "Atendimentos Totem por Chegada"
3. Aplicar filtros (opcional)
4. Extrair os dados da tabela de resultados
5. Retornar os dados em formato JSON

A automação é feita usando [Playwright](https://playwright.dev/), que controla um navegador real, e [FastAPI](https://fastapi.tiangolo.com/) para expor um endpoint de API simples.

## Requisitos do Sistema

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)
- Docker (opcional, para execução em contêiner)

## Instalação

### Opção 1: Instalação direta (sem Docker)

1. Clone este repositório:
   ```
   git clone [URL do repositório]
   cd NETRIS-IMAGO-API-TOTEM-master
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Instale os navegadores necessários para o Playwright:
   ```
   playwright install chromium
   ```

### Opção 2: Usando Docker

1. Clone este repositório:
   ```
   git clone [URL do repositório]
   cd NETRIS-IMAGO-API-TOTEM-master
   ```

2. Construa a imagem Docker:
   ```
   docker build -t imago-api .
   ```

3. Execute o contêiner:
   ```
   docker run -p 8000:8000 imago-api
   ```

## Configuração

### Configuração de variáveis de ambiente

Você pode configurar as credenciais de login usando variáveis de ambiente. Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:

```
j_username=seu_usuario
j_password=sua_senha
```

**Observação**: Você também pode fornecer estas credenciais diretamente na chamada de API, sem necessidade de configurar o arquivo `.env`.

## Usando a API

A API possui apenas um endpoint principal:

### POST /scrape

Este endpoint executa o processo de login e extração de dados do sistema PACS Imago Radiologia.

**URL**: `http://localhost:8000/scrape`

**Método**: `POST`

**Corpo da requisição (JSON)**:

```json
{
  "j_username": "seu_usuario",
  "j_password": "sua_senha",
  "headless": true,
  "viewport_width": 1280,
  "viewport_height": 800,
  "filter_options": {
    "grupo_totem": "Selecione um grupo totem",
    "guiche": "Selecione um guichê",
    "tipo": "Selecione um tipo",
    "prioridade": "Selecione uma prioridade",
    "modalidade": "Selecione uma modalidade"
  }
}
```

**Campos obrigatórios**:
- `j_username`: Seu nome de usuário para login no sistema PACS
- `j_password`: Sua senha para login no sistema PACS

**Campos opcionais**:
- `headless`: Se `true`, o navegador executará em modo invisível (sem interface gráfica). Recomendado `true` para servidores. (padrão: `true`)
- `viewport_width`: Largura da janela do navegador (padrão: 1280)
- `viewport_height`: Altura da janela do navegador (padrão: 800)
- `filter_options`: Opções de filtro para a tabela de resultados (todas são opcionais)
  - `grupo_totem`: Filtro de grupo totem
  - `guiche`: Filtro de guichê
  - `tipo`: Filtro de tipo
  - `prioridade`: Filtro de prioridade
  - `modalidade`: Filtro de modalidade

**Resposta bem-sucedida**:

```json
{
  "status": "success",
  "data": [
    {
      "paciente": "NOME DO PACIENTE",
      "atendimento": "123456",
      "convenio": "NOME DO CONVÊNIO",
      "data_chegada": "01/01/2025 10:00",
      "modalidade": "TIPO DE EXAME",
      "prioridade": "NORMAL",
      "guiche": "GUICHÊ 1",
      "status": "AGUARDANDO"
    },
    ...
  ],
  "message": "Dados extraídos com sucesso",
  "timestamp": "2025-03-06T15:30:45.123456"
}
```

**Resposta de erro**:

```json
{
  "status": "failed",
  "data": [],
  "message": "Descrição do erro ocorrido",
  "timestamp": "2025-03-06T15:30:45.123456"
}
```

### GET /

Retorna informações básicas sobre a API.

**URL**: `http://localhost:8000/`

**Método**: `GET`

## Integração com n8n

Para integrar esta API com o [n8n](https://n8n.io/), siga estas etapas:

1. Crie um novo fluxo de trabalho no n8n
2. Adicione um nó "HTTP Request"
3. Configure o nó com as seguintes opções:
   - **Método**: POST
   - **URL**: http://seu-servidor:8000/scrape (substitua "seu-servidor" pelo endereço IP ou nome do host onde a API está rodando)
   - **Corpo da Requisição**: JSON
   ```json
   {
     "j_username": "seu_usuario",
     "j_password": "sua_senha",
     "headless": true
   }
   ```
   - **Opções Avançadas**: Aumente o timeout para pelo menos 60000ms (60 segundos), pois o processo de automação pode levar algum tempo

4. Conecte o nó "HTTP Request" a outros nós para processar os dados recebidos

**Importante**: O nó n8n esperará até que a API complete todo o processo (login, navegação, extração de dados) e retorne o resultado, sem necessidade de verificações adicionais.

## Resolução de Problemas

### Problemas comuns:

1. **Erro de autenticação**:
   - Verifique se as credenciais (j_username e j_password) estão corretas
   - Confirme que você tem acesso ao sistema PACS com essas credenciais

2. **Timeout durante a execução**:
   - Aumente os valores de timeout para requisições
   - Verifique a conexão com a internet
   - Verifique se o site do PACS está acessível

3. **Erro ao iniciar o navegador**:
   - Se estiver usando Docker, verifique se a imagem foi construída corretamente
   - Se estiver instalando localmente, certifique-se de que o Playwright foi instalado com `playwright install chromium`

4. **Dados não retornados**:
   - Verifique se os filtros aplicados retornam algum resultado
   - Use o [Modo de Inspeção](#modo-de-inspeção) para identificar alterações na estrutura da página

### Verificação de logs:

Se estiver executando a API diretamente:
```
python api.py
```

Se estiver usando Docker:
```
docker logs [nome-ou-id-do-container]
```

## Modo de Inspeção

O projeto inclui um modo de inspeção que permite visualizar o processo de automação e identificar elementos na página. Isso é útil para:

- Entender como a automação funciona
- Identificar mudanças na estrutura da página
- Resolver problemas de automação

Para executar o modo de inspeção:

```
python inspector_mode.py
```

Isso abrirá:
1. Um navegador mostrando o processo de login
2. Uma janela do Playwright Inspector que permite interagir com os elementos da página

Siga as instruções exibidas no terminal para usar o Inspector.

---

## Licença

Este projeto é para uso interno e não está licenciado para distribuição pública.

---

*Última atualização: Março 2025*
# API-TOTEM-CLIENTS
