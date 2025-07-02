import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import io
import base64
from typing import Dict, List, Optional, Tuple, Union
from functools import partial
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================
# CONFIGURAÇÕES E CONSTANTES
# =============================================
class AppConfig:
    """Configurações da aplicação e constantes"""
    
    # Configuração da página
    PAGE_CONFIG = {
        "page_title": "BI Ampolas & Tanques",
        "page_icon": "🏭",
        "layout": "wide",
        "initial_sidebar_state": "expanded"
    }
    
    # Cores e temas
    COLORS = {
        'primary': '#F4A100',
        'secondary': '#2456F0',
        'success': '#21C1F3',
        'warning': '#FFD600',
        'danger': '#E94D5A',
        'background': '#FFFBE7',
        'text': '#333333'
    }
    
    # Estilos CSS
    STYLES = """
    <style>
        /* Estilos gerais */
        body {
            font-family: 'Inter', Arial, sans-serif;
            color: #333;
        }
        
        /* Cabeçalho */
        .main-header {
            font-size: 2.2rem !important; 
            font-weight: 900; 
            text-align: center; 
            margin: 1.2rem 0 0.7rem 0;
            background: linear-gradient(90deg,#ffd600 0%,#ffe066 50%,#fff5cc 100%);
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent;
        }
        
        /* Cards de métricas */
        .metric-container {
            background: #fffbe7; 
            border-radius: 18px; 
            box-shadow: 0 3px 24px #f7e09860; 
            padding: 1.4rem 0.6rem 1rem;
            text-align: center;
            margin-bottom: 1rem;
        }
        .metric-title {
            font-size: 1rem;
            color: #9e8b36;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #f4a100;
        }
        
        /* Seções */
        .section-header {
            font-size: 1.3rem; 
            font-weight: 700; 
            color: #f4a100; 
            margin: 2.3rem 0 1.2rem 0; 
            letter-spacing:1px;
        }
        
        /* Footer */
        .footer {
            text-align: center; 
            color: #9e8b36; 
            margin: 2rem 0 1rem 0;
            font-size: 0.9rem;
        }
        
        /* Botões */
        .stDownloadButton button {
            background: #f4a100 !important; 
            color: white !important; 
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        .stDownloadButton button:hover {
            background: #ffd600 !important; 
            color: #454545 !important;
            transform: scale(1.02);
        }
        
        /* Sidebar */
        .st-emotion-cache-1wivap2 {
            background: #fffbe7;
        }
        
        /* Tabelas */
        .stDataFrame {
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
    </style>
    """
    
    # Configurações de gráficos
    CHART_CONFIG = {
        'font': dict(family="Inter, Arial, sans-serif", size=14, color="#444"),
        'plot_bgcolor': '#FFFBE7',
        'paper_bgcolor': '#FFFBE7',
        'hovermode': 'closest',
        'margin': dict(l=20, r=20, t=40, b=20)
    }
    
    # Mapeamento das abas do Excel
    SHEET_MAPPING = [
        {'sheet': 'orc_A', 'item_type': 'Ampola', 'stage': 'Orçamento',
         'columns': {
             'nota_fiscal': 'Nota Fiscal', 
             'numero_serie': 'Número de Série', 
             'numero_lacre': 'Número do Lacre',
             'cliente': 'Cliente', 
             'laudo_tecnico': 'Análise Técnica:',
             'status_th': 'Necessário Teste Hidrostático?', 
             'data_th': 'Data do Teste Hidrostático',
             'data_inicio': 'Início:'
         }},
        {'sheet': 'rec_A', 'item_type': 'Ampola', 'stage': 'Recarga',
         'columns': {
             'nota_fiscal': 'Número da Nota Fiscal', 
             'numero_serie': 'Número de Série', 
             'numero_lacre': 'Número do Lacre',
             'cliente': '', 
             'laudo_tecnico': 'Laudo.', 
             'status_th': 'Realizado Teste Hidrostático?',
             'data_th': 'Data Fabricação / Teste Hidrostático', 
             'data_inicio': 'Início:'
         }},
        # Adicione os outros mapeamentos conforme seu original
    ]

# =============================================
# FUNÇÕES UTILITÁRIAS
# =============================================
def display_logo(file_path: str, height: int = 85) -> None:
    """Exibe o logo centralizado"""
    try:
        with open(file_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode()
            st.markdown(
                f'<div style="display: flex; justify-content: center; margin: 1.5rem 0 0.3rem 0;">'
                f'<img src="data:image/png;base64,{encoded}" height="{height}"></div>',
                unsafe_allow_html=True
            )
    except Exception as e:
        logger.error(f"Erro ao carregar logo: {str(e)}")
        st.warning("Não foi possível carregar o logo.")

def standardize_key(value: Union[str, float, int]) -> str:
    """Padroniza valores de chave para consistência"""
    try:
        if pd.isna(value):
            return ""
            
        value = str(value).strip().upper()
        
        # Trata números decimais que são inteiros (ex: 123.0 -> 123)
        if '.' in value:
            try:
                float_val = float(value)
                if float_val.is_integer():
                    value = str(int(float_val))
            except ValueError:
                pass
                
        return "" if value in ["", "NAN", "NONE", "NULL"] else value
    except Exception as e:
        logger.warning(f"Erro ao padronizar valor '{value}': {str(e)}")
        return ""

def create_item_key(row: pd.Series, key_fields: List[str]) -> str:
    """Cria uma chave única baseada nos campos selecionados"""
    try:
        return "|".join(standardize_key(row.get(field, "")) for field in key_fields)
    except Exception as e:
        logger.error(f"Erro ao criar chave do item: {str(e)}")
        return ""

def convert_to_date(date_str: Union[str, datetime]) -> Optional[datetime]:
    """Converte string para objeto datetime"""
    if pd.isna(date_str):
        return None
        
    if isinstance(date_str, datetime):
        return date_str
        
    try:
        return pd.to_datetime(date_str, errors='coerce')
    except Exception as e:
        logger.warning(f"Erro ao converter data '{date_str}': {str(e)}")
        return None

def group_small_categories(df: pd.DataFrame, column: str, threshold: int = 7) -> pd.DataFrame:
    """Agrupa categorias pequenas em 'Outros'"""
    if column not in df.columns:
        return df
        
    value_counts = df[column].value_counts()
    top_categories = value_counts.nlargest(threshold).index
    df[f"{column}_grouped"] = df[column].where(df[column].isin(top_categories), 'Outros')
    return df

def to_excel(df: pd.DataFrame) -> bytes:
    """Converte DataFrame para bytes (formato Excel)"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# =============================================
# PROCESSAMENTO DE DADOS
# =============================================
@st.cache_data(ttl=3600, show_spinner="Processando dados...")
def process_uploaded_file(uploaded_file: io.BytesIO, key_fields: List[str]) -> pd.DataFrame:
    """Processa o arquivo Excel carregado e retorna um DataFrame consolidado"""
    try:
        xl = pd.ExcelFile(uploaded_file)
        frames = []
        
        for config in AppConfig.SHEET_MAPPING:
            if config['sheet'] in xl.sheet_names:
                try:
                    df = xl.parse(config['sheet'])
                    
                    # Padroniza colunas
                    for new_col, old_col in config['columns'].items():
                        if old_col and old_col in df.columns:
                            df[new_col] = df[old_col].apply(standardize_key)
                        else:
                            df[new_col] = ""
                    
                    # Adiciona metadados
                    df['item_type'] = config['item_type']
                    df['stage'] = config['stage']
                    df['item_key'] = df.apply(partial(create_item_key, fields=key_fields), axis=1)
                    
                    # Converte datas
                    if 'data_inicio' in df.columns:
                        df['data_inicio'] = df['data_inicio'].apply(convert_to_date)
                    if 'data_th' in df.columns:
                        df['data_th'] = df['data_th'].apply(convert_to_date)
                    
                    frames.append(df)
                    
                except Exception as e:
                    logger.error(f"Erro ao processar aba {config['sheet']}: {str(e)}")
                    continue
        
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivo: {str(e)}")
        st.error("Erro ao processar o arquivo. Verifique o formato e tente novamente.")
        return pd.DataFrame()

def identify_critical_items(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica itens críticos (TH vencido ou não realizado)"""
    critical_items = []
    today = pd.Timestamp.now().normalize()
    ten_years = timedelta(days=365.25 * 10)
    eight_and_half_years = timedelta(days=365.25 * 8.5)
    
    for _, row in df.iterrows():
        critical_type = None
        days_overdue = None
        
        stage = row.get('stage', '')
        status_th = str(row.get('status_th', '')).lower()
        th_date = row.get('data_th')
        start_date = row.get('data_inicio')
        reference_date = th_date if pd.notna(th_date) else start_date
        
        if stage == 'Orçamento' and 'sim' in status_th:
            # Verifica se TH foi realizado
            has_th = False
            
            # Verifica na etapa de recarga
            recarga_mask = (df['item_key'] == row['item_key']) & (df['stage'] == 'Recarga')
            if any(recarga_mask):
                recarga_status = df.loc[recarga_mask, 'status_th'].iloc[0]
                if 'não' not in str(recarga_status).lower():
                    has_th = True
            
            if not has_th:
                critical_type = 'TH não realizado'
                
        elif stage == 'Recarga' and pd.notna(reference_date):
            # Verifica vencimento do TH
            time_elapsed = today - reference_date
            
            if time_elapsed > ten_years:
                critical_type = 'TH vencido'
                days_overdue = (today - reference_date).days
            elif time_elapsed > eight_and_half_years:
                critical_type = 'TH quase vencido'
                days_overdue = (today - reference_date).days
                
        if critical_type:
            critical_item = row.to_dict()
            critical_item['critical_type'] = critical_type
            critical_item['days_overdue'] = days_overdue
            critical_items.append(critical_item)
    
    return pd.DataFrame(critical_items) if critical_items else pd.DataFrame()

# =============================================
# COMPONENTES VISUAIS
# =============================================
def render_metric_card(title: str, value: Union[str, int, float], help_text: str = "") -> None:
    """Renderiza um card de métrica estilizado"""
    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
    """, unsafe_allow_html=True)

def render_funnel_chart(df: pd.DataFrame, item_type: str) -> None:
    """Renderiza o gráfico de funil do processo"""
    try:
        # Filtra por tipo de item e conta por etapa
        stage_counts = df[df['item_type'] == item_type]['stage'].value_counts().reset_index()
        stage_counts.columns = ['stage', 'count']
        
        # Ordena conforme o fluxo do processo
        stage_order = ['Orçamento', 'Recarga', 'Finalização']
        stage_counts['stage'] = pd.Categorical(stage_counts['stage'], categories=stage_order, ordered=True)
        stage_counts = stage_counts.sort_values('stage')
        
        # Cores para cada etapa
        color_map = {
            'Orçamento': AppConfig.COLORS['primary'],
            'Recarga': AppConfig.COLORS['success'],
            'Finalização': AppConfig.COLORS['danger']
        }
        
        fig = px.funnel(
            stage_counts,
            x='count',
            y='stage',
            title=f"Funil de Processo - {item_type}",
            color='stage',
            color_discrete_map=color_map,
            labels={'count': 'Quantidade', 'stage': 'Etapa'}
        )
        
        fig.update_layout(AppConfig.CHART_CONFIG)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Erro ao renderizar funil: {str(e)}")
        st.warning("Não foi possível gerar o gráfico de funil.")

def render_sankey_diagram(df: pd.DataFrame, item_type: str) -> None:
    """Renderiza diagrama Sankey do fluxo entre etapas"""
    try:
        # Filtra e prepara dados
        filtered_df = df[df['item_type'] == item_type]
        stages = ['Orçamento', 'Recarga', 'Finalização']
        filtered_df = filtered_df[filtered_df['stage'].isin(stages)]
        
        # Agrupa por item e coleta o caminho
        paths = filtered_df.groupby('item_key')['stage'].apply(list)
        
        # Conta transições entre etapas
        sankey_data = []
        for path in paths:
            path = [p for p in path if p in stages]
            if len(path) >= 2:
                for i in range(len(path)-1):
                    sankey_data.append((path[i], path[i+1]))
        
        if not sankey_data:
            st.info("Dados insuficientes para gerar o diagrama Sankey.")
            return
            
        sankey_counts = pd.DataFrame(sankey_data, columns=['source', 'target']).value_counts().reset_index(name='count')
        
        # Prepara labels e índices
        labels = stages
        label_idx = {label: idx for idx, label in enumerate(labels)}
        
        # Mapeia fontes e destinos
        sources = [label_idx[row['source']] for _, row in sankey_counts.iterrows()]
        targets = [label_idx[row['target']] for _, row in sankey_counts.iterrows()]
        values = sankey_counts['count'].tolist()
        
        # Cria figura
        fig = go.Figure(go.Sankey(
            node=dict(
                pad=30,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=[AppConfig.COLORS['primary'], AppConfig.COLORS['success'], AppConfig.COLORS['danger']]
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color="rgba(180, 180, 180, 0.4)"
            )
        ))
        
        fig.update_layout(
            title_text=f"Fluxo entre Etapas - {item_type}",
            font_size=14,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Erro ao renderizar Sankey: {str(e)}")
        st.warning("Erro ao gerar o diagrama Sankey.")

def render_top_clients(df: pd.DataFrame, item_type: str) -> None:
    """Renderiza gráfico dos top 10 clientes"""
    try:
        if 'cliente' not in df.columns or df['cliente'].isna().all():
            st.info("Dados de cliente não disponíveis.")
            return
            
        # Filtra e conta clientes
        top_clients = (
            df[df['item_type'] == item_type]
            .groupby('cliente')
            .size()
            .nlargest(10)
            .reset_index(name='count')
        )
        
        if top_clients.empty:
            st.info("Nenhum dado de cliente para exibir.")
            return
            
        # Cria gráfico
        fig = px.bar(
            top_clients,
            x='count',
            y='cliente',
            orientation='h',
            title=f"Top 10 Clientes - {item_type}",
            labels={'count': 'Quantidade', 'cliente': 'Cliente'},
            color='count',
            color_continuous_scale='YlOrBr'
        )
        
        fig.update_layout(AppConfig.CHART_CONFIG)
        st.plotly_chart(fig, use_container_width=True)
        
        # Botões de download
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Baixar top clientes (CSV)",
                data=top_clients.to_csv(index=False),
                file_name=f"top_clientes_{item_type.lower()}.csv",
                mime="text/csv"
            )
        with col2:
            st.download_button(
                label="Baixar top clientes (Excel)",
                data=to_excel(top_clients),
                file_name=f"top_clientes_{item_type.lower()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        logger.error(f"Erro ao renderizar top clientes: {str(e)}")
        st.warning("Erro ao gerar gráfico de clientes.")

# =============================================
# APLICAÇÃO PRINCIPAL
# =============================================
def main():
    # Configuração inicial
    st.set_page_config(**AppConfig.PAGE_CONFIG)
    st.markdown(AppConfig.STYLES, unsafe_allow_html=True)
    
    # Cabeçalho
    display_logo("logo.png")
    st.markdown('<h1 class="main-header">BI Ampolas & Tanques - Grupo Franzen</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #F4A100;">Dashboard de processos, laudos, riscos e TH</p>', unsafe_allow_html=True)
    
    # Upload do arquivo
    uploaded_file = st.file_uploader(
        "Selecione o arquivo Excel (.xlsx) com as abas brutas", 
        type=["xlsx"],
        help="O arquivo deve conter as abas mapeadas conforme o padrão estabelecido."
    )
    
    if not uploaded_file:
        st.info("Faça upload do arquivo Excel para iniciar a análise.")
        st.markdown('<div class="footer">BI Ampolas & Tanques • Profissional • Powered by Streamlit</div>', unsafe_allow_html=True)
        return
    
    # Sidebar - Configurações
    st.sidebar.header("Configurações")
    
    # Seleção de campos para chave única
    key_options = ["nota_fiscal", "numero_serie", "numero_lacre"]
    key_labels = ["Nota Fiscal", "Número de Série", "Número do Lacre"]
    selected_keys = st.sidebar.multiselect(
        "Campos para chave única:",
        options=key_labels,
        default=key_labels[:2],
        help="Combine campos para criar identificadores únicos dos itens."
    )
    
    if not selected_keys:
        st.warning("Selecione pelo menos um campo para compor a chave única.")
        return
        
    # Mapeia labels para nomes de colunas
    key_mapping = dict(zip(key_labels, key_options))
    selected_columns = [key_mapping[label] for label in selected_keys]
    
    # Processa o arquivo
    with st.spinner("Processando dados..."):
        df = process_uploaded_file(uploaded_file, selected_columns)
        
        if df.empty:
            st.error("Nenhum dado válido encontrado. Verifique o formato do arquivo.")
            return
            
        # Identifica itens críticos
        critical_items = identify_critical_items(df)
        
    # Filtros na sidebar
    st.sidebar.header("Filtros")
    
    # Tipo de item
    item_types = df['item_type'].unique()
    selected_type = st.sidebar.selectbox(
        "Tipo de Item:",
        options=item_types,
        index=0
    )
    
    # Filtra por tipo
    filtered_df = df[df['item_type'] == selected_type]
    
    # Cliente (se disponível)
    clientes = []
    if 'cliente' in filtered_df.columns:
        clientes = sorted(filtered_df['cliente'].dropna().unique())
        selected_client = st.sidebar.selectbox(
            f"Cliente ({selected_type}):",
            options=["Todos"] + clientes,
            index=0
        )
        
        if selected_client != "Todos":
            filtered_df = filtered_df[filtered_df['cliente'] == selected_client]
    
    # Etapas
    available_stages = filtered_df['stage'].unique()
    selected_stages = st.sidebar.multiselect(
        f"Etapas ({selected_type}):",
        options=available_stages,
        default=available_stages
    )
    
    if selected_stages:
        filtered_df = filtered_df[filtered_df['stage'].isin(selected_stages)]
    
    # Filtro por data
    if 'data_inicio' in filtered_df.columns:
        valid_dates = filtered_df['data_inicio'].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            
            date_range = st.sidebar.date_input(
                f"Período ({selected_type}):",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = filtered_df[
                    (filtered_df['data_inicio'].dt.date >= start_date) & 
                    (filtered_df['data_inicio'].dt.date <= end_date)
                ]
    
    # Busca textual
    search_text = st.sidebar.text_input(
        "Busca textual:",
        placeholder="Filtrar por cliente, nota, laudo...",
        help="Busca em todos os campos textuais."
    )
    
    if search_text:
        search_text = search_text.lower()
        text_columns = [col for col in filtered_df.columns if filtered_df[col].dtype == 'object']
        mask = pd.Series(False, index=filtered_df.index)
        
        for col in text_columns:
            mask |= filtered_df[col].astype(str).str.lower().str.contains(search_text)
            
        filtered_df = filtered_df[mask]
    
    # =============================================
    # VISUALIZAÇÕES PRINCIPAIS
    # =============================================
    st.markdown(f'<h2 class="section-header">{selected_type}</h2>', unsafe_allow_html=True)
    
    # Métricas de resumo
    st.subheader("Visão Geral")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_items = len(filtered_df['item_key'].unique())
        render_metric_card("Itens Únicos", total_items)
    
    with col2:
        orcados = len(filtered_df[filtered_df['stage'] == 'Orçamento']['item_key'].unique())
        render_metric_card("Orçados", orcados)
    
    with col3:
        recarregados = len(filtered_df[filtered_df['stage'] == 'Recarga']['item_key'].unique())
        render_metric_card("Recarregados", recarregados)
    
    with col4:
        finalizados = len(filtered_df[filtered_df['stage'] == 'Finalização']['item_key'].unique())
        render_metric_card("Finalizados", finalizados)
    
    with col5:
        critical_count = len(critical_items[critical_items['item_type'] == selected_type])
        render_metric_card("Itens Críticos", critical_count)
    
    # Seção de críticos
    if not critical_items.empty:
        st.subheader("Itens Críticos")
        
        current_criticals = critical_items[critical_items['item_type'] == selected_type]
        
        if not current_criticals.empty:
            # Calcula porcentagem de críticos
            total_orcados = len(filtered_df[filtered_df['stage'] == 'Orçamento']['item_key'].unique())
            pct_critical = (len(current_criticals) / total_orcados * 100) if total_orcados > 0 else 0
            
            # Exibe alerta para itens prestes a vencer
            soon_expiring = current_criticals[current_criticals['critical_type'] == 'TH quase vencido']
            
            if not soon_expiring.empty:
                min_days = soon_expiring['days_overdue'].min()
                st.warning(
                    f"⚠️ {len(soon_expiring)} itens com TH prestes a vencer! "
                    f"Mais próximo: {min_days} dias",
                    icon="⚠️"
                )
            
            # Tabela de itens críticos
            st.dataframe(
                current_criticals[
                    ['item_key', 'critical_type', 'days_overdue', 'stage', 'cliente', 'nota_fiscal']
                ].sort_values('days_overdue', ascending=False),
                use_container_width=True
            )
            
            # Botões de download
            st.download_button(
                label="Baixar itens críticos (Excel)",
                data=to_excel(current_criticals),
                file_name=f"itens_criticos_{selected_type.lower()}.xlsx"
            )
        else:
            st.success("Nenhum item crítico encontrado para este tipo.")
    
    # Gráfico de funil
    st.subheader("Fluxo do Processo")
    render_funnel_chart(filtered_df, selected_type)
    
    # Diagrama Sankey
    st.subheader("Fluxo entre Etapas")
    render_sankey_diagram(filtered_df, selected_type)
    
    # Top clientes
    st.subheader("Principais Clientes")
    render_top_clients(filtered_df, selected_type)
    
    # Footer
    st.markdown('<div class="footer">BI Ampolas & Tanques • Profissional • Powered by Rennan Miranda</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()