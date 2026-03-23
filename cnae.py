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

def normalizar(texto):
    texto = texto.lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

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

        query = """
            SELECT 
                `Column 0`  AS cnpj_basico,
                `Column 1`  AS cnpj_ordem,
                `Column 2`  AS cnpj_dv,
                `Column 3`  AS identificador_matriz_filial,
                `Column 4`  AS nome_fantasia,
                `Column 5`  AS situacao_cadastral,
                `Column 6`  AS data_situacao_cadastral,
                `Column 7`  AS motivo_situaçao_cadastral,
                `Column 8`  AS nome_ciadde_exterior,
                `Column 9`  AS país,
                `Column 10` AS data_inicio_atividade,
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
                `Column 25` AS ddd_fax,
                `Column 26` AS fax,
                `Column 27` AS email,
                `Column 28` AS situacao_especial,
                `Column 29` AS data_situacao_especial
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

        colunas = [desc[0] for desc in cursor.description]
        df_empresas = pd.DataFrame(lista_empresas, columns=colunas)

        total_filtro = len(df_empresas)

        if total_filtro > 0:
            st.success(f"Foram encontradas {total_filtro} empresas com os filtros aplicados.")

            if preferencia == "Apenas E-mails":
                df_saida = df_empresas[['email']]
            elif preferencia == "Apenas Telefones":
                df_saida = df_empresas[['ddd1', 'telefone1', 'ddd2', 'telefone2']]
            else:
                df_saida = df_empresas[['email', 'ddd1', 'telefone1', 'ddd2', 'telefone2']]

            # ✅ LIMPEZA (CORREÇÃO APLICADA)
            df_saida = df_saida.dropna(how='all')

            if 'email' in df_saida.columns:
                df_saida['email'] = df_saida['email'].astype(str).str.strip().str.lower()
                df_saida = df_saida[df_saida['email'] != '']
                df_saida = df_saida[df_saida['email'] != 'nan']
                df_saida = df_saida.drop_duplicates(subset=['email'])
            else:
                df_saida = df_saida.drop_duplicates()

            filtros_nome = ""
            if cnae_selecionado:
                filtros_nome += f"{cnae_selecionado}_"
            if atividade:
                filtros_nome += f"{atividade}_"
            if cep:
                filtros_nome += f"{cep}_"
            if ddd_preferencia:
                filtros_nome += f"{ddd_preferencia}_"

            data_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            df_saida.to_csv(
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
                f"Resultados encontrados: {len(df_saida)}\n"
                f"WhatsApp Cliente: {seu_whatsapp}\n"
                f"Data/Hora da consulta: {data_hora}"
            )
        else:
            st.warning("Não existem empresas com esses filtros.")
            texto_msg = "Nenhum resultado encontrado."

        cursor.close()
        db.close()

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
