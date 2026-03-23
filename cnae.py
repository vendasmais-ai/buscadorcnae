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
        cnae_selecionado = ""
else:
    cnae_selecionado = ""

if cnae_selecionado:
    st.divider()
    st.subheader("📋 Informações Adicionais")
    
    cep = st.text_input("Digite CEP desejado (apenas números ou início):")
    cep = "".join(filter(str.isdigit, cep))
    
    preferencia = st.radio("O que deseja receber?", ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones"))
    
    seu_whatsapp = st.text_input("Seu WhatsApp com DDD (ex: 11999999999):")
    seu_whatsapp = "".join(filter(str.isdigit, seu_whatsapp))
    
    ddd_preferencia = st.text_input("DDD da região (ex: 11):")
    ddd_preferencia = "".join(filter(str.isdigit, ddd_preferencia))

    if st.button("🚀 FINALIZAR E BAIXAR"):
        if len(cep) < 5:
            st.error("❌ Digite pelo menos 5 números do CEP")
        elif len(seu_whatsapp) < 10:
            st.error("❌ WhatsApp inválido")
        elif len(ddd_preferencia) < 2:
            st.error("❌ DDD inválido")
        else:
            with st.spinner("🔍 Buscando contatos..."):
                # CONEXÃO
                conn = mysql.connector.connect(
                    host="127.0.0.1", user="root", password="", database="CNAE"
                )
                
                # CONTAGEM TOTAL
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM estabelecimento1 WHERE `Column 11` = %s", (cnae_selecionado,))
                total_brasil = cursor.fetchone()[0]
                
                # CONTAGEM COM FILTRO
                cursor.execute("""
                    SELECT COUNT(*) FROM estabelecimento1 
                    WHERE `Column 11` = %s AND `Column 18` LIKE %s 
                    AND (`Column 21` = %s OR `Column 23` = %s)
                """, (cnae_selecionado, cep + "%", ddd_preferencia, ddd_preferencia))
                total_filtro = cursor.fetchone()[0]
                
                # 🔥 QUERY ESPECÍFICA POR PREFERÊNCIA
                if preferencia == "Apenas E-mails":
                    query = """
                        SELECT `Column 24` as email 
                        FROM estabelecimento1 
                        WHERE `Column 11` = %s AND `Column 18` LIKE %s 
                        AND `Column 24` IS NOT NULL AND `Column 24` != ''
                        AND (`Column 21` = %s OR `Column 23` = %s)
                        LIMIT 1000
                    """
                    nome_csv = f"emails_CNAE{cnae_selecionado}_CEP{cep}.csv"
                elif preferencia == "Apenas Telefones":
                    query = """
                        SELECT `Column 21` as ddd1, `Column 23` as telefone1
                        FROM estabelecimento1 
                        WHERE `Column 11` = %s AND `Column 18` LIKE %s 
                        AND (`Column 21` = %s OR `Column 23` = %s)
                        AND (`Column 21` IS NOT NULL OR `Column 23` IS NOT NULL)
                        LIMIT 1000
                    """
                    nome_csv = f"telefones_CNAE{cnae_selecionado}_CEP{cep}.csv"
                else:  # E-mails + Telefones
                    query = """
                        SELECT `Column 24` as email, `Column 21` as ddd1, `Column 23` as telefone1
                        FROM estabelecimento1 
                        WHERE `Column 11` = %s AND `Column 18` LIKE %s 
                        AND (`Column 21` = %s OR `Column 23` = %s)
                        LIMIT 1000
                    """
                    nome_csv = f"contatos_CNAE{cnae_selecionado}_CEP{cep}.csv"
                
                df = pd.read_sql(query, conn, params=(cnae_selecionado, cep + "%", ddd_preferencia, ddd_preferencia))
                
                conn.close()
                
                if len(df) > 0:
                    st.success(f"✅ {len(df)} {preferencia.lower()} encontrados!")
                    
                    # PREVIEW
                    st.subheader("📋 Preview dos dados:")
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    # DOWNLOAD
                    csv_data = df.to_csv(index=False, encoding='utf-8').encode('utf-8')
                    st.download_button(
                        label=f"📥 DOWNLOAD {preferencia.upper()} ({len(df)} linhas)",
                        data=csv_data,
                        file_name=nome_csv,
                        mime='text/csv'
                    )
                    
                    # WHATSAPP
                    msg = f"""✅ LISTA PRONTA CNAE {cnae_selecionado}
CEP: {cep} | DDD: {ddd_preferencia}
📊 {len(df)} {preferencia.lower()} encontrados
💼 Cliente: {seu_whatsapp}"""
                    
                else:
                    st.warning(f"❌ Nenhum {preferencia.lower()} encontrado com esses filtros")
                    msg = f"""❌ CNAE {cnae_selecionado}
CEP: {cep} | DDD: {ddd_preferencia}
Nenhum resultado com esses filtros
💼 Cliente: {seu_whatsapp}
Total Brasil: {total_brasil} empresas"""
                
                # LINK WHATSAPP
                wa_link = f"https://wa.me/5512981779669?text={urllib.parse.quote(msg)}"
                st.markdown(f"""
                <a href="{wa_link}" target="_blank" style="
                    background: linear-gradient(45deg, #25D366, #128C7E);
                    color: white; padding: 15px 30px; border: none; 
                    border-radius: 25px; cursor: pointer; width: 100%; 
                    font-weight: bold; font-size: 18px; text-align: center;
                    display: block; text-decoration: none; margin-top: 20px;">
                    🚀 ENVIAR RELATÓRIO NO WHATSAPP
                </a>
                """, unsafe_allow_html=True)
