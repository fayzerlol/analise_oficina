import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="BI Ampolas & Tanques", page_icon="🏭", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .main-header {font-size: 2.2rem !important; font-weight: 900; text-align: center; margin: 2rem 0 1.5rem 0;
        background: linear-gradient(90deg,#667eea,#764ba2 60%,#f093fb 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .metric-container {background: #fff; border-radius: 18px; box-shadow: 0 4px 24px #eee; padding: 1.5rem 0.7rem 1rem;}
    .section-header {font-size: 1.5rem; font-weight: 700; color: #4f46e5; margin: 2.5rem 0 1.2rem 0;}
    .footer {text-align: center; color: #64748b; margin: 2rem 0 1rem 0;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">BI Ampolas & Tanques - Grupo Franzen</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #475569;">Dashboard de processos, laudos, riscos e filtros avançados</p>', unsafe_allow_html=True)

arquivo = st.file_uploader("Selecione o arquivo Excel (.xlsx) com as abas brutas", type=["xlsx"])

def padroniza_chave(s):
    try:
        s = str(s)
        if '.' in s:
            try:
                s_float = float(s)
                if s_float.is_integer():
                    s = str(int(s_float))
            except:
                pass
        s = s.strip().upper()
        if s in ["", "NAN", "NONE"]:
            return ""
        return s
    except:
        return ""

def padroniza(df, mapa):
    for novo, antigo in mapa.items():
        if antigo in df.columns:
            df[novo] = df[antigo].apply(padroniza_chave)
        else:
            df[novo] = ""
    return df

def agrupar_outros(df, coluna, top=7):
    if coluna not in df.columns:
        return df
    top_cats = df[coluna].value_counts().nlargest(top).index
    df[coluna + '_agrup'] = df[coluna].where(df[coluna].isin(top_cats), 'Outros')
    return df

if arquivo:
    xl = pd.ExcelFile(arquivo)
    frames = []
    mapeamento = [
        # Ampolas
        {'aba': 'orc_A', 'tipo_item': 'Ampola', 'etapa': 'Orçamento',
         'mapa': {'nota_fiscal': 'Nota Fiscal', 'numero_serie': 'Número de Série', 'numero_lacre': 'Número do Lacre',
                  'cliente': 'Cliente', 'laudo_tecnico': 'Análise Técnica:',
                  'status_th': 'Necessário Teste Hidrostático?', 'data_th': 'Data do Teste Hidrostático',
                  'data_inicio': 'Início:'}},
        {'aba': 'rec_A', 'tipo_item': 'Ampola', 'etapa': 'Recarga',
         'mapa': {'nota_fiscal': 'Número da Nota Fiscal', 'numero_serie': 'Número de Série', 'numero_lacre': 'Número do Lacre',
                  'cliente': '', 'laudo_tecnico': 'Laudo.', 'status_th': 'Realizado Teste Hidrostático?',
                  'data_th': 'Data Fabricação / Teste Hidrostático', 'data_inicio': 'Início:'}},
        {'aba': 'fin_A', 'tipo_item': 'Ampola', 'etapa': 'Finalização',
         'mapa': {'nota_fiscal': 'Número da Nota Fiscal', 'numero_serie': 'Número de Série', 'numero_lacre': 'Número do Lacre',
                  'cliente': '', 'laudo_tecnico': 'Laudo.', 'status_th': '', 'data_th': '', 'data_inicio': 'Início:'}},
        # Tanques pressurizados
        {'aba': 'orc_T_P', 'tipo_item': 'Tanque Pressurizado', 'etapa': 'Orçamento',
         'mapa': {'nota_fiscal': 'Nº Nota Fiscal', 'numero_serie': 'Número de Série', 'numero_lacre': 'Número do Lacre',
                  'cliente': 'Cliente', 'laudo_tecnico': 'Laudo', 'status_th': 'Necessário Teste Hidrostático?',
                  'data_th': 'Data Fabricação / Teste Hidrostático', 'data_inicio': 'Início:'}},
        {'aba': 'rec_T_P', 'tipo_item': 'Tanque Pressurizado', 'etapa': 'Recarga',
         'mapa': {'nota_fiscal': 'Nº Nota Fiscal', 'numero_serie': 'Nº de Série', 'numero_lacre': 'Número do Lacre',
                  'cliente': '', 'laudo_tecnico': 'Laudo', 'status_th': 'Teste Hidrostático Realizado?',
                  'data_th': 'Data Fabricação / Teste Hidrostático', 'data_inicio': 'Início:'}},
        {'aba': 'fin_T_P', 'tipo_item': 'Tanque Pressurizado', 'etapa': 'Finalização',
         'mapa': {'nota_fiscal': 'Número da Nota Fiscal', 'numero_serie': 'Número de Série', 'numero_lacre': 'Número do Lacre',
                  'cliente': '', 'laudo_tecnico': 'Laudo.', 'status_th': '', 'data_th': '', 'data_inicio': 'Início:'}},
        # Tanques sem pressão
        {'aba': 'orc_T_S', 'tipo_item': 'Tanque Sem Pressão', 'etapa': 'Orçamento',
         'mapa': {'nota_fiscal': 'Nota Fiscal', 'numero_serie': 'Número de Série', 'numero_lacre': 'Número do Lacre',
                  'cliente': 'Cliente', 'laudo_tecnico': 'Análise Técnica:', 'status_th': 'Necessário Teste Hidrostático?',
                  'data_th': 'Data Fabricação / Teste Hidrostático', 'data_inicio': 'Início:'}},
        {'aba': 'rec_T_S', 'tipo_item': 'Tanque Sem Pressão', 'etapa': 'Recarga',
         'mapa': {'nota_fiscal': 'Nº Nota Fiscal', 'numero_serie': 'Nº de Série', 'numero_lacre': 'Nº do Lacre',
                  'cliente': '', 'laudo_tecnico': 'Laudo/Observação', 'status_th': 'Teste Hidrostático Realizado?',
                  'data_th': 'Data Fabricação / Teste Hidrostático', 'data_inicio': 'Início:'}},
    ]

    for meta in mapeamento:
        aba = meta['aba']
        if aba in xl.sheet_names:
            df = xl.parse(aba)
            df = padroniza(df, meta['mapa'])
            df['tipo_item'] = meta['tipo_item']
            df['etapa'] = meta['etapa']
            frames.append(df[['nota_fiscal', 'numero_serie', 'numero_lacre', 'cliente', 'laudo_tecnico', 'status_th', 'data_th', 'data_inicio', 'tipo_item', 'etapa']])
    df = pd.concat(frames, ignore_index=True)

    st.sidebar.markdown(
        "Escolha quais campos formam a chave única para rastrear cada item no funil. "
        "Por exemplo: marque só 'Nota Fiscal' para ver por lote, ou adicione 'Número de Série' para ver item a item."
    )

    opcoes_chave = ["Nota Fiscal", "Número de Série", "Número do Lacre"]
    chave_selecionada = st.sidebar.multiselect(
        "Quais campos compõem a chave única?",
        opcoes_chave,
        default=["Nota Fiscal", "Número de Série"]
    )

    if not chave_selecionada:
        st.warning("Selecione ao menos um campo para compor a chave única.")
        st.stop()

    def monta_chave(row, campos):
        valores = []
        if "Nota Fiscal" in campos:
            valores.append(row['nota_fiscal'])
        if "Número de Série" in campos:
            valores.append(row['numero_serie'])
        if "Número do Lacre" in campos:
            valores.append(row['numero_lacre'])
        if not valores:
            valores.append(row['nota_fiscal'])
        return "|".join([v if v else "" for v in valores])

    df['chave_item'] = df.apply(lambda row: monta_chave(row, chave_selecionada), axis=1)

    # --- Navegação dinâmica: só um painel por vez, sidebar e gráficos sincronizados ---
    painel_titulos = ["Ampolas", "Tanque Pressurizado", "Tanque Sem Pressão"]
    painel_opcoes = ["Ampola", "Tanque Pressurizado", "Tanque Sem Pressão"]
    painel_idx = st.sidebar.radio("Escolha o painel", painel_titulos, index=0)
    tipo_nome = painel_opcoes[painel_titulos.index(painel_idx)]
    df_tipo = df[df['tipo_item'] == tipo_nome].copy()

    # --- Filtros dinâmicos: só para o painel ativo ---
    st.sidebar.markdown(f"#### Filtros para {painel_idx}")
    clientes = sorted([c for c in df_tipo[df_tipo['etapa'] == 'Orçamento']['cliente'].unique() if c and c.lower() != 'nan']) if 'cliente' in df_tipo.columns else []
    cliente = st.sidebar.selectbox(f"Cliente ({painel_idx}):", ["Todos"] + clientes)

    # NOTA FISCAL dependente do CLIENTE!
    if cliente != "Todos":
        notas = sorted([n for n in df_tipo[(df_tipo['etapa'] == 'Orçamento') & (df_tipo['cliente'] == cliente)]['nota_fiscal'].unique() if n and n.lower() != 'nan'])
    else:
        notas = sorted([n for n in df_tipo['nota_fiscal'].unique() if n and n.lower() != 'nan'])
    nota = st.sidebar.selectbox(f"Nota Fiscal ({painel_idx}):", ["Todas"] + notas)

    etapas = sorted(df_tipo['etapa'].unique()) if 'etapa' in df_tipo.columns else []
    etapa = st.sidebar.multiselect(f"Etapa ({painel_idx}):", etapas, default=etapas)

    # === Filtro de período (intervalo de datas de início) ===
    data_col = 'data_inicio'

    # === 1. Identifica as chaves do orçamento do cliente selecionado (NO DF COMPLETO) ===
    if cliente != "Todos":
        chaves_cliente = set(df[(df['tipo_item'] == tipo_nome) & (df['etapa'] == 'Orçamento') & (df['cliente'] == cliente)]['chave_item'])
    else:
        chaves_cliente = set(df[(df['tipo_item'] == tipo_nome) & (df['etapa'] == 'Orçamento')]['chave_item'])

    # === 2. Filtra o dataframe do painel:
    # (a) Orçamento: só linhas que são do cliente (se filtrando cliente), nota, etapa, data.
    # (b) Recarga/finalização: só linhas cuja chave está nas chaves_cliente (não pelo campo cliente!)

    # ORÇAMENTO (só do cliente), OUTRAS ETAPAS filtradas só pelas chaves do orçamento
    if cliente != "Todos":
        df_tipo_orc = df_tipo[(df_tipo['etapa'] == 'Orçamento') & (df_tipo['cliente'] == cliente)].copy()
    else:
        df_tipo_orc = df_tipo[df_tipo['etapa'] == 'Orçamento'].copy()
    df_tipo_outras = df_tipo[df_tipo['etapa'] != 'Orçamento'].copy()
    df_tipo_outras = df_tipo_outras[df_tipo_outras['chave_item'].isin(chaves_cliente)]

    # Junta tudo para aplicar filtros de nota, etapa e datas (painel inteiro, mas as outras etapas só mostram o que tem no orçamento daquele cliente)
    df_tipo_filt = pd.concat([df_tipo_orc, df_tipo_outras])

    # Agora filtra por nota, etapa, datas:
    if nota != "Todas" and 'nota_fiscal' in df_tipo_filt.columns:
        df_tipo_filt = df_tipo_filt[df_tipo_filt['nota_fiscal'] == nota]
    if etapa and 'etapa' in df_tipo_filt.columns:
        df_tipo_filt = df_tipo_filt[df_tipo_filt['etapa'].isin(etapa)]

    # Filtro por período (Data de Início)
    df_tipo_filt[data_col] = pd.to_datetime(df_tipo_filt[data_col], errors="coerce")
    datas_validas = df_tipo_filt[data_col].dropna()
    if not datas_validas.empty:
        min_date = datas_validas.min().date()
        max_date = datas_validas.max().date()
        data_ini, data_fim = st.sidebar.date_input(
            f"Período ({painel_idx}):",
            (min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        df_tipo_filt = df_tipo_filt[
            (df_tipo_filt[data_col].dt.date >= data_ini) &
            (df_tipo_filt[data_col].dt.date <= data_fim)
        ]
    else:
        st.sidebar.info("Sem datas de início válidas para filtrar o período.")

    # KPIs e Funil: sempre com as chaves do orçamento do cliente
    etapas_kpi = ['Orçamento', 'Recarga', 'Finalização']
    kpi_counts = {}
    for etapa_ in etapas_kpi:
        chaves_etapa = set(df_tipo_filt[df_tipo_filt['etapa'] == etapa_]['chave_item'])
        chaves_cruzadas = chaves_etapa & chaves_cliente
        kpi_counts[etapa_] = len(chaves_cruzadas)

    orcados = kpi_counts['Orçamento']
    recarregados = kpi_counts['Recarga']
    finalizados = kpi_counts['Finalização']
    total = orcados
    pendencias = 0

    st.markdown(f'<h2 class="section-header">{painel_idx}</h2>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(f"""<div class="metric-container"><div class="metric-title">Total</div><div class="metric-value">{total}</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="metric-container"><div class="metric-title">Orçados</div><div class="metric-value">{orcados}</div></div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="metric-container"><div class="metric-title">Recarregados</div><div class="metric-value">{recarregados}</div></div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="metric-container"><div class="metric-title">Finalizados</div><div class="metric-value">{finalizados}</div></div>""", unsafe_allow_html=True)
    k5.markdown(f"""<div class="metric-container"><div class="metric-title">Pendências</div><div class="metric-value">{pendencias}</div></div>""", unsafe_allow_html=True)

    # --- FUNIL/FLUXO CRUZADO (por chave única do cliente) ---
    st.markdown("### Fluxo de Itens (Funil Real por Chave Única)")
    etapas_funil = [e for e in etapas_kpi if not etapa or e in etapa]
    funil_counts = {}
    for etapa_ in etapas_funil:
        chaves_etapa = set(df_tipo_filt[df_tipo_filt['etapa'] == etapa_]['chave_item'])
        chaves_cruzadas = chaves_etapa & chaves_cliente
        funil_counts[etapa_] = len(chaves_cruzadas)
    funil_plot = pd.DataFrame({'Etapa': etapas_funil, 'Qtd': [funil_counts[e] for e in etapas_funil]})

    fig_funil = px.bar(funil_plot, x='Etapa', y='Qtd', text_auto=True, color='Etapa', title='Funil do Processo - Itens Únicos')
    st.plotly_chart(fig_funil, use_container_width=True)

    # --- SANKEY FLOW (FLUXO ENTRE ETAPAS) ---
    st.markdown("### Fluxo Sankey entre Etapas")

    # Pega as etapas possíveis (Orçamento, Recarga, Finalização)
    etapas_sankey = ['Orçamento', 'Recarga', 'Finalização']
    df_sankey = df_tipo_filt[df_tipo_filt['etapa'].isin(etapas_sankey)].copy()

    # Para cada chave única, qual caminho ela percorreu?
    paths = df_sankey.groupby('chave_item')['etapa'].apply(list)

    sankey_data = []
    for etapas in paths:
        etapas = [e for e in etapas_sankey if e in etapas]  # Garante ordem
        if len(etapas) >= 2:
            for i in range(len(etapas)-1):
                sankey_data.append((etapas[i], etapas[i+1]))

    if sankey_data:
        sankey_df = pd.DataFrame(sankey_data, columns=['source', 'target'])
        sankey_counts = sankey_df.value_counts().reset_index(name='count')

        import plotly.graph_objects as go
        labels = etapas_sankey
        label_idx = {l: i for i, l in enumerate(labels)}
        sources = [label_idx[row['source']] for _, row in sankey_counts.iterrows()]
        targets = [label_idx[row['target']] for _, row in sankey_counts.iterrows()]
        values = sankey_counts['count'].tolist()

        fig_sankey = go.Figure(go.Sankey(
            node=dict(label=labels, pad=30, thickness=20, color="blue"),
            link=dict(source=sources, target=targets, value=values)
        ))
        fig_sankey.update_layout(title_text="Fluxo de Itens entre Etapas (Sankey)", font_size=14)
        st.plotly_chart(fig_sankey, use_container_width=True)
    else:
        st.info("Não há fluxo suficiente entre etapas para gerar o Sankey.")

    # --- TOP CLIENTES ---
    st.markdown("### Top 10 Clientes")
    if 'cliente' in df_tipo_filt.columns and not df_tipo_filt['cliente'].isna().all():
        top_cli = df_tipo_filt['cliente'].value_counts().reset_index()
        top_cli.columns = ['Cliente', 'Qtd']
        if not top_cli.empty:
            st.download_button(
                label="Baixar top 10 clientes (Excel/CSV)",
                data=top_cli.head(10).to_csv(index=False),
                file_name=f"{painel_idx.lower()}_top_clientes.csv",
                mime="text/csv"
            )
            fig_cli = px.bar(top_cli.head(10), x="Cliente", y="Qtd", title="Top 10 Clientes", text_auto=True)
            st.plotly_chart(fig_cli, use_container_width=True)
        else:
            st.info("Sem dados de cliente para exibir.")
    else:
        st.info("Coluna de cliente não encontrada.")

    # --- LAUDOS (pizza agrupada) ---
    st.markdown("### Distribuição dos Laudos Técnicos")
    if 'laudo_tecnico' in df_tipo_filt.columns and not df_tipo_filt['laudo_tecnico'].isna().all():
        df_tipo_filt = agrupar_outros(df_tipo_filt, 'laudo_tecnico', top=7)
        laudo_agrupado = df_tipo_filt['laudo_tecnico_agrup'].value_counts().reset_index()
        laudo_agrupado.columns = ['Laudo', 'Qtd']
        if not laudo_agrupado.empty:
            st.download_button(
                label="Baixar laudos (Excel/CSV)",
                data=laudo_agrupado.to_csv(index=False),
                file_name=f"{painel_idx.lower()}_laudos.csv",
                mime="text/csv"
            )
            fig_laudo = px.pie(laudo_agrupado, names="Laudo", values="Qtd", title="Laudos Técnicos (Top 7 + Outros)")
            st.plotly_chart(fig_laudo, use_container_width=True)
        else:
            st.info("Sem dados de laudo técnico para exibir.")
    else:
        st.info("Coluna de laudo técnico não encontrada.")

    # --- TIMELINE (datas de início) ---
    st.markdown("### Evolução dos Eventos no Tempo (Data de Início)")
    if 'data_inicio' in df_tipo_filt.columns and not df_tipo_filt['data_inicio'].isna().all():
        # df_tipo_filt['data_inicio'] já está convertido no filtro acima!
        if df_tipo_filt['data_inicio'].notna().any():
            st.download_button(
                label="Baixar datas de início (Excel/CSV)",
                data=df_tipo_filt[['data_inicio', 'etapa']].dropna().to_csv(index=False),
                file_name=f"{painel_idx.lower()}_datas_inicio.csv",
                mime="text/csv"
            )
            fig_time = px.histogram(df_tipo_filt, x='data_inicio', color="etapa", title="Evolução dos Eventos (Data de Início)")
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Sem dados de datas de início para exibir.")
    else:
        st.info("Coluna de data de início não encontrada.")

    # --- CRÍTICOS (mapa de risco) ---
    st.markdown("### Itens Críticos / Risco")
    if 'status_th' in df_tipo_filt.columns:
        criticos = df_tipo_filt[df_tipo_filt['status_th'].str.lower().isin(['crítico','vencido'])]
        if not criticos.empty:
            st.download_button(
                label="Baixar itens críticos (Excel/CSV)",
                data=criticos.to_csv(index=False),
                file_name=f"{painel_idx.lower()}_itens_criticos.csv",
                mime="text/csv"
            )
            st.dataframe(criticos, use_container_width=True)
        else:
            st.info("Nenhum item crítico encontrado para o filtro.")
    else:
        st.info("Coluna status_th não encontrada.")

    # --- DUPLICIDADES ---
    st.markdown("### Duplicidades (mesma chave e etapa)")
    if 'chave_item' in df_tipo_filt.columns:
        duplicados = df_tipo_filt[df_tipo_filt.duplicated(['chave_item', 'etapa'], keep=False)].sort_values(['chave_item', 'etapa'])
        if not duplicados.empty:
            st.download_button(
                label="Baixar duplicados (Excel/CSV)",
                data=duplicados.to_csv(index=False),
                file_name=f"{painel_idx.lower()}_duplicados.csv",
                mime="text/csv"
            )
            st.dataframe(duplicados, use_container_width=True)
        else:
            st.info("Nenhuma duplicidade detectada para o filtro.")
    else:
        st.info("Coluna chave_item não encontrada.")

else:
    st.info("Faça upload do Excel para explorar o BI completo!")

st.markdown('<div class="footer">BI Ampolas & Tanques • Profissional • Powered by OpenAI</div>', unsafe_allow_html=True)
