# Arquivo: espinha.py
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import google.generativeai as genai
import math
# --- CONFIGURAÇÃO ---
try:
    # IMPORTANTE: Coloque sua chave de API aqui também
   genai.configure(api_key="AIzaSyDMiRzuKh2Hkd_VDy_MjOR0VKkrUSAEySI")
except Exception as e:
    print(f"Erro ao configurar a API no espinha.py. Verifique sua chave. Erro: {e}")
    exit()

MODELO_PROCESSADOR = 'gemini-2.5-flash'
data_hoje = datetime.now()

def processar_com_ia(prompt: str) -> dict:
    model = genai.GenerativeModel(MODELO_PROCESSADOR)
    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(json_text)
    except Exception as e:
        print(f"ERRO ao processar com IA: {e}")
        return {"erro": "Não foi possível processar a solicitação com a IA."}
    
# Arquivo: espinha.py

# ... (restante dos imports) ...

data_atual = datetime.now()

def converter_prazo_para_meses(prazo_limite_str: str) -> int:
    """
    Converte uma string de prazo (ex: '2027', '3 anos', '18 meses', 'janeiro de 2028')
    para o número de meses restantes a partir de agora.
    """
    agora = datetime.now()
    s = (prazo_limite_str or "").strip().lower()

    meses_map = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }

    # Caso A: ano puro (ex: "2027")
    if len(s) == 4 and s.isdigit():
        try:
            ano_meta = int(s)
            data_meta = datetime(ano_meta, 12, 31)
            diff = relativedelta(data_meta, agora)
            return max(0, diff.years * 12 + diff.months + (1 if diff.days > 0 else 0))
        except ValueError:
            pass

    # Caso B: "mês de AAAA" (ex: "janeiro de 2028", "novembro 2026")
    for nome_mes, num_mes in meses_map.items():
        if nome_mes in s:
            partes = s.replace("de", " ").split()
            ano = next((int(p) for p in partes if p.isdigit() and len(p) == 4), None)
            if ano:
                try:
                    data_meta = datetime(ano, num_mes, 1)
                    diff = relativedelta(data_meta, agora)
                    return max(0, diff.years * 12 + diff.months + (1 if diff.days > 0 else 0))
                except ValueError:
                    pass
            break  # havia um mês, mas ano não entendido

    # Caso C: "X anos"
    if "ano" in s:
        for p in s.split():
            if p.isdigit():
                return int(p) * 12

    # Caso D: "X meses"
    if "mes" in s or "mês" in s:
        for p in s.replace("mês", "mes").split():
            if p.isdigit():
                return int(p)

    # Caso desconhecido
    return 0


# Arquivo: espinha.py (Função analisar_gastos_com_ia CORRIGIDA para Precisão de Cálculo)

# ... (outros imports e funções) ...

# Arquivo: espinha.py (Função analisar_gastos_com_ia CORRIGIDA para o NameError)

# ... (outros imports e funções) ...

# Arquivo: espinha.py (Função analisar_gastos_com_ia - VERSÃO FINAL COMPLETA)

# Lembre-se de que as funções processar_com_ia e os imports (datetime, json, math)
# devem estar no topo do arquivo.

def analisar_gastos_com_ia(mes: str) -> dict:
    with open('dados.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)

    meses_map = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    # Extrai o nome do mês (ignora 'de 2025' ou qualquer coisa após a primeira palavra)
    mes_nome_simples = mes.lower().split()[0]
    mes_atual_num = meses_map.get(mes_nome_simples)

    if mes_atual_num is None:
        return {"erro": "Mês não reconhecido."}
        
    # --- CÁLCULO DE GASTOS COMPLETO (Python) ---
    
    def calcular_gastos(mes_num, ano):
        gastos = {}
        total_gasto = 0.0
        for t in dados['transacoes']:
            data_transacao = datetime.fromisoformat(t['data'])
            if t.get('operacao') == 'debito' and data_transacao.month == mes_num and data_transacao.year == ano:
                categoria = t.get('categoria', 'Outros')
                valor = abs(t['valor'])
                gastos[categoria] = gastos.get(categoria, 0) + valor
                total_gasto += valor
        return gastos, total_gasto

    ano_base = datetime.now().year 

    # Mês Atual
    gastos_mes_atual, total_gasto_atual = calcular_gastos(mes_atual_num, ano_base)
    
    if not gastos_mes_atual:
        return {"total_gasto": 0, "gastos_por_categoria": {}, "insight": "Nenhum gasto encontrado para este mês."}

    # Mês Anterior (Para comparação)
    mes_anterior_num = mes_atual_num - 1
    ano_anterior = ano_base
    if mes_anterior_num == 0:
        mes_anterior_num = 12
        ano_anterior -= 1 
    gastos_mes_anterior, _ = calcular_gastos(mes_anterior_num, ano_anterior)

    # Ordena os gastos do mês atual para inclusão de TODAS as categorias
    gastos_ordenados = sorted(gastos_mes_atual.items(), key=lambda item: item[1], reverse=True)
    todas_as_categorias_gastos = dict(gastos_ordenados) # Inclui todas as categorias

    # Calcula as variações (Para insights)
    insights_comparativos = {}
    todas_categorias = set(gastos_mes_atual.keys()) | set(gastos_mes_anterior.keys())
    
    for categoria in todas_categorias:
        gasto_atual = gastos_mes_atual.get(categoria, 0)
        gasto_anterior = gastos_mes_anterior.get(categoria, 0)

        if gasto_anterior > 0:
            variacao = ((gasto_atual - gasto_anterior) / gasto_anterior) * 100
            insights_comparativos[categoria] = f"{variacao:.1f}%"
        elif gasto_atual > 0:
            insights_comparativos[categoria] = "Novo Gasto"


    # --- PYTHON CRIA A LISTA FORMATADA EXATA ---
    lista_categorias_formatada = ""
    for categoria, valor in todas_as_categorias_gastos.items():
        # Concatena a string exata com R$ X.XX para a IA 'copiar e colar'
        lista_categorias_formatada += f"* {categoria}: R$ {valor:.2f}\n"


    # --- CONSTRUÇÃO DO PROMPT DA IA (FORÇANDO SAÍDA JSON) ---

    prompt = f"""
    Você é um analista financeiro sênior do BTG Pactual. Analise os dados e gere a resposta formatada final.

    **DADOS CRÍTICOS (USE EXATAMENTE ESTES VALORES):**
    - Lista de Categorias Formatada: "{lista_categorias_formatada.strip()}"
    - Gasto Total Exato: R$ {total_gasto_atual:.2f}
    - Insights de Variação: {json.dumps(insights_comparativos, indent=2)}

    Sua tarefa é criar a resposta de texto completa no formato JSON estrito, utilizando os dados fornecidos.

    **Retorne um objeto JSON com a chave "mensagem_final" contendo todo o texto formatado:**
    1.  Comece com: "Ok, aqui está o resumo dos seus gastos de {mes.title()}:"
    2.  Liste TODAS as categorias de gastos usando **EXATAMENTE** a **Lista de Categorias Formatada** fornecida acima (ela já está correta, apenas cole-a).
    3.  Apresente o gasto total: "Seu gasto total no mês foi de R$ {total_gasto_atual:.2f}." (USE ESTE VALOR).
    4.  Finalize com um insight (baseado nos Insights de Variação).

    Responda APENAS com o objeto JSON.
    ```json
    """
    
    # Chama a função de processamento (que tem o try/except)
    resultado_ia = processar_com_ia(prompt)
    
    # Em caso de sucesso, retorna o dicionário JSON (se falhar, retorna o erro do processar_com_ia)
    return resultado_ia
# Arquivo: espinha.py (Nova função de Convite)

def iniciar_plano_de_riqueza(valor_meta: float, finalidade: str, prazo_limite: str = None) -> dict:
    """
    PASSO 1: Calcula o prazo necessário e gera a mensagem de convite/validação (similar ao PS5).
    """
    with open('dados.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    sobra_mensal = dados['usuario']['media_mensal_sobra']

    # ... (Lógica de cálculo de prazo e aporte necessária, como na função anterior) ...
    # (Usaremos o código completo que verifica o prazo limite)
    
    meses_necessarios = math.ceil(valor_meta / sobra_mensal)
    prazo_real_em_meses = meses_necessarios
    mensagem_alerta = ""

    if prazo_limite:
        meses_limite = converter_prazo_para_meses(prazo_limite)
        if meses_limite <= 0:
             # Retorna o erro de prazo no passado
             return {"tipo_resposta": "erro_prazo", "mensagem": f"O prazo limite... [mensagem de erro de prazo]"}
        
        if meses_limite < meses_necessarios:
            prazo_real_em_meses = meses_limite
            aporte_necessario = math.ceil(valor_meta / meses_limite)
            mensagem_alerta = f"ATENÇÃO: Você quer atingir a meta em {meses_limite} meses, mas com seu aporte atual de R$ {sobra_mensal:.2f} levaria {meses_necessarios} meses. Para cumprir o prazo, você precisará aumentar seu aporte mensal para R$ {aporte_necessario:.2f}."
        else:
             prazo_real_em_meses = meses_necessarios
             
    
    # PROMPT PARA GERAR O CONVITE (Pilar 2: PS5)
    prompt = f"""
    Você é um assistente do BTG Pactual. Gere uma mensagem de convite para o usuário iniciar o planejamento de sua meta.
    
    **DADOS:**
    - Finalidade: {finalidade}
    - Valor: R$ {valor_meta:.2f}
    - Prazo Calculado: {prazo_real_em_meses} meses
    - Sobra Mensal: R$ {sobra_mensal:.2f}

    {mensagem_alerta}

    **Sua Tarefa:**
    Crie uma mensagem curta, entusiasmada e que CUMPRA EXATAMENTE esta estrutura:
    1.  Elogio entusiasmado ("Ótima meta!").
    2.  Confirmação do prazo e aporte calculado (ex: "Você alcançaria em X meses com aporte de Y").
    3.  A pergunta final deve ser: "**Quer que eu inicie o plano de investimento, perguntando sobre seu perfil de risco para essa meta?**"
    
    Retorne um objeto JSON com:
    - "tipo_resposta": "convite_planejamento"
    - "pergunta": [A MENSAGEM GERADA]
    - "contexto": [Seu dicionário de contexto para salvar]
    ```json
    """
    
    resultado_ia = processar_com_ia(prompt)
    
    # Adiciona o contexto para o próximo passo no app.py
    if 'erro' not in resultado_ia:
        resultado_ia['contexto'] = {
            "valor_meta": valor_meta,
            "meses_necessarios": prazo_real_em_meses, 
            "finalidade": finalidade
        }
    return resultado_ia
def iniciar_pergunta_risco(valor_meta: float, finalidade: str, prazo_limite: str = None) -> dict:
    """
    PRIMEIRO PASSO: Calcula o prazo, verifica o limite do usuário e usa a IA para fazer a pergunta
    de Suitability. O argumento 'prazo_limite' foi adicionado e é opcional.
    """
    with open('dados.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
    sobra_mensal = dados['usuario']['media_mensal_sobra']
    perfil_de_risco_usuario = dados['usuario']['perfil_de_risco']
    
    if sobra_mensal <= 0: 
        return {"erro": True, "mensagem": "A sobra mensal do usuário não é positiva. Não é possível iniciar um plano."}

    # 1. CÁLCULO DO PRAZO BASE (O prazo que o dinheiro leva para atingir a meta)
    meses_necessarios = math.ceil(valor_meta / sobra_mensal)
    prazo_real_em_meses = meses_necessarios
    mensagem_alerta = ""

    # 2. VERIFICAÇÃO DO PRAZO LIMITE DO USUÁRIO
    if prazo_limite:
        # CHAMA A FUNÇÃO DE CONVERSÃO
        meses_limite = converter_prazo_para_meses(prazo_limite) 

        # 3. VALIDAÇÃO DE DATA NO PASSADO (Resolve o problema de "comprar um carro até 2023")
        if meses_limite <= 0:
            return {
                "tipo_resposta": "erro_prazo", 
                "mensagem": f"O prazo limite que você informou, '{prazo_limite}', parece ser uma data que já passou (ou é o mês atual). Para planejar, por favor, me diga um ano futuro (ex: 2028) ou um prazo em meses/anos (ex: '3 anos')."
            }
        
        # 4. COMPARAÇÃO DO PRAZO LIMITE VS. PRAZO NECESSÁRIO
        if meses_limite < meses_necessarios:
            # O prazo desejado (limite) é menor que o necessário.
            prazo_real_em_meses = meses_limite # <--- AGORA USAMOS O PRAZO CURTO DO USUÁRIO
            aporte_necessario = math.ceil(valor_meta / meses_limite)
            
            mensagem_alerta = f"""
            ATENÇÃO: Você quer atingir a meta em {meses_limite} meses, mas com seu aporte atual de R$ {sobra_mensal:.2f} levaria {meses_necessarios} meses.
            Para cumprir o prazo, você precisará aumentar seu aporte mensal para R$ {aporte_necessario:.2f}.
            """
        else:
             # O prazo necessário é igual ou menor que o limite. Usamos o necessário.
             prazo_real_em_meses = meses_necessarios
             
    # --- PROMPT DO CONSULTOR INTELIGENTE ---
    prompt = f"""
        Você é um consultor de investimentos do BTG Pactual. Um cliente já informou que tem o objetivo de "{finalidade}" no valor de R$ {valor_meta:.2f}.
        O prazo final para ele atingir essa meta é de {prazo_real_em_meses} meses e seu perfil de risco geral é {perfil_de_risco_usuario}.

        # **OBSERVAÇÃO DE NEGÓCIO PARA O MODELO:**
        # {mensagem_alerta}
        
        Sua tarefa é CONFIRMAR a meta e fazer UMA pergunta chave para entender a tolerância a risco do cliente para ESTE objetivo específico.

        Retorne um objeto JSON com a seguinte estrutura:
        - "tipo_resposta": a string "pergunta_suitability".
        - "pergunta": Uma frase que comece confirmando o objetivo...
        
        Responda APENAS com o objeto JSON.
        ```json
        """
    
    resultado_ia = processar_com_ia(prompt)
    
    # Adiciona o contexto manualmente após a IA gerar a pergunta
    if 'erro' not in resultado_ia:
        resultado_ia['contexto'] = {
            "valor_meta": valor_meta,
            "meses_necessarios": prazo_real_em_meses, # AGORA É O PRAZO REAL
            "finalidade": finalidade
        }
    return resultado_ia
# Em espinha.py

# Arquivo: espinha.py (Função finalizar_proposta_carteira CORRIGIDA)
def finalizar_proposta_carteira(resposta_usuario: str, contexto: dict) -> dict:
    """
    SEGUNDO PASSO: Recebe a resposta do cliente sobre risco e o contexto.
    Gera a carteira de investimento, salva a meta e retorna a mensagem final.
    """
    valor_meta = contexto.get('valor_meta', 0.0)
    meses_necessarios = contexto.get('meses_necessarios', 0)
    finalidade = contexto.get('finalidade', "Meta de Investimento")
    
    # 1. GERAR A CARTEIRA DE INVESTIMENTO COM A IA
    prompt = f"""
    Você é um estrategista de investimentos sênior do BTG Pactual.

    **Contexto do Cliente:**
    - **Meta:** Atingir R$ {valor_meta:.2f} em {meses_necessarios} meses.
    - **Resposta sobre Risco:** "{resposta_usuario}".

    **Sua Tarefa:**
    Crie uma resposta para o WhatsApp, usando formatação (negrito `*`, itálico `_`).

    Retorne um objeto JSON com a seguinte estrutura:
    - "mensagem_formatada": [A MENSAGEM COMPLETA DA CARTEIRA, INCLUINDO DEFINIÇÃO DE PERFIL E PRODUTOS SUGERIDOS].

    Responda APENAS com o objeto JSON.
    ```json
    """
    
    resultado_ia = processar_com_ia(prompt)
    
    # Se a IA falhar na geração do JSON, retorne o erro imediatamente
    if resultado_ia.get("erro"):
        return resultado_ia

    # 2. DEFINIR E SALVAR O APORTE SUGERIDO (CÁLCULO SIMPLIFICADO)
    aporte_mensal = valor_meta / meses_necessarios if meses_necessarios > 0 else 0.0

    # 3. PERSISTIR OS DADOS NO dados.json
    try:
        with open('dados.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except Exception:
        # Se falhar ao ler, pelo menos retorna a mensagem da IA
        return resultado_ia
        
    nova_meta = {
        "nome": finalidade,
        "valor_total": valor_meta,
        "valor_atual": 0.00,
        "prazo_meses": meses_necessarios,
        "aporte_mensal_sugerido": round(aporte_mensal, 2),
        "tipo_investimento_sugerido": "Curto Prazo" # A IA deveria definir isso, mas simplificamos
    }

    # Adicionar e salvar
    dados['metas_ativas'].append(nova_meta)
    
    try:
        with open('dados.json', 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception:
        print("AVISO: Falha ao persistir a meta no dados.json.")
    
    # 4. RETORNAR O RESULTADO DA IA (que tem a chave "mensagem_formatada")
    return resultado_ia

def alertar_gastos_com_ia(categoria: str, limite_maximo: float) -> dict:
    with open('dados.json', 'r', encoding='utf-8') as f:
        dados = json.load(f)
        
    # 1. Calcular gastos na categoria no mês atual (assumindo Setembro para o teste)
    # Na vida real, você calcularia para o mês corrente.
    mes_atual = datetime.now().month
    gastos_na_categoria = 0.0
    transacoes_relevantes = []

    for t in dados['transacoes']:
        data_transacao = datetime.fromisoformat(t['data'])
        # Considera apenas débitos e a categoria e o mês relevantes
        if t.get('operacao') == 'debito' and t.get('categoria').lower() == categoria.lower() and data_transacao.month == mes_atual:
            # Transações de débito são armazenadas como negativas, então usamos abs()
            gastos_na_categoria += abs(t['valor'])
            transacoes_relevantes.append(t)
            
    # 2. Gerar o Prompt para a IA
    status = "ATINGIDO" if gastos_na_categoria >= limite_maximo else "ABAIXO"
    
    prompt = f"""
    Você é o assistente financeiro proativo do cliente x, que estabeleceu um limite de gastos para a categoria '{categoria}'.
    
    Detalhes:
    - Limite Máximo Estipulado: R$ {limite_maximo:.2f}
    - Gasto Atual na Categoria '{categoria}' (Mês {mes_atual}): R$ {gastos_na_categoria:.2f}
    - Status do Limite: {status}
    
    Sua tarefa é gerar uma mensagem de alerta/motivação. O tom deve ser de suporte e proativo.
    
    Se o limite foi {status}:
    - Se {status} for 'ATINGIDO' ou PRÓXIMO: Apresente o gasto atual, compare com o limite e sugira uma ação imediata (e.g., "Pause os gastos nesta categoria por 1 semana"). Mantenha o foco na meta.
    - Se {status} for 'ABAIXO': Parabenize o cliente e reforce a importância de manter o ritmo para a meta principal.

    sempre use a {data_atual} como referência para qualquer sugestão de tempo.

    Retorne um objeto JSON com a chave "alerta_motivacional" contendo a mensagem gerada.
    Responda APENAS com o objeto JSON.
    ```json
    """
    with open('dados.json', 'r+', encoding='utf-8') as f:
        dados = json.load(f)
        
        # O novo alerta a ser salvo é 'novo_alerta'
        novo_alerta = {
            "categoria": categoria,
            "limite_maximo": limite_maximo,
            "gasto_atual": gastos_na_categoria,
            "status": status,
            "data_criacao": datetime.now().isoformat()
        }
        
        # NOTA: Usando 'alertas' para compatibilidade com dados.json
        if 'alertas' not in dados:
            dados['alertas'] = []
        
        # Adiciona o alerta à lista
        dados['alertas'].append(novo_alerta)
        
        # Volta ao início do arquivo, salva e trunca (incluindo ensure_ascii=False)
        f.seek(0)
        json.dump(dados, f, indent=4, ensure_ascii=False) # <--- CORRIGIDO
        f.truncate()
    
    # --- FIM DO BLOCO DE SALVAMENTO ---
        

    return processar_com_ia(prompt)

# Arquivo: espinha.py

# ... (Mantenha todos os imports e funções existentes) ...

# ADICIONAR ESTA FUNÇÃO AUXILIAR
def _simular_rentabilidade(valor_atual: float, taxa_mensal: float = 0.001) -> float:
    """
    Simula um rendimento simples de 0.1% ao mês (equivalente a ~1.2% ao ano / ~100% CDI).
    Para simplificação, apenas o rendimento mensal é aplicado ao valor total.
    """
    rendimento = valor_atual * taxa_mensal
    return round(valor_atual + rendimento, 2)

# ADICIONAR ESTA FUNÇÃO AUXILIAR
def _atualizar_caixinhas(caixinhas: list) -> list:
    """
    Aplica a rentabilidade simulada a todas as caixinhas para manter o Asset Management ativo.
    """
    for caixinha in caixinhas:
        # Apenas atualiza o valor atual (simulando o rendimento)
        caixinha['valor_atual'] = _simular_rentabilidade(caixinha.get('valor_atual', 0.0))
        # Adiciona uma data de atualização (opcional, mas bom para tracking)
        caixinha['ultima_atualizacao'] = datetime.now().isoformat()
    return caixinhas


def manipular_caixinha_investimento(nome_caixinha: str, valor_aporte: float = None) -> dict:
    """
    Cria uma nova caixinha, adiciona aporte ou consulta (Lógica de Asset Management).
    """
    
    # 1. Carrega os dados
    try:
        with open('dados.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except Exception as e:
        return {"tipo_resposta": "erro_tecnico", "mensagem": f"Erro ao ler dados: {e}"}

    # Aplica rentabilidade ANTES de procurar/manipular a caixinha (Lógica de Asset)
    dados['caixinhas_ativas'] = _atualizar_caixinhas(dados.get('caixinhas_ativas', []))

    caixinhas = dados.get('caixinhas_ativas', [])
    nome_caixinha = nome_caixinha.strip()
    
    caixinha_existente = next((c for c in caixinhas if c['nome'].lower() == nome_caixinha.lower()), None)
    
    
    # --- CENÁRIO A: CRIAÇÃO DE NOVA CAIXINHA (NÃO EXISTE) ---
    if not caixinha_existente and valor_aporte is None:
        # A caixinha NÃO existe e o valor INICIAL não foi informado
        return {
            "tipo_resposta": "pergunta_valor_caixinha",
            "pergunta": f"Claro! Você está criando a caixinha *{nome_caixinha}*, que renderá 0.5% ao mês. Qual será o *valor inicial* que você quer depositar?",
            "contexto": {"nome_caixinha": nome_caixinha}
        }
    
    # --- CENÁRIO B: CRIAÇÃO PÓS-PERGUNTA DE VALOR (Recebeu o valor final) ---
    if not caixinha_existente and valor_aporte is not None and valor_aporte > 0:
        # A caixinha NÃO existe, mas o valor foi informado
        novo_aporte = round(valor_aporte, 2)
        nova_caixinha = {
            "nome": nome_caixinha,
            "valor_atual": novo_aporte,
            "data_criacao": datetime.now().isoformat()
        }
        dados['caixinhas_ativas'].append(nova_caixinha)
        
        mensagem = f"✅ Caixinha *{nome_caixinha}* criada com sucesso! Seu valor inicial de *R$ {novo_aporte:.2f}* foi aplicado e já está rendendo 0.5% ao mês. 🚀"
        
    # --- CENÁRIO C: APORTE EM CAIXINHA EXISTENTE ---
    elif caixinha_existente and valor_aporte is not None and valor_aporte > 0:
        
        # A caixinha existe e o valor de aporte foi informado
        novo_aporte = round(valor_aporte, 2)
        
        # Aporte é somado ao valor já corrigido (pela função _atualizar_caixinhas)
        caixinha_existente['valor_atual'] += novo_aporte
        caixinha_existente['valor_atual'] = round(caixinha_existente['valor_atual'], 2)
        
        mensagem = f"💰 Aporte de *R$ {novo_aporte:.2f}* adicionado à caixinha *{nome_caixinha}*. Seu novo saldo com rendimentos é de *R$ {caixinha_existente['valor_atual']:.2f}*. O Asset Management está ativo! 💪"

    # --- CENÁRIO D: CONSULTA/CRIAÇÃO DUPLICADA (Caixinha existe mas sem valor informado) ---
    elif caixinha_existente and valor_aporte is None:
        # **A caixinha existe.** O usuário tentou consultá-la ou criar uma duplicada.
        # Foco em Asset Management: Informar saldo e evitar a criação.
        mensagem = "A caixinha já existe."
        saldo_atual = caixinha_existente['valor_atual']
        
        # Tenta encontrar uma meta correspondente nas metas_ativas
        meta_relacionada = next((m for m in dados.get('metas_ativas', []) if m.get('nome', '').lower() == nome_caixinha.lower()), None)
        
        if meta_relacionada:
            # Se houver meta, a consulta foca no progresso
            valor_total = meta_relacionada.get('valor_total', 0.0)
            if valor_total > 0:
                percentual = (saldo_atual / valor_total) * 100
                mensagem = f"A caixinha *{nome_caixinha}* já existe! Seu saldo atual (com rendimentos) é de *R$ {saldo_atual:.2f}*. Você já atingiu *{percentual:.1f}%* da meta de R$ {valor_total:.2f}. Quer *adicionar* mais hoje?"
            else:
                mensagem = f"A caixinha *{nome_caixinha}* já existe e está ativa! Seu saldo é de *R$ {saldo_atual:.2f}* (já com os rendimentos de Asset). Quanto você gostaria de *adicionar* hoje?"
        else:
            # Se não houver meta, a consulta foca no rendimento
            mensagem = f"A caixinha *{nome_caixinha}* já está ativa. Seu saldo atual é de *R$ {saldo_atual:.2f}* (já com os rendimentos de Asset). Quanto você gostaria de *adicionar* hoje?"
            
        # Não salva contexto, a IA fará a chamada de função novamente com o valor
        return {"tipo_resposta": "responder_texto", "conteudo": mensagem}
         
    else:
        return {"tipo_resposta": "erro_tecnico", "mensagem": "Não foi possível processar. Certifique-se de que o valor é positivo."}

    # 2. Persiste os dados (Cenários B e C)
    try:
        with open('dados.json', 'w', encoding='utf-8') as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
    except Exception:
        print("AVISO: Falha ao persistir a caixinha no dados.json.")
        
    # 3. Retorna a mensagem final
    return {"tipo_resposta": "resposta_final", "mensagem_formatada": mensagem}
