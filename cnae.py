import streamlit as st
import pandas as pd
import urllib
import mysql.connector
import unicodedata

def normalizar(texto):
    texto = texto.lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

st.title("🔎 Buscador de CNAE")
busca = st.text_input("Digite o CNAE ou palavras ou descrição para a busca:")

if busca:
    busca_limpa = normalizar(busca)
    tabela_cnae = [
        {"cnae": "6612-6/01", "desc": "Corretoras de títulos e valores mobiliários"},
        {"cnae": "6201-5/01", "desc": "Desenvolvimento de programas de computador"},
        {"cnae": "4711-3/02", "desc": "Supermercados"},
        {"cnae": "5611-2/01", "desc": "Restaurantes"},
        {"cnae": "4619-2/00", "desc": "Representantes comerciais e agentes do comércio de mercadorias em geral não especializado"},
    ]
    
    resultados_filtrados = [item for item in tabela_cnae if busca_limpa in normalizar(item["desc"]) or busca_limpa in "".join(filter(str.isdigit, item["cnae"]))]
    
    if resultados_filtrados:
        resultado = pd.DataFrame({
            "CNAE": [ "".join(filter(str.isdigit, item["cnae"])) for item in resultados_filtrados ],
            "Descrição": [item["desc"] for item in resultados_filtrados]
        })
        cnae_selecionado = st.selectbox("Selecione o CNAE encontrado:", resultado["CNAE"])
    else:
        st.warning("Nenhum CNAE encontrado para essa busca.")
        resultado = pd.DataFrame()
        cnae_selecionado = ""
else:
    resultado = pd.DataFrame()
    cnae_selecionado = ""

if busca and not resultado.empty:
    st.divider()
    st.subheader("📋 Informações Adicionais")
    
    cep = st.text_input("Digite CEP desejado (apenas números ou início):")
    cep = "".join(filter(str.isdigit, cep))
    
    preferencia = st.radio("O que deseja receber?", ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones"))
    
    seu_whatsapp = st.text_input("Seu WhatsApp com DDD (ex: 11999999999):")
    seu_whatsapp = "".join(filter(str.isdigit, seu_whatsapp))
    
    ddd_preferencia = st.text_input("DDD da região (ex: 11):")
    ddd_preferencia = "".join(filter(str.isdigit, ddd_preferencia))

    if st.button("Finalizar e Gerar Mensagem"):
        if len(cep) < 5:
            st.warning("Digite pelo menos 5 números do CEP.")
        elif len(seu_whatsapp) < 10:
            st.warning("WhatsApp inválido.")
        elif len(ddd_preferencia) < 2:
            st.warning("DDD inválido.")
        else:
            db = mysql.connector.connect(host="127.0.0.1", user="root", password="", database="CNAE")
            cursor = db.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM estabelecimento1 WHERE `Column 11` = %s", (cnae_selecionado,))
            total_brasil = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM estabelecimento1 WHERE `Column 11` = %s AND `Column 18` LIKE %s AND (`Column 21` = %s OR `Column 23` = %s)", 
                          (cnae_selecionado, cep + "%", ddd_preferencia, ddd_preferencia))
            total_filtro = cursor.fetchone()[0]
            
            # 🔥 FIX DEFINITIVO - APENAS AS COLUNAS PEDIDAS
            if preferencia == "Apenas E-mails":
                query_csv = "SELECT `Column 24` as email FROM estabelecimento1 WHERE `Column 11` = %s AND `Column 18` LIKE %s AND (`Column 21` = %s OR `Column 23` = %s) LIMIT 1000"
                nome_arquivo = f"emails_CNAE_{cnae_selecionado}_{cep}.csv"
            elif preferencia == "Apenas Telefones":
                query_csv = "SELECT `Column 21` as ddd1, `Column 23` as telefone1 FROM estabelecimento1 WHERE `Column 11` = %s AND `Column 18` LIKE %s AND (`Column 21` = %s OR `Column 23` = %s) LIMIT 1000"
                nome_arquivo = f"telefones_CNAE_{cnae_selecionado}_{cep}.csv"
            else:
                query_csv = "SELECT `Column 24` as email, `Column 21` as ddd1, `Column 23` as telefone1 FROM estabelecimento1 WHERE `Column 11` = %s AND `Column 18` LIKE %s AND (`Column 21` = %s OR `Column 23` = %s) LIMIT 1000"
                nome_arquivo = f"contatos_CNAE_{cnae_selecionado}_{cep}.csv"
            
            df_contatos = pd.read_sql(query_csv, db, params=(cnae_selecionado, cep + "%", ddd_preferencia, ddd_preferencia))
            
            cursor.close()
            db.close()
            
            if total_filtro > 0:
                texto_msg = f"Novo Interesse de CNAE\n\nCNAE: {cnae_selecionado}\nCEP: {cep}\nDDD: {ddd_preferencia}\nResultados encontrados: {total_filtro}\nDeseja: {preferencia}\nWhatsApp Cliente: {seu_whatsapp}"
                
                st.success(f"✅ {total_filtro} {preferencia.lower()} encontrados!")
                st.dataframe(df_contatos.head())
                
                csv = df_contatos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Baixar {preferencia} ({len(df_contatos)} linhas)",
                    data=csv,
                    file_name=nome_arquivo,
                    mime='text/csv'
                )
            else:
                texto_msg = f"CNAE: {cnae_selecionado}\nCEP informado: {cep}\nDDD informado: {ddd_preferencia}\nWhatsApp Cliente: {seu_whatsapp}\n\nNão existem empresas com esse CNAE com esses filtros.\n\nMas encontrei {total_brasil} empresas no Brasil com esse CNAE.\n\nVou preparar uma lista qualificada para você.\nPodemos filtrar por região, cidade ou contatos válidos."
                st.warning("Nenhum contato com esses filtros.")
            
            msg_codificada = urllib.parse.quote(texto_msg)
            link_whatsapp = f"https://wa.me/5512981779669?text={msg_codificada}"
            st.markdown(f"""
                <a href="{link_whatsapp}" target="_blank">
                    <button style="background-color: #25D366; color: white; padding: 15px 30px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px;">
                        CLIQUE AQUI PARA ENVIAR NO WHATSAPP
                    </button>
                </a>
            """, unsafe_allow_html=True)
