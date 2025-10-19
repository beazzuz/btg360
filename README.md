# 🤖 Assistente Financeiro BTG Pactual (Demo Hackathon)

Este projeto demonstra um assistente de IA conversacional para gestão financeira, desenvolvido utilizando a API Gemini (Google AI) e a arquitetura de *Tool Calling* (Chamada de Função). O assistente simula funcionalidades bancárias complexas, como análise de gastos, criação de metas financeiras e alertas para gastos.

## 💡 Conceito e Arquitetura

O projeto é baseado em uma arquitetura modular que separa a inteligência (Gemini), a lógica de negócios (Python) e a simulação de dados.

| Arquivo | Função Principal | Responsabilidade |
| :--- | :--- | :--- |
| `cerebro.py` | Roteador de IA | Contém a lógica de conversação do Gemini. Decidi qual ação tomar: responder com texto ou chamar uma das funções (*Tool Calling*). |
| `espinha.py` | Lógica de Negócios | Implementa as funções que a IA pode chamar (ex: `analisar_gastos`, `alertar_gastos`). Lida com a leitura e escrita do `dados.json`. |
| `classificador.py` | Regras de Categoria | Contém as regras de classificação de transações (ex: "UBER" vira "Transporte"). |
| `dados.json` | Banco de Dados (Mock) | Simula o banco de dados do usuário, armazenando saldos, metas, transações e alertas. |

## 🛠️ Dependências do Projeto

Para rodar este projeto, você precisará ter o Python instalado (versão 3.8+), uma conta no Google AI Studio, Twilio e ngrok e as bibliotecas listadas abaixo.

### Adicionar`requirements.txt`

### Gerar chave da API do Google

A Chave da API Gemini é o seu token de autenticação, permite que o código Python se conecte e utilize os modelos de Inteligência Artificial do Google.

#### Como Gerar sua Chave

A chave de API é gerada através da plataforma de desenvolvedores do Google AI Studio.

1.  **Acesse o Google AI Studio:**
    * Navegue até o site oficial: https://ai.google.dev/gemini-api/docs/api-key
2.  **Faça Login:**
    * Entre com sua Conta Google.
3.  **Crie a Chave:**
    * Na página de gerenciamento de chaves, clique em "Create API key in a new project" (ou similar) para gerar seu token.
4.  **Copie a Chave:**
    * Uma chave alfanumérica longa (começando com AIzaSy...) será exibida. Copie-a imediatamente, pois por motivos de segurança, ela só é mostrada uma vez.

#### Como Adicionar a Chave ao Seu Projeto

A maneira mais segura de injetar a chave no seu projeto é usando **Variáveis de Ambiente**. Isso impede que sua chave seja armazenada em texto simples dentro dos seus arquivos e garante a segurança em ambientes compartilhados ou repositórios Git.

Antes de executar qualquer script Python, você deve definir a variável GEMINI_API_KEY no terminal:

| Sistema Operacional | Comando (SUA_CHAVE_AQUI) |
| :--- | :--- |
| **Linux/macOS** | export GEMINI_API_KEY="SUA_CHAVE_AQUI" |
| **Windows (CMD)** | set GEMINI_API_KEY="SUA_CHAVE_AQUI" |
| **Windows (PowerShell)** | $env:GEMINI_API_KEY="SUA_CHAVE_AQUI" |

### Dependência Opcional: Twilio

O arquivo `app.py` foi originalmente configurado para funcionar como um *webhook* para o Twilio, permitindo que o assistente responda a mensagens de usuários enviadas via WhatsApp.
Para essa parte é necessário ter criado uma conta no Twilio e Ngrok.

**Esta dependência é OBRIGATÓRIA se você quiser usar o assistente através de um canal de mensagens, mas é OPCIONAL para testes de desenvolvimento local.**

#### Rodando com o Twilio

**Na pasta do projeto**

Passo 1:Configurar o Ambiente Virtual
1. Crie e acesse um diretório para o projeto:
   * mkdir twilio-whatsapp-api
   * cd twilio-whatsapp-api
3. Crie o ambiente virtual:
	* python3 -m venv .venv
4. Ative o ambiente
	* source .venv/bin/activate

Você saberá que funcionou porque o nome (.venv) aparecerá no início do seu prompt do terminal, assim:
(.venv) User@User:~/twilio-whatsapp-api$

Passo 2: Preparar o Ambiente Python
1. Instalar pacotes necessários:
	* pip install flask
	* pip install twilio
	* pip install google-generativeai
	* pip install python-dateutil

Passo 3: Rodar a API Flask Localmente
1. Inicie o servidor
 	* python3 app.py

**EM OUTRO TERMINAL**

1. Inicie o Ngrok:
 	* ngrok http 5000
2. Copie a URL Forwarding:
	* Forwarding      https://SEU_CODIGO_ALEATORIO.ngrok-free.app -> http://localhost:5000

Passo 4: Conectar Twilio ao Ngrok 
O passo final é dizer ao Twilio para enviar as mensagens de WhatsApp para o seu novo endereço público do Ngrok.

1. Acesse o Console do Twilio: Faça login na sua conta Twilio.
2. Vá para o Sandbox do WhatsApp: Navegue até a seção Messaging > Try it out > Send a WhatsApp message. Lá você encontrará as configurações do Sandbox.
3. Configure o Webhook: Encontre o campo chamado "WHEN A MESSAGE COMES IN".
   * Cole a URL do Ngrok que você copiou.
   * Adicione a rota da sua API que recebe as mensagens. Pelos seus logs, a rota é /whatsapp.
   * A URL final ficará assim: https://3ae68670333a.ngrok-free.app/whatsapp
   * Verifique se o método está configurado como HTTP POST.
4. Salve as alterações.
