import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Medições dos Contratos", layout="wide")

# Dicionário de meses em português
meses_pt = {
    1: "jan", 2: "fev", 3: "mar", 4: "abr", 5: "mai", 6: "jun",
    7: "jul", 8: "ago", 9: "set", 10: "out", 11: "nov", 12: "dez"
}

@st.cache_data
def carregar_dados():
    df_med = pd.read_excel('1 - Acompanhamento Medições.xlsx', sheet_name='Recebimentos')
    df_contr = pd.read_excel('1 - Acompanhamento Medições.xlsx', sheet_name='Contratos')

    df_med['PERÍODO'] = pd.to_datetime(df_med['PERÍODO'])
    df_med['MÊS'] = df_med['PERÍODO'].dt.month
    df_med['ANO'] = df_med['PERÍODO'].dt.year
    df_med['MÊS/ANO'] = df_med['PERÍODO'].apply(lambda d: f"{meses_pt[d.month]}/{d.year}")
    df_med['ORDENAÇÃO'] = df_med['PERÍODO'].dt.to_period('M').dt.to_timestamp()
    df_med['PREVISTO'] = df_med['PREVISTO'].fillna(0)
    df_med['FATURADO'] = df_med['FATURADO'].fillna(0)
    reordenado = ['CENTRO DE CUSTO', 'OBRA', 'MÊS/ANO', 'PREVISTO', 'FATURADO', 'REGIONAL', 'GESTÃO', 'PERÍODO', 'MÊS', 'ANO', 'ORDENAÇÃO']
    df_med = df_med[reordenado]

    df_contr['VALOR_CONTRATO'] = pd.to_numeric(df_contr['VALOR_CONTRATO'], errors='coerce').fillna(0)

    return df_med, df_contr

medicoes, contratos = carregar_dados()

aba1, aba2 = st.tabs(["📜 Medições dos Contratos", "📊 Análises Avançadas"])

# Função de filtros aplicáveis em ambas as abas
def aplicar_filtros(df, prefixo=""):
    col1, col2, col3 = st.columns(3)
    obras = ['Todas as obras'] + sorted(df['OBRA'].unique().tolist())
    obra = col1.selectbox("🏗️ Obra", obras, key=f"{prefixo}_obra")

    anos = sorted(df['ANO'].unique().tolist())
    ano = col2.selectbox("📅 Ano", ['Todos'] + anos, key=f"{prefixo}_ano")

    meses = sorted(df['MÊS'].unique().tolist())
    nomes_meses = ['Todos'] + [meses_pt[m] for m in meses]
    nome_mes = col3.selectbox("📆 Mês", nomes_meses, key=f"{prefixo}_mes")

    if obra != 'Todas as obras':
        df = df[df['OBRA'] == obra]
    if ano != 'Todos':
        df = df[df['ANO'] == ano]
    if nome_mes != 'Todos':
        num_mes = {v: k for k, v in meses_pt.items()}[nome_mes]
        df = df[df['MÊS'] == num_mes]

    return df, obra

# ===== ABA 1: MEDIÇÕES DOS CONTRATOS =====
with aba1:
    st.title("📜 Medições dos Contratos")
    df_filtrado, obra_selecionada = aplicar_filtros(medicoes, prefixo="medicoes")


    # Cálculos
    valor_previsto = df_filtrado["PREVISTO"].sum()
    valor_faturado = df_filtrado["FATURADO"].sum()
    percentual = (valor_faturado / valor_previsto * 100) if valor_previsto > 0 else 0

    if obra_selecionada == 'Todas as obras':
        valor_contrato = contratos['VALOR_CONTRATO'].sum()
    else:
        valor_contrato = contratos.loc[contratos['OBRA'] == obra_selecionada, 'VALOR_CONTRATO'].sum()

    percentual_contrato = (valor_faturado / valor_contrato * 100) if valor_contrato > 0 else 0
    saldo_contrato = valor_contrato - valor_faturado

    st.subheader("📑 Indicadores do Contrato")
    col1, col2, col3 = st.columns(3)
    col1.metric("🏗️ Valor do Contrato", f"R$ {valor_contrato:,.2f}")
    col2.metric("📊 % do Contrato Faturado", f"{percentual_contrato:.1f}%")
    col3.metric("🧾 Saldo Contratual", f"R$ {saldo_contrato:,.2f}")
       
    st.subheader("📌 Indicadores Gerais")
    col4, col5, col6 = st.columns(3)
    col4.metric("📜 Valor Previsto", f"R$ {valor_previsto:,.2f}")
    col5.metric("💰 Valor Faturado", f"R$ {valor_faturado:,.2f}")
    col6.metric("📈 % Realizado sobre Previsto", f"{percentual:.1f}%")

    # Gráficos
    df_long = pd.melt(
        df_filtrado,
        id_vars=["MÊS/ANO", "ORDENAÇÃO"],
        value_vars=["PREVISTO", "FATURADO"],
        var_name="Tipo",
        value_name="Valor"
    )
    ordem = df_long.sort_values("ORDENAÇÃO")["MÊS/ANO"].unique().tolist()

    st.subheader("📊 Comparativo Mensal: Previsto x Faturado")
    st.plotly_chart(
        px.bar(df_long, x="MÊS/ANO", y="Valor", color="Tipo", barmode="group",
               category_orders={"MÊS/ANO": ordem}, text_auto='.2s')
        .update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)"),
        use_container_width=True
    )

    st.subheader("📈 Evolução Temporal das Medições")
    st.plotly_chart(
        px.line(df_long, x="MÊS/ANO", y="Valor", color="Tipo", markers=True,
                category_orders={"MÊS/ANO": ordem})
        .update_layout(xaxis_title="Mês/Ano", yaxis_title="Valor (R$)"),
        use_container_width=True
    )

    st.download_button(
        "📥 Baixar dados filtrados (.csv)",
        data=df_filtrado.to_csv(index=False).encode('utf-8'),
        file_name='medicoes_filtradas.csv',
        mime='text/csv'
    )

    st.subheader("📋 Detalhamento dos Dados")
    st.dataframe(
        df_filtrado.style.format({'PREVISTO': 'R$ {:,.2f}', 'FATURADO': 'R$ {:,.2f}'})
    )

    # CURVA S - Planejado vs Realizado acumulado
    st.subheader("📈 Curva S - Execução Acumulada do Contrato")

    curva = (
        df_filtrado.groupby('PERÍODO')[['PREVISTO', 'FATURADO']]
        .sum()
        .sort_index()
        .cumsum()
        .reset_index()
    )

    curva['MÊS/ANO'] = curva['PERÍODO'].apply(lambda d: f"{meses_pt[d.month]}/{d.year}")

    fig_curva = px.line(
        curva,
        x='MÊS/ANO',
        y=['PREVISTO', 'FATURADO'],
        markers=True,
        labels={'value': 'Valor acumulado (R$)', 'MÊS/ANO': 'Data', 'variable': 'Tipo'},
        color_discrete_map={'PREVISTO': '#1f77b4', 'FATURADO': '#2ca02c'},
        title=f"Curva S - {obra_selecionada}" if obra_selecionada != "Todas as obras" else "Curva S - Todas as Obras"
    )

    fig_curva.update_layout(
        xaxis_title="Mês/Ano",
        yaxis_title="Valor acumulado (R$)",
        legend_title_text="Tipo de Medição",
        hovermode="x unified"
    )

    st.plotly_chart(fig_curva, use_container_width=True)


# ===== ABA 2: ANÁLISES AVANÇADAS =====
with aba2:
    st.title("📊 Análises Avançadas")

    # Novo filtro apenas por ano e mês
    col1, col2 = st.columns(2)
    anos = sorted(medicoes['ANO'].unique())
    ano = col1.selectbox("📅 Ano", ['Todos'] + anos, key="analises_ano")

    meses = sorted(medicoes['MÊS'].unique())
    nomes_meses = ['Todos'] + [meses_pt[m] for m in meses]
    nome_mes = col2.selectbox("📆 Mês", nomes_meses, key="analises_mes")

    df_analise = medicoes.copy()
    if ano != 'Todos':
        df_analise = df_analise[df_analise['ANO'] == ano]
    if nome_mes != 'Todos':
        num_mes = {v: k for k, v in meses_pt.items()}[nome_mes]
        df_analise = df_analise[df_analise['MÊS'] == num_mes]

    # Ranking de execução por contrato
    st.subheader("🏆 Ranking de Execução por Contrato")
    execucao = df_analise.groupby('OBRA')['FATURADO'].sum().reset_index(name='FATURADO_TOTAL')
    execucao = execucao.merge(contratos, on='OBRA', how='left')
    execucao['% EXECUTADO'] = execucao['FATURADO_TOTAL'] / execucao['VALOR_CONTRATO'] * 100
    execucao = execucao.sort_values('% EXECUTADO', ascending=False)

    st.dataframe(execucao[['OBRA', 'FATURADO_TOTAL', 'VALOR_CONTRATO', '% EXECUTADO']]
                 .style.format({
                     'FATURADO_TOTAL': 'R$ {:,.2f}',
                     'VALOR_CONTRATO': 'R$ {:,.2f}',
                     '% EXECUTADO': '{:.1f}%'
                 }))

    st.plotly_chart(
        px.bar(execucao, x='% EXECUTADO', y='OBRA', orientation='h',
               text='% EXECUTADO', labels={'% EXECUTADO': '% Executado'}, color='OBRA')
        .update_traces(texttemplate='%{x:.1f}%', textposition='outside')
        .update_layout(showlegend=False),
        use_container_width=True
    )

    # Média mensal de faturamento por contrato
    st.subheader("📉 Média Mensal de Faturamento por Contrato")
    df_analise['MES_ANO'] = df_analise['PERÍODO'].dt.to_period('M')
    media = df_analise.groupby(['OBRA', 'MES_ANO'])['FATURADO'].sum().reset_index()
    media = media.groupby('OBRA')['FATURADO'].mean().reset_index(name='MÉDIA_FATURAMENTO')

    st.dataframe(media.style.format({'MÉDIA_FATURAMENTO': 'R$ {:,.2f}'}))

    st.plotly_chart(
        px.bar(media, x='OBRA', y='MÉDIA_FATURAMENTO', text='MÉDIA_FATURAMENTO',
               labels={'MÉDIA_FATURAMENTO': 'Média (R$)'})
        .update_traces(texttemplate='R$ %{y:,.0f}', textposition='outside'),
        use_container_width=True
    )

    # Participação das obras no total faturado (gráfico de barras)
    st.subheader("🏗️ Participação das Obras no Total Faturado")
    participacao = df_analise.groupby('OBRA')['FATURADO'].sum().reset_index(name='TOTAL_FATURADO')
    participacao = participacao.sort_values('TOTAL_FATURADO', ascending=True)

    st.plotly_chart(
        px.bar(participacao, x='TOTAL_FATURADO', y='OBRA', orientation='h',
               text='TOTAL_FATURADO', labels={'TOTAL_FATURADO': 'Total Faturado (R$)'})
        .update_traces(texttemplate='R$ %{x:,.0f}', textposition='outside')
        .update_layout(showlegend=False),
        use_container_width=True
    )