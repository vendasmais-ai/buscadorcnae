import streamlit as st
import pandas as pd
import urllib
import mysql.connector
import unicodedata

# --- MOSTRAR LISTA DE CNAEs NO INÍCIO ---
try:
    df_lista = pd.read_csv("ListaCNAES.txt", sep=";", header=None, names=["CNAE", "Descrição"])
    st.subheader("📑 Lista de CNAEs disponíveis")
    st.dataframe(df_lista)
except Exception as e:
    st.warning("Não foi possível carregar a lista de CNAEs. Verifique se o arquivo ListaCNAES.txt está na pasta.")

# 🔧 FUNÇÃO PARA NORMALIZAR TEXTO (remove acento)
def normalizar(texto):
    texto = texto.lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

# --- PARTE 1: FILTROS DE CONSULTA ---
st.title("🔎 Buscador de Empresas")

cnae_selecionado = st.text_input("Digite o CNAE (apenas números):")
atividade = st.text_input("Digite a atividade (palavras):")
cep = st.text_input("Digite CEP desejado (apenas números ou início):")
cep = "".join(filter(str.isdigit, cep))
ddd_preferencia = st.text_input("DDD da região (ex: 11):")
ddd_preferencia = "".join(filter(str.isdigit, ddd_preferencia))

preferencia = st.radio("O que deseja receber?", ("Apenas E-mails", "Apenas Telefones", "E-mails + Telefones"))
seu_whatsapp = st.text_input("Seu WhatsApp com DDD (ex: 11999999999):")
seu_whatsapp = "".join(filter(str.isdigit, seu_whatsapp))

# --- PARTE 2: EXECUTAR CONSULTA ---
if st.button("Finalizar e Gerar Mensagem"):

    if len(seu_whatsapp) < 10:
        st.warning("WhatsApp inválido.")
    else:
        db = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="",
            database="CNAE"
        )
        cursor = db.cursor()

        # --- QUERY DINÂMICA ---
        query = """
            SELECT `Column 5` AS Nome, `Column 18` AS CEP, `Column 21` AS DDD, 
                   `Column 22` AS Telefone, `Column 23` AS DDD2, `Column 24` AS Telefone2, 
                   `Column 25` AS Email
            FROM estabelecimentos
            WHERE 1=1
        """
        params = []

        if cnae_selecionado:
            query += " AND `Column 11` = %s"
            params.append(cnae_selecionado)

        if atividade:
            query += " AND `Column 5` LIKE %s"
            params.append("%" + atividade + "%")

        if cep:
            query += " AND `Column 18` LIKE %s"
            params.append(cep + "%")

        if ddd_preferencia:
            query += " AND (`Column 21` = %s OR `Column 23` = %s)"
            params.extend([ddd_preferencia, ddd_preferencia])

        cursor.execute(query, tuple(params))
        lista_empresas = cursor.fetchall()
        colunas = ["Nome", "CEP", "DDD", "Telefone", "DDD2", "Telefone2", "Email"]
        df_empresas = pd.DataFrame(lista_empresas, columns=colunas)

        total_filtro = len(df_empresas)

        if total_filtro > 0:
            st.success(f"Foram encontradas {total_filtro} empresas com os filtros aplicados.")

            # Nome do arquivo com filtros usados
            filtros_nome = ""
            if cnae_selecionado:
                filtros_nome += f"{cnae_selecionado}_"
            if atividade:
                filtros_nome += f"{atividade}_"
            if cep:
                filtros_nome += f"{cep}_"
            if ddd_preferencia:
                filtros_nome += f"{ddd_preferencia}_"

            df_empresas.to_csv(
                f"consulta_{filtros_nome}{preferencia}_{seu_whatsapp}.csv",
                index=False,
                encoding="utf-8-sig"
            )
            st.info("Arquivo de consulta foi salvo localmente com os resultados.")

            texto_msg = (
                f"Novo Interesse de Consulta\n\n"
                f"CNAE: {cnae_selecionado}\n"
                f"Atividade: {atividade}\n"
                f"CEP: {cep}\n"
                f"DDD: {ddd_preferencia}\n"
                f"Deseja: {preferencia}\n"
                f"Resultados encontrados: {total_filtro}\n"
                f"WhatsApp Cliente: {seu_whatsapp}"
            )
        else:
            st.warning("Não existem empresas com esses filtros.")
            texto_msg = (
                f"CNAE: {cnae_selecionado}\n"
                f"Atividade: {atividade}\n"
                f"CEP informado: {cep}\n"
                f"DDD informado: {ddd_preferencia}\n"
                f"Deseja: {preferencia}\n"
                f"WhatsApp Cliente: {seu_whatsapp}\n\n"
                f"Não existem empresas com esses filtros.\n\n"
                f"Podemos refinar a busca por região, cidade ou contatos válidos."
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
