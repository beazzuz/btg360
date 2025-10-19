# Arquivo: cerebro.py
import google.generativeai as genai
from google.generativeai.types import Tool
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

# --- CONFIGURAÇÃO ---
try:
    genai.configure(api_key="AIzaSyDMiRzuKh2Hkd_VDy_MjOR0VKkrUSAEySI")
except Exception as e:
    print(f"Erro ao configurar a API no cerebro.py: {e}")
    exit()

# --- DEFINIÇÃO DAS FERRAMENTAS (Versão Aprimorada com Exemplos) ---
MINHAS_FERRAMENTAS = [
    {
       "name": "analisar_gastos_com_ia",
        "description": "Analisa os gastos de um cliente para um mês específico.",
        "parameters": { "type": "OBJECT", "properties": {"mes": {"type": "STRING", "description": "O mês para a análise, ex: 'setembro'."}}, "required": ["mes"]}
    },
    {
        "name": "iniciar_plano_de_riqueza",
        "description": "Inicia um plano de investimento complexo (Wealth Management) para metas de médio e longo prazo, que exige cálculo de aporte e avaliação de risco. Extrai o valor e a finalidade da meta a partir da conversa.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "valor_meta": {"type": "NUMBER", "description": "O valor total da meta. Ex: 100000, 4500."},
                "finalidade": {"type": "STRING", "description": "O objetivo do cliente. Ex: 'comprar uma casa', 'viajar para o Japão'."},
                "prazo_limite": {"type": "STRING", "description": "O prazo máximo que o cliente quer atingir a meta, ex: '3 anos', '2027'"}
            },
            "required": ["valor_meta", "finalidade"]
        }
    },
    {
        "name": "alertar_gastos_com_ia",
        "description": "Cria um limite de gastos para uma categoria específica e verifica o status atual.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "categoria": {"type": "STRING", "description": "A categoria de gasto a ser monitorada. Ex: 'Alimentação', 'Moradia'."},
                "limite_maximo": {"type": "NUMBER", "description": "O valor máximo de gasto estipulado. Ex: 1000, 800."}
            },
            "required": ["categoria", "limite_maximo"]
        }
    },
    {
        "name": "manipular_caixinha_investimento",
        "description": "Cria uma nova 'Caixinha' de investimento ou adiciona valor a uma existente ou **CONSULTA O SALDO ATUAL** (Asset Management) de uma caixinha de investimento existente. Ideal para *metas de curto prazo, reserva de emergência e objetivos simples*, com foco em liquidez e self-service. Igual ao Asset Management do btg.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "nome_caixinha": {"type": "STRING", "description": "O nome que o cliente deu à caixinha, ex: 'caixa2', 'viagem'."},
                "valor_aporte": {"type": "NUMBER", "description": "O valor que o cliente deseja adicionar (opcional na criação). Ex: 1000, 500. Se for criação, o valor inicial."}
            },
            "required": ["nome_caixinha"]
        }
    },
]
DATA_ATUAL_HOJE = datetime.now()
MODELO = 'gemini-2.5-flash'
INSTRUCAO_SISTEMA = (f"""
Você é um **Consultor Financeiro Sênior e Proativo do BTG Pactual**. Sua função primária é facilitar a gestão financeira do usuário e atuar como um concierge de metas e investimentos. Seu tom é profissional, acessível, e você deve usar emojis, negrito e boa formatação para rápida visualização.

**[DATA ATUAL CRÍTICA]: Hoje é {DATA_ATUAL_HOJE}. Use esta data como referência para todos os cálculos de prazo.**

Para respostas quem envolvam tempo ou datas, utilize a [DATA ATUAL CRÍTICA] como base, por exemplo, para interpretar prazos como 'mês que vem' ou 'em 3 meses'. Além disso, sempre converta meses sem ano para o formato 'nome do mês de AAAA', considerando a [DATA ATUAL CRÍTICA]. Exemplo: se hoje é junho de 2024 e o usuário menciona 'setembro', interprete como 'setembro de 2024'. 

**Funções e Permissões:**
* Você tem acesso à conta bancária e permissões para simular transações, PIX e pagamentos, mas **NUNCA** execute uma transação sem uma confirmação explícita do usuário.
* Assuma que você pode programar mensagens de lembrete (embora esta função seja apenas simulada no momento).
* Você tem acesso a todas as APIs de investimento do BTG e conhece todos os serviços.

**Regras de Ação (Prioridade Máxima):**
1.  **Chamar Ferramentas:** SEMPRE utilize as ferramentas disponíveis ("analisar_gastos_com_ia, iniciar_plano_de_riqueza, alertar_gastos_com_ia") para realizar tarefas financeiras.
2.  **Execução Imediata:** Se a conversa fornecer todos os argumentos necessários, chame a função IMEDIATAMENTE, sem pedir confirmação.
3.  **Contexto e Inferência:** Use o histórico da conversa para inferir argumentos faltantes.
4.  **Noção Temporal:** Se o usuário usar termos como 'mês que vem' ou um mês sem ano, **converta o prazo para o formato 'nome do mês de AAAA'** (ex: 'novembro de 2025', 'janeiro de 2028'), usando a [DATA ATUAL CRÍTICA] como referência. **IMPORTANTE: Se a intenção é ANALISAR GASTOS, use apenas o nome do mês (ex: 'novembro') para o argumento 'mes' da função, ignorando o ano que você inferiu.**

**Regras de Tratamento de Assunto (Coerência):**
5.  **Perguntas Gerais (Foco Financeiro):** Responda a perguntas fora do domínio financeiro de forma breve e, IMEDIATAMENTE, traga o foco de volta para as finanças e ferramentas.
    * *Exemplo:* 'Hoje é {DATA_ATUAL_HOJE}. Gostaria de planejar alguma nova meta?'
6.  **Recusa/Foco em Economia:** Se o usuário não quiser investir, ou quiser apenas economizar, pivote a conversa para a ferramenta de análise de gastos.
    * *Exemplo:* 'Entendo, focar na economia é um ótimo primeiro passo. Qual mês você gostaria de analisar?'
7.  **Agendamento/Encaminhamento:** Se o usuário pedir para 'agendar uma conversa' ou 'falar com alguém', forneça este link e encerre: 'Para falar com um de nossos assessores e dar o próximo passo, use este link: [https://btgpactual.com.br/agendamento].'
8.  **Resposta Desconhecida:** Se não souber a resposta ou faltar informação essencial, peça desculpas e peça mais detalhes para o usuário.
""")

modelo_com_ferramentas = genai.GenerativeModel(
    MODELO,
    system_instruction=INSTRUCAO_SISTEMA,
    tools=MINHAS_FERRAMENTAS
)

# --- NOVA LÓGICA DE MEMÓRIA DE CONVERSA ---
ACTIVE_CHATS = {}

# Arquivo: cerebro.py (Função roteador_ia - VERSÃO MAIS ROBUSTA)

# ... (código omitido) ...

def roteador_ia(mensagem_usuario: str, user_id: str) -> dict:
    """
    Mantém uma sessão de chat contínua para cada usuário e decide a próxima ação.
    """
    global ACTIVE_CHATS
    
    # Se não houver um chat ativo para este usuário, crie um novo.
    if user_id not in ACTIVE_CHATS:
        print(f"DEBUG: Criando nova sessão de chat para {user_id}")
        ACTIVE_CHATS[user_id] = modelo_com_ferramentas.start_chat()
    
    chat = ACTIVE_CHATS[user_id]
    
    try:
        resposta = chat.send_message(mensagem_usuario)
        primeira_parte = resposta.parts[0]

        if hasattr(primeira_parte, 'function_call') and primeira_parte.function_call:
            
            ordem = primeira_parte.function_call
            
            # --- EXTRAÇÃO ROBUSTA DOS ARGUMENTOS ---
            # Converte para dict, o que deve ser seguro
            argumentos = dict(ordem.args)
            
            # GARANTIA DE ARGUMENTOS NULOS para todas as ferramentas que usam argumentos opcionais
            
            # 1. Ferramenta de Planejamento de Meta
            if ordem.name == "iniciar_plano_de_riqueza":
                argumentos['prazo_limite'] = argumentos.get('prazo_limite') # Se não existir, retorna None
            
            # 2. Ferramenta de Análise de Gastos (Apenas 'mes' é obrigatório)
            if ordem.name == "analisar_gastos_com_ia":
                 argumentos['mes'] = argumentos.get('mes')

            # -----------------------------------------------

            # Se a IA chamar uma função, a conversa "de perguntas" termina.
            del ACTIVE_CHATS[user_id]
            
            return {"tipo_acao": "chamar_funcao", "nome_funcao": ordem.name, "argumentos": argumentos}
        else:
           return {"tipo_acao": "responder_texto", "conteudo": resposta.text}
            
    except Exception as e:
        print(f"ERRO no cérebro da IA: {e}")
        # Limpa o chat em caso de erro para recomeçar.
        if user_id in ACTIVE_CHATS: del ACTIVE_CHATS[user_id]
        
        # Resposta mais clara para o usuário sobre o problema
        return {"tipo_acao": "responder_texto", "conteudo": "Desculpe, ocorreu um erro técnico na comunicação. Por favor, tente reformular sua frase, dizendo o valor, a meta e o prazo na mesma mensagem (ex: 'Quero investir 20 mil para a Disney em 2026')."}