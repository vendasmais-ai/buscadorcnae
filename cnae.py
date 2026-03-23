import streamlit as st
import pandas as pd
import urllib
import mysql.connector
import unicodedata

def normalizar(texto):
    if texto:
        texto = texto.lower().strip()
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return ""

st.title("🔎 Buscador de CNAE")
busca = st.text_input("Digite o CNAE ou palavras para busca:")

if busca:
    busca_limpa = normalizar(busca)
    tabela_cnae = [
        {"cnae": "6612-6/01", "desc": "Corretoras de títulos e valores mobiliários"},
        {"cnae": "6201-5/01", "desc": "Desenvolvimento de programas de computador"},
        {"cnae": "4711-3/02", "desc": "Supermercados"},
        {"cnae": "5611-2/01", "desc": "Restaurantes"},
        {"cnae": "4619-2/00", "desc": "Representantes comerciais"}
    ]
    
    resultados = [item for item in tabela_cnae 
                 if busca_limpa in normalizar(item["desc"]) or 
                 busca_limpa in "".join(filter(str.isdigit, item["cnae"]))]
    
    if resultados:
        df_cnae = pd.DataFrame({
            "CNAE": [''.join(filter(str.isdigit, item["cnae"])) for item in resultados],
            "Descrição": [item["desc"] for item in resultados]
        })
        cnae_selecionado = st.selectbox("Selecione CNAE:", df_cnae["CNAE"])
    else:
        st.warning("❌ Nenhum CNAE encontrado")
        cnae_selecionado = ""
else:
    cnae_selecionado = ""

if cnae_selecionado:
    st.divider()
    st.subheader("📋 Filtros do Cliente")
    
    cep = st.text_input("CEP (apenas números):")
    cep = ''.join(filter(str.isdigit, cep))
    
    preferencia = st.radio("Cliente quer:", ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones"))
    
    whatsapp_cliente = st.text_input("WhatsApp do cliente:")
    whatsapp_cliente = ''.join(filter(str.isdigit, whatsapp_cliente))
    
    ddd = st.text_input("DDD:")
    ddd = ''.join(filter(str.isdigit, ddd))

    if st.button("🚀 BUSCAR E BAIXAR", type="primary"):
        if len(cep) < 5:
            st.error("CEP precisa de 5+ dígitos")
        elif len(whatsapp_cliente) < 10:
            st.error("WhatsApp inválido")
        elif len(ddd) < 2:
            st.error("DDD inválido")
        else:
            with st.spinner("Procurando contatos..."):
                # CONECTA MYSQL
                conn = mysql.connector.connect(
                    host="127.0.0.1", user="root", password="", database="CNAE"
                )
                
                # QUERY ESPECÍFICA POR ESCOLHA
                if preferencia == "Apenas E-mails":
                    query = """
                        SELECT `Column 24` as email
                        FROM estabelecimento1 
                        WHERE `Column 11` = %s 
                        AND `Column 18` LIKE %s
                        AND `Column 24` IS NOT NULL 
                        AND `Column 24` != ''
                        AND (`Column 21` = %s OR `Column 23` = %s)
                        LIMIT 5000
                    """
                    filename = f"emails_CNAE_{cnae_selecionado}_CEP_{cep}.csv"
                elif preferencia == "Apenas Telefones":
                    query = """
                        SELECT `Column 21` as ddd1, `Column 23` as telefone1
                        FROM estabelecimento1 
                        WHERE `Column 11` = %s 
                        AND `Column 18` LIKE %s
                        AND (`Column 21` = %s OR `Column 23` = %s)
                        AND (`Column 21` IS NOT NULL OR `Column 23` IS NOT NULL)
                        LIMIT 5000
                    """
                    filename = f"telefones_CNAE_{cnae_selecionado}_CEP_{cep}.csv"
                else:  # Ambos
                    query = """
                        SELECT `Column 24` as email, `Column 21` as ddd1, `Column 23` as telefone1
                        FROM estabelecimento1 
                        WHERE `Column 11` = %s 
                        AND `Column 18` LIKE %s
                        AND (`Column 21` = %s OR `Column 23` = %s)
                        LIMIT 5000
                    """
                    filename = f"contatos_CNAE_{cnae_selecionado}_CEP_{cep}.csv"
                
                df_resultado = pd.read_sql(query, conn, 
                    params=(cnae_selecionado, f"%{cep}%", ddd, ddd))
                
                conn.close()
                
                if len(df_resultado) > 0:
                    st.success(f"✅ {len(df_resultado)} contatos encontrados!")
                    
                    # MOSTRA PREVIEW
                    st.subheader("👀 Preview:")
                    st.dataframe(df_resultado.head(5), use_container_width=True)
                    
                    # DOWNLOAD
                    csv = df_resultado.to_csv(index=False, encoding='utf-8').encode('utf-8')
                    st.download_button(
                        label=f"📥 BAIXAR CSV ({len(df_resultado)} linhas)",
                        data=csv,
                        file_name=filename,
                        mime="text/csv"
                    )
                    
                    # WHATSAPP
                    mensagem = f"""✅ LISTA CNAE {cnae_selecionado}
CEP {cep} | DDD {ddd}
📊 {len(df_resultado)} {preferencia.lower()}
👤 Cliente: {whatsapp_cliente}"""
                    
                else:
                    st.warning("❌ Nenhum contato encontrado")
                    mensagem = f"""❌ CNAE {cnae_selecionado}
CEP {cep} | DDD {ddd}
Nenhum resultado
👤 Cliente: {whatsapp_cliente}"""
                
                # BOTÃO WHATSAPP
                st.markdown(f"""
                <a href="https://wa.me/5512981779669?text={urllib.parse.quote(mensagem)}" 
                   target="_blank" style="
                   background: #25D366; color: white; padding: 15px; 
                   border-radius: 10px; text-decoration: none; 
                   font-weight: bold; width: 100%; text-align: center;
                   display: block; margin-top: 20px;">
                   📱 ENVIAR RELATÓRIO WHATSAPP
                </a>
                """, unsafe_allow_html=True)
