import streamlit as st
import pandas as pd
import urllib

# --- PARTE 1: SIMULAÇÃO DE RESULTADO ---
# Substitua isso pela sua busca real de CNAE
busca = True
resultado = pd.DataFrame({"CNAE": ["1234-5/00"]})  # Exemplo de resultado

# --- PARTE 2: DADOS DO CLIENTE ---
if busca:
    if not resultado.empty:
        st.divider()
        st.subheader("📋 Informações Adicionais")
        
        # Campo CEP
        cep = st.text_input("Digite seu CEP (apenas números):", max_chars=8)
        cep = "".join(filter(str.isdigit, cep))
        
        # Preferência de contato
        preferencia = st.radio(
            "O que deseja receber?",
            ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones")
        )
        
        # WhatsApp do cliente
        seu_whatsapp = st.text_input("Seu WhatsApp com DDD (ex: 11999999999):")
        seu_whatsapp = "".join(filter(str.isdigit, seu_whatsapp))

        # DDD preferido
        ddd_preferencia = st.text_input("Digite o DDD da região que deseja receber contatos (ex: 11):")
        ddd_preferencia = "".join(filter(str.isdigit, ddd_preferencia))

        # --- PARTE 3: ENVIO ---
        if st.button("Finalizar e Gerar Mensagem"):
            if len(cep) < 8:
                st.warning("Por favor, digite um CEP válido com 8 dígitos.")
            elif len(seu_whatsapp) < 10:
                st.warning("Por favor, digite um WhatsApp válido com DDD.")
            elif len(ddd_preferencia) < 2:
                st.warning("Por favor, digite um DDD válido com 2 dígitos.")
            else:
                # Pegando o CNAE selecionado do resultado
                cnae_selecionado = resultado["CNAE"].iloc[0]

                texto_msg = (
                    f"*Novo Interesse de CNAE*\n\n"
                    f"*CNAE:* {cnae_selecionado}\n"
                    f"*CEP:* {cep}\n"
                    f"*Deseja:* {preferencia}\n"
                    f"*DDD Preferência:* {ddd_preferencia}\n"
                    f"*WhatsApp Cliente:* {seu_whatsapp}"
                )
                
                # Codificando a mensagem para o link do WhatsApp
                msg_codificada = urllib.parse.quote(texto_msg)
                link_whatsapp = f"https://wa.me/5512981779669?text={msg_codificada}"
                
                # Botão estilizado para enviar no WhatsApp
                st.markdown(f"""
                    <a href="{link_whatsapp}" target="_blank">
                        <button style="background-color: #25D366; color: white; padding: 15px 30px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px;">
                            ✅ CLIQUE AQUI PARA ENVIAR NO WHATSAPP
                        </button>
                    </a>
                """, unsafe_allow_html=True)
    else:
        st.warning("Nenhum resultado encontrado para a busca de CNAE.")
else:
    st.info("Ainda não foi realizada nenhuma busca.")
