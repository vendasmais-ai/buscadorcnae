import streamlit as st
import pandas as pd
import urllib.parse
import mysql.connector
import unicodedata

# Função normalizar
def normalizar(texto):
    if texto:
        texto = str(texto).lower().strip()
        return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return ''

st.title("🔎 Buscador CNAE")

# 1. Seleção CNAE
st.header("1️⃣ Escolha o CNAE")
cnae = st.selectbox("Selecione CNAE:", ["6201", "5611", "4711", "6612", "4619"])

# 2. Filtros
st.header("2️⃣ Filtros")
col1, col2 = st.columns(2)
with col1:
    cep = st.text_input("CEP:", value="12230")
    cep = ''.join(filter(str.isdigit, cep))
with col2:
    ddd = st.text_input("DDD:", value="12")
    ddd = ''.join(filter(str.isdigit, ddd))

tipo = st.radio("Tipo de contato:", ["📧 Apenas E-mails", "📞 Apenas Telefones", "📧📞 Ambos"])
whatsapp = st.text_input("Seu WhatsApp:", value="11999999999")

# 3. Botão executar
if st.button("🚀 BUSCAR E BAIXAR", type="primary"):
    if len(cep) < 5 or len(ddd) < 2:
        st.error("CEP e DDD inválidos!")
    else:
        try:
            # Conectar MySQL
            conn = mysql.connector.connect(
                host="127.0.0.1",
                user="root", 
                password="",
                database="CNAE"
            )
            
            # Query específica por tipo
            if "E-mails" in tipo:
                query = f"""
                    SELECT `Column 24` as email 
                    FROM estabelecimento1 
                    WHERE `Column 11` = '{cnae}' 
                    AND `Column 18` LIKE '%{cep}%'
                    AND `Column 24` IS NOT NULL 
                    AND `Column 24` != ''
                    AND (`Column 21` = '{ddd}' OR `Column 23` = '{ddd}')
                    LIMIT 1000
                """
                nome_csv = f"emails_CNAE_{cnae}_CEP_{cep}.csv"
            elif "Telefones" in tipo:
                query = f"""
                    SELECT `Column 21` as ddd1, `Column 23` as telefone1
                    FROM estabelecimento1 
                    WHERE `Column 11` = '{cnae}' 
                    AND `Column 18` LIKE '%{cep}%'
                    AND (`Column 21` = '{ddd}' OR `Column 23` = '{ddd}')
                    LIMIT 1000
                """
                nome_csv = f"telefones_CNAE_{cnae}_CEP_{cep}.csv"
            else:
                query = f"""
                    SELECT `Column 24` as email, 
                           `Column 21` as ddd1, 
                           `Column 23` as telefone1
                    FROM estabelecimento1 
                    WHERE `Column 11` = '{cnae}' 
                    AND `Column 18` LIKE '%{cep}%'
                    AND (`Column 21` = '{ddd}' OR `Column 23` = '{ddd}')
                    LIMIT 1000
                """
                nome_csv = f"contatos_CNAE_{cnae}_CEP_{cep}.csv"
            
            # Executar
            df = pd.read_sql(query, conn)
            conn.close()
            
            if len(df) > 0:
                st.success(f"✅ {len(df)} contatos encontrados!")
                
                # Preview
                st.subheader("📋 Preview:")
                st.dataframe(df.head(10))
                
                # Download
                csv_data = df.to_csv(index=False, encoding='utf-8').encode('utf-8')
                st.download_button(
                    label=f"📥 DOWNLOAD CSV ({len(df)} linhas)",
                    data=csv_data,
                    file_name=nome_csv,
                    mime='text/csv'
                )
                
                # WhatsApp
                msg = f"""✅ CNAE {cnae}
CEP: {cep} | DDD: {ddd}
📊 {len(df)} contatos
{tipo}
Cliente: {whatsapp}"""
                
                st.markdown(f"""
                <a href="https://wa.me/5512981779669?text={urllib.parse.quote(msg)}" 
                   target="_blank" style="background: #25D366; color: white; padding: 15px 30px; border-radius: 25px; text-decoration: none; font-weight: bold; width: 100%; text-align: center; display: block;">
                   📱 Enviar WhatsApp
                </a>
                """, unsafe_allow_html=True)
                
            else:
                st.warning("❌ Nenhum contato encontrado")
                
        except Exception as e:
            st.error(f"Erro: {e}")

st.markdown("---")
st.caption("✅ Código completo - copia e cola")
