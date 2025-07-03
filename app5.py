import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import io
import base64
import re

# === Configuração da página e CSS ===
st.set_page_config(page_title="BI Ampolas & Tanques", page_icon="🏭", layout="wide")
st.markdown("""
<style>
body { background-color: #F8F9FA; font-family: 'Inter', sans-serif; }
.main-header { font-size:2.4rem; font-weight:900; text-align:center;
  background:linear-gradient(90deg,#ffd600,#ffe066,#fff5cc);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  margin:1.5rem 0; }
.section-header { font-size:1.5rem; font-weight:700; color:#f4a100; margin:1.5rem 0; }
.metric-container { background:#fffbe7; border-radius:12px;
  box-shadow:0 4px 20px rgba(0,0,0,0.05); padding:1.2rem; text-align:center;
  margin-bottom:1rem; }
.metric-title { font-size:1.1rem; color:#3366CC; margin-bottom:0.5rem; }
.metric-value { font-size:2rem; font-weight:700; color:#f4a100; }
.footer { text-align:center; color:#9e8b36; margin:2rem 0 1rem 0; }
</style>
""", unsafe_allow_html=True)

# === Funções Utilitárias ===
def display_logo(path="logo.png", height=80):
    try:
        with open(path, "rb") as f: img = f.read()
        b64 = base64.b64encode(img).decode()
        st.markdown(f"<div style='text-align:center;'><img src='data:image/png;base64,{b64}' height='{height}'></div>", unsafe_allow_html=True)
    except FileNotFoundError: pass

def to_excel(df_to_export):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_to_export.to_excel(writer, index=False)
    return buf.getvalue()

def highlight_critical(val):
    if pd.isna(val): return ''
    if val > 365*10: return 'background-color: #ff4d4d; color: white;'
    if val > 365*8.5: return 'background-color: #ffa500; color: white;'
    return ''

# === LÓGICA DE PROCESSAMENTO DE DADOS ===
@st.cache_data
def load_and_process_data(uploaded_file, unique_key_cols):
    xls = pd.ExcelFile(uploaded_file)
    SHEETS = [
        ("orc_A", "Ampola", "Orçamento"), ("rec_A", "Ampola", "Recarga"), ("fin_A", "Ampola", "Finalização"),
        ("orc_T_P", "Tanque Pressurizado", "Orçamento"), ("rec_T_P", "Tanque Pressurizado", "Recarga"), ("fin_T_P", "Tanque Pressurizado", "Finalização"),
        ("orc_T_S", "Tanque Sem Pressão", "Orçamento"), ("rec_T_S", "Tanque Sem Pressão", "Recarga")
    ]
    COLMAP = {
        "nota_fiscal": ["Nota Fiscal", "Número da Nota Fiscal", "Nº Nota Fiscal"],
        "numero_serie": ["Número de Série", "Nº de Série"],
        "numero_lacre": ["Número do Lacre", "Nº do Lacre"],
        "cliente": ["Cliente"], "laudo_tecnico": ["Análise Técnica:", "Laudo.", "Laudo Técnico"],
        "status_th": ["Necessário Teste Hidrostático?", "Realizado Teste Hidrostático?", "Teste Hidrostático Realizado?"],
        "data_th": ["Data do Teste Hidrostático", "Data Fabricação / Teste Hidrostático"], "data_inicio": ["Início:"]
    }

    def clean_key_text(text):
        if pd.isna(text): return ""
        s = str(text).replace('.0', '')
        s = re.sub(r'[^A-Z0-9]', '', s.upper()); return s
    def clean_client_name(text):
        if pd.isna(text): return ""
        return str(text).strip().upper()

    all_data = []
    for sheet_name, tipo_item, etapa in SHEETS:
        if sheet_name in xls.sheet_names:
            df_raw = xls.parse(sheet_name)
            df_processed = pd.DataFrame()
            for target_col, source_options in COLMAP.items():
                found_col = next((col for col in source_options if col in df_raw.columns), None)
                if found_col:
                    if target_col in ["nota_fiscal", "numero_serie", "numero_lacre"]: df_processed[target_col] = df_raw[found_col].apply(clean_key_text)
                    elif target_col == 'cliente': df_processed[target_col] = df_raw[found_col].apply(clean_client_name)
                    else: df_processed[target_col] = pd.to_datetime(df_raw[found_col], errors='coerce') if "data" in target_col else df_raw[found_col]
                else: df_processed[target_col] = "" if "data" not in target_col else pd.NaT
            df_processed["tipo_item"], df_processed["etapa"] = tipo_item, etapa
            all_data.append(df_processed)

    if not all_data: return pd.DataFrame(), {}
    
    df_full = pd.concat(all_data, ignore_index=True)
    stats = {"rows_read": len(df_full)}
    
    df_full['chave'] = df_full[unique_key_cols].agg(lambda x: "|".join(x.astype(str)), axis=1)
    df_full = df_full[df_full['chave'].str.replace('|', '').str.strip().astype(bool)]
    stats["rows_after_key_drop"] = len(df_full)

    df_com_cliente = df_full[df_full['cliente'].astype(str).str.strip() != ''].copy()
    mapa_mestre_clientes = df_com_cliente.drop_duplicates('chave', keep='first').set_index('chave')['cliente']
    df_full['cliente'] = df_full['chave'].map(mapa_mestre_clientes)
    df_full.dropna(subset=['cliente'], inplace=True)
    stats["rows_after_orphans_drop"] = len(df_full)
    
    return df_full, stats

@st.cache_data
def calculate_lead_times(df):
    if df.empty: return pd.DataFrame()
    df_pivot = df.pivot_table(index='chave', columns='etapa', values='data_inicio', aggfunc='min')
    if 'Orçamento' in df_pivot and 'Recarga' in df_pivot: df_pivot['lead_orc_rec'] = (df_pivot['Recarga'] - df_pivot['Orçamento']).dt.days
    if 'Recarga' in df_pivot and 'Finalização' in df_pivot: df_pivot['lead_rec_fin'] = (df_pivot['Finalização'] - df_pivot['Recarga']).dt.days
    if 'Orçamento' in df_pivot and 'Finalização' in df_pivot: df_pivot['lead_total'] = (df_pivot['Finalização'] - df_pivot['Orçamento']).dt.days
    return df_pivot.reset_index()

@st.cache_data
def identify_critical_items(df):
    if df.empty: return pd.DataFrame()
    df_sorted = df.sort_values("data_inicio", ascending=False)
    latest_status = df_sorted.drop_duplicates(subset=['chave'], keep='first')
    crit_list = []; today = pd.Timestamp.now().normalize()
    ten_years, eight_half = timedelta(days=365.25 * 10), timedelta(days=365.25 * 8.5)
    for _, row in latest_status.iterrows():
        ref_date = row["data_th"] if pd.notna(row["data_th"]) else row["data_inicio"]
        if pd.notna(ref_date):
            if row["etapa"] in ["Orçamento", "Recarga"]:
                delta = today - ref_date
                if delta > ten_years: crit_list.append({**row.to_dict(), "crit_tipo": "TH vencido", "dias_vencido": delta.days})
                elif delta > eight_half: crit_list.append({**row.to_dict(), "crit_tipo": "TH quase vencido", "dias_vencido": delta.days})
    return pd.DataFrame(crit_list)

# === UI e Lógica Principal ===
display_logo()
st.markdown('<h1 class="main-header">BI Ampolas & Tanques - Grupo Franzen</h1>', unsafe_allow_html=True)

upload = st.sidebar.file_uploader("Upload do arquivo Excel (.xlsx)", type=["xlsx"])
if not upload: st.info("Por favor, faça o upload de um arquivo Excel para começar."); st.stop()

st.sidebar.header("Filtros Dinâmicos")
if st.sidebar.button("🧹 Limpar Todos os Filtros"):
    st.session_state.keys_multiselect = ["nota_fiscal", "numero_serie", "numero_lacre"]
    st.session_state.painel_radio = "Todos"; st.session_state.cliente_select = "Todos"
    st.rerun()

if 'keys_multiselect' not in st.session_state: st.session_state.keys_multiselect = ["nota_fiscal", "numero_serie", "numero_lacre"]
keys = st.sidebar.multiselect("Campos para chave única:", ["nota_fiscal", "numero_serie", "numero_lacre"], key='keys_multiselect')
if not keys: st.sidebar.error("Selecione ao menos um campo para a chave única."); st.stop()

df_main, stats = load_and_process_data(upload, keys)
if df_main.empty: st.error("Nenhum dado válido encontrado."); st.stop()

# --- Filtros ---
if 'painel_radio' not in st.session_state: st.session_state.painel_radio = "Todos"
painel = st.sidebar.radio("Painel:", ["Todos", "Ampola", "Tanque Pressurizado", "Tanque Sem Pressão"], key='painel_radio')
data_df = df_main.copy()
if painel != "Todos": data_df = data_df[data_df["tipo_item"] == painel]
clientes_disponiveis = ["Todos"] + sorted(data_df["cliente"].unique())
if 'cliente_select' not in st.session_state: st.session_state.cliente_select = "Todos"
sel_cli = st.sidebar.selectbox("Cliente:", clientes_disponiveis, key='cliente_select')
if sel_cli != "Todos": data_df = data_df[data_df["cliente"] == sel_cli]

# --- Abas do Dashboard ---
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Principal", "🔍 Análise de Processos", "🚨 Monitoramento de Riscos"])
with tab1:
    st.markdown(f"<h2 class='section-header'>Painel Geral: {painel} | Cliente: {sel_cli}</h2>", unsafe_allow_html=True)
    if data_df.empty: st.warning("Nenhum dado encontrado para os filtros selecionados."); st.stop()
    
    # KPIs - LINHA CORRIGIDA
    total_unicos = data_df['chave'].nunique()
    orcados = data_df[data_df['etapa'] == 'Orçamento']['chave'].nunique()
    recarregados = data_df[data_df['etapa'] == 'Recarga']['chave'].nunique()
    finalizados = data_df[data_df['etapa'] == 'Finalização']['chave'].nunique()
    
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"<div class='metric-container'><div class='metric-title'>Itens Únicos</div><div class='metric-value'>{total_unicos}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-container'><div class='metric-title'>Orçados</div><div class='metric-value'>{orcados}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-container'><div class='metric-title'>Recarregados</div><div class='metric-value'>{recarregados}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-container'><div class='metric-title'>Finalizados</div><div class='metric-value'>{finalizados}</div></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("##### Funil de Processos (Itens Únicos)"); funil_data = data_df.groupby("etapa")["chave"].nunique().reindex(["Orçamento","Recarga","Finalização"],fill_value=0)
        fig=go.Figure(go.Funnel(y=funil_data.index,x=funil_data.values,textinfo="value+percent initial")); fig.update_layout(margin=dict(l=0,r=0,t=0,b=0)); st.plotly_chart(fig,use_container_width=True)
    with col2:
        st.markdown("##### Top 10 Clientes"); top_cli=data_df[data_df["cliente"]!=""].cliente.value_counts().nlargest(10).reset_index(); top_cli.columns=["Cliente","Quantidade"]
        fig=px.bar(top_cli,x="Quantidade",y="Cliente",orientation="h",text="Quantidade"); fig.update_layout(yaxis={'categoryorder':'total ascending'},margin=dict(l=0,r=0,t=0,b=0)); st.plotly_chart(fig,use_container_width=True)

with tab2:
    st.markdown("<h2 class='section-header'>Análise de Performance do Processo (Lead Time)</h2>", unsafe_allow_html=True)
    df_lead_times = calculate_lead_times(data_df)
    if df_lead_times.empty or df_lead_times.drop(columns=['chave']).isnull().all().all(): st.info("Não há dados para calcular o tempo entre etapas.")
    else:
        st.markdown("##### Tempo Médio Entre Etapas (em dias)"); c1,c2,c3=st.columns(3)
        mean_orc_rec=df_lead_times['lead_orc_rec'].mean() if 'lead_orc_rec' in df_lead_times else 0
        mean_rec_fin=df_lead_times['lead_rec_fin'].mean() if 'lead_rec_fin' in df_lead_times else 0
        mean_total=df_lead_times['lead_total'].mean() if 'lead_total' in df_lead_times else 0
        c1.metric("Orçamento ➔ Recarga",f"{mean_orc_rec:.1f} dias"); c2.metric("Recarga ➔ Finalização",f"{mean_rec_fin:.1f} dias"); c3.metric("Tempo Total",f"{mean_total:.1f} dias")
        st.markdown("##### Distribuição do Tempo de Ciclo")
        lead_cols=[col for col in ['lead_orc_rec','lead_rec_fin','lead_total'] if col in df_lead_times and df_lead_times[col].notna().any()]
        if lead_cols:
            sel_lead=st.selectbox("Analisar tempo de ciclo:",lead_cols); fig=px.histogram(df_lead_times,x=sel_lead,nbins=30,title=f"Distribuição: {sel_lead}")
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("<h2 class='section-header'>Monitoramento de Riscos e Prazos</h2>", unsafe_allow_html=True)
    df_crit = identify_critical_items(data_df)
    if df_crit.empty: st.info("Nenhum item com risco de vencimento de teste hidrostático encontrado para os filtros atuais.")
    else:
        crit_tipos = df_crit.crit_tipo.unique()
        cols_to_show = ['cliente'] + keys + ['data_th', 'dias_vencido']
        if "TH quase vencido" in crit_tipos:
            st.markdown("##### ⚠️ Quase Vencido")
            df_q = df_crit[df_crit.crit_tipo=="TH quase vencido"]
            st.dataframe(df_q[cols_to_show].style.map(highlight_critical, subset=['dias_vencido']))
        if "TH vencido" in crit_tipos:
            st.markdown("##### 🔥 Vencido")
            df_v = df_crit[df_crit.crit_tipo=="TH vencido"]
            st.dataframe(df_v[cols_to_show].style.map(highlight_critical, subset=['dias_vencido']))

# --- Sidebar: Rodapé e Infos ---
with st.sidebar.expander("ℹ️ Qualidade dos Dados"):
    st.write(f"Linhas lidas: **{stats.get('rows_read', 0)}**")
    st.write(f"Linhas c/ chave vazia: **{stats.get('rows_read', 0) - stats.get('rows_after_key_drop', 0)}**")
    st.write(f"Itens órfãos (sem cliente): **{stats.get('rows_after_key_drop', 0) - stats.get('rows_after_orphans_drop', 0)}**")
    st.write(f"Total de registros válidos: **{stats.get('rows_after_orphans_drop', 0)}**")

st.sidebar.download_button("📥 Baixar Dados Filtrados (.xlsx)", to_excel(data_df), f"bi_dados_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx", "application/vnd.ms-excel")
st.markdown('<div class="footer">BI Ampolas & Tanques • Powered by Rennan Miranda</div>', unsafe_allow_html=True)