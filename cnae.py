import streamlit as st
import pandas as pd
import urllib.parse

# Configuração da página
st.set_page_config(page_title="Busca de CNAE e Contato", layout="centered")

# Função para carregar os dados do arquivo TXT
@st.cache_data
def carregar_dados():
    cnaes = []
    try:
        # Tenta ler o arquivo. Certifique-se que o nome está igual ao do GitHub
        with open("ListaCNAES.txt", "r", encoding="utf-8") as f:
            for linha in f:
                codigo = linha[:7].strip()
                descricao = linha[7:].strip().replace('"', '')
                if codigo and descricao:
                    cnaes.append({"codigo": codigo, "descricao": descricao})
        return pd.DataFrame(cnaes)
    except FileNotFoundError:
        st.error("Erro: O arquivo 'ListaCNAES.txt' não foi encontrado no GitHub.")
        return pd.DataFrame(columns=["codigo", "descricao"])

df = carregar_dados()

st.title("🔍 Localizador de CNAE")
st.write("Encontre o código da sua atividade e solicite informações.")

# --- PARTE 1: PESQUISA ---
busca = st.text_input("Digite até 3 palavras da sua atividade (ex: abate aves):").lower()
palavras = busca.split()[:3] 

resultado = pd.DataFrame()

if busca:
    # Filtra as linhas que contenham todas as palavras digitadas
    mask = df['descricao'].str.lower().apply(lambda x: all(p in x for p in palavras))
    resultado = df[mask]

    if not resultado.empty:
        st.success(f"Encontramos {len(resultado)} resultados:")
        escolha = st.selectbox("Selecione o CNAE mais próximo:", 
                              options=resultado.index, 
                              format_func=lambda x: f"{resultado.loc[x, 'codigo']} - {resultado.loc[x, 'descricao']}")
        
        cnae_selecionado = f"{resultado.loc[escolha, 'codigo']} - {resultado.loc[escolha, 'descricao']}"
    else:
        st.error("Nenhum CNAE encontrado com essas palavras.")
else:
    st.info("Aguardando pesquisa...")

# --- PARTE 2: DADOS DO CLIENTE ---
if busca and not resultado.empty:
    st.divider()
    st.subheader("📋 Informações Adicionais")
    
    cep = st.text_input("Digite seu CEP (apenas números):", max_chars=8)
    # Limpa o CEP para garantir que só tenha números
    cep = "".join(filter(str.isdigit, cep))
    
    preferencia = st.radio(
        "O que deseja receber?",
        ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones")
    )
    
    seu_whatsapp = st.text_input("Seu WhatsApp com DDD (ex: 11999999999):")
    seu_whatsapp = "".join(filter(str.isdigit, seu_whatsapp))

    # --- PARTE 3: ENVIO ---
    if st.button("Finalizar e Gerar Mensagem"):
        if len(cep) < 8:
            st.warning("Por favor, digite um CEP válido com 8 dígitos.")
        elif len(seu_whatsapp) < 10:
            st.warning("Por favor, digite um WhatsApp válido com DDD.")
        else:
            # Montagem da mensagem para o WhatsApp
            texto_msg = (
                f"*Novo Interesse de CNAE*\n\n"
                f"*CNAE:* {cnae_selecionado}\n"
                f"*CEP:* {cep}\n"
                f"*Deseja:* {preferencia}\n"
                f"*WhatsApp Cliente:* {seu_whatsapp}"
            )
            
            # Codifica a mensagem para URL
            msg_codificada = urllib.parse.quote(texto_msg)
            link_whatsapp = f"https://wa.me/5512981779669?text={msg_codificada}"
            
            # AQUI ESTAVA O ERRO: mudei 'unsafe_allow_index' para 'unsafe_allow_html'
            st.markdown(f"""
                <a href="{link_whatsapp}" target="_blank">
                    <button style="background-color: #25D366; color: white; padding: 15px 30px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px;">
                        ✅ CLIQUE AQUI PARA ENVIAR NO WHATSAPP
                    </button>
                </a>
            """, unsafe_allow_html=True)
