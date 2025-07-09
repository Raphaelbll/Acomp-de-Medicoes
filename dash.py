import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Medições dos Contratos", layout="wide")
st.title("📜 Medições dos Contratos")

# Função para carregar e preparar os dados
@st.cache_data
def carregar_dados():
    df = pd.read_excel('1 - Acompanhamento Medições.xlsx', sheet_name='Recebimentos')
    df['PERÍODO'] = pd.to_datetime(df['PERÍODO'])
    df['MÊS/ANO'] = df['PERÍODO'].dt.strftime('%m/%Y')
    df['ORDENAÇÃO'] = df['PERÍODO'].dt.to_period('M').dt.to_timestamp()
    df['PREVISTO'] = df['PREVISTO'].fillna(0)
    df['FATURADO'] = df['FATURADO'].fillna(0)
    return df

# Carregar os dados
medicoes = carregar_dados()

# Filtro por obra
obras = ['Todas as obras'] + sorted(medicoes['OBRA'].unique().tolist())
obra_selecionada = st.selectbox("Contrato:", obras)

# Filtro por ano
anos = medicoes['PERÍODO'].dt.year.unique()
ano_selecionado = st.selectbox("Ano:", ['Todos'] + sorted(anos.tolist()))

# Aplicar filtros
medicoes_filtradas = medicoes.copy()
if obra_selecionada != 'Todas as obras':
    medicoes_filtradas = medicoes_filtradas[medicoes_filtradas['OBRA'] == obra_selecionada]
if ano_selecionado != 'Todos':
    medicoes_filtradas = medicoes_filtradas[medicoes_filtradas['PERÍODO'].dt.year == ano_selecionado]

# Calcular valores para os cards
valor_previsto = medicoes_filtradas["PREVISTO"].sum()
valor_faturado = medicoes_filtradas["FATURADO"].sum()
percentual = (valor_faturado / valor_previsto * 100) if valor_previsto > 0 else 0

# Exibir métricas
col1, col2, col3 = st.columns(3)
col1.metric("📜 Valor Previsto", f"R$ {valor_previsto:,.2f}")
col2.metric("💰 Valor Faturado", f"R$ {valor_faturado:,.2f}")
col3.metric("📈 Percentual Realizado", f"{percentual:.1f}%")

# Preparar dados longos para gráficos
df_long = pd.melt(
    medicoes_filtradas,
    id_vars=["MÊS/ANO", "ORDENAÇÃO"],
    value_vars=["PREVISTO", "FATURADO"],
    var_name="Tipo",
    value_name="Valor"
)
df_long = df_long.sort_values("ORDENAÇÃO")

# Gráfico de barras agrupadas
grafico_barra = px.bar(
    df_long,
    x="MÊS/ANO",
    y="Valor",
    color="Tipo",
    barmode="group",
    title="📊 Comparativo Mensal: Previsto x Faturado"
)
grafico_barra.update_traces(texttemplate='%{y:.2s}', textposition='outside')
grafico_barra.update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)", uniformtext_minsize=8)

# Gráfico de linha
grafico_linha = px.line(
    df_long,
    x="MÊS/ANO",
    y="Valor",
    color="Tipo",
    markers=True,
    title="📈 Evolução Mensal: Previsto x Faturado"
)

# Exibir gráficos
st.plotly_chart(grafico_barra, use_container_width=True)
st.plotly_chart(grafico_linha, use_container_width=True)

# Botão de download
st.download_button(
    label="📥 Baixar dados filtrados (.csv)",
    data=medicoes_filtradas.to_csv(index=False).encode('utf-8'),
    file_name='medicoes_filtradas.csv',
    mime='text/csv'
)

# Tabela com destaque
st.subheader("📋 Detalhamento dos Dados")
st.dataframe(
    medicoes_filtradas.style.format({'PREVISTO': 'R$ {:,.2f}', 'FATURADO': 'R$ {:,.2f}'})
)
