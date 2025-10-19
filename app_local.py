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

#mapeamento de funções disponíveis
FUNCOES_DISPONIVEIS = {
    "analisar_gastos_com_ia": analisar_gastos_com_ia,
    "iniciar_plano_de_riqueza": iniciar_plano_de_riqueza,
    "alertar_gastos_com_ia": alertar_gastos_com_ia,
    "manipular_caixinha_investimento": manipular_caixinha_investimento,
    # iniciar_pergunta_risco / finalizar_proposta_carteira são chamadas pelo próprio app no fluxo multi-etapas
}

#memoria curta de conversas (em memória)
CONVERSATION_CONTEXT = {}

app = Flask(__name__)

#pag do chat local
HTML_CHAT = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <title>Assistente Financeiro — Chat Local</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <style>
    :root{
      --bg:#0b1220;        /* fundo da página */
      --panel:#0f172a;     /* painéis (header/composer) */
      --border:#1a2440;    /* linhas e contornos */
      --text:#e5e7eb;      /* texto base */
      --muted:#a1a7b3;     /* texto secundário */
      --bubble:#111827;    /* bolha do bot */
      --primary:#2563eb;   /* bolha do usuário */
      --accent:#22c55e;    /* botão */
      --shadow:0 6px 24px rgba(0,0,0,.25);
      --radius:16px;
    }
    *{box-sizing:border-box}
    html,body{height:100%}
    body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial}

    /* Header */
    header{
      position:sticky; top:0; z-index:10;
      background:linear-gradient(180deg,rgba(15,23,42,.9),rgba(15,23,42,.75));
      backdrop-filter:saturate(120%) blur(6px);
      border-bottom:1px solid var(--border);
      padding:14px 16px;
    }
    .wrap{max-width:900px;margin:0 auto}
    .title{display:flex;align-items:center;gap:10px;font-weight:700;font-size:18px}
    .title .dot{width:10px;height:10px;border-radius:999px;background:var(--accent);box-shadow:0 0 12px var(--accent)}
    .subtitle{margin-top:6px;color:var(--muted);font-size:13px}

    /* Chat area */
    #chat{
      max-width:900px;margin:0 auto;padding:20px 16px 120px;
      min-height:calc(100vh - 150px);
      overflow-y:auto;scroll-behavior:smooth;
    }
    /* scrollbar */
    #chat::-webkit-scrollbar{width:10px}
    #chat::-webkit-scrollbar-thumb{background:#1f2a44;border-radius:10px}
    #chat::-webkit-scrollbar-thumb:hover{background:#2a375b}

    /* Messages */
    .msg{display:flex;margin:12px 0;gap:10px;animation:pop .16s ease-out}
    @keyframes pop{from{transform:translateY(6px);opacity:0}to{transform:translateY(0);opacity:1}}
    .msg.you{justify-content:flex-end}
    .avatar{
      width:32px;height:32px;border-radius:10px;background:#19233b;display:flex;align-items:center;justify-content:center;
      color:#9fb4ff;font-weight:800;flex-shrink:0;border:1px solid var(--border)
    }
    .bubble{
      min-width:min(72%,680px);
      padding:12px 14px;border-radius:var(--radius);line-height:1.4;white-space:pre-wrap;word-wrap:break-word;
      border:1px solid var(--border);box-shadow:var(--shadow)
    }
    .bot .bubble{background:var(--bubble);border-bottom-left-radius:8px}
    .you .bubble{background:var(--primary);color:#fff;border-bottom-right-radius:8px;border-color:rgba(255,255,255,.08)}
    .meta{margin-top:6px;color:var(--muted);font-size:12px}

    /* Composer */
    #composer{
      position:sticky; bottom:0; z-index:20;
      background:linear-gradient(180deg,rgba(11,18,32,0),var(--panel) 22%);
      padding:14px 16px;border-top:1px solid var(--border);
    }
    .composer-inner{
      max-width:900px;margin:0 auto;
      background:#0b1326;border:1px solid var(--border);border-radius:14px;padding:10px;display:flex;gap:10px;align-items:flex-end;
      box-shadow:var(--shadow);
    }
    textarea{
      flex:1;min-height:20px;max-height:160px;resize:none;border:0;outline:none;background:transparent;color:var(--text);
      font:16px/1.45 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial;padding:8px 10px;
    }
    button{
      border:0;cursor:pointer;background:var(--accent);color:#0b1220;font-weight:800;border-radius:12px;
      padding:12px 16px;min-width:92px;transition:transform .08s ease,filter .08s ease
    }
    button:hover{transform:translateY(-1px);filter:brightness(1.05)}
    button:active{transform:translateY(0)}
    .hint{margin-top:8px;color:var(--muted);font-size:12px;text-align:left}
    a{color:#86b7ff;text-decoration:none}
    a:hover{text-decoration:underline}
    @media (max-width:560px){
      .bubble{max-width:85%}
      button{min-width:84px;padding:11px 14px}
    }
  </style>
</head>
<body>
  <header>
    <div class="wrap">
      <div class="title"><span class="dot"></span> Assistente Financeiro — Modo Local</div>
      <div class="subtitle">Dica: “status de caixa”, “gastos de setembro”, “quero comprar uma casa em 2028”.</div>
    </div>
  </header>

  <div id="chat" class="wrap"></div>

  <div id="composer">
    <div class="composer-inner">
      <textarea id="msg" placeholder="Digite sua mensagem... (Enter envia • Shift+Enter quebra linha)" autocomplete="off"></textarea>
      <button id="send">Enviar</button>
    </div>
    <div class="wrap hint">User ID atual: <code id="uid"></code>. Troque adicionando <code>?user_id=seu_numero</code> na URL.</div>
  </div>

<script>
  const chat   = document.getElementById('chat');
  const msgEl  = document.getElementById('msg');
  const sendBt = document.getElementById('send');
  const uidEl  = document.getElementById('uid');

  const qs = new URLSearchParams(location.search);
  const userId = qs.get('user_id') || 'local:teste';
  uidEl.textContent = userId;

  function ts(){ // timestamp HH:MM
    const d = new Date(); return d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
  }

  function addBubble(text, who='bot'){
    const row = document.createElement('div');
    row.className = 'msg ' + who;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = who === 'you' ? 'Você' : 'IA';
    avatar.style.fontSize = '10px';

    const right = document.createElement('div');
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;

    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = ts();

    right.appendChild(bubble);
    right.appendChild(meta);

    if (who === 'you'){ row.appendChild(right); row.appendChild(avatar); }
    else { row.appendChild(avatar); row.appendChild(right); }

    chat.appendChild(row);
    chat.scrollTop = chat.scrollHeight + 200;
  }

  // Auto-resize do textarea
  function autoresize(){
    msgEl.style.height = 'auto';
    msgEl.style.height = Math.min(msgEl.scrollHeight, 160) + 'px';
  }
  msgEl.addEventListener('input', autoresize);
  setTimeout(autoresize, 10);

  // Enter envia / Shift+Enter = nova linha
  msgEl.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey){
      e.preventDefault();
      sendBt.click();
    }
  });

  sendBt.addEventListener('click', async () => {
    const text = msgEl.value.trim();
    if (!text) return;
    addBubble(text, 'you');
    msgEl.value = '';
    autoresize();

    try{
      const r = await fetch('/api/message', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ user_id: userId, mensagem: text })
      });
      const data = await r.json();
      addBubble(data.resposta || '(sem resposta)', 'bot');
    }catch(err){
      addBubble('⚠️ Erro ao enviar: ' + (err.message || err), 'bot');
    }
  });

  // Mensagem de boas-vindas
  addBubble('👋 Olá! Estou pronto no modo local. Como posso ajudar?', 'bot');
</script>
</body>
</html>
"""



# Home (UI do chat local)@app.get("/")
def home():
    return Response(HTML_CHAT, mimetype="text/html; charset=utf-8")


# API de mensagens locais (simula o webhook)
@app.post("/api/message")
def api_message():
    payload = request.get_json(force=True, silent=True) or {}
    incoming_msg = (payload.get("mensagem") or "").strip()
    user_id = payload.get("user_id") or "local:teste"

    print("\n\n################################################################################")
    print(f"## [REQUISIÇÃO INICIADA] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print("################################################################################")
    print(f"## USUÁRIO (ID): {user_id}")
    print(f"## MENSAGEM RECEBIDA: '{incoming_msg}'")
    print("################################################################################")

    response_msg = "Desculpe, não consegui processar sua solicitação."

   
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

   
    # NOVA CONVERSA 
  
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
