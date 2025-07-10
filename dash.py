import pandas as pd
import streamlit as st
import plotly.express as px

# Locale para meses em português (Linux/Mac)
locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil.1252')

st.set_page_config(page_title="Medições dos Contratos", layout="wide")
st.title("📜 Medições dos Contratos")

# Função para carregar dados com cache
@st.cache_data
def carregar_dados():
    df_medicoes = pd.read_excel('1 - Acompanhamento Medições.xlsx', sheet_name='Recebimentos')
    df_medicoes['PERÍODO'] = pd.to_datetime(df_medicoes['PERÍODO'])
    df_medicoes['MÊS/ANO'] = df_medicoes['PERÍODO'].dt.strftime('%b/%Y').str.lower()
    df_medicoes['ORDENAÇÃO'] = df_medicoes['PERÍODO'].dt.to_period('M').dt.to_timestamp()
    df_medicoes['PREVISTO'] = df_medicoes['PREVISTO'].fillna(0)
    df_medicoes['FATURADO'] = df_medicoes['FATURADO'].fillna(0)

    df_contratos = pd.read_excel('1 - Acompanhamento Medições.xlsx', sheet_name='Contratos')
    df_contratos['VALOR_CONTRATO'] = pd.to_numeric(df_contratos['VALOR_CONTRATO'], errors='coerce').fillna(0)

    return df_medicoes, df_contratos

# Carregando dados
medicoes, contratos = carregar_dados()

# Filtros
with st.sidebar:
    st.header("🔎 Filtros")
    obras = ['Todas as obras'] + sorted(medicoes['OBRA'].unique().tolist())
    obra_selecionada = st.selectbox("🏗️ Selecione a Obra:", obras)

    anos = medicoes['PERÍODO'].dt.year.unique()
    ano_selecionado = st.selectbox("📆 Filtrar por Ano:", ['Todos'] + sorted(anos.tolist()))

# Aplicar filtros
medicoes_filtradas = medicoes.copy()
if obra_selecionada != 'Todas as obras':
    medicoes_filtradas = medicoes_filtradas[medicoes_filtradas['OBRA'] == obra_selecionada]

if ano_selecionado != 'Todos':
    medicoes_filtradas = medicoes_filtradas[medicoes_filtradas['PERÍODO'].dt.year == ano_selecionado]

# Cálculo dos valores
valor_previsto = medicoes_filtradas["PREVISTO"].sum()
valor_faturado = medicoes_filtradas["FATURADO"].sum()
percentual = (valor_faturado / valor_previsto * 100) if valor_previsto > 0 else 0


if obra_selecionada == 'Todas as obras':
    valor_contrato = contratos['VALOR_CONTRATO'].sum()
else:
    valor_contrato = contratos.loc[contratos['OBRA'] == obra_selecionada, 'VALOR_CONTRATO'].sum()

percentual_contrato = (valor_faturado / valor_contrato * 100) if valor_contrato > 0 else 0
saldo_contrato = valor_contrato - valor_faturado

# Linha 1 - Indicadores gerais
st.subheader("📌 Indicadores Gerais")
col1, col2, col3 = st.columns(3)
col1.metric("📜 Valor Previsto", f"R$ {valor_previsto:,.2f}")
col2.metric("💰 Valor Faturado", f"R$ {valor_faturado:,.2f}")
col3.metric("📈 % Realizado sobre Previsto", f"{percentual:.1f}%")

# Linha 2 - Contrato
st.subheader("📑 Indicadores do Contrato")
col4, col5, col6 = st.columns(3)
col4.metric("🏗️ Valor do Contrato", f"R$ {valor_contrato:,.2f}")
col5.metric("📊 % do Contrato Faturado", f"{percentual_contrato:.1f}%")
col6.metric("🧾 Saldo Contratual", f"R$ {saldo_contrato:,.2f}")

# Preparar dados para gráficos
df_long = pd.melt(
    medicoes_filtradas,
    id_vars=["MÊS/ANO", "ORDENAÇÃO"],
    value_vars=["PREVISTO", "FATURADO"],
    var_name="Tipo",
    value_name="Valor"
)
df_long = df_long.sort_values("ORDENAÇÃO")

# Gráfico de barras
st.subheader("📊 Comparativo Mensal: Previsto x Faturado")
grafico_barra = px.bar(
    df_long,
    x="MÊS/ANO",
    y="Valor",
    color="Tipo",
    barmode="group",
    category_orders={"MÊS/ANO": sorted(df_long["MÊS/ANO"].unique(), key=lambda x: pd.to_datetime(x, format='%b/%Y'))},
    text_auto='.2s'
)
grafico_barra.update_layout(
    xaxis_title="Mês/Ano",
    yaxis_title="Valor (R$)",
    legend_title="Tipo",
    uniformtext_minsize=8,
    uniformtext_mode='hide'
)
st.plotly_chart(grafico_barra, use_container_width=True)

# Gráfico de linha
st.subheader("📈 Evolução Temporal das Medições")
grafico_linha = px.line(
    df_long,
    x="MÊS/ANO",
    y="Valor",
    color="Tipo",
    markers=True,
    category_orders={"MÊS/ANO": sorted(df_long["MÊS/ANO"].unique(), key=lambda x: pd.to_datetime(x, format='%b/%Y'))}
)
grafico_linha.update_layout(
    xaxis_title="Mês/Ano",
    yaxis_title="Valor (R$)",
    legend_title="Tipo"
)
st.plotly_chart(grafico_linha, use_container_width=True)

# Botão de download
st.subheader("📥 Exportar Dados")
st.download_button(
    label="Baixar dados filtrados (.csv)",
    data=medicoes_filtradas.to_csv(index=False).encode('utf-8'),
    file_name='medicoes_filtradas.csv',
    mime='text/csv'
)

# Tabela final
st.subheader("📋 Detalhamento dos Dados")
st.dataframe(
    medicoes_filtradas.style.format({'PREVISTO': 'R$ {:,.2f}', 'FATURADO': 'R$ {:,.2f}'})
)
