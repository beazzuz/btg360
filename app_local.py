# ============================================================
# app_local.py — versão para rodar LOCALMENTE (sem Twilio)
# Mantém a mesma lógica do seu app.py, mas expõe um chat web
# e uma API local para simular mensagens.
# ============================================================

print("="*60)
print("==> INICIANDO O SERVIDOR LOCAL DO ASSISTENTE FINANCEIRO <== (Sem Twilio)")
print("="*60)

from flask import Flask, request, jsonify, Response
from datetime import datetime

# === IMPORTAÇÕES DO SEU CÓDIGO DE NEGÓCIO ===
from cerebro import roteador_ia
from espinha import (
    analisar_gastos_com_ia,
    # Fluxo Wealth (2 passos)
    iniciar_plano_de_riqueza,
    iniciar_pergunta_risco,
    finalizar_proposta_carteira,
    # Ações únicas
    alertar_gastos_com_ia,
    manipular_caixinha_investimento
)

# ------------------------------------------------------------
# Mapeamento das funções invocáveis pela IA
# (nomes precisam bater com o que o roteador retorna)
# ------------------------------------------------------------
FUNCOES_DISPONIVEIS = {
    "analisar_gastos_com_ia": analisar_gastos_com_ia,
    "iniciar_plano_de_riqueza": iniciar_plano_de_riqueza,
    "alertar_gastos_com_ia": alertar_gastos_com_ia,
    "manipular_caixinha_investimento": manipular_caixinha_investimento,
    # iniciar_pergunta_risco / finalizar_proposta_carteira são chamadas pelo próprio app no fluxo multi-etapas
}

# Memória curta por usuário (igual ao app com Twilio)
CONVERSATION_CONTEXT = {}

app = Flask(__name__)

# ------------------------------------------------------------
# PÁGINA DE CHAT LOCAL (HTML simples)
# ------------------------------------------------------------
HTML_CHAT = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <title>Assistente Financeiro - Chat Local</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 0; background:#0b1220; color:#eee; }
    header { padding:16px; background:#0f172a; border-bottom:1px solid #19233b; }
    h1 { margin:0; font-size:18px; }
    #chat { max-width: 820px; margin: 0 auto; padding: 16px; height: calc(100vh - 160px); overflow-y: auto; }
    .msg { margin: 10px 0; display: flex; }
    .you { justify-content: flex-end; }
    .bot { justify-content: flex-start; }
    .bubble { padding: 10px 12px; border-radius: 14px; max-width: 70%; line-height: 1.4; white-space: pre-wrap; }
    .you .bubble { background:#2563eb; color:#fff; border-bottom-right-radius: 4px; }
    .bot .bubble { background:#111827; border:1px solid #1f2937; color:#e5e7eb; border-bottom-left-radius: 4px; }
    #composer { position: fixed; bottom: 0; left: 0; right: 0; background:#0f172a; border-top:1px solid #19233b; padding: 12px; }
    form { display:flex; gap:8px; max-width:820px; margin: 0 auto; }
    input, button { font-size:16px; }
    input { flex:1; padding:10px 12px; border-radius: 10px; border:1px solid #334155; background:#0b1220; color:#e5e7eb; }
    button { padding:10px 16px; border-radius:10px; border:0; background:#22c55e; color:#0b1220; font-weight:700; cursor:pointer; }
    .meta { opacity:.7; font-size:12px; margin-top:2px; }
    .row { max-width:820px; margin:0 auto; color:#9ca3af; padding:0 16px 8px; }
    a { color:#60a5fa; }
  </style>
</head>
<body>
  <header>
    <h1>Assistente Financeiro — Modo Local</h1>
    <div class="row">Dica: testes rápidos — “status de caixa”, “gastos de setembro”, “quero comprar um carro em 2028”.</div>
  </header>
  <div id="chat"></div>
  <div id="composer">
    <form id="f">
      <input id="msg" placeholder="Digite sua mensagem..." autocomplete="off"/>
      <button>Enviar</button>
    </form>
    <div class="row meta">User ID atual: <code id="uid"></code>. Para trocar o usuário, adicione ?user_id=seu_numero na URL.</div>
  </div>
<script>
  const chat = document.getElementById('chat');
  const f = document.getElementById('f');
  const msg = document.getElementById('msg');
  const uidEl = document.getElementById('uid');

  const qs = new URLSearchParams(location.search);
  const userId = qs.get('user_id') || 'local:teste';

  uidEl.textContent = userId;

  function addBubble(text, who) {
    const wrap = document.createElement('div');
    wrap.className = 'msg ' + (who === 'you' ? 'you' : 'bot');
    const b = document.createElement('div');
    b.className = 'bubble';
    b.textContent = text;
    wrap.appendChild(b);
    chat.appendChild(wrap);
    chat.scrollTop = chat.scrollHeight;
  }

  f.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = msg.value.trim();
    if (!text) return;
    addBubble(text, 'you');
    msg.value = '';
    const r = await fetch('/api/message', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ user_id: userId, mensagem: text })
    });
    const data = await r.json();
    addBubble(data.resposta || '(sem resposta)', 'bot');
  });

  addBubble('👋 Olá! Estou pronto no modo local. Como posso ajudar?', 'bot');
</script>
</body>
</html>
"""

# ------------------------------------------------------------
# Home (UI do chat local)
# ------------------------------------------------------------
@app.get("/")
def home():
    return Response(HTML_CHAT, mimetype="text/html; charset=utf-8")

# ------------------------------------------------------------
# API de mensagens locais (simula o webhook)
# ------------------------------------------------------------
@app.post("/api/message")
def api_message():
    payload = request.get_json(force=True, silent=True) or {}
    incoming_msg = (payload.get("mensagem") or "").strip()
    user_id = payload.get("user_id") or "local:teste"

    # --- LOG VISÍVEL ---
    print("\n\n################################################################################")
    print(f"## [REQUISIÇÃO INICIADA] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print("################################################################################")
    print(f"## USUÁRIO (ID): {user_id}")
    print(f"## MENSAGEM RECEBIDA: '{incoming_msg}'")
    print("################################################################################")

    response_msg = "Desculpe, não consegui processar sua solicitação."

    # =========================
    # 1) CONTINUAÇÃO DE FLUXO
    # =========================
    if user_id in CONVERSATION_CONTEXT:
        contexto_salvo = CONVERSATION_CONTEXT[user_id]

        # --- BLOCO 1: Convite (Wealth) ---
        if contexto_salvo.get('tipo_resposta') == 'convite_planejamento':
            contexto_de_dados = contexto_salvo.get('contexto', {})

            # 1a) negativa
            if any(word in incoming_msg.lower() for word in ["não", "nao", "negativo", "n"]):
                print("## [FLUXO DE NEGÓCIO] Convite NEGADO pelo usuário.")
                if any(w in incoming_msg.lower() for w in ["aumente", "mude", "tempo", "prazo", "meses", "alterar", "modificar", "recalcular", "ajustar"]):
                    response_msg = ("Entendi que você gostaria de ajustar o plano. "
                                    "Para recalcular, por favor, comece de novo com a meta, o valor e o NOVO prazo na mesma frase.")
                else:
                    response_msg = "Entendido! Se mudar de ideia ou quiser planejar outra meta, é só me chamar. 😊"
                del CONVERSATION_CONTEXT[user_id]

            # 1b) afirmativa → suitability
            else:
                print("## [FLUXO DE NEGÓCIO] Convite ACEITO. Avançando para a Pergunta de Risco...")
                resultado_pergunta = iniciar_pergunta_risco(
                    valor_meta=contexto_de_dados.get("valor_meta"),
                    finalidade=contexto_de_dados.get("finalidade"),
                    prazo_limite=contexto_de_dados.get("prazo_limite")
                )

                if resultado_pergunta.get("tipo_resposta") == "pergunta_suitability":
                    CONVERSATION_CONTEXT[user_id] = resultado_pergunta
                    # alguns espinha.py usam 'mensagem_final', outros 'pergunta'
                    response_msg = resultado_pergunta.get('mensagem_final') or resultado_pergunta.get('pergunta') \
                                   or "Qual seu conforto com oscilações se o valor acumulado ficar abaixo do esperado?"
                else:
                    response_msg = "Ocorreu um erro ao gerar a pergunta de risco."
                    del CONVERSATION_CONTEXT[user_id]

        # --- BLOCO 2: Suitability (Wealth) ---
        elif contexto_salvo.get('tipo_resposta') == 'pergunta_suitability':
            print("## [FLUXO DE NEGÓCIO] Pergunta de Risco ENCONTRADA. Finalizando planejamento...")

            contexto_de_dados = contexto_salvo.get('contexto', {})
            # diferentes variantes de assinatura – suportar ambas:
            try:
                resultado_final = finalizar_proposta_carteira(incoming_msg, contexto_de_dados)
            except TypeError:
                # fallback com kwargs explícitos
                resultado_final = finalizar_proposta_carteira(
                    resposta_risco=incoming_msg,
                    valor_meta=contexto_de_dados.get("valor_meta"),
                    finalidade=contexto_de_dados.get("finalidade"),
                    prazo_limite=contexto_de_dados.get("prazo_limite"),
                )

            response_msg = resultado_final.get("mensagem_formatada") or resultado_final.get("mensagem_final") \
                           or "Planejamento finalizado."
            del CONVERSATION_CONTEXT[user_id]

        # --- BLOCO 3: Caixinha (pergunta de valor) ---
        elif contexto_salvo.get('tipo_resposta') == 'pergunta_valor_caixinha':
            print("## [FLUXO DE NEGÓCIO] Pergunta de Valor da Caixinha ENCONTRADA. Finalizando criação...")

            nome_caixinha = contexto_salvo.get('contexto', {}).get("nome_caixinha")
            try:
                valor_aporte = float(incoming_msg.replace(',', '.').strip())
            except ValueError:
                response_msg = "O valor inicial é inválido. Por favor, digite apenas o número (ex: 1000)."
                return jsonify({"resposta": response_msg})

            resultado_final = manipular_caixinha_investimento(
                nome_caixinha=nome_caixinha, valor_aporte=valor_aporte
            )
            response_msg = resultado_final.get("mensagem_formatada", "Ocorreu um erro ao criar/aportar na caixinha.")
            del CONVERSATION_CONTEXT[user_id]

        # --- qualquer outro tipo de contexto ---
        else:
            response_msg = "Seu contexto de conversa expirou ou está corrompido. Por favor, comece uma nova solicitação."
            del CONVERSATION_CONTEXT[user_id]

        return jsonify({"resposta": response_msg})

    # =========================
    # 2) NOVA CONVERSA / AÇÃO
    # =========================
    print("## [FLUXO DE NEGÓCIO] Contexto NÃO encontrado. Chamando o Roteador da IA...")

    acao_sugerida = roteador_ia(incoming_msg, user_id)
    tipo_acao = acao_sugerida.get("tipo_acao")

    print("--------------------------------------------------------------------------------")
    print(f"## [AÇÃO DA IA] TIPO DE AÇÃO: {tipo_acao}")

    if tipo_acao == "chamar_funcao":
        nome_funcao = acao_sugerida.get("nome_funcao")
        argumentos = acao_sugerida.get("argumentos", {}) or {}

        print(f"## [AÇÃO DA IA] FUNÇÃO CHAMADA: {nome_funcao}")
        print(f"## [AÇÃO DA IA] ARGUMENTOS: {argumentos}")

        if nome_funcao in FUNCOES_DISPONIVEIS:
            fn = FUNCOES_DISPONIVEIS[nome_funcao]

            # Adaptadores de assinatura (como no seu app)
            if nome_funcao == "analisar_gastos_com_ia":
                resultado = fn(**argumentos) if argumentos else fn()
            elif nome_funcao == "iniciar_plano_de_riqueza":
                resultado = fn(
                    valor_meta=argumentos.get("valor_meta"),
                    finalidade=argumentos.get("finalidade"),
                    prazo_limite=argumentos.get("prazo_limite")
                )
            elif nome_funcao == "manipular_caixinha_investimento":
                resultado = fn(**argumentos)
            elif nome_funcao == "alertar_gastos_com_ia":
                resultado = fn(**argumentos)
            else:
                resultado = fn(**argumentos)

            print(f"## [AÇÃO DE NEGÓCIO] Função '{nome_funcao}' FINALIZADA.")

            # Pós-processamento por função
            if nome_funcao == "analisar_gastos_com_ia":
                if isinstance(resultado, dict) and resultado.get("total_gasto") == 0:
                    response_msg = "Não encontrei nenhum gasto para este mês. Que tal tentarmos outro?"
                else:
                    response_msg = resultado.get("mensagem_final", "Análise pronta.")

            elif nome_funcao == "iniciar_plano_de_riqueza":
                if isinstance(resultado, dict) and resultado.get("tipo_resposta") == "convite_planejamento":
                    print(f"## [MEMÓRIA SALVA] SALVANDO contexto para {user_id} (Wealth)")
                    CONVERSATION_CONTEXT[user_id] = resultado
                    response_msg = resultado.get('pergunta') or resultado.get('mensagem_final') \
                                   or "Posso iniciar seu plano? (sim/não)"
                else:
                    response_msg = "Ocorreu um erro ao iniciar seu planejamento. Tente novamente."

            elif nome_funcao == "manipular_caixinha_investimento":
                if isinstance(resultado, dict) and resultado.get("tipo_resposta") == "pergunta_valor_caixinha":
                    print(f"## [MEMÓRIA SALVA] SALVANDO contexto para {user_id} (Caixinha)")
                    CONVERSATION_CONTEXT[user_id] = resultado
                    response_msg = resultado.get('pergunta', 'Qual valor deseja aportar na caixinha?')
                else:
                    response_msg = resultado.get("mensagem_formatada", resultado.get("conteudo", "Ação executada com Caixinha."))

            elif nome_funcao == "alertar_gastos_com_ia":
                response_msg = resultado.get('alerta_motivacional', "Alerta processado.")

            else:
                response_msg = str(resultado) if resultado else "Ação executada."

        else:
            response_msg = f"Erro: A IA tentou chamar uma função desconhecida: {nome_funcao}"

    elif tipo_acao == "responder_texto":
        response_msg = acao_sugerida.get("conteudo", "Certo! Como posso ajudar nas suas finanças hoje?")
    else:
        response_msg = "Desculpe, a IA não retornou uma ação válida."

    print("--------------------------------------------------------------------------------")
    print(f"## [RESPOSTA FINAL] LOCAL:")
    print(f"## {response_msg}")
    print("################################################################################\n")

    return jsonify({"resposta": response_msg})


if __name__ == "__main__":
    print("Servidor local rodando em http://127.0.0.1:5001")
    app.run(host="127.0.0.1", port=5001, debug=True, use_reloader=False)
