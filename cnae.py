import streamlit as st
import pandas as pd
import urllib

# --- PARTE 1: BUSCA DE CNAE ---
st.title("🔎 Buscador de CNAE")

# Campo de busca
busca = st.text_input("Digite o CNAE ou descrição para buscar:")

# Simulação de resultado da busca (substitua pela sua lógica real)
if busca:
    # Exemplo: dataframe com resultados
    resultado = pd.DataFrame({
        "CNAE": ["1234-5/00", "5678-9/10"],
        "Descrição": ["Comércio varejista", "Serviços de informática"]
    })

    # Seleção do CNAE
    cnae_selecionado = st.selectbox("Selecione o CNAE encontrado:", resultado["CNAE"])
else:
    resultado = pd.DataFrame()
    cnae_selecionado = ""

# --- PARTE 2: DADOS DO CLIENTE ---
if busca and not resultado.empty:
    st.divider()
    st.subheader("📋 Informações Adicionais")
    
    cep = st.text_input("Digite seu CEP (apenas números):", max_chars=8)
    cep = "".join(filter(str.isdigit, cep))
    
    preferencia = st.radio(
        "O que deseja receber?",
        ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones")
    )
    
    seu_whatsapp = st.text_input("Seu WhatsApp com DDD (ex: 11999999999):")
    seu_whatsapp = "".join(filter(str.isdigit, seu_whatsapp))

    # ✅ Novo campo para DDD preferido
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
            texto_msg = (
                f"*Novo Interesse de CNAE*\n\n"
                f"*CNAE:* {cnae_selecionado}\n"
                f"*CEP:* {cep}\n"
                f"*Deseja:* {preferencia}\n"
                f"*DDD Preferência:* {ddd_preferencia}\n"
                f"*WhatsApp Cliente:* {seu_whatsapp}"
            )
            
            msg_codificada = urllib.parse.quote(texto_msg)
            link_whatsapp = f"https://wa.me/5512981779669?text={msg_codificada}"
            
            st.markdown(f"""
                <a href="{link_whatsapp}" target="_blank">
                    <button style="background-color: #25D366; color: white; padding: 15px 30px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px;">
                        ✅ CLIQUE AQUI PARA ENVIAR NO WHATSAPP
                    </button>
                </a>
            """, unsafe_allow_html=True)
