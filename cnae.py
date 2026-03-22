import streamlit as st
import pandas as pd
import urllib
import mysql.connector
import unicodedata
import datetime

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
cep = st.text_input("Digite CEP desejado (prefixo, ex: 122):")
cep = "".join(filter(str.isdigit, cep))
ddd_preferencia = st.text_input("DDD da região (ex: 12):")
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

        # --- QUERY DINÂMICA COM TODAS AS 30 COLUNAS ---
        query = """
            SELECT 
                `Column 0`  AS cnpj,
                `Column 1`  AS matriz_filial,
                `Column 2`  AS situacao,
                `Column 3`  AS motivo_situacao,
                `Column 4`  AS nome_fantasia,
                `Column 5`  AS razao_social,
                `Column 6`  AS data_abertura,
                `Column 7`  AS porte,
                `Column 8`  AS opcao_simples,
                `Column 9`  AS data_opcao_simples,
                `Column 10` AS data_exclusao_simples,
                `Column 11` AS cnae_principal,
                `Column 12` AS cnae_secundario,
                `Column 13` AS tipo_logradouro,
                `Column 14` AS logradouro,
                `Column 15` AS numero,
                `Column 16` AS complemento,
                `Column 17` AS bairro,
                `Column 18` AS cep,
                `Column 19` AS uf,
                `Column 20` AS municipio,
                `Column 21` AS ddd1,
                `Column 22` AS telefone1,
                `Column 23` AS ddd2,
                `Column 24` AS telefone2,
                `Column 25` AS email,
                `Column 26` AS situacao_especial,
                `Column 27` AS data_situacao_especial,
                `Column 28` AS capital_social,
                `Column 29` AS responsavel
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
            query += " AND (TRIM(`Column 21`) LIKE %s OR TRIM(`Column 23`) LIKE %s)"
            params.extend(["%" + ddd_preferencia + "%", "%" + ddd_preferencia + "%"])

        cursor.execute(query, tuple(params))
        lista_empresas = cursor.fetchall()

        colunas = [
            "cnpj","matriz_filial","situacao","motivo_situacao","nome_fantasia","razao_social",
            "data_abertura","porte","opcao_simples","data_opcao_simples","data_exclusao_simples",
            "cnae_principal","cnae_secundario","tipo_logradouro","logradouro","numero","complemento",
            "bairro","cep","uf","municipio","ddd1","telefone1","ddd2","telefone2","email",
            "situacao_especial","data_situacao_especial","capital_social","responsavel"
        ]

        df_empresas = pd.DataFrame(lista_empresas, columns=colunas)

        total_filtro = len(df_empresas)

        if total_filtro > 0:
            st.success(f"Foram encontradas {total_filtro} empresas com os filtros aplicados.")

            filtros_nome = ""
            if cnae_selecionado:
                filtros_nome += f"{cnae_selecionado}_"
            if atividade:
                filtros_nome += f"{atividade}_"
            if cep:
                filtros_nome += f"{cep}_"
            if ddd_preferencia:
                filtros_nome += f"{ddd_preferencia}_"

            # 👉 Adiciona data e hora no nome do arquivo
            data_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            df_empresas.to_csv(
                f"consulta_{filtros_nome}{preferencia}_{seu_whatsapp}_{data_hora}.csv",
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
                f"WhatsApp Cliente: {seu_whatsapp}\n"
                f"Data/Hora da consulta: {data_hora}"
            )
        else:
            st.warning("Não existem empresas com esses filtros.")
            texto_msg = (
                f"CNAE: {cnae_selecionado}\n"
                f"Atividade: {atividade}\n"
                f"CEP informado: {cep}\n"
                f"DDD informado: {ddd_preferencia}\n"
                f"Deseja: {preferencia}\n"
                f"WhatsApp Cliente: {seu_whatsapp}\n"
                f"Data/Hora da consulta: {datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}\n\n"
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
