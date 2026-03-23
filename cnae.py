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

st.title("🔎 Buscador CNAE - APENAS Contatos")
st.markdown("---")

# 1. BUSCA CNAE
busca = st.text_input("🔍 Digite CNAE ou descrição:")

if busca:
    busca_limpa = normalizar(busca)
    cnaes = [
        {"codigo": "6612", "desc": "Corretoras de valores"},
        {"codigo": "6201", "desc": "Desenvolvimento software"}, 
        {"codigo": "4711", "desc": "Supermercados"},
        {"codigo": "5611", "desc": "Restaurantes"},
        {"codigo": "4619", "desc": "Representantes comerciais"}
    ]
    
    resultados = [c for c in cnaes if busca_limpa in normalizar(c["desc"]) or busca_limpa in c["codigo"]]
    
    if resultados:
        cnae_selecionado = st.selectbox("✅ CNAE encontrado:", 
                                       [f"{c['codigo']} - {c['desc']}" for c in resultados])
        cnae_numero = cnae_selecionado.split(" - ")[0]
    else:
        st.error("❌ CNAE não encontrado")
        st.stop()
else:
    st.warning("Digite algo para buscar CNAE")
    st.stop()

# 2. FILTROS
st.subheader("📋 Filtros do Cliente")
col1, col2 = st.columns(2)
with col1:
    cep = st.text_input("CEP:", value="12230")
    cep = ''.join(filter(str.isdigit, cep))
with col2:
    ddd = st.text_input("DDD:", value="12")
    ddd = ''.join(filter(str.isdigit, ddd))

preferencia = st.radio("💼 Cliente quer:", 
                      ("📧 Apenas E-mails", "📞 Apenas Telefones", "📧📞 E-mails + Telefones"))

whatsapp = st.text_input("📱 WhatsApp cliente:", value="11999999999")
whatsapp = ''.join(filter(str.isdigit, whatsapp))

# 3. EXECUTAR
if st.button("🚀 BUSCAR CONTATOS", type="primary"):
    if len(cep) < 5 or len(ddd) < 2 or len(whatsapp) < 10:
        st.error("❌ Preencha todos os campos corretamente")
    else:
        with st.spinner("🔍 Buscando no banco..."):
            # CONEXÃO
            conn = mysql.connector.connect(
                host="127.0.0.1", user="root", password="", database="CNAE"
            )
            
            # QUERY ESPECÍFICA
            if "E-mails" in preferencia and "Telefones" not in preferencia:
                # APENAS EMAIL
                query = """
                    SELECT `Column 24` as email 
                    FROM estabelecimento1 
                    WHERE `Column 11` = %s 
                    AND `Column 18` LIKE %s
                    AND `Column 24` != '' 
                    AND `Column 24` IS NOT NULL
                    AND (`Column 21` = %s OR `Column 23` = %s)
                """
                nome_arquivo = f"emails_CNAE{cnae_numero}_CEP{cep}.csv"
            elif "Telefones" in preferencia and "E-mails" not in preferencia:
                # APENAS TELEFONE
                query = """
                    SELECT `Column 21` as ddd1, `Column 23` as telefone1
                    FROM estabelecimento1 
                    WHERE `Column 11` = %s 
                    AND `Column 18` LIKE %s
                    AND (`Column 21` = %s OR `Column 23` = %s)
                """
                nome_arquivo = f"tel_CNAE{cnae_numero}_CEP{cep}.csv"
            else:
                # AMBOS
                query = """
                    SELECT `Column 24` as email, `Column 21` as ddd1, `Column 23` as telefone1
                    FROM estabelecimento1 
                    WHERE `Column 11` = %s 
                    AND `Column 18` LIKE %s
                    AND (`Column 21` = %s OR `Column 23` = %s)
                """
                nome_arquivo = f"contatos_CNAE{cnae_numero}_CEP{cep}.csv"
            
            df = pd.read_sql(query, conn, params=(cnae_numero, f"%{cep}%", ddd, ddd))
            conn.close()
        
        if len(df) > 0:
            st.success(f"✅ {len(df)} contatos encontrados!")
            
            # PREVIEW
            st.subheader("📊 Preview:")
            st.dataframe(df.head(), use_container_width=True)
            
            # DOWNLOAD
            csv_data = df.to_csv(index=False, encoding='utf-8').encode('utf-8')
            st.download_button(
                label=f"📥 DOWNLOAD {len(df)} LINHAS",
                data=csv_data,
                file_name=nome_arquivo,
                mime='text/csv',
                type="secondary"
            )
            
            # WHATSAPP
            msg = f"""✅ LISTA PRONTA!
CNAE: {cnae_numero}
CEP: {cep} DDD: {ddd}
📊 {len(df)} {preferencia.split()[0].lower()}s
👤 Cliente: ({whatsapp})"""
            
            st.markdown(f"""
            <a href="https://wa.me/5512981779669?text={urllib.parse.quote(msg)}" 
               target="_blank" style="
               background: linear-gradient(45deg, #25D366, #128C7E);
               color: white; padding: 20px; border-radius: 15px; 
               text-decoration: none; font-weight: bold; font-size: 18px;
               width: 100%; text-align: center; display: block; 
               box-shadow: 0 4px 15px rgba(37,211,102,0.3);">
               📱 ENVIAR WHATSAPP
            </a>
            """, unsafe_allow_html=True)
            
        else:
            st.warning("❌ Zero contatos encontrados")
            st.info("Tente outro CEP ou DDD")

st.markdown("---")
st.caption("👨‍💻 Feito para DeBocaEmBoca - Caçapava/SP")
