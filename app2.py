import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
import io
import base64

st.set_page_config(page_title="BI Ampolas & Tanques", page_icon="🏭", layout="wide", initial_sidebar_state="expanded")

# CSS para estilos e logo
st.markdown("""
    <style>
    .main-header {font-size: 2.2rem !important; font-weight: 900; text-align: center; margin: 1.2rem 0 0.7rem 0;
        background: linear-gradient(90deg,#ffd600 0%,#ffe066 50%,#fff5cc 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .metric-container {background: #fffbe7; border-radius: 18px; box-shadow: 0 3px 24px #f7e09860; padding: 1.4rem 0.6rem 1rem;}
    .section-header {font-size: 1.3rem; font-weight: 700; color: #f4a100; margin: 2.3rem 0 1.2rem 0; letter-spacing:1px;}
    .footer {text-align: center; color: #9e8b36; margin: 2rem 0 1rem 0;}
    .logo-header {display: flex; justify-content: center; align-items: center; margin-top:1.5rem; margin-bottom:0.3rem;}
    .stDownloadButton button {background: #f4a100 !important; color: white !important; border-radius: 10px;}
    .stDownloadButton button:hover {background: #ffd600 !important; color: #454545 !important;}
    .st-emotion-cache-1wivap2 {background: #fffbe7;}
    .css-1v0mbdj, .st-emotion-cache-10trblm {color:#555 !important;}
    </style>
""", unsafe_allow_html=True)

# LOGO CENTRALIZADA
def show_logo(file_path):
    with open(file_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f'<div class="logo-header"><img src="data:image/png;base64,{encoded}" height="85"></div>',
            unsafe_allow_html=True
        )

show_logo("logo.png")

st.markdown('<h1 class="main-header">BI Ampolas & Tanques - Grupo Franzen</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #F4A100;">Dashboard visual de processos, laudos, riscos, TH e exportação avançada</p>', unsafe_allow_html=True)

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

def to_excel(df):
    out = io.BytesIO()
    df.to_excel(out, index=False, engine='openpyxl')
    return out.getvalue()

if arquivo:
    xl = pd.ExcelFile(arquivo)
    frames = []
    mapeamento = [
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
        {'aba': 'orc_T_S', 'tipo_item': 'Tanque Sem Pressão', 'etapa': 'Orçamento',
         'mapa': {'nota_fiscal': 'Nota Fiscal', 'numero_serie': 'Número de Série', 'numero_lacre': 'Número do Lacre',
                  'cliente': 'Cliente', 'laudo_tecnico': 'Análise Técnica:', 'status_th': 'Necessário Teste Hidrostático?',
                  'data_th': 'Data Fabricação / Teste Hidrostático', 'data_inicio': 'Início:'}},
        {'aba': 'rec_T_S', 'tipo_item': 'Tanque Sem Pressão', 'etapa': 'Recarga',
         'mapa': {'nota_fiscal': 'Nº Nota Fiscal', 'numero_serie': 'Nº de Série', 'numero_lacre': 'Nº do Lacre',
                  'cliente': '', 'laudo_tecnico': 'Laudo/Observação', 'status_th': 'Teste Hidrostático Realizado?',
                  'data_th': 'Data Fabricação / Teste Hidrostático', 'data_inicio': 'Início:'}},
    ]

    esperadas = [m['aba'] for m in mapeamento]
    for meta in mapeamento:
        aba = meta['aba']
        if aba in xl.sheet_names:
            df = xl.parse(aba)
            df = padroniza(df, meta['mapa'])
            df['tipo_item'] = meta['tipo_item']
            df['etapa'] = meta['etapa']
            frames.append(df[['nota_fiscal', 'numero_serie', 'numero_lacre', 'cliente', 'laudo_tecnico', 'status_th', 'data_th', 'data_inicio', 'tipo_item', 'etapa']])

    if frames:
        df = pd.concat(frames, ignore_index=True)
    else:
        st.error(
            "Nenhuma das abas esperadas foi encontrada: "
            + ", ".join(esperadas)
        )
        st.stop()

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

    painel_titulos = ["Ampolas", "Tanque Pressurizado", "Tanque Sem Pressão"]
    painel_opcoes = ["Ampola", "Tanque Pressurizado", "Tanque Sem Pressão"]
    painel_idx = st.sidebar.radio("Escolha o painel", painel_titulos, index=0)
    tipo_nome = painel_opcoes[painel_titulos.index(painel_idx)]
    df_tipo = df[df['tipo_item'] == tipo_nome].copy()

    st.sidebar.markdown(f"#### Filtros para {painel_idx}")
    clientes = sorted([c for c in df_tipo[df_tipo['etapa'] == 'Orçamento']['cliente'].unique() if c and c.lower() != 'nan']) if 'cliente' in df_tipo.columns else []
    cliente = st.sidebar.selectbox(f"Cliente ({painel_idx}):", ["Todos"] + clientes)

    if cliente != "Todos":
        notas = sorted([n for n in df_tipo[(df_tipo['etapa'] == 'Orçamento') & (df_tipo['cliente'] == cliente)]['nota_fiscal'].unique() if n and n.lower() != 'nan'])
    else:
        notas = sorted([n for n in df_tipo['nota_fiscal'].unique() if n and n.lower() != 'nan'])
    nota = st.sidebar.selectbox(f"Nota Fiscal ({painel_idx}):", ["Todas"] + notas)

    etapas = sorted(df_tipo['etapa'].unique()) if 'etapa' in df_tipo.columns else []
    etapa = st.sidebar.multiselect(f"Etapa ({painel_idx}):", etapas, default=etapas)

    st.sidebar.markdown("#### Busca rápida (texto livre)")
    busca_txt = st.sidebar.text_input(
        "Filtrar por cliente, nota, laudo, análise técnica, etc.",
        value="", placeholder="Digite parte do texto..."
    )

    data_col = 'data_inicio'

    if cliente != "Todos":
        chaves_cliente = set(df[(df['tipo_item'] == tipo_nome) & (df['etapa'] == 'Orçamento') & (df['cliente'] == cliente)]['chave_item'])
    else:
        chaves_cliente = set(df[(df['tipo_item'] == tipo_nome) & (df['etapa'] == 'Orçamento')]['chave_item'])

    if cliente != "Todos":
        df_tipo_orc = df_tipo[(df_tipo['etapa'] == 'Orçamento') & (df_tipo['cliente'] == cliente)].copy()
    else:
        df_tipo_orc = df_tipo[df_tipo['etapa'] == 'Orçamento'].copy()
    df_tipo_outras = df_tipo[df_tipo['etapa'] != 'Orçamento'].copy()
    df_tipo_outras = df_tipo_outras[df_tipo_outras['chave_item'].isin(chaves_cliente)]
    df_tipo_filt = pd.concat([df_tipo_orc, df_tipo_outras])

    if nota != "Todas" and 'nota_fiscal' in df_tipo_filt.columns:
        df_tipo_filt = df_tipo_filt[df_tipo_filt['nota_fiscal'] == nota]
    if etapa and 'etapa' in df_tipo_filt.columns:
        df_tipo_filt = df_tipo_filt[df_tipo_filt['etapa'].isin(etapa)]

    if busca_txt.strip():
        busca_txt_low = busca_txt.lower()
        campos_busca = ['cliente', 'nota_fiscal', 'laudo_tecnico', 'status_th', 'data_th', 'data_inicio']
        mask = np.zeros(len(df_tipo_filt), dtype=bool)
        for campo in campos_busca:
            if campo in df_tipo_filt.columns:
                mask |= df_tipo_filt[campo].astype(str).str.lower().str.contains(busca_txt_low)
        df_tipo_filt = df_tipo_filt[mask]

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

    aba_th = "th_A"
    if aba_th in xl.sheet_names:
        df_th = xl.parse(aba_th)
        df_th['nota_fiscal'] = df_th['Número da Nota Fiscal'].apply(padroniza_chave)
        df_th['numero_serie'] = df_th['Número de Série'].apply(padroniza_chave)
        df_th['chave_item'] = df_th.apply(lambda row: monta_chave(row, chave_selecionada), axis=1)
        df_th['data_inicio'] = pd.to_datetime(df_th['Início:'], errors='coerce')
    else:
        df_th = pd.DataFrame()
    criticos = []
    hoje = pd.Timestamp.now().normalize()
    anos10 = timedelta(days=365.25*10)
    anos85 = timedelta(days=365.25*8.5)
    for idx, row in df_tipo_filt.iterrows():
        critico = None
        chave = row['chave_item']
        etapa = row['etapa']
        status_th = str(row.get('status_th', '')).lower()
        data_th = pd.to_datetime(row.get('data_th'), errors='coerce')
        data_inicio = pd.to_datetime(row.get('data_inicio'), errors='coerce')
        ref = data_th if not pd.isnull(data_th) else data_inicio
        if etapa == 'Orçamento' and 'sim' in status_th:
            th_feito = False
            recarga = df_tipo_filt[(df_tipo_filt['chave_item'] == chave) & (df_tipo_filt['etapa'] == 'Recarga')]
            th_row = df_th[df_th['chave_item'] == chave] if not df_th.empty else pd.DataFrame()
            if (recarga.empty or recarga['status_th'].str.lower().str.contains('não').any()) and th_row.empty:
                critico = 'TH não realizado'
        if etapa == 'Recarga':
            if ref is not None and not pd.isnull(ref):
                vencimento = hoje - ref
                if vencimento > anos10:
                    critico = 'TH vencido'
                elif vencimento > anos85:
                    critico = 'TH quase vencido'
        if critico:
            criticos.append({
                **row,
                "tipo_critico": critico,
                "dias_vencido": (hoje - ref).days if etapa == 'Recarga' else None
            })
    df_criticos = pd.DataFrame(criticos)

    # CRÍTICOS e % críticos
    orcados = len(set(df_tipo_filt[df_tipo_filt['etapa'] == 'Orçamento']['chave_item']))
    pct_criticos = (len(df_criticos) / orcados) * 100 if orcados > 0 else 0
    k6, k7 = st.columns([2,3])
    k6.metric("% de Críticos", f"{pct_criticos:.1f}%")
    if not df_criticos.empty:
        vencendo = df_criticos[df_criticos['tipo_critico'].str.contains('quase', case=False, na=False)]
        if not vencendo.empty:
            n_criticos = len(vencendo)
            dias_min = vencendo['dias_vencido'].min() if 'dias_vencido' in vencendo else None
            k7.warning(f"⚠️ {n_criticos} itens vão vencer TH em até 1,5 anos! Mais próximo: {dias_min} dias", icon="⚠️")

    # FUNIL (agora sempre usando todas as etapas, não depende do filtro de etapa)
    df_funil = pd.concat([df_tipo_orc, df_tipo_outras])
    etapas_kpi = ['Orçamento', 'Recarga', 'Finalização']
    funil_colors = ["#2456f0", "#21c1f3", "#f4a100"]
    funil_counts = {}
    for etapa_ in etapas_kpi:
        chaves_etapa = set(df_funil[df_funil['etapa'] == etapa_]['chave_item'])
        chaves_cruzadas = chaves_etapa & chaves_cliente
        funil_counts[etapa_] = len(chaves_cruzadas)
    funil_plot = pd.DataFrame({'Etapa': etapas_kpi, 'Qtd': [funil_counts[e] for e in etapas_kpi]})
    st.markdown(f'<h2 class="section-header">{painel_idx}</h2>', unsafe_allow_html=True)
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.markdown(f"""<div class="metric-container"><div class="metric-title">Total</div><div class="metric-value">{funil_counts['Orçamento']}</div></div>""", unsafe_allow_html=True)
    k2.markdown(f"""<div class="metric-container"><div class="metric-title">Orçados</div><div class="metric-value">{funil_counts['Orçamento']}</div></div>""", unsafe_allow_html=True)
    k3.markdown(f"""<div class="metric-container"><div class="metric-title">Recarregados</div><div class="metric-value">{funil_counts['Recarga']}</div></div>""", unsafe_allow_html=True)
    k4.markdown(f"""<div class="metric-container"><div class="metric-title">Finalizados</div><div class="metric-value">{funil_counts['Finalização']}</div></div>""", unsafe_allow_html=True)
    k5.markdown(f"""<div class="metric-container"><div class="metric-title">Pendências</div><div class="metric-value">0</div></div>""", unsafe_allow_html=True)
    st.markdown("### Fluxo de Itens (Funil Real por Chave Única)")
    fig_funil = px.bar(funil_plot, x='Etapa', y='Qtd', text_auto=True, color='Etapa', title='Funil do Processo - Itens Únicos',
                       color_discrete_sequence=funil_colors)
    fig_funil.update_layout(font=dict(family="Inter, Arial, sans-serif", size=16, color="#444"),
                           plot_bgcolor='#fffbe7', paper_bgcolor='#fffbe7')
    st.plotly_chart(fig_funil, use_container_width=True)

    # Sankey
    st.markdown("### Fluxo Sankey entre Etapas")
    etapas_sankey = ['Orçamento', 'Recarga', 'Finalização']
    df_sankey = df_tipo_filt[df_tipo_filt['etapa'].isin(etapas_sankey)].copy()
    paths = df_sankey.groupby('chave_item')['etapa'].apply(list)
    sankey_data = []
    for etapas_ in paths:
        etapas_ = [e for e in etapas_sankey if e in etapas_]
        if len(etapas_) >= 2:
            for i in range(len(etapas_)-1):
                sankey_data.append((etapas_[i], etapas_[i+1]))
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
            node=dict(label=labels, pad=30, thickness=20, color=["#2456f0","#21c1f3","#e94d5a"]),
            link=dict(source=sources, target=targets, value=values)
        ))
        fig_sankey.update_layout(title_text="Fluxo de Itens entre Etapas (Sankey)", font_size=14)
        st.plotly_chart(fig_sankey, use_container_width=True)
    else:
        st.info("Não há fluxo suficiente entre etapas para gerar o Sankey.")

    # TOP CLIENTES
    st.markdown("### Top 10 Clientes")
    if 'cliente' in df_tipo_filt.columns and not df_tipo_filt['cliente'].isna().all():
        top_cli = df_tipo_filt[df_tipo_filt['cliente'].notna() & (df_tipo_filt['cliente'] != '')]['cliente'].value_counts().head(10).reset_index()
        top_cli.columns = ['Cliente', 'Qtd']
        if not top_cli.empty:
            st.download_button(
                label="Baixar top 10 clientes (CSV)",
                data=top_cli.to_csv(index=False),
                file_name=f"{painel_idx.lower()}_top_clientes.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Baixar top 10 clientes (Excel)",
                data=to_excel(top_cli),
                file_name=f"{painel_idx.lower()}_top_clientes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            fig_cli = px.bar(top_cli, x="Cliente", y="Qtd", title="Top 10 Clientes", text_auto=True,
                             color_discrete_sequence=["#2456f0"])
            fig_cli.update_layout(font=dict(family="Inter, Arial, sans-serif", size=16, color="#444"),
                                 plot_bgcolor='#fffbe7', paper_bgcolor='#fffbe7')
            st.plotly_chart(fig_cli, use_container_width=True)
        else:
            st.info("Sem dados de cliente para exibir.")
    else:
        st.info("Coluna de cliente não encontrada.")

    # LAUDOS (pizza)
    st.markdown("### Distribuição dos Laudos Técnicos")
    if 'laudo_tecnico' in df_tipo_filt.columns and not df_tipo_filt['laudo_tecnico'].isna().all():
        df_tipo_filt = agrupar_outros(df_tipo_filt, 'laudo_tecnico', top=7)
        laudo_agrupado = df_tipo_filt['laudo_tecnico_agrup'].value_counts().reset_index()
        laudo_agrupado.columns = ['Laudo', 'Qtd']
        if not laudo_agrupado.empty:
            st.download_button(
                label="Baixar laudos (CSV)",
                data=laudo_agrupado.to_csv(index=False),
                file_name=f"{painel_idx.lower()}_laudos.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Baixar laudos (Excel)",
                data=to_excel(laudo_agrupado),
                file_name=f"{painel_idx.lower()}_laudos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            fig_laudo = px.pie(laudo_agrupado, names="Laudo", values="Qtd", title="Laudos Técnicos (Top 7 + Outros)",
                               color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_laudo.update_layout(font=dict(family="Inter, Arial, sans-serif", size=15, color="#444"))
            st.plotly_chart(fig_laudo, use_container_width=True)
        else:
            st.info("Sem dados de laudo técnico para exibir.")
    else:
        st.info("Coluna de laudo técnico não encontrada.")

    # TIMELINE
    st.markdown("### Evolução dos Eventos no Tempo (Data de Início)")
    if 'data_inicio' in df_tipo_filt.columns and not df_tipo_filt['data_inicio'].isna().all():
        if df_tipo_filt['data_inicio'].notna().any():
            st.download_button(
                label="Baixar datas de início (CSV)",
                data=df_tipo_filt[['data_inicio', 'etapa']].dropna().to_csv(index=False),
                file_name=f"{painel_idx.lower()}_datas_inicio.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Baixar datas de início (Excel)",
                data=to_excel(df_tipo_filt[['data_inicio', 'etapa']].dropna()),
                file_name=f"{painel_idx.lower()}_datas_inicio.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            fig_time = px.histogram(df_tipo_filt, x='data_inicio', color="etapa", title="Evolução dos Eventos (Data de Início)",
                                    color_discrete_sequence=funil_colors)
            fig_time.update_layout(font=dict(family="Inter, Arial, sans-serif", size=14, color="#444"))
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Sem dados de datas de início para exibir.")
    else:
        st.info("Coluna de data de início não encontrada.")

    # DUPLICIDADES
    st.markdown("### Duplicidades (mesma chave e etapa)")
    if 'chave_item' in df_tipo_filt.columns:
        duplicados = df_tipo_filt[df_tipo_filt.duplicated(['chave_item', 'etapa'], keep=False)].sort_values(['chave_item', 'etapa'])
        if not duplicados.empty:
            st.download_button(
                label="Baixar duplicados (CSV)",
                data=duplicados.to_csv(index=False),
                file_name=f"{painel_idx.lower()}_duplicados.csv",
                mime="text/csv"
            )
            st.download_button(
                label="Baixar duplicados (Excel)",
                data=to_excel(duplicados),
                file_name=f"{painel_idx.lower()}_duplicados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.dataframe(duplicados, use_container_width=True)
        else:
            st.info("Nenhuma duplicidade detectada para o filtro.")
    else:
        st.info("Coluna chave_item não encontrada.")

else:
    st.info("Faça upload do Excel para explorar o BI completo!")

st.markdown('<div class="footer">BI Ampolas & Tanques • Profissional • Powered by Rennan Miranda</div>', unsafe_allow_html=True)
