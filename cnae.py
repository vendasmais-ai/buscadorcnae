import streamlit as st
import pandas as pd
import urllib
import mysql.connector
import unicodedata

# 🔧 FUNÇÃO PARA NORMALIZAR TEXTO (remove acento)
def normalizar(texto):
    texto = texto.lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

# --- PARTE 1: BUSCA DE CNAE ---
st.title("🔎 Buscador de CNAE")

busca = st.text_input("Digite o CNAE ou palavras ou descrição para a busca:")

if busca:
    busca_limpa = normalizar(busca)

    # 🔥 BASE DE CNAE
    tabela_cnae = [
        {"cnae": "6612-6/01", "desc": "Corretoras de títulos e valores mobiliários"},
        {"cnae": "6201-5/01", "desc": "Desenvolvimento de programas de computador"},
        {"cnae": "4711-3/02", "desc": "Supermercados"},
        {"cnae": "5611-2/01", "desc": "Restaurantes"},
        {"cnae": "4619-2/00", "desc": "Representantes comerciais e agentes do comércio de mercadorias em geral não especializado"},
    ]

    resultados_filtrados = [
        item for item in tabela_cnae
        if busca_limpa in normalizar(item["desc"])
        or busca_limpa in "".join(filter(str.isdigit, item["cnae"]))
    ]

    if resultados_filtrados:
        resultado = pd.DataFrame({
            "CNAE": [
                "".join(filter(str.isdigit, item["cnae"]))
                for item in resultados_filtrados
            ],
            "Descrição": [item["desc"] for item in resultados_filtrados]
        })

        cnae_selecionado = st.selectbox(
            "Selecione o CNAE encontrado:",
            resultado["CNAE"]
        )
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
        "O que deseja receber?",
        ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones")
    )
    
    seu_whatsapp = st.text_input("Seu WhatsApp com DDD (ex: 11999999999):")
    seu_whatsapp = "".join(filter(str.isdigit, seu_whatsapp))

    ddd_preferencia = st.text_input("DDD da região (ex: 11):")
    ddd_preferencia = "".join(filter(str.isdigit, ddd_preferencia))

    # --- PARTE 3: ENVIO ---
    if st.button("Finalizar e Gerar Mensagem"):

        if len(cep) < 5:
            st.warning("Digite pelo menos 5 números do CEP.")
        
        elif len(seu_whatsapp) < 10:
            st.warning("WhatsApp inválido.")
        
        elif len(ddd_preferencia) < 2:
            st.warning("DDD inválido.")
        
        else:
            # 🔧 CONEXÃO MYSQL LOCAL
            db = mysql.connector.connect(
                host="127.0.0.1",
                user="root",
                password="",
                database="CNAE"
            )
            cursor = db.cursor()

            # 🔎 TOTAL BRASIL
            cursor.execute(
                "SELECT COUNT(*) FROM estabelecimento1 WHERE `Column 11` = %s",
                (cnae_selecionado,)
            )
            total_brasil = cursor.fetchone()[0]

            # 🔎 COM FILTROS
            cursor.execute("""
                SELECT COUNT(*) FROM estabelecimento1
                WHERE `Column 11` = %s
                AND `Column 18` LIKE %s
                AND (`Column 21` = %s OR `Column 23` = %s)
            """, (cnae_selecionado, cep + "%", ddd_preferencia, ddd_preferencia))

            total_filtro = cursor.fetchone()[0]

            if total_filtro > 0:
                cursor.execute("""
                    SELECT `Column 5` AS Nome, `Column 18` AS CEP, `Column 21` AS DDD, 
                           `Column 22` AS Telefone, `Column 23` AS DDD2, `Column 24` AS Telefone2, 
                           `Column 25` AS Email
                    FROM estabelecimento1
                    WHERE `Column 11` = %s
                    AND `Column 18` LIKE %s
                    AND (`Column 21` = %s OR `Column 23` = %s)
                """, (cnae_selecionado, cep + "%", ddd_preferencia, ddd_preferencia))

                lista_empresas = cursor.fetchall()
                colunas = ["Nome", "CEP", "DDD", "Telefone", "DDD2", "Telefone2", "Email"]
                df_empresas = pd.DataFrame(lista_empresas, columns=colunas)

                st.success(f"Foram encontradas {total_filtro} empresas com os filtros aplicados.")
                # st.dataframe(df_empresas.head(10))  # mostra só prévia

                # Exporta para CSV externo (apenas local, sem download)
                df_empresas.to_csv("empresas_filtradas.csv", index=False, encoding="utf-8-sig")
                st.info("Arquivo 'empresas_filtradas.csv' foi salvo localmente com os resultados.")

                texto_msg = (
                    f"Novo Interesse de CNAE\n\n"
                    f"CNAE: {cnae_selecionado}\n"
                    f"CEP: {cep}\n"
                    f"DDD: {ddd_preferencia}\n"
                    f"Deseja: {preferencia}\n"
                    f"Resultados encontrados: {total_filtro}\n"
                    f"WhatsApp Cliente: {seu_whatsapp}"
                )
            else:
                st.warning("Não existem empresas com esse CNAE com esses filtros.")
                st.info(f"Mas encontrei {total_brasil} empresas no Brasil com esse CNAE.")

                # Buscar todas as empresas no Brasil com esse CNAE
                cursor.execute("""
                    SELECT `Column 5` AS Nome, `Column 18` AS CEP, `Column 21` AS DDD, 
                           `Column 22` AS Telefone, `Column 23` AS DDD2, `Column 24` AS Telefone2, 
                           `Column 25` AS Email
                    FROM estabelecimento1
                    WHERE `Column 11` = %s
                """, (cnae_selecionado,))

                lista_empresas = cursor.fetchall()
                colunas = ["Nome", "CEP", "DDD", "Telefone", "DDD2", "Telefone2", "Email"]
                df_empresas = pd.DataFrame(lista_empresas, columns=colunas)

                st.success(f"Foram encontradas {total_brasil} empresas no Brasil com esse CNAE.")
                # st.dataframe(df_empresas.head(10))  # mostra só prévia

                # Exporta para CSV externo (apenas local, sem download)
                df_empresas.to_csv("empresas_brasil.csv", index=False, encoding="utf-8-sig")
                st.info("Arquivo 'empresas_brasil.csv' foi salvo localmente com os resultados.")

                texto_msg = (
                    f"CNAE: {cnae_selecionado}\n"
                    f"CEP informado: {cep}\n"
                    f"DDD informado: {ddd_preferencia}\n"
                    f"Deseja: {preferencia}\n"
                    f"WhatsApp Cliente: {seu_whatsapp}\n\n"
                    f"Não existem empresas com esse CNAE com esses filtros.\n\n"
                    f"Mas encontrei {total_brasil} empresas no Brasil com esse CNAE.\n\n"
                    f"Vou preparar uma lista qualificada para você.\n"
                    f"Podemos filtrar por região, cidade ou contatos válidos."
                )

            cursor.close()
            db.close()

            # 🔗 SAÍDA PARA WHATSAPP
            msg_codificada = urllib.parse.quote(texto_msg, safe='', encoding='utf-8')
            link_whatsapp = f"https://wa.me/5512981779669?text={msg_codificada}"

            st.markdown(
                f"""
                <a href="{link_whatsapp}" target="_blank">
                    <button style="background-color: #25D366; color: white; padding: 15px 30px; border: none; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold; font-size: 16px;">
                        CLIQUE AQUI PARA ENVIAR NO WHATSAPP
                    </button>
                </a>
                """,
                unsafe_allow_html=True
            )
