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
        iniciar_plano_de_riqueza, 
        iniciar_pergunta_risco, 
        finalizar_proposta_carteira,
        alertar_gastos_com_ia,
        manipular_caixinha_investimento
    )
    from datetime import datetime
    print("[STATUS] [OK] Todas as bibliotecas e arquivos foram importados com sucesso.")
except ImportError as e:
    print(f"[STATUS] [ERRO FATAL] Não foi possível importar uma dependência: {e}")
    exit()

FUNCOES_DISPONIVEIS = {
    "analisar_gastos_com_ia": analisar_gastos_com_ia,
    "iniciar_plano_de_riqueza": iniciar_plano_de_riqueza, 
    "alertar_gastos_com_ia": alertar_gastos_com_ia,
    "manipular_caixinha_investimento": manipular_caixinha_investimento,
}

CONVERSATION_CONTEXT = {}

app = Flask(__name__)


@app.route('/whatsapp', methods=['POST'])
def webhook_whatsapp():
    incoming_msg = request.values.get('Body', '').strip()
    user_id = request.values.get('From', '')
    response_msg = "Desculpe, não consegui processar sua solicitação."

    print("\n\n################################################################################")
    print(f"## [REQUISIÇÃO INICIADA] [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print("################################################################################")
    print(f"## USUÁRIO (ID): {user_id}")
    print(f"## MENSAGEM RECEBIDA: '{incoming_msg}'")
    print("################################################################################")

    if user_id in CONVERSATION_CONTEXT:
        contexto_salvo = CONVERSATION_CONTEXT[user_id]
        
        if contexto_salvo.get('tipo_resposta') == 'convite_planejamento':
            contexto_de_dados = contexto_salvo.get('contexto', {})
            
            if any(word in incoming_msg.lower() for word in ["não", "nao", "negativo", "n"]):
                 print(f"## [FLUXO DE NEGÓCIO] Convite NEGADO pelo usuário.")
                 
                 if any(word in incoming_msg.lower() for word in ["aumente", "mude", "tempo", "prazo", "meses", "alterar", "modificar", "recalcular", "ajustar"]):
                     response_msg = "Entendi que você gostaria de ajustar o plano. Para recalcular, por favor, comece de novo com a meta, o valor e o NOVO prazo na mesma frase."
                 else:
                     response_msg = "Entendido! Se mudar de ideia ou quiser planejar outra meta, é só me chamar. 😊"
                 del CONVERSATION_CONTEXT[user_id]
            
            else:
                print(f"## [FLUXO DE NEGÓCIO] Convite ACEITO. Avançando para a Pergunta de Risco...")
                
                resultado_pergunta = iniciar_pergunta_risco(
                    valor_meta=contexto_de_dados.get("valor_meta"),
                    finalidade=contexto_de_dados.get("finalidade"),
                    prazo_limite=contexto_de_dados.get("prazo_limite")
                )
                
                if resultado_pergunta.get("tipo_resposta") == "pergunta_suitability":
                    CONVERSATION_CONTEXT[user_id] = resultado_pergunta 
                    response_msg = resultado_pergunta.get('pergunta')
                else:
                    response_msg = "Ocorreu um erro ao gerar a pergunta de risco."
                    del CONVERSATION_CONTEXT[user_id]
                 
        elif contexto_salvo.get('tipo_resposta') == 'pergunta_suitability':
            print(f"## [FLUXO DE NEGÓCIO] Pergunta de Risco ENCONTRADA. Finalizando planejamento...")
            
            contexto_de_dados = contexto_salvo.get('contexto', {})
            resultado_final = finalizar_proposta_carteira(incoming_msg, contexto_de_dados)
            
            response_msg = resultado_final.get("mensagem_formatada", "Ocorreu um erro ao finalizar seu planejamento.")
            
            del CONVERSATION_CONTEXT[user_id]
            
        elif contexto_salvo.get('tipo_resposta') == 'pergunta_valor_caixinha':
            print(f"## [FLUXO DE NEGÓCIO] Pergunta de Valor da Caixinha ENCONTRADA. Finalizando criação...")
            
            nome_caixinha = contexto_salvo.get('contexto', {}).get("nome_caixinha")
            
            try:
                valor_aporte = float(incoming_msg.replace(',', '.').strip()) 
            except ValueError:
                response_msg = "O valor inicial é inválido. Por favor, digite apenas o número (ex: 1000)."
                twiml_response = MessagingResponse()
                twiml_response.message(response_msg)
                return str(twiml_response)

            resultado_final = manipular_caixinha_investimento(nome_caixinha=nome_caixinha, valor_aporte=valor_aporte)
            
            response_msg = resultado_final.get("mensagem_formatada", "Ocorreu um erro ao criar/aportar na caixinha.")
            
            del CONVERSATION_CONTEXT[user_id]
            
        else:
            response_msg = "Seu contexto de conversa expirou ou está corrompido. Por favor, comece uma nova solicitação."
            del CONVERSATION_CONTEXT[user_id]


    else:
        print(f"## [FLUXO DE NEGÓCIO] Contexto NÃO encontrado. Chamando o Roteador da IA...")
        
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
                
                resultado_da_funcao = funcao_para_executar(**argumentos)
                
                print(f"## [AÇÃO DE NEGÓCIO] Função '{nome_funcao}' FINALIZADA.")
                
                if nome_funcao == "analisar_gastos_com_ia":
                    if isinstance(resultado_da_funcao, dict) and resultado_da_funcao.get("total_gasto") == 0:
                        response_msg = "Não encontrei nenhum gasto para este mês. Que tal tentarmos outro?"
                    else:
                        response_msg = resultado_da_funcao.get("mensagem_final", "Erro ao gerar análise.")
                
                elif nome_funcao == "iniciar_plano_de_riqueza": 
                    if isinstance(resultado_da_funcao, dict) and resultado_da_funcao.get("tipo_resposta") == "convite_planejamento":
                        print(f"## [MEMÓRIA SALVA] SALVANDO contexto para {user_id} (Wealth)")
                        CONVERSATION_CONTEXT[user_id] = resultado_da_funcao
                        response_msg = resultado_da_funcao.get('pergunta')
                    else:
                        response_msg = "Ocorreu um erro ao iniciar seu planejamento. Tente novamente."
                        
                elif nome_funcao == "manipular_caixinha_investimento": 
                    if isinstance(resultado_da_funcao, dict) and resultado_da_funcao.get("tipo_resposta") == "pergunta_valor_caixinha":
                        print(f"## [MEMÓRIA SALVA] SALVANDO contexto para {user_id} (Caixinha)")
                        CONVERSATION_CONTEXT[user_id] = resultado_da_funcao
                        response_msg = resultado_da_funcao.get('pergunta')
                    else:
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
