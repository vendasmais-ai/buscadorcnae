import streamlit as st
import pandas as pd
import urllib
import mysql.connector
import unicodedata

# 🔧 FUNÇÃO PARA NORMALIZAR TEXTO (remove acento)
def normalizar(texto):
    if not texto: return ""
    texto = str(texto).lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

# --- PARTE 1: BUSCA DE CNAE ---
st.set_page_config(page_title="Buscador de CNAE", layout="centered")
st.title("🔎 Buscador de CNAE")
busca = st.text_input("Digite o CNAE ou palavras ou descrição para a busca:")

if busca:
    busca_limpa = normalizar(busca)
    # 🔥 BASE DE CNAE (Exemplo)
    tabela_cnae = [
        {"cnae": "6612-6/01", "desc": "Corretoras de títulos e valores mobiliários"},
        {"cnae": "6201-5/01", "desc": "Desenvolvimento de programas de computador"},
        {"cnae": "4711-3/02", "desc": "Supermercados"},
        {"cnae": "5611-2/01", "desc": "Restaurantes"},
        {"cnae": "4619-2/00", "desc": "Representantes comerciais e agentes do comércio de mercadorias em geral não especializado"},
    ]

    resultados_filtrados = [
        item for item in tabela_cnae 
        if busca_limpa in normalizar(item["desc"]) or busca_limpa in "".join(filter(str.isdigit, item["cnae"]))
    ]

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

# --- PARTE 2: DADOS DO CLIENTE ---
if busca and not resultado.empty:
    st.divider()
    st.subheader("📋 Informações Adicionais")
    
    cep = st.text_input("Digite CEP desejado (apenas números ou início):")
    cep = "".join(filter(str.isdigit, cep))
    
    preferencia = st.radio(
        "O que deseja receber no arquivo?",
        ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones")
    )
    
    seu_whatsapp = st.text_input("Seu WhatsApp com DDD (ex: 11999999999):")
    seu_whatsapp = "".join(filter(str.isdigit, seu_whatsapp))
    
    ddd_preferencia = st.text_input("DDD da região (ex: 11):")
    ddd_preferencia = "".join(filter(str.isdigit, ddd_preferencia))

    # --- PARTE 3: PROCESSAMENTO E GERAÇÃO DE ARQUIVO ---
    if st.button("Finalizar e Gerar Lista"):
        if len(cep) < 5:
            st.warning("Digite pelo menos 5 números do CEP.")
        elif len(seu_whatsapp) < 10:
            st.warning("WhatsApp inválido.")
        elif len(ddd_preferencia) < 2:
            st.warning("DDD inválido.")
        else:
            try:
                # 🔧 CONEXÃO MYSQL
                db = mysql.connector.connect(
                    host="127.0.0.1", user="root", password="", database="CNAE"
                )
                cursor = db.cursor()

                # 🔎 BUSCA DOS DADOS COMPLETOS PARA FILTRAGEM
                # Selecionamos cnpj, razão social e os contatos
                query = """
                    SELECT cnpj, razao_social, email, ddd1, telefone1, ddd2, telefone2 
                    FROM estabelecimento1 
                    WHERE `Column 11` = %s AND `Column 18` LIKE %s AND (`Column 21` = %s OR `Column 23` = %s)
                """
                cursor.execute(query, (cnae_selecionado, cep + "%", ddd_preferencia, ddd_preferencia))
                colunas_bd = [i[0] for i in cursor.description]
                dados = cursor.fetchall()
                df_bruto = pd.DataFrame(dados, columns=colunas_bd)

                # 🔎 BUSCA TOTAL BRASIL PARA A MENSAGEM
                cursor.execute("SELECT COUNT(*) FROM estabelecimento1 WHERE `Column 11` = %s", (cnae_selecionado,))
                total_brasil = cursor.fetchone()[0]

                cursor.close()
                db.close()

                # 🎯 FILTRAGEM DAS COLUNAS CONFORME ESCOLHA DO CLIENTE
                cols_base = ['cnpj', 'razao_social']
                if preferencia == "Apenas E-mails":
                    df_final = df_bruto[cols_base + ['email']]
                elif preferencia == "Apenas Telefones":
                    df_final = df_bruto[cols_base + ['ddd1', 'telefone1', 'ddd2', 'telefone2']]
                else:
                    df_final = df_bruto # Mantém todas (Email + Telefones)

                total_encontrado = len(df_final)

                if total_encontrado > 0:
                    st.success(f"Encontrados {total_encontrado} contatos!")
                    
                    # Gerar CSV para download
                    csv_data = df_final.to_csv(index=False, sep=';', encoding='utf-8-sig')
                    st.download_button(
                        label=f"📥 Baixar CSV ({preferencia})",
                        data=csv_data,
                        file_name=f"contatos_{cnae_selecionado}.csv",
                        mime="text/csv"
                    )

                    # Preparar Mensagem WhatsApp
                    texto_msg = (
                        f"Novo Interesse de CNAE\n"
                        f"CNAE: {cnae_selecionado}\n"
                        f"Resultados: {total_encontrado}\n"
                        f"Deseja: {preferencia}\n"
                        f"WhatsApp: {seu_whatsapp}"
                    )
                else:
                    texto_msg = (
                        f"CNAE: {cnae_selecionado} não encontrado nesta região.\n"
                        f"No Brasil existem {total_brasil} empresas."
                    )
                    st.info("Nenhum resultado local, mas a mensagem foi preparada.")

                # Link WhatsApp
                msg_url = urllib.parse.quote(texto_msg)
                link_wa = f"https://wa.me/5512981779669?text={msg_url}"
                st.markdown(f"""
                    <a href="{link_wa}" target="_blank">
                        <button style="background-color: #25D366; color: white; padding: 15px; border: none; border-radius: 8px; width: 100%; cursor: pointer; font-weight: bold;">
                            ENVIAR RESUMO NO WHATSAPP
                        </button>
                    </a>
                """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Erro ao conectar no banco: {e}")
