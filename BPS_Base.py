import streamlit as st
import pandas as pd
import zipfile

st.set_page_config(
    page_title="Dashboard BPS Mundimed",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def carregar_dados_zip(zip_path):
    with zipfile.ZipFile(zip_path, "r") as z:
        lista_arquivos = [f for f in z.namelist() if f.endswith('.xlsx')]
        if not lista_arquivos:
            st.error("Nenhum arquivo .xlsx encontrado dentro do .zip.")
            return pd.DataFrame(), None
        with z.open(lista_arquivos[0]) as f:
            df = pd.read_excel(f)
            df.columns = df.columns.str.strip()
            return df, lista_arquivos[0]

CAMINHO_ZIP = "Banco de Preço em Saúde - BPS Unificado BI Mundimed.zip"

with st.spinner("🔄 Carregando sistema e banco de dados, por favor aguarde..."):

    df_bps, nome_arquivo = carregar_dados_zip(CAMINHO_ZIP)

    if df_bps.empty:
        st.error("Base de dados vazia ou não foi possível ler o arquivo ZIP.")
        st.stop()

    st.success("Sistema carregado com sucesso!")

    col_municipio = "Município Instituição"
    col_uf = "UF"
    col_produto = "Descrição CATMAT"
    col_fornecedor = "Fornecedor"
    col_fabricante = "Fabricante"
    col_ano = "Ano"
    col_preco_total = "Preço Total"
    col_preco_unitario = "Preço Unitário"
    col_qtd = "Qtd Itens Comprados"

    for col in [col_preco_total, col_preco_unitario, col_qtd]:
        df_bps[col] = pd.to_numeric(df_bps[col], errors="coerce")

    df_bps[col_ano] = df_bps[col_ano].astype(str).str.replace(".0", "", regex=False).fillna("Não informado")

    st.title("🩺 Dashboard BPS Mundimed - Com Prévia de Produtos")
    st.info(f"Arquivo carregado: **{nome_arquivo}**")

    resetar = st.button("🔄 Resetar Filtros")

    if resetar:
        st.session_state.produto_busca = ""
        st.session_state.estado = "Todos"
        st.session_state.municipio = "Todos"
        st.session_state.fornecedor = "Todos"
        st.session_state.ano = "Todos"

    estados = ["Todos"] + sorted(df_bps[col_uf].dropna().unique())
    estado = st.selectbox("Estado:", estados, key="estado")
    municipios = ["Todos"] + sorted(df_bps[df_bps[col_uf] == estado][col_municipio].dropna().unique()) if estado != "Todos" else ["Todos"] + sorted(df_bps[col_municipio].dropna().unique())
    municipio = st.selectbox("Município:", municipios, key="municipio")
    fornecedores = ["Todos"] + sorted(df_bps[col_fornecedor].dropna().unique())
    fornecedor = st.selectbox("Fornecedor:", fornecedores, key="fornecedor")
    anos = ["Todos"] + sorted(df_bps[col_ano].dropna().unique())
    ano = st.selectbox("Ano:", anos, key="ano")

    produto_busca = st.text_input("🔎 Buscar Produto (busca parcial):", st.session_state.get("produto_busca", ""))
    st.session_state["produto_busca"] = produto_busca

    if produto_busca.strip():
        preview_produtos = (
            df_bps[df_bps[col_produto].str.contains(produto_busca, case=False, na=False)][col_produto]
            .dropna().unique()[:10]
        )
        if len(preview_produtos):
            st.markdown("##### 📝 Prévia dos produtos encontrados:")
            for item in preview_produtos:
                st.markdown(f"- {item}")
        else:
            st.warning("Nenhum produto encontrado com esse termo!")

    df_filtrado = df_bps.copy()
    if estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_uf] == estado]
    if municipio != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_municipio] == municipio]
    if fornecedor != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_fornecedor] == fornecedor]
    if ano != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_ano] == ano]
    if produto_busca.strip():
        df_filtrado = df_filtrado[df_filtrado[col_produto].str.contains(produto_busca.strip(), case=False, na=False)]

    st.markdown("## 📊 KPIs Detalhados")

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros.")
    else:
        col1, col2, col3 = st.columns(3)

        preco_total = df_filtrado[col_preco_total].sum()
        qtd_total = df_filtrado[col_qtd].sum()
        preco_medio = df_filtrado[col_preco_unitario].mean()

        col1.metric("💰 Valor Total", f"R$ {preco_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("📦 Quantidade Total", f"{qtd_total:,.0f}".replace(",", "."))
        col3.metric("💡 Preço Médio", f"R$ {preco_medio:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        menor = df_filtrado.loc[df_filtrado[col_preco_unitario].idxmin()]
        st.markdown(f"""
        ### 🏆 Melhor Compra
        - Produto: **{menor[col_produto]}**
        - Fornecedor: **{menor[col_fornecedor]}**
        - Fabricante: **{menor[col_fabricante]}**
        - Ano: **{menor[col_ano]}**
        - Preço Unitário: **R$ {menor[col_preco_unitario]:,.2f}**
        """, unsafe_allow_html=True)

        st.markdown("## 📄 Registros Detalhados")
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

        csv_bytes = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Baixar Dados Filtrados (CSV)",
            data=csv_bytes,
            file_name="BPS_filtrado.csv",
            mime="text/csv"
        )

    st.markdown("<div style='text-align:right; color: #888; font-size: 11px;'>Desenvolvido para Mundimed | Pharmajal 2025</div>", unsafe_allow_html=True)
