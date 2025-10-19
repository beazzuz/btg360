# Arquivo: app.py (Versão Final com Debug Altamente Visível e Fluxo Caixinha)
print("="*60)
print("==> INICIANDO O SERVIDOR DO ASSISTENTE FINANCEIRO <== (Com Twilio)")
print("="*60)

try:
    from flask import Flask, request
    from twilio.twiml.messaging_response import MessagingResponse
    import json

    from cerebro import roteador_ia
    from espinha import (
        analisar_gastos_com_ia,
        # Funções do fluxo Wealth Management (2 passos)
        iniciar_plano_de_riqueza, 
        iniciar_pergunta_risco, 
        finalizar_proposta_carteira, # Novo nome para o final do fluxo
        # Funções de ação única
        alertar_gastos_com_ia,
        manipular_caixinha_investimento
    )
    from datetime import datetime
    print("[STATUS] [OK] Todas as bibliotecas e arquivos foram importados com sucesso.")
except ImportError as e:
    print(f"[STATUS] [ERRO FATAL] Não foi possível importar uma dependência: {e}")
    exit()

# FUNCOES_DISPONIVEIS: Mapeia o nome da função que a IA chama para a função Python real
FUNCOES_DISPONIVEIS = {
    "analisar_gastos_com_ia": analisar_gastos_com_ia,
    "iniciar_plano_de_riqueza": iniciar_plano_de_riqueza, 
    "alertar_gastos_com_ia": alertar_gastos_com_ia,
    "manipular_caixinha_investimento": manipular_caixinha_investimento,
    # 'iniciar_pergunta_risco' e 'finalizar_proposta_carteira' são chamadas DENTRO da lógica do app.py
}

# A memória de curto prazo para conversas de múltiplos passos (Wealth e Caixinha)
CONVERSATION_CONTEXT = {}

app = Flask(__name__)

# Arquivo: app.py (Função webhook_whatsapp - VERSÃO FINAL COMPLETA E ATUALIZADA)

@app.route('/whatsapp', methods=['POST'])
def webhook_whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    # No Twilio, o user_id é o número do WhatsApp, que é CRÍTICO para o contexto.
    user_id = request.values.get('From', '')
    response_msg = "Desculpe, não consegui processar sua solicitação."

    # --- INÍCIO DA REQUISIÇÃO E DADOS ---
    print("\n\n################################################################################")
    print(f"## [REQUISIÇÃO INICIADA] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print("################################################################################")
    print(f"## USUÁRIO (ID): {user_id}")
    print(f"## MENSAGEM RECEBIDA: '{incoming_msg}'")
    print("################################################################################")

    if user_id in CONVERSATION_CONTEXT:
        contexto_salvo = CONVERSATION_CONTEXT[user_id]
        
        # --- BLOCO 1: TRATAMENTO DO FLUXO DE CONVITE (Wealth Management) ---
        if contexto_salvo.get('tipo_resposta') == 'convite_planejamento':
            contexto_de_dados = contexto_salvo.get('contexto', {})
            
            # 1a. Verifica se o usuário negou o convite
            if any(word in incoming_msg.lower() for word in ["não", "nao", "negativo", "n"]):
                 print(f"## [FLUXO DE NEGÓCIO] Convite NEGADO pelo usuário.")
                 
                 # 1b. Verifica se o usuário quer modificar o plano (Aumente o prazo)
                 if any(word in incoming_msg.lower() for word in ["aumente", "mude", "tempo", "prazo", "meses", "alterar", "modificar", "recalcular", "ajustar"]):
                     response_msg = "Entendi que você gostaria de ajustar o plano. Para recalcular, por favor, comece de novo com a meta, o valor e o NOVO prazo na mesma frase."
                 else:
                     response_msg = "Entendido! Se mudar de ideia ou quiser planejar outra meta, é só me chamar. 😊"
                 del CONVERSATION_CONTEXT[user_id]
            
            # 1c. Se não for negativa, assume que é afirmativa (AVANÇA PARA SUITABILITY)
            else:
                print(f"## [FLUXO DE NEGÓCIO] Convite ACEITO. Avançando para a Pergunta de Risco...")
                
                resultado_pergunta = iniciar_pergunta_risco(
                    valor_meta=contexto_de_dados.get("valor_meta"),
                    finalidade=contexto_de_dados.get("finalidade"),
                    prazo_limite=contexto_de_dados.get("prazo_limite") # Passa o prazo limite original, se existir
                )
                
                if resultado_pergunta.get("tipo_resposta") == "pergunta_suitability":
                    CONVERSATION_CONTEXT[user_id] = resultado_pergunta 
                    response_msg = resultado_pergunta.get('pergunta')
                else:
                    response_msg = "Ocorreu um erro ao gerar a pergunta de risco."
                    del CONVERSATION_CONTEXT[user_id]
                 
        # --- BLOCO 2: TRATAMENTO DO FLUXO DE SUITABILITY (Wealth Management) ---
        elif contexto_salvo.get('tipo_resposta') == 'pergunta_suitability':
            print(f"## [FLUXO DE NEGÓCIO] Pergunta de Risco ENCONTRADA. Finalizando planejamento...")
            
            contexto_de_dados = contexto_salvo.get('contexto', {})
            # Chama a função final que gera carteira e salva a meta
            resultado_final = finalizar_proposta_carteira(incoming_msg, contexto_de_dados)
            
            response_msg = resultado_final.get("mensagem_formatada", "Ocorreu um erro ao finalizar seu planejamento.")
            
            del CONVERSATION_CONTEXT[user_id]
            
        # --- BLOCO 3: TRATAMENTO DO FLUXO DE CAIXINHA (Asset Management - Passo 2) ---
        elif contexto_salvo.get('tipo_resposta') == 'pergunta_valor_caixinha':
            print(f"## [FLUXO DE NEGÓCIO] Pergunta de Valor da Caixinha ENCONTRADA. Finalizando criação...")
            
            nome_caixinha = contexto_salvo.get('contexto', {}).get("nome_caixinha")
            
            # Tenta converter a mensagem do usuário para float
            try:
                # Substitui vírgula por ponto para facilitar a conversão
                valor_aporte = float(incoming_msg.replace(',', '.').strip()) 
            except ValueError:
                response_msg = "O valor inicial é inválido. Por favor, digite apenas o número (ex: 1000)."
                # Mantém o contexto para nova tentativa.
                twiml_response = MessagingResponse()
                twiml_response.message(response_msg)
                return str(twiml_response)

            # Chama a função manipuladora para criar ou aportar (Cenário B)
            resultado_final = manipular_caixinha_investimento(nome_caixinha=nome_caixinha, valor_aporte=valor_aporte)
            
            # A mensagem formatada vem da espinha.py
            response_msg = resultado_final.get("mensagem_formatada", "Ocorreu um erro ao criar/aportar na caixinha.")
            
            del CONVERSATION_CONTEXT[user_id] # Limpa a memória após a finalização
            
        # --- TRATAMENTO DE ERRO DE CONTEXTO ---
        else:
            response_msg = "Seu contexto de conversa expirou ou está corrompido. Por favor, comece uma nova solicitação."
            del CONVERSATION_CONTEXT[user_id]


    # --- LÓGICA DE ROTEAMENTO (NOVA CONVERSA OU AÇÃO ÚNICA) ---
    else:
        print(f"## [FLUXO DE NEGÓCIO] Contexto NÃO encontrado. Chamando o Roteador da IA...")
        
        # CHAMA IA para rotear e decidir a ação
        acao_sugerida = roteador_ia(incoming_msg, user_id)
        
        tipo_acao = acao_sugerida.get("tipo_acao")

        print("--------------------------------------------------------------------------------")
        print(f"## [AÇÃO DA IA] TIPO DE AÇÃO: {tipo_acao}")
        
        if tipo_acao == "chamar_funcao":
            nome_funcao = acao_sugerida.get("nome_funcao")
            argumentos = acao_sugerida.get("argumentos", {})

            print(f"## [AÇÃO DA IA] FUNÇÃO CHAMADA: {nome_funcao}")
            print(f"## [AÇÃO DA IA] ARGUMENTOS: {argumentos}")

            if nome_funcao in FUNCOES_DISPONIVEIS:
                funcao_para_executar = FUNCOES_DISPONIVEIS[nome_funcao]
                
                # Executa a função de negócio
                resultado_da_funcao = funcao_para_executar(**argumentos)
                
                print(f"## [AÇÃO DE NEGÓCIO] Função '{nome_funcao}' FINALIZADA.")
                
                # --- PROCESSAMENTO DOS RESULTADOS DA FUNÇÃO ---
                if nome_funcao == "analisar_gastos_com_ia":
                    if isinstance(resultado_da_funcao, dict) and resultado_da_funcao.get("total_gasto") == 0:
                        response_msg = "Não encontrei nenhum gasto para este mês. Que tal tentarmos outro?"
                    else:
                        response_msg = resultado_da_funcao.get("mensagem_final", "Erro ao gerar análise.")
                
                elif nome_funcao == "iniciar_plano_de_riqueza": 
                    # Wealth Management: Inicia a conversa de planejamento (convite -> suitability)
                    if isinstance(resultado_da_funcao, dict) and resultado_da_funcao.get("tipo_resposta") == "convite_planejamento":
                        print(f"## [MEMÓRIA SALVA] SALVANDO contexto para {user_id} (Wealth)")
                        CONVERSATION_CONTEXT[user_id] = resultado_da_funcao
                        response_msg = resultado_da_funcao.get('pergunta')
                    else:
                        response_msg = "Ocorreu um erro ao iniciar seu planejamento. Tente novamente."
                        
                elif nome_funcao == "manipular_caixinha_investimento": 
                    # Asset Management: Aporte, Consulta ou Pergunta de Valor (Passo 1)
                    if isinstance(resultado_da_funcao, dict) and resultado_da_funcao.get("tipo_resposta") == "pergunta_valor_caixinha":
                        # Cenário A: Caixinha nova e precisa de valor. Salva o contexto.
                        print(f"## [MEMÓRIA SALVA] SALVANDO contexto para {user_id} (Caixinha)")
                        CONVERSATION_CONTEXT[user_id] = resultado_da_funcao
                        response_msg = resultado_da_funcao.get('pergunta')
                    else:
                        # Cenário C/D: Resposta direta para aporte ou consulta existente.
                        response_msg = resultado_da_funcao.get("mensagem_formatada", resultado_da_funcao.get("conteudo", "Ação executada com Caixinha."))

                elif nome_funcao == "alertar_gastos_com_ia":
                    response_msg = resultado_da_funcao.get('alerta_motivacional', "Alerta processado.")
                
                else: 
                    response_msg = str(resultado_da_funcao) if resultado_da_funcao else "Ação executada."
            else:
                 response_msg = f"Erro: A IA tentou chamar uma função desconhecida: {nome_funcao}"
        
        elif tipo_acao == "responder_texto":
            response_msg = acao_sugerida.get("conteudo")
        else:
             response_msg = "Desculpe, a IA não retornou uma ação válida."

    # --- FIM DA REQUISIÇÃO E RESPOSTA FINAL ---
    print("--------------------------------------------------------------------------------")
    print(f"## [RESPOSTA FINAL] ENVIANDO PARA O TWILIO:")
    print(f"## {response_msg}")
    print("################################################################################\n")
    
    twiml_response = MessagingResponse()
    twiml_response.message(response_msg)
    
    return str(twiml_response)

if __name__ == '__main__':
    print("Iniciando servidor Flask na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
