"""
Risk Appetite Backtester — v6
- Visual Bloomberg (dark theme)
- Cota Master de fundo brasileiro (CDI na base, P&L ativo por cima)
- Benchmark apenas como linha comparativa no grafico
- Modo Long-Only Fund (150% / 100% / 50%)
- Futuros e ETFs separados | Sinal invertivel (panico=subida/queda)
- Exclusao de periodos (GFC/COVID/custom) | Testes de consistencia
"""

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# BLOOMBERG THEME — CSS
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Risk Appetite Backtester", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  /* ── Esconde banner branco e botão Deploy do Streamlit ── */
  header[data-testid="stHeader"]  { display: none !important; }
  [data-testid="stToolbar"]       { display: none !important; }
  #MainMenu                       { display: none !important; }
  footer                          { display: none !important; }
  [data-testid="stDecoration"]    { display: none !important; }

  /* ── Sidebar sempre visivel e fixa: elimina o botao de colapsar (nao
     funcionava de forma confiavel para reabrir) e trava a largura minima
     para impedir que seja arrastada/colapsada de qualquer outra forma. ── */
  [data-testid="stSidebarCollapsedControl"],
  [data-testid="collapsedControl"],
  [data-testid*="SidebarCollapse" i],
  [data-testid*="CollapsedControl" i] {
      display: none !important;
  }
  [data-testid="stSidebar"] {
      min-width: 280px !important;
  }

  /* ── Fundo geral ── */
  .stApp, .main, [data-testid="stAppViewContainer"] {
      background-color: #000000 !important;
  }
  /* ── Sidebar ── */
  [data-testid="stSidebar"], [data-testid="stSidebarContent"] {
      background-color: #0d0d0d !important;
      border-right: 1px solid #2a2a2a !important;
  }
  /* ── Texto geral (áreas escuras) ── */
  html, body, [class*="css"], p, span, label, div {
      color: #d0d0d0 !important;
      font-family: 'Courier New', Courier, monospace !important;
  }
  /* ── Preserva a fonte de icones Material (ex.: seta de colapsar a sidebar) ──
     A regra acima forca Courier New em todo <span>, o que faz o ligature
     do icone (ex.: "keyboard_double_arrow_left") aparecer como texto literal
     em vez do glifo. Restauramos a fonte correta apenas para esses spans. ── */
  [data-testid="stIconMaterial"] {
      font-family: 'Material Symbols Rounded', 'Material Icons' !important;
  }
  /* ── Dropdowns: fundo escuro, texto claro ── */
  [data-baseweb="select"] > div,
  [data-baseweb="select"] input,
  [data-testid="stSelectbox"] > div > div {
      background-color: #111111 !important;
      border: 1px solid #333333 !important;
      color: #e0e0e0 !important;
  }
  /* Texto do item selecionado no select */
  [data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
  [data-baseweb="select"] span,
  [data-baseweb="select"] div {
      color: #e0e0e0 !important;
  }
  /* ── Lista de opções do dropdown (popover) ── */
  [data-baseweb="popover"],
  [data-baseweb="menu"],
  [role="listbox"],
  [role="option"],
  ul[data-baseweb="menu"] {
      background-color: #1a1a1a !important;
      border: 1px solid #333333 !important;
  }
  /* Cada item da lista — texto preto sobre fundo claro NÃO; aqui fundo escuro, texto branco */
  [role="option"] div,
  [role="option"] span,
  [role="option"] li,
  [data-baseweb="menu-item"],
  [data-baseweb="menu-item"] div,
  [data-baseweb="menu-item"] span {
      background-color: #1a1a1a !important;
      color: #ffffff !important;
  }
  /* Hover no item */
  [role="option"]:hover div,
  [role="option"]:hover span,
  [data-baseweb="menu-item"]:hover,
  [data-baseweb="menu-item"]:hover div {
      background-color: #FF7700 !important;
      color: #000000 !important;
  }
  /* ── Título principal ── */
  h1 { color: #FF7700 !important; font-size: 1.4rem !important; letter-spacing: 2px; }
  h2, h3 { color: #FF7700 !important; }
  /* ── Subtítulos pequenos ── */
  small, .stCaption, [data-testid="stCaptionContainer"] { color: #606060 !important; }
  /* ── Botão principal ── */
  [data-testid="stBaseButton-primary"] button,
  .stButton > button[kind="primary"],
  button[kind="primary"] {
      background-color: #FF7700 !important;
      color: #000000 !important;
      font-weight: bold !important;
      border: none !important;
      font-family: 'Courier New', monospace !important;
      letter-spacing: 1px;
  }
  /* ── Botão secundário/padrão (ex: OTIMIZAR, "Usar") — sem isso cai no
     branco padrão do tema light do Streamlit, ilegível sobre fundo preto ── */
  [data-testid="stBaseButton-secondary"] button,
  .stButton > button[kind="secondary"],
  .stButton > button,
  button[kind="secondary"] {
      background-color: #111111 !important;
      color: #e0e0e0 !important;
      border: 1px solid #444444 !important;
      font-family: 'Courier New', monospace !important;
  }
  [data-testid="stBaseButton-secondary"] button:hover,
  .stButton > button[kind="secondary"]:hover,
  .stButton > button:hover,
  button[kind="secondary"]:hover {
      background-color: #FF7700 !important;
      color: #000000 !important;
      border-color: #FF7700 !important;
  }
  [data-testid="stBaseButton-secondary"] button:disabled,
  .stButton > button[kind="secondary"]:disabled,
  .stButton > button:disabled,
  button[kind="secondary"]:disabled {
      background-color: #1a1a1a !important;
      color: #777777 !important;
      border: 1px solid #333333 !important;
  }
  /* ── Métricas ── */
  [data-testid="stMetric"] {
      background-color: #0d0d0d !important;
      border: 1px solid #2a2a2a !important;
      border-radius: 4px;
      padding: 8px 12px !important;
  }
  [data-testid="stMetricValue"] { color: #FFFFFF !important; font-size: 1.2rem !important; }
  [data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
  /* ── Divisores ── */
  hr { border-color: #2a2a2a !important; }
  /* ── Tabelas ── */
  [data-testid="stDataFrame"] { border: 1px solid #2a2a2a !important; }
  thead th { background-color: #1a1a1a !important; color: #FF7700 !important; }
  /* ── Alertas ── */
  [data-testid="stAlert"] { background-color: #111111 !important; border: 1px solid #333 !important; }
  /* ── Tabs ── */
  [data-baseweb="tab-list"] { background-color: #0d0d0d !important; }
  [data-baseweb="tab"] { color: #808080 !important; }
  [aria-selected="true"] { color: #FF7700 !important; border-bottom: 2px solid #FF7700 !important; }
  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0d0d0d; }
  ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
  /* ── Date picker — fundo BBG total ── */
  [data-baseweb="popover"],
  [data-baseweb="popover"] > div,
  [data-baseweb="calendar"],
  [data-baseweb="calendar"] > div,
  [data-baseweb="datepicker"],
  div[class*="CalendarHeader"],
  div[class*="calendarHeader"] { background-color: #111111 !important; border: 1px solid #333 !important; }

  /* Todos os textos dentro do calendario */
  [data-baseweb="calendar"] *,
  [data-baseweb="popover"] * { color: #e0e0e0 !important; }

  /* Cabecalho mes/ano e botoes de navegacao */
  [data-baseweb="calendar"] button,
  [data-baseweb="calendar"] [data-baseweb="select"] > div,
  [data-baseweb="calendar"] [data-baseweb="select"] button { background-color: #1a1a1a !important; border-color: #444 !important; }

  /* Nomes dos dias da semana */
  [data-baseweb="calendar"] div[aria-label],
  [data-baseweb="calendar"] [class*="weekday"],
  [data-baseweb="calendar"] [class*="WeekDay"] { background-color: #111111 !important; color: #888 !important; }

  /* Celulas dos dias */
  [data-baseweb="calendar"] [role="gridcell"] > button,
  [data-baseweb="calendar"] [role="gridcell"] > div { background-color: transparent !important; }
  [data-baseweb="calendar"] [role="gridcell"] > button:hover { background-color: #333 !important; }

  /* Dia selecionado: laranja BBG */
  [data-baseweb="calendar"] [aria-selected="true"],
  [data-baseweb="calendar"] [aria-selected="true"] * { background-color: #FF7700 !important; color: #000 !important; }

  /* Dias desabilitados */
  [data-baseweb="calendar"] [aria-disabled="true"] { color: #444 !important; }

  /* Input de data no sidebar */
  [data-baseweb="input"],
  [data-baseweb="input"] > div { background-color: #1a1a1a !important; border-color: #444 !important; }
  [data-baseweb="input"] input { color: #e0e0e0 !important; background-color: #1a1a1a !important; }

  /* Dropdown mes/ano dentro do calendario */
  [data-baseweb="select"] [data-baseweb="popover"],
  [data-baseweb="select"] ul,
  [data-baseweb="menu"] { background-color: #1a1a1a !important; border: 1px solid #444 !important; }
  [data-baseweb="menu"] li:hover { background-color: #333 !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# I18N — internationalization (English default; 9 languages)
# ============================================================
LANGUAGES = {
    "en": "English",
    "pt": "Português",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "ja": "日本語",
    "zh": "中文",
    "ko": "한국어",
    "ar": "العربية",
}

TR = {
    'benchmark_check_spinner': {
        'en': 'Checking {ticker} history...',
        'pt': 'Verificando historico de {ticker}...',
        'es': 'Verificando historial de {ticker}...',
        'fr': "Verification de l'historique de {ticker}...",
        'de': 'Uberprufe Historie von {ticker}...',
        'ja': '{ticker} の履歴を確認中...',
        'zh': '正在检查 {ticker} 的历史数据...',
        'ko': '{ticker} 기록 확인 중...',
        'ar': 'جاري التحقق من سجل {ticker}...',
    },
    'benchmark_coverage_ok': {
        'en': '{ticker}: history covers the required period (since {start}).',
        'pt': '{ticker}: historico cobre o periodo necessario (desde {start}).',
        'es': '{ticker}: el historial cubre el periodo necesario (desde {start}).',
        'fr': "{ticker} : l'historique couvre la periode requise (depuis {start}).",
        'de': '{ticker}: Historie deckt den benotigten Zeitraum ab (seit {start}).',
        'ja': '{ticker}：履歴は必要な期間をカバーしています（{start}以降）。',
        'zh': '{ticker}：历史数据覆盖所需期间（自 {start} 起）。',
        'ko': '{ticker}: 기록이 필요한 기간을 포함합니다 ({start} 이후).',
        'ar': '{ticker}: يغطي السجل الفترة المطلوبة (منذ {start}).',
    },
    'benchmark_coverage_late_start': {
        'en': "{ticker}: data starts on {start}, after the IS start ({is_start}). The earlier period will use CDI/zero as base.",
        'pt': "{ticker}: dados comecam em {start}, apos o inicio do IS ({is_start}). O periodo anterior usara CDI/zero como base.",
        'es': "{ticker}: los datos comienzan el {start}, despues del inicio del IS ({is_start}). El periodo anterior usara CDI/cero como base.",
        'fr': "{ticker} : les donnees commencent le {start}, apres le debut de l'IS ({is_start}). La periode anterieure utilisera CDI/zero comme base.",
        'de': '{ticker}: Daten beginnen am {start}, nach dem IS-Start ({is_start}). Der fruhere Zeitraum verwendet CDI/Null als Basis.',
        'ja': '{ticker}：データはISの開始（{is_start}）より後の{start}から始まります。それ以前の期間はCDI/ゼロを基準として使用します。',
        'zh': '{ticker}：数据从 {start} 开始，晚于IS起始日（{is_start}）。更早的时期将使用CDI/零作为基准。',
        'ko': '{ticker}: 데이터가 IS 시작({is_start}) 이후인 {start}부터 시작됩니다. 이전 기간은 CDI/0을 기준으로 사용합니다.',
        'ar': '{ticker}: تبدأ البيانات في {start}، بعد بداية IS ({is_start}). ستستخدم الفترة السابقة CDI/صفر كقاعدة.',
    },
    'benchmark_coverage_stale_end': {
        'en': '{ticker}: data only available up to {end} ({days}-day gap). Recent periods may lack an updated benchmark.',
        'pt': '{ticker}: dados disponiveis somente até {end} (defasagem de {days} dias). Periodos recentes podem ficar sem benchmark atualizado.',
        'es': '{ticker}: datos disponibles solo hasta {end} (desfase de {days} dias). Los periodos recientes pueden quedar sin benchmark actualizado.',
        'fr': "{ticker} : donnees disponibles seulement jusqu'au {end} (decalage de {days} jours). Les periodes recentes peuvent manquer d'un benchmark a jour.",
        'de': '{ticker}: Daten nur bis {end} verfugbar ({days} Tage Verzogerung). Aktuelle Zeitraume haben moglicherweise keinen aktualisierten Benchmark.',
        'ja': '{ticker}：データは{end}までしか利用できません（{days}日のギャップ）。直近の期間は最新のベンチマークがない可能性があります。',
        'zh': '{ticker}：数据仅更新至 {end}（相差 {days} 天）。近期可能缺少最新的基准数据。',
        'ko': '{ticker}: 데이터가 {end}까지만 제공됩니다 ({days}일 차이). 최근 기간은 최신 벤치마크가 없을 수 있습니다.',
        'ar': '{ticker}: البيانات متوفرة فقط حتى {end} (فجوة {days} يومًا). قد تفتقر الفترات الأخيرة إلى معيار محدث.',
    },
    'benchmark_coverage_not_found': {
        'en': "{ticker}: could not retrieve history. CDI will be used as the benchmark instead.",
        'pt': "{ticker}: nao foi possivel obter historico. Sera usado CDI como benchmark.",
        'es': "{ticker}: no fue posible obtener historial. Se usara CDI como benchmark.",
        'fr': "{ticker} : impossible de recuperer l'historique. Le CDI sera utilise comme benchmark.",
        'de': '{ticker}: Historie konnte nicht abgerufen werden. CDI wird stattdessen als Benchmark verwendet.',
        'ja': '{ticker}：履歴を取得できませんでした。代わりにCDIをベンチマークとして使用します。',
        'zh': '{ticker}：无法获取历史数据。将使用CDI作为基准。',
        'ko': '{ticker}: 기록을 가져올 수 없습니다. 대신 CDI를 벤치마크로 사용합니다.',
        'ar': '{ticker}: تعذر استرداد السجل. سيتم استخدام CDI كمعيار بدلاً من ذلك.',
    },
    'error_download_failed': {
        'en': 'Error downloading {ticker}: {err}',
        'pt': 'Erro ao baixar {ticker}: {err}',
        'es': 'Error al descargar {ticker}: {err}',
        'fr': 'Erreur lors du telechargement de {ticker} : {err}',
        'de': 'Fehler beim Herunterladen von {ticker}: {err}',
        'ja': '{ticker} のダウンロードエラー: {err}',
        'zh': '下载 {ticker} 时出错：{err}',
        'ko': '{ticker} 다운로드 오류: {err}',
        'ar': 'خطأ في تنزيل {ticker}: {err}',
    },
    'label_model_master_quota': {
        'en': 'Model: Master Quota',
        'pt': 'Modelo: Cota Master',
        'es': 'Modelo: Cuota Master',
        'fr': 'Modele : Part Master',
        'de': 'Modell: Master-Quote',
        'ja': 'モデル：マスタークオータ',
        'zh': '模型：主份额',
        'ko': '모델: 마스터 쿼터',
        'ar': 'النموذج: الحصة الرئيسية',
    },
    'header_indicator_label': {
        'en': 'INDICATOR',
        'pt': 'INDICADOR',
        'es': 'INDICADOR',
        'fr': 'INDICATEUR',
        'de': 'INDIKATOR',
        'ja': 'インジケーター',
        'zh': '指标',
        'ko': '지표',
        'ar': 'المؤشر',
    },
    'header_data_label': {
        'en': 'DATA',
        'pt': 'DADOS',
        'es': 'DATOS',
        'fr': 'DONNEES',
        'de': 'DATEN',
        'ja': 'データ',
        'zh': '数据',
        'ko': '데이터',
        'ar': 'البيانات',
    },
    'language_label': {
        'en': 'Language',
        'pt': 'Idioma',
        'es': 'Idioma',
        'fr': 'Langue',
        'de': 'Sprache',
        'ja': '言語',
        'zh': '语言',
        'ko': '언어',
        'ar': 'اللغة',
    },
    'sidebar_params': {
        'en': 'PARAMETERS',
        'pt': 'PARAMETROS',
        'es': 'PARAMETROS',
        'fr': 'PARAMETRES',
        'de': 'PARAMETER',
        'ja': 'パラメータ',
        'zh': '参数',
        'ko': '매개변수',
        'ar': 'المعلمات',
    },
    'asset_type_label': {
        'en': 'ASSET TYPE',
        'pt': 'TIPO DE ATIVO',
        'es': 'TIPO DE ACTIVO',
        'fr': "TYPE D'ACTIF",
        'de': 'ASSETKLASSE',
        'ja': '資産タイプ',
        'zh': '资产类型',
        'ko': '자산 유형',
        'ar': 'نوع الأصل',
    },
    'opt_futuros': {
        'en': 'Futures',
        'pt': 'Futuros',
        'es': 'Futuros',
        'fr': 'Contrats a terme',
        'de': 'Futures',
        'ja': '先物',
        'zh': '期货',
        'ko': '선물',
        'ar': 'العقود الآجلة',
    },
    'opt_etfs': {
        'en': 'ETFs',
        'pt': 'ETFs',
        'es': 'ETFs',
        'fr': 'ETFs',
        'de': 'ETFs',
        'ja': 'ETF',
        'zh': 'ETF',
        'ko': 'ETF',
        'ar': 'صناديق المؤشرات المتداولة',
    },
    'help_tipo_ativo': {
        'en': 'Futures: CME/COMEX/CBOT/ICE contracts with =F suffix (continuous front-month) + FX spot. ETFs: equity, fixed income and commodity funds.',
        'pt': 'Futuros: contratos CME/COMEX/CBOT/ICE com sufixo =F (front-month continuo) + FX spot. ETFs: fundos de acoes, renda fixa e commodities.',
        'es': 'Futuros: contratos CME/COMEX/CBOT/ICE con sufijo =F (frente continuo) + FX spot. ETFs: fondos de acciones, renta fija y materias primas.',
        'fr': 'Contrats a terme : contrats CME/COMEX/CBOT/ICE avec suffixe =F (premier mois continu) + change spot. ETFs : fonds actions, obligataires et matieres premieres.',
        'de': 'Futures: CME/COMEX/CBOT/ICE-Kontrakte mit Suffix =F (fortlaufender Frontmonat) + FX-Spot. ETFs: Aktien-, Renten- und Rohstofffonds.',
        'ja': '先物: =F接尾辞付きのCME/COMEX/CBOT/ICE契約（連続フロントマンス）+ FXスポット。ETF: 株式、債券、コモディティファンド。',
        'zh': '期货：带=F后缀的CME/COMEX/CBOT/ICE合约（连续近月合约）+ 外汇即期。ETF：股票、固定收益和商品基金。',
        'ko': '선물: =F 접미사가 붙은 CME/COMEX/CBOT/ICE 계약(연속 근월물) + FX 스팟. ETF: 주식, 채권, 원자재 펀드.',
        'ar': 'العقود الآجلة: عقود CME/COMEX/CBOT/ICE بإضافة =F (الشهر الأمامي المستمر) + الفوركس الفوري. صناديق المؤشرات: صناديق الأسهم والدخل الثابت والسلع.',
    },
    'caption_futuros': {
        'en': 'Continuous front-month contracts. Daily percentage returns — roll gap is irrelevant.',
        'pt': 'Contratos front-month continuos. Retornos percentuais diarios — gap de rolagem irrelevante.',
        'es': 'Contratos de frente continuo. Retornos porcentuales diarios — el gap de rolado es irrelevante.',
        'fr': "Contrats premier mois continus. Rendements quotidiens en pourcentage — l'ecart de roulement est sans incidence.",
        'de': 'Fortlaufende Frontmonat-Kontrakte. Tagliche prozentuale Renditen — Roll-Gap ist irrelevant.',
        'ja': '連続フロントマンス契約。日次パーセンテージリターン — ロールギャップは無関係。',
        'zh': '连续近月合约。每日百分比收益 — 换月价差无关紧要。',
        'ko': '연속 근월물 계약. 일일 백분율 수익률 — 롤오버 갭은 무관함.',
        'ar': 'عقود الشهر الأمامي المستمرة. عوائد نسبية يومية — فجوة التدوير غير ذات أهمية.',
    },
    'caption_etfs': {
        'en': 'Equity, fixed income and commodity ETFs. Adjusted closing price.',
        'pt': 'ETFs de acoes, renda fixa e commodities. Preco de fechamento ajustado.',
        'es': 'ETFs de acciones, renta fija y materias primas. Precio de cierre ajustado.',
        'fr': 'ETFs actions, obligataires et matieres premieres. Cours de cloture ajuste.',
        'de': 'Aktien-, Renten- und Rohstoff-ETFs. Bereinigter Schlusskurs.',
        'ja': '株式、債券、コモディティETF。調整後終値。',
        'zh': '股票、固定收益和商品ETF。调整后收盘价。',
        'ko': '주식, 채권, 원자재 ETF. 수정 종가.',
        'ar': 'صناديق مؤشرات الأسهم والدخل الثابت والسلع. سعر الإغلاق المعدل.',
    },
    'asset_label': {
        'en': 'ASSET',
        'pt': 'ATIVO',
        'es': 'ACTIVO',
        'fr': 'ACTIF',
        'de': 'ASSET',
        'ja': '資産',
        'zh': '资产',
        'ko': '자산',
        'ar': 'الأصل',
    },
    'help_ativo': {
        'en': "Type part of the name to filter. E.g.: 'Gold', 'Treasury', 'EUR', 'ES=F'",
        'pt': "Digite parte do nome para filtrar. Ex: 'Gold', 'Treasury', 'EUR', 'ES=F'",
        'es': "Escriba parte del nombre para filtrar. Ej: 'Gold', 'Treasury', 'EUR', 'ES=F'",
        'fr': "Saisissez une partie du nom pour filtrer. Ex : 'Gold', 'Treasury', 'EUR', 'ES=F'",
        'de': "Geben Sie einen Teil des Namens ein, um zu filtern. Z. B.: 'Gold', 'Treasury', 'EUR', 'ES=F'",
        'ja': "名前の一部を入力してフィルタします。例：'Gold'、'Treasury'、'EUR'、'ES=F'",
        'zh': "输入名称的一部分进行筛选。例如：'Gold'、'Treasury'、'EUR'、'ES=F'",
        'ko': "이름의 일부를 입력하여 필터링하세요. 예: 'Gold', 'Treasury', 'EUR', 'ES=F'",
        'ar': "اكتب جزءًا من الاسم للتصفية. مثال: 'Gold'، 'Treasury'، 'EUR'، 'ES=F'",
    },
    'caption_selected': {
        'en': 'Selected: {ticker}',
        'pt': 'Selecionado: {ticker}',
        'es': 'Seleccionado: {ticker}',
        'fr': 'Selectionne : {ticker}',
        'de': 'Ausgewahlt: {ticker}',
        'ja': '選択中: {ticker}',
        'zh': '已选择：{ticker}',
        'ko': '선택됨: {ticker}',
        'ar': 'المحدد: {ticker}',
    },
    'period_label': {
        'en': 'PERIOD',
        'pt': 'PERIODO',
        'es': 'PERIODO',
        'fr': 'PERIODE',
        'de': 'ZEITRAUM',
        'ja': '期間',
        'zh': '周期',
        'ko': '기간',
        'ar': 'الفترة',
    },
    'is_start_label': {
        'en': 'In-Sample (IS) Start',
        'pt': 'Inicio In-Sample (IS)',
        'es': 'Inicio In-Sample (IS)',
        'fr': 'Debut In-Sample (IS)',
        'de': 'Start In-Sample (IS)',
        'ja': 'インサンプル(IS)開始',
        'zh': '样本内(IS)开始',
        'ko': '인샘플(IS) 시작',
        'ar': 'بداية العينة الداخلية (IS)',
    },
    'help_is_start': {
        'en': 'First day of training (IS). Change this to exclude the 2008 crisis, for example.',
        'pt': 'Primeiro dia do treinamento (IS). Mude para excluir a crise de 2008, por exemplo.',
        'es': 'Primer dia del entrenamiento (IS). Cambielo para excluir la crisis de 2008, por ejemplo.',
        'fr': "Premier jour de l'entrainement (IS). Modifiez ceci pour exclure la crise de 2008, par exemple.",
        'de': 'Erster Tag des Trainings (IS). Andern Sie dies, um z. B. die Krise von 2008 auszuschliessen.',
        'ja': '学習期間（IS）の初日。例えば2008年の危機を除外する場合に変更します。',
        'zh': '训练期（IS）的第一天。例如可修改以排除2008年危机。',
        'ko': '학습 기간(IS)의 첫째 날. 예를 들어 2008년 위기를 제외하려면 변경하세요.',
        'ar': 'أول يوم للتدريب (IS). غيّر هذا لاستثناء أزمة 2008 على سبيل المثال.',
    },
    'is_end_label': {
        'en': 'In-Sample (IS) End',
        'pt': 'Fim In-Sample (IS)',
        'es': 'Fin In-Sample (IS)',
        'fr': 'Fin In-Sample (IS)',
        'de': 'Ende In-Sample (IS)',
        'ja': 'インサンプル(IS)終了',
        'zh': '样本内(IS)结束',
        'ko': '인샘플(IS) 종료',
        'ar': 'نهاية العينة الداخلية (IS)',
    },
    'caption_oos': {
        'en': 'Out-of-Sample (OOS): {date} →',
        'pt': 'Out-of-Sample (OOS): {date} →',
        'es': 'Out-of-Sample (OOS): {date} →',
        'fr': 'Out-of-Sample (OOS) : {date} →',
        'de': 'Out-of-Sample (OOS): {date} →',
        'ja': 'アウトオブサンプル(OOS)：{date} →',
        'zh': '样本外(OOS)：{date} →',
        'ko': '아웃오브샘플(OOS): {date} →',
        'ar': 'العينة الخارجية (OOS): {date} ←',
    },
    'exclude_periods_label': {
        'en': 'EXCLUDE PERIODS FROM IS',
        'pt': 'EXCLUIR PERIODOS DO IS',
        'es': 'EXCLUIR PERIODOS DEL IS',
        'fr': "EXCLURE DES PERIODES DE L'IS",
        'de': 'ZEITRAEUME AUS IS AUSSCHLIESSEN',
        'ja': 'ISから期間を除外',
        'zh': '从IS中排除期间',
        'ko': 'IS에서 기간 제외',
        'ar': 'استثناء فترات من العينة الداخلية',
    },
    'excl_gfc_label': {
        'en': 'GFC — Sep/2008 to Mar/2009',
        'pt': 'GFC — Set/2008 a Mar/2009',
        'es': 'GFC — Sep/2008 a Mar/2009',
        'fr': 'GFC — Sept/2008 a Mars/2009',
        'de': 'GFC — Sep/2008 bis Mar/2009',
        'ja': 'GFC — 2008年9月〜2009年3月',
        'zh': '全球金融危机 — 2008年9月至2009年3月',
        'ko': 'GFC — 2008년 9월~2009년 3월',
        'ar': 'الأزمة المالية العالمية — سبتمبر 2008 إلى مارس 2009',
    },
    'help_excl_gfc': {
        'en': 'Excludes the global financial crisis from IS training',
        'pt': 'Exclui a crise financeira global do treinamento IS',
        'es': 'Excluye la crisis financiera global del entrenamiento IS',
        'fr': "Exclut la crise financiere mondiale de l'entrainement IS",
        'de': 'Schliesst die globale Finanzkrise aus dem IS-Training aus',
        'ja': 'ISトレーニングから世界金融危機を除外します',
        'zh': '从IS训练中排除全球金融危机',
        'ko': 'IS 학습에서 글로벌 금융위기를 제외합니다',
        'ar': 'يستثني الأزمة المالية العالمية من تدريب العينة الداخلية',
    },
    'excl_covid_label': {
        'en': 'COVID — Feb/2020 to Nov/2020',
        'pt': 'COVID — Fev/2020 a Nov/2020',
        'es': 'COVID — Feb/2020 a Nov/2020',
        'fr': 'COVID — Fev/2020 a Nov/2020',
        'de': 'COVID — Feb/2020 bis Nov/2020',
        'ja': 'COVID — 2020年2月〜2020年11月',
        'zh': '新冠疫情 — 2020年2月至2020年11月',
        'ko': '코로나19 — 2020년 2월~2020년 11월',
        'ar': 'كوفيد — فبراير 2020 إلى نوفمبر 2020',
    },
    'help_excl_covid': {
        'en': 'Excludes the COVID crisis from IS training',
        'pt': 'Exclui a crise COVID do treinamento IS',
        'es': 'Excluye la crisis COVID del entrenamiento IS',
        'fr': "Exclut la crise COVID de l'entrainement IS",
        'de': 'Schliesst die COVID-Krise aus dem IS-Training aus',
        'ja': 'ISトレーニングからCOVID危機を除外します',
        'zh': '从IS训练中排除新冠疫情危机',
        'ko': 'IS 학습에서 코로나19 위기를 제외합니다',
        'ar': 'يستثني أزمة كوفيد من تدريب العينة الداخلية',
    },
    'excl_custom_label': {
        'en': 'Custom period',
        'pt': 'Periodo customizado',
        'es': 'Periodo personalizado',
        'fr': 'Periode personnalisee',
        'de': 'Benutzerdefinierter Zeitraum',
        'ja': 'カスタム期間',
        'zh': '自定义期间',
        'ko': '사용자 지정 기간',
        'ar': 'فترة مخصصة',
    },
    'from_label': {
        'en': 'From',
        'pt': 'De',
        'es': 'Desde',
        'fr': 'Du',
        'de': 'Von',
        'ja': '開始',
        'zh': '从',
        'ko': '시작',
        'ar': 'من',
    },
    'to_label': {
        'en': 'To',
        'pt': 'Ate',
        'es': 'Hasta',
        'fr': 'Au',
        'de': 'Bis',
        'ja': '終了',
        'zh': '至',
        'ko': '종료',
        'ar': 'إلى',
    },
    'strategy_label': {
        'en': 'STRATEGY — CONTRARIAN',
        'pt': 'ESTRATEGIA — CONTRARIAN',
        'es': 'ESTRATEGIA — CONTRARIAN',
        'fr': 'STRATEGIE — CONTRARIAN',
        'de': 'STRATEGIE — CONTRARIAN',
        'ja': '戦略 — コントラリアン',
        'zh': '策略 — 反向（逆势）',
        'ko': '전략 — 컨트래리언',
        'ar': 'الاستراتيجية — معاكسة للسوق',
    },
    'caption_strategy': {
        'en': 'Buy on panic (low P) | Sell on euphoria (high P).',
        'pt': 'Compra no panico (P baixo) | Vende na euforia (P alto).',
        'es': 'Compra en panico (P bajo) | Vende en euforia (P alto).',
        'fr': "Achat en periode de panique (P bas) | Vente en periode d'euphorie (P haut).",
        'de': 'Kauf bei Panik (niedriges P) | Verkauf bei Euphorie (hohes P).',
        'ja': 'パニック時（低P）に買い、ユーフォリア時（高P）に売る。',
        'zh': '恐慌时（低P）买入 | 亢奋时（高P）卖出。',
        'ko': '패닉(낮은 P) 시 매수 | 도취(높은 P) 시 매도.',
        'ar': 'الشراء عند الذعر (P منخفض) | البيع عند النشوة (P مرتفع).',
    },
    'entry_euphoria_label': {
        'en': 'Entry EUPHORIA — SHORT',
        'pt': 'Entrada EUFORIA — SHORT',
        'es': 'Entrada EUFORIA — SHORT',
        'fr': 'Entree EUPHORIE — SHORT',
        'de': 'Einstieg EUPHORIE — SHORT',
        'ja': 'エントリー：ユーフォリア — SHORT',
        'zh': '进场：亢奋 — 做空',
        'ko': '진입: 도취 — SHORT',
        'ar': 'الدخول عند النشوة — بيع',
    },
    'entry_panic_label': {
        'en': 'Entry PANIC — LONG',
        'pt': 'Entrada PANICO — LONG',
        'es': 'Entrada PANICO — LONG',
        'fr': 'Entree PANIQUE — LONG',
        'de': 'Einstieg PANIK — LONG',
        'ja': 'エントリー：パニック — LONG',
        'zh': '进场：恐慌 — 做多',
        'ko': '진입: 패닉 — LONG',
        'ar': 'الدخول عند الذعر — شراء',
    },
    'exit_label_slider': {
        'en': 'Exit (average percentile)',
        'pt': 'Saida (percentil medio)',
        'es': 'Salida (percentil promedio)',
        'fr': 'Sortie (percentile moyen)',
        'de': 'Ausstieg (mittleres Perzentil)',
        'ja': 'エグジット（平均パーセンタイル）',
        'zh': '出场（平均百分位）',
        'ko': '청산(평균 백분위)',
        'ar': 'الخروج (المئين المتوسط)',
    },
    'leverage_label': {
        'en': 'LEVERAGE',
        'pt': 'ALAVANCAGEM',
        'es': 'APALANCAMIENTO',
        'fr': 'LEVIER',
        'de': 'HEBEL',
        'ja': 'レバレッジ',
        'zh': '杠杆',
        'ko': '레버리지',
        'ar': 'الرافعة المالية',
    },
    'long_only_label': {
        'en': 'Long-Only Fund Mode (150% / 100% / 50%)',
        'pt': 'Modo Long-Only Fund  (150% / 100% / 50%)',
        'es': 'Modo Long-Only Fund (150% / 100% / 50%)',
        'fr': 'Mode Fonds Long-Only (150% / 100% / 50%)',
        'de': 'Long-Only-Fund-Modus (150% / 100% / 50%)',
        'ja': 'ロングオンリーファンドモード (150% / 100% / 50%)',
        'zh': '纯多头基金模式（150% / 100% / 50%）',
        'ko': '롱온리 펀드 모드 (150% / 100% / 50%)',
        'ar': 'وضع الصندوق الطويل فقط (150% / 100% / 50%)',
    },
    'help_long_only': {
        'en': 'LONG signal → 150% | Flat → 100% | SHORT signal → 50%',
        'pt': 'LONG signal → 150% | Flat → 100% | SHORT signal → 50%',
        'es': 'Senal LONG → 150% | Plano → 100% | Senal SHORT → 50%',
        'fr': 'Signal LONG → 150% | Neutre → 100% | Signal SHORT → 50%',
        'de': 'LONG-Signal → 150% | Flat → 100% | SHORT-Signal → 50%',
        'ja': 'LONG信号 → 150% | フラット → 100% | SHORT信号 → 50%',
        'zh': '做多信号 → 150% | 空仓 → 100% | 做空信号 → 50%',
        'ko': 'LONG 신호 → 150% | 평탄 → 100% | SHORT 신호 → 50%',
        'ar': 'إشارة شراء → 150% | محايد → 100% | إشارة بيع → 50%',
    },
    'hedge_cost_label': {
        'en': 'FX HEDGE COST',
        'pt': 'CUSTO DO HEDGE CAMBIAL',
        'es': 'COSTO DE COBERTURA CAMBIARIA',
        'fr': 'COUT DE COUVERTURE DE CHANGE',
        'de': 'FX-HEDGEKOSTEN',
        'ja': 'FXヘッジコスト',
        'zh': '外汇对冲成本',
        'ko': 'FX 헤지 비용',
        'ar': 'تكلفة تغطية الصرف الأجنبي',
    },
    'caption_hedge': {
        'en': 'Spread = 1M FX Coupon - 1M SOFR. Zero = theoretical base case. Typical: 30-80 bps/year.',
        'pt': 'Spread = Cupom Cambial 1M - SOFR 1M. Zero = caso base teorico. Tipico: 30-80 bps/ano.',
        'es': 'Spread = Cupon Cambiario 1M - SOFR 1M. Cero = caso base teorico. Tipico: 30-80 bps/ano.',
        'fr': 'Spread = Coupon de change 1M - SOFR 1M. Zero = cas de base theorique. Typique : 30-80 pb/an.',
        'de': 'Spread = 1M FX-Kupon - 1M SOFR. Null = theoretischer Basisfall. Typisch: 30-80 Bp/Jahr.',
        'ja': 'スプレッド = 1Mキャンビアルクーポン - 1M SOFR。ゼロ = 理論上の基準ケース。一般的に年間30-80bps。',
        'zh': '价差 = 1个月外汇息票 - 1个月SOFR。零 = 理论基准情形。典型值：每年30-80个基点。',
        'ko': '스프레드 = 1개월 FX 쿠폰 - 1개월 SOFR. 0 = 이론적 기준 사례. 일반적으로 연 30-80bp.',
        'ar': 'الفرق = قسيمة الصرف لشهر واحد - SOFR لشهر واحد. صفر = الحالة الأساسية النظرية. النموذجي: 30-80 نقطة أساس سنويًا.',
    },
    'hedge_slider_label': {
        'en': 'Spread bps/year',
        'pt': 'Spread bps/ano',
        'es': 'Spread bps/ano',
        'fr': 'Spread pb/an',
        'de': 'Spread Bp/Jahr',
        'ja': 'スプレッド bps/年',
        'zh': '价差 基点/年',
        'ko': '스프레드 bps/년',
        'ar': 'الفرق نقطة أساس/سنة',
    },
    'help_hedge_slider': {
        'en': '0 bps = theoretical limit (zero spread). Historically 30-80 bps in normal markets.',
        'pt': '0 bps = limite teorico (spread zero). Historicamente 30-80 bps em mercados normais.',
        'es': '0 bps = limite teorico (spread cero). Historicamente 30-80 bps en mercados normales.',
        'fr': '0 pb = limite theorique (spread nul). Historiquement 30-80 pb dans des marches normaux.',
        'de': '0 Bp = theoretische Grenze (Spread null). Historisch 30-80 Bp in normalen Markten.',
        'ja': '0bps = 理論上の限界（スプレッドゼロ）。通常の市場では歴史的に30-80bps。',
        'zh': '0个基点 = 理论极限（零价差）。在正常市场中历史上为30-80个基点。',
        'ko': '0bps = 이론적 한계(스프레드 0). 정상 시장에서 역사적으로 30-80bps.',
        'ar': '0 نقطة أساس = الحد النظري (فرق صفري). تاريخيًا 30-80 نقطة أساس في الأسواق العادية.',
    },
    'benchmark_label': {
        'en': 'BENCHMARK (comparison line on chart)',
        'pt': 'BENCHMARK (linha comparativa no grafico)',
        'es': 'BENCHMARK (linea comparativa en el grafico)',
        'fr': 'BENCHMARK (ligne de comparaison sur le graphique)',
        'de': 'BENCHMARK (Vergleichslinie im Chart)',
        'ja': 'ベンチマーク（チャート上の比較線）',
        'zh': '基准（图表中的对比线）',
        'ko': '벤치마크(차트의 비교선)',
        'ar': 'المؤشر القياسي (خط المقارنة في الرسم البياني)',
    },
    'caption_benchmark': {
        'en': 'The strategy uses CDI as its base (Master Quota model).',
        'pt': 'A estrategia usa CDI como base (modelo cota Master).',
        'es': 'La estrategia usa CDI como base (modelo de cuota Master).',
        'fr': 'La strategie utilise le CDI comme base (modele de part Master).',
        'de': 'Die Strategie verwendet CDI als Basis (Master-Quoten-Modell).',
        'ja': '戦略はCDIをベースに使用します（マスタークオータモデル）。',
        'zh': '策略以CDI为基础（主份额模型）。',
        'ko': '전략은 CDI를 기준으로 사용합니다(마스터 쿼터 모델).',
        'ar': 'تستخدم الاستراتيجية CDI كقاعدة (نموذج الحصة الرئيسية).',
    },
    'bench_opt_zero': {
        'en': '0% — Pure strategy alpha',
        'pt': '0% — Alpha puro da estrategia',
        'es': '0% — Alpha puro de la estrategia',
        'fr': '0% — Alpha pur de la strategie',
        'de': '0% — Reines Strategie-Alpha',
        'ja': '0% — 戦略の純粋なアルファ',
        'zh': '0% — 策略纯阿尔法',
        'ko': '0% — 전략 순수 알파',
        'ar': '0% — ألفا الاستراتيجية الصافي',
    },
    'bench_opt_cdi': {
        'en': 'CDI / SELIC — Brazil',
        'pt': 'CDI / SELIC — Brasil',
        'es': 'CDI / SELIC — Brasil',
        'fr': 'CDI / SELIC — Bresil',
        'de': 'CDI / SELIC — Brasilien',
        'ja': 'CDI / SELIC — ブラジル',
        'zh': 'CDI / SELIC — 巴西',
        'ko': 'CDI / SELIC — 브라질',
        'ar': 'CDI / SELIC — البرازيل',
    },
    'bench_opt_fed': {
        'en': 'Fed Funds — USA',
        'pt': 'Fed Funds — EUA',
        'es': 'Fed Funds — EE.UU.',
        'fr': 'Fed Funds — Etats-Unis',
        'de': 'Fed Funds — USA',
        'ja': 'Fed Funds — 米国',
        'zh': '联邦基金利率 — 美国',
        'ko': 'Fed Funds — 미국',
        'ar': 'أموال الاحتياطي الفيدرالي — الولايات المتحدة',
    },
    'bench_opt_passive': {
        'en': 'Passive in the asset',
        'pt': 'Passivo no ativo',
        'es': 'Pasivo en el activo',
        'fr': "Passif sur l'actif",
        'de': 'Passiv im Basiswert',
        'ja': '資産にパッシブ',
        'zh': '资产被动持有',
        'ko': '자산 패시브',
        'ar': 'سلبي في الأصل',
    },
    'bench_opt_other': {
        'en': 'Other ticker',
        'pt': 'Outro ticker',
        'es': 'Otro ticker',
        'fr': 'Autre symbole',
        'de': 'Anderer Ticker',
        'ja': '他のティッカー',
        'zh': '其他代码',
        'ko': '다른 티커',
        'ar': 'رمز آخر',
    },
    'benchmark_ticker_label': {
        'en': 'Benchmark ticker',
        'pt': 'Ticker benchmark',
        'es': 'Ticker benchmark',
        'fr': 'Symbole benchmark',
        'de': 'Benchmark-Ticker',
        'ja': 'ベンチマークティッカー',
        'zh': '基准代码',
        'ko': '벤치마크 티커',
        'ar': 'رمز المؤشر القياسي',
    },
    'run_button': {
        'en': '▶  RUN BACKTEST',
        'pt': '▶  RODAR BACKTEST',
        'es': '▶  EJECUTAR BACKTEST',
        'fr': '▶  LANCER LE BACKTEST',
        'de': '▶  BACKTEST STARTEN',
        'ja': '▶  バックテスト実行',
        'zh': '▶  运行回测',
        'ko': '▶  백테스트 실행',
        'ar': '▶  تشغيل الاختبار الخلفي',
    },
    'optimize_button': {
        'en': '🔍  OPTIMIZE (Walk-Forward)',
        'pt': '🔍  OTIMIZAR (Walk-Forward)',
        'es': '🔍  OPTIMIZAR (Walk-Forward)',
        'fr': '🔍  OPTIMISER (Walk-Forward)',
        'de': '🔍  OPTIMIEREN (Walk-Forward)',
        'ja': '🔍  最適化 (ウォークフォワード)',
        'zh': '🔍  优化 (前向滚动)',
        'ko': '🔍  최적화 (워크포워드)',
        'ar': '🔍  تحسين (Walk-Forward)',
    },
    'spinner_loading_asset': {
        'en': 'Loading {ticker} (Yahoo Finance)...',
        'pt': 'Carregando {ticker} (Yahoo Finance)...',
        'es': 'Cargando {ticker} (Yahoo Finance)...',
        'fr': 'Chargement de {ticker} (Yahoo Finance)...',
        'de': 'Lade {ticker} (Yahoo Finance)...',
        'ja': '{ticker} を読み込み中 (Yahoo Finance)...',
        'zh': '正在加载 {ticker} (雅虎财经)...',
        'ko': '{ticker} 로딩 중 (Yahoo Finance)...',
        'ar': 'تحميل {ticker} (Yahoo Finance)...',
    },
    'error_ticker_not_found': {
        'en': "Ticker '{ticker}' not found. Check and try again.",
        'pt': "Ticker '{ticker}' nao encontrado. Verifique e tente novamente.",
        'es': "Ticker '{ticker}' no encontrado. Verifique e intente de nuevo.",
        'fr': "Symbole '{ticker}' introuvable. Verifiez et reessayez.",
        'de': "Ticker '{ticker}' nicht gefunden. Bitte uberprufen und erneut versuchen.",
        'ja': "ティッカー '{ticker}' が見つかりません。確認して再試行してください。",
        'zh': "未找到代码 '{ticker}'。请检查后重试。",
        'ko': "티커 '{ticker}'를 찾을 수 없습니다. 확인 후 다시 시도하세요.",
        'ar': "الرمز '{ticker}' غير موجود. تحقق وحاول مرة أخرى.",
    },
    'error_insufficient_data_align': {
        'en': 'Insufficient data after alignment ({n} days).',
        'pt': 'Dados insuficientes apos alinhamento ({n} dias).',
        'es': 'Datos insuficientes despues de la alineacion ({n} dias).',
        'fr': 'Donnees insuffisantes apres alignement ({n} jours).',
        'de': 'Unzureichende Daten nach Abgleich ({n} Tage).',
        'ja': 'アラインメント後のデータが不足しています（{n}日）。',
        'zh': '对齐后数据不足（{n}天）。',
        'ko': '정렬 후 데이터가 부족합니다 ({n}일).',
        'ar': 'بيانات غير كافية بعد المحاذاة ({n} يومًا).',
    },
    'warning_few_data_excl': {
        'en': 'Warning: little data left after excluding periods. Using full IS to calibrate.',
        'pt': 'Aviso: poucos dados apos excluir periodos. Usando IS completo para calibrar.',
        'es': 'Aviso: quedan pocos datos tras excluir periodos. Usando IS completo para calibrar.',
        'fr': "Attention : peu de donnees restantes apres exclusion des periodes. Utilisation de l'IS complet pour calibrer.",
        'de': 'Hinweis: wenig Daten nach Ausschluss der Zeitraeume. Vollstaendiges IS wird zur Kalibrierung verwendet.',
        'ja': '警告：期間を除外した後のデータが少なくなっています。完全なISでキャリブレーションします。',
        'zh': '警告：排除期间后剩余数据较少。将使用完整IS进行校准。',
        'ko': '경고: 기간 제외 후 데이터가 거의 남지 않았습니다. 전체 IS로 보정합니다.',
        'ar': 'تحذير: تبقت بيانات قليلة بعد استثناء الفترات. سيتم استخدام العينة الداخلية الكاملة للمعايرة.',
    },
    'error_is_too_short': {
        'en': 'In-Sample too short.',
        'pt': 'In-Sample muito curto.',
        'es': 'In-Sample demasiado corto.',
        'fr': 'IS trop court.',
        'de': 'In-Sample zu kurz.',
        'ja': 'インサンプルが短すぎます。',
        'zh': '样本内期间过短。',
        'ko': '인샘플 기간이 너무 짧습니다.',
        'ar': 'العينة الداخلية قصيرة جدًا.',
    },
    'error_oos_too_short': {
        'en': 'Out-of-Sample too short.',
        'pt': 'Out-of-Sample muito curto.',
        'es': 'Out-of-Sample demasiado corto.',
        'fr': 'OOS trop court.',
        'de': 'Out-of-Sample zu kurz.',
        'ja': 'アウトオブサンプルが短すぎます。',
        'zh': '样本外期间过短。',
        'ko': '아웃오브샘플 기간이 너무 짧습니다.',
        'ar': 'العينة الخارجية قصيرة جدًا.',
    },
    'spinner_running_is': {
        'en': 'Running In-Sample (IS) backtest...',
        'pt': 'Rodando backtest In-Sample (IS)...',
        'es': 'Ejecutando backtest In-Sample (IS)...',
        'fr': 'Execution du backtest In-Sample (IS)...',
        'de': 'Fuhre In-Sample (IS) Backtest aus...',
        'ja': 'インサンプル(IS)バックテストを実行中...',
        'zh': '正在运行样本内(IS)回测...',
        'ko': '인샘플(IS) 백테스트 실행 중...',
        'ar': 'تشغيل اختبار العينة الداخلية (IS)...',
    },
    'spinner_expanding_pct': {
        'en': 'Calculating expanding percentiles...',
        'pt': 'Calculando percentis expansivos...',
        'es': 'Calculando percentiles expansivos...',
        'fr': 'Calcul des percentiles expansifs...',
        'de': 'Berechne expandierende Perzentile...',
        'ja': '拡張パーセンタイルを計算中...',
        'zh': '正在计算扩展百分位数...',
        'ko': '확장 백분위수 계산 중...',
        'ar': 'حساب المئينات المتوسعة...',
    },
    'spinner_running_oos': {
        'en': 'Running Out-of-Sample (OOS) backtest...',
        'pt': 'Rodando backtest Out-of-Sample (OOS)...',
        'es': 'Ejecutando backtest Out-of-Sample (OOS)...',
        'fr': 'Execution du backtest Out-of-Sample (OOS)...',
        'de': 'Fuhre Out-of-Sample (OOS) Backtest aus...',
        'ja': 'アウトオブサンプル(OOS)バックテストを実行中...',
        'zh': '正在运行样本外(OOS)回测...',
        'ko': '아웃오브샘플(OOS) 백테스트 실행 중...',
        'ar': 'تشغيل اختبار العينة الخارجية (OOS)...',
    },
    'spinner_loading_benchmark': {
        'en': 'Loading benchmark {ticker}...',
        'pt': 'Carregando benchmark {ticker}...',
        'es': 'Cargando benchmark {ticker}...',
        'fr': 'Chargement du benchmark {ticker}...',
        'de': 'Lade Benchmark {ticker}...',
        'ja': 'ベンチマーク {ticker} を読み込み中...',
        'zh': '正在加载基准 {ticker}...',
        'ko': '벤치마크 {ticker} 로딩 중...',
        'ar': 'تحميل المؤشر القياسي {ticker}...',
    },
    'warning_benchmark_not_found': {
        'en': 'Benchmark not found. Using CDI.',
        'pt': 'Benchmark nao encontrado. Usando CDI.',
        'es': 'Benchmark no encontrado. Usando CDI.',
        'fr': 'Benchmark introuvable. Utilisation du CDI.',
        'de': 'Benchmark nicht gefunden. Verwende CDI.',
        'ja': 'ベンチマークが見つかりません。CDIを使用します。',
        'zh': '未找到基准。将使用CDI。',
        'ko': '벤치마크를 찾을 수 없습니다. CDI를 사용합니다.',
        'ar': 'المؤشر القياسي غير موجود. سيتم استخدام CDI.',
    },
    'bench_name_alpha': {
        'en': '0% (Alpha)',
        'pt': '0% (Alpha)',
        'es': '0% (Alpha)',
        'fr': '0% (Alpha)',
        'de': '0% (Alpha)',
        'ja': '0%（アルファ）',
        'zh': '0%（阿尔法）',
        'ko': '0%(알파)',
        'ar': '0% (ألفا)',
    },
    'bench_name_fed': {
        'en': 'Fed Funds',
        'pt': 'Fed Funds',
        'es': 'Fed Funds',
        'fr': 'Fed Funds',
        'de': 'Fed Funds',
        'ja': 'Fed Funds',
        'zh': '联邦基金利率',
        'ko': 'Fed Funds',
        'ar': 'أموال الاحتياطي الفيدرالي',
    },
    'bench_name_cdi': {
        'en': 'CDI/SELIC',
        'pt': 'CDI/SELIC',
        'es': 'CDI/SELIC',
        'fr': 'CDI/SELIC',
        'de': 'CDI/SELIC',
        'ja': 'CDI/SELIC',
        'zh': 'CDI/SELIC',
        'ko': 'CDI/SELIC',
        'ar': 'CDI/SELIC',
    },
    'bench_name_passive': {
        'en': '{ticker} (passive)',
        'pt': '{ticker} (passivo)',
        'es': '{ticker} (pasivo)',
        'fr': '{ticker} (passif)',
        'de': '{ticker} (passiv)',
        'ja': '{ticker}（パッシブ）',
        'zh': '{ticker}（被动）',
        'ko': '{ticker}(패시브)',
        'ar': '{ticker} (سلبي)',
    },
    'mode_long_only': {
        'en': 'Long-Only 150/50',
        'pt': 'Long-Only 150/50',
        'es': 'Long-Only 150/50',
        'fr': 'Long-Only 150/50',
        'de': 'Long-Only 150/50',
        'ja': 'ロングオンリー 150/50',
        'zh': '纯多头 150/50',
        'ko': '롱온리 150/50',
        'ar': 'طويل فقط 150/50',
    },
    'mode_contrarian': {
        'en': 'CONTRARIAN',
        'pt': 'CONTRARIAN',
        'es': 'CONTRARIAN',
        'fr': 'CONTRARIAN',
        'de': 'CONTRARIAN',
        'ja': 'コントラリアン',
        'zh': '反向（逆势）',
        'ko': '컨트래리언',
        'ar': 'معاكسة للسوق',
    },
    'delta_vs_buyhold': {
        'en': 'vs Buy&Hold',
        'pt': 'vs Buy&Hold',
        'es': 'vs Buy&Hold',
        'fr': 'vs Buy&Hold',
        'de': 'vs Buy&Hold',
        'ja': 'vs バイ&ホールド',
        'zh': 'vs 买入持有',
        'ko': 'vs Buy&Hold',
        'ar': 'مقابل الشراء والاحتفاظ',
    },
    'metric_quota_is': {
        'en': 'Quota In-Sample (IS)',
        'pt': 'Cota In-Sample (IS)',
        'es': 'Cuota In-Sample (IS)',
        'fr': 'Part In-Sample (IS)',
        'de': 'Quote In-Sample (IS)',
        'ja': 'クオータ インサンプル (IS)',
        'zh': '份额 样本内(IS)',
        'ko': '쿼터 인샘플(IS)',
        'ar': 'الحصة - العينة الداخلية (IS)',
    },
    'metric_quota_oos': {
        'en': 'Quota Out-of-Sample (OOS)',
        'pt': 'Cota Out-of-Sample (OOS)',
        'es': 'Cuota Out-of-Sample (OOS)',
        'fr': 'Part Out-of-Sample (OOS)',
        'de': 'Quote Out-of-Sample (OOS)',
        'ja': 'クオータ アウトオブサンプル (OOS)',
        'zh': '份额 样本外(OOS)',
        'ko': '쿼터 아웃오브샘플(OOS)',
        'ar': 'الحصة - العينة الخارجية (OOS)',
    },
    'metric_sharpe': {
        'en': 'SHARPE  In-Sample / Out-of-Sample',
        'pt': 'SHARPE  In-Sample / Out-of-Sample',
        'es': 'SHARPE  In-Sample / Out-of-Sample',
        'fr': 'SHARPE  In-Sample / Out-of-Sample',
        'de': 'SHARPE  In-Sample / Out-of-Sample',
        'ja': 'シャープレシオ  IS / OOS',
        'zh': '夏普比率  样本内/样本外',
        'ko': '샤프  인샘플 / 아웃오브샘플',
        'ar': 'شارب  العينة الداخلية / الخارجية',
    },
    'metric_maxdd': {
        'en': 'MAX DD  In-Sample / Out-of-Sample',
        'pt': 'MAX DD  In-Sample / Out-of-Sample',
        'es': 'MAX DD  In-Sample / Out-of-Sample',
        'fr': 'MAX DD  In-Sample / Out-of-Sample',
        'de': 'MAX DD  In-Sample / Out-of-Sample',
        'ja': '最大ドローダウン  IS / OOS',
        'zh': '最大回撤  样本内/样本外',
        'ko': '최대낙폭  인샘플 / 아웃오브샘플',
        'ar': 'أقصى تراجع  العينة الداخلية / الخارجية',
    },
    'chart_title_capital': {
        'en': 'CAPITAL CURVE (BASE 100)',
        'pt': 'CURVA DE CAPITAL (BASE 100)',
        'es': 'CURVA DE CAPITAL (BASE 100)',
        'fr': 'COURBE DE CAPITAL (BASE 100)',
        'de': 'KAPITALKURVE (BASIS 100)',
        'ja': '資本カーブ（ベース100）',
        'zh': '资金曲线（基数100）',
        'ko': '자본 곡선 (베이스 100)',
        'ar': 'منحنى رأس المال (الأساس 100)',
    },
    'chart_title_riskapp': {
        'en': 'RISK APPETITE INDICATOR',
        'pt': 'RISK APPETITE INDICATOR',
        'es': 'INDICADOR RISK APPETITE',
        'fr': 'INDICATEUR RISK APPETITE',
        'de': 'RISK APPETITE INDIKATOR',
        'ja': 'リスクアペタイト指標',
        'zh': '风险偏好指标',
        'ko': '리스크 어피타이트 지표',
        'ar': 'مؤشر شهية المخاطرة',
    },
    'curve_label_alpha_is': {
        'en': 'Alpha In-Sample (IS)',
        'pt': 'Alpha In-Sample (IS)',
        'es': 'Alpha In-Sample (IS)',
        'fr': 'Alpha In-Sample (IS)',
        'de': 'Alpha In-Sample (IS)',
        'ja': 'アルファ インサンプル (IS)',
        'zh': '阿尔法 样本内(IS)',
        'ko': '알파 인샘플(IS)',
        'ar': 'ألفا - العينة الداخلية (IS)',
    },
    'curve_label_quota_is': {
        'en': 'Master Quota In-Sample (IS)',
        'pt': 'Cota Master In-Sample (IS)',
        'es': 'Cuota Master In-Sample (IS)',
        'fr': 'Part Master In-Sample (IS)',
        'de': 'Master-Quote In-Sample (IS)',
        'ja': 'マスタークオータ インサンプル (IS)',
        'zh': '主份额 样本内(IS)',
        'ko': '마스터 쿼터 인샘플(IS)',
        'ar': 'الحصة الرئيسية - العينة الداخلية (IS)',
    },
    'curve_label_alpha_oos': {
        'en': 'Alpha Out-of-Sample (OOS)',
        'pt': 'Alpha Out-of-Sample (OOS)',
        'es': 'Alpha Out-of-Sample (OOS)',
        'fr': 'Alpha Out-of-Sample (OOS)',
        'de': 'Alpha Out-of-Sample (OOS)',
        'ja': 'アルファ アウトオブサンプル (OOS)',
        'zh': '阿尔法 样本外(OOS)',
        'ko': '알파 아웃오브샘플(OOS)',
        'ar': 'ألفا - العينة الخارجية (OOS)',
    },
    'curve_label_quota_oos': {
        'en': 'Master Quota Out-of-Sample (OOS)',
        'pt': 'Cota Master Out-of-Sample (OOS)',
        'es': 'Cuota Master Out-of-Sample (OOS)',
        'fr': 'Part Master Out-of-Sample (OOS)',
        'de': 'Master-Quote Out-of-Sample (OOS)',
        'ja': 'マスタークオータ アウトオブサンプル (OOS)',
        'zh': '主份额 样本外(OOS)',
        'ko': '마스터 쿼터 아웃오브샘플(OOS)',
        'ar': 'الحصة الرئيسية - العينة الخارجية (OOS)',
    },
    'trace_buyhold_is': {
        'en': 'Buy&Hold In-Sample (IS) — {bench}',
        'pt': 'Buy&Hold In-Sample (IS) — {bench}',
        'es': 'Buy&Hold In-Sample (IS) — {bench}',
        'fr': 'Buy&Hold In-Sample (IS) — {bench}',
        'de': 'Buy&Hold In-Sample (IS) — {bench}',
        'ja': 'バイ&ホールド インサンプル (IS) — {bench}',
        'zh': '买入持有 样本内(IS) — {bench}',
        'ko': 'Buy&Hold 인샘플(IS) — {bench}',
        'ar': 'الشراء والاحتفاظ - العينة الداخلية (IS) — {bench}',
    },
    'trace_buyhold_oos': {
        'en': 'Buy&Hold Out-of-Sample (OOS) — {bench}',
        'pt': 'Buy&Hold Out-of-Sample (OOS) — {bench}',
        'es': 'Buy&Hold Out-of-Sample (OOS) — {bench}',
        'fr': 'Buy&Hold Out-of-Sample (OOS) — {bench}',
        'de': 'Buy&Hold Out-of-Sample (OOS) — {bench}',
        'ja': 'バイ&ホールド アウトオブサンプル (OOS) — {bench}',
        'zh': '买入持有 样本外(OOS) — {bench}',
        'ko': 'Buy&Hold 아웃오브샘플(OOS) — {bench}',
        'ar': 'الشراء والاحتفاظ - العينة الخارجية (OOS) — {bench}',
    },
    'annotation_is': {
        'en': '◀  In-Sample  ▶',
        'pt': '◀  In-Sample  ▶',
        'es': '◀  In-Sample  ▶',
        'fr': '◀  In-Sample  ▶',
        'de': '◀  In-Sample  ▶',
        'ja': '◀  インサンプル  ▶',
        'zh': '◀  样本内  ▶',
        'ko': '◀  인샘플  ▶',
        'ar': '◀  العينة الداخلية  ▶',
    },
    'annotation_oos': {
        'en': '◀  Out-of-Sample  ▶',
        'pt': '◀  Out-of-Sample  ▶',
        'es': '◀  Out-of-Sample  ▶',
        'fr': '◀  Out-of-Sample  ▶',
        'de': '◀  Out-of-Sample  ▶',
        'ja': '◀  アウトオブサンプル  ▶',
        'zh': '◀  样本外  ▶',
        'ko': '◀  아웃오브샘플  ▶',
        'ar': '◀  العينة الخارجية  ▶',
    },
    'label_risk_appetite': {
        'en': 'Risk Appetite',
        'pt': 'Risk Appetite',
        'es': 'Risk Appetite',
        'fr': 'Risk Appetite',
        'de': 'Risk Appetite',
        'ja': 'リスクアペタイト',
        'zh': '风险偏好',
        'ko': '리스크 어피타이트',
        'ar': 'شهية المخاطرة',
    },
    'label_rhs': {
        'en': '(RHS)',
        'pt': '(RHS)',
        'es': '(RHS)',
        'fr': '(RHS)',
        'de': '(RHS)',
        'ja': '（右軸）',
        'zh': '（右轴）',
        'ko': '(우측축)',
        'ar': '(المحور الأيمن)',
    },
    'label_exit_suffix': {
        'en': '(exit)',
        'pt': '(saida)',
        'es': '(salida)',
        'fr': '(sortie)',
        'de': '(Ausstieg)',
        'ja': '（エグジット）',
        'zh': '（出场）',
        'ko': '(청산)',
        'ar': '(خروج)',
    },
    'label_is_suffix': {
        'en': '(IS)',
        'pt': '(IS)',
        'es': '(IS)',
        'fr': '(IS)',
        'de': '(IS)',
        'ja': '（IS）',
        'zh': '（样本内）',
        'ko': '(IS)',
        'ar': '(العينة الداخلية)',
    },
    'label_oos_suffix': {
        'en': '(OOS)',
        'pt': '(OOS)',
        'es': '(OOS)',
        'fr': '(OOS)',
        'de': '(OOS)',
        'ja': '（OOS）',
        'zh': '（样本外）',
        'ko': '(OOS)',
        'ar': '(العينة الخارجية)',
    },
    'yaxis_base100': {
        'en': 'Base 100',
        'pt': 'Base 100',
        'es': 'Base 100',
        'fr': 'Base 100',
        'de': 'Basis 100',
        'ja': 'ベース100',
        'zh': '基数100',
        'ko': '베이스 100',
        'ar': 'الأساس 100',
    },
    'yaxis_indicator': {
        'en': 'Indicator',
        'pt': 'Indicador',
        'es': 'Indicador',
        'fr': 'Indicateur',
        'de': 'Indikator',
        'ja': '指標',
        'zh': '指标',
        'ko': '지표',
        'ar': 'المؤشر',
    },
    'metrics_table_title': {
        'en': '📊 COMPARATIVE METRICS',
        'pt': '📊 METRICAS COMPARATIVAS',
        'es': '📊 METRICAS COMPARATIVAS',
        'fr': '📊 METRIQUES COMPARATIVES',
        'de': '📊 VERGLEICHSKENNZAHLEN',
        'ja': '📊 比較指標',
        'zh': '📊 对比指标',
        'ko': '📊 비교 지표',
        'ar': '📊 المقاييس المقارنة',
    },
    'col_metric': {
        'en': 'Metric',
        'pt': 'Metrica',
        'es': 'Metrica',
        'fr': 'Metrique',
        'de': 'Kennzahl',
        'ja': '指標',
        'zh': '指标',
        'ko': '지표',
        'ar': 'المقياس',
    },
    'col_is_strategy': {
        'en': 'In-Sample (IS) — Strategy',
        'pt': 'In-Sample (IS) — Estrategia',
        'es': 'In-Sample (IS) — Estrategia',
        'fr': 'In-Sample (IS) — Strategie',
        'de': 'In-Sample (IS) — Strategie',
        'ja': 'インサンプル (IS) — 戦略',
        'zh': '样本内(IS) — 策略',
        'ko': '인샘플(IS) — 전략',
        'ar': 'العينة الداخلية (IS) — الاستراتيجية',
    },
    'col_is_buyhold': {
        'en': 'In-Sample (IS) — Buy&Hold ({bench})',
        'pt': 'In-Sample (IS) — Buy&Hold ({bench})',
        'es': 'In-Sample (IS) — Buy&Hold ({bench})',
        'fr': 'In-Sample (IS) — Buy&Hold ({bench})',
        'de': 'In-Sample (IS) — Buy&Hold ({bench})',
        'ja': 'インサンプル (IS) — バイ&ホールド ({bench})',
        'zh': '样本内(IS) — 买入持有 ({bench})',
        'ko': '인샘플(IS) — Buy&Hold ({bench})',
        'ar': 'العينة الداخلية (IS) — الشراء والاحتفاظ ({bench})',
    },
    'col_oos_strategy': {
        'en': 'Out-of-Sample (OOS) — Strategy',
        'pt': 'Out-of-Sample (OOS) — Estrategia',
        'es': 'Out-of-Sample (OOS) — Estrategia',
        'fr': 'Out-of-Sample (OOS) — Strategie',
        'de': 'Out-of-Sample (OOS) — Strategie',
        'ja': 'アウトオブサンプル (OOS) — 戦略',
        'zh': '样本外(OOS) — 策略',
        'ko': '아웃오브샘플(OOS) — 전략',
        'ar': 'العينة الخارجية (OOS) — الاستراتيجية',
    },
    'col_oos_buyhold': {
        'en': 'Out-of-Sample (OOS) — Buy&Hold ({bench})',
        'pt': 'Out-of-Sample (OOS) — Buy&Hold ({bench})',
        'es': 'Out-of-Sample (OOS) — Buy&Hold ({bench})',
        'fr': 'Out-of-Sample (OOS) — Buy&Hold ({bench})',
        'de': 'Out-of-Sample (OOS) — Buy&Hold ({bench})',
        'ja': 'アウトオブサンプル (OOS) — バイ&ホールド ({bench})',
        'zh': '样本外(OOS) — 买入持有 ({bench})',
        'ko': '아웃오브샘플(OOS) — Buy&Hold ({bench})',
        'ar': 'العينة الخارجية (OOS) — الشراء والاحتفاظ ({bench})',
    },
    'row_total_return': {
        'en': 'Total Return',
        'pt': 'Retorno Total',
        'es': 'Retorno Total',
        'fr': 'Rendement Total',
        'de': 'Gesamtrendite',
        'ja': '合計リターン',
        'zh': '总回报',
        'ko': '총수익률',
        'ar': 'العائد الإجمالي',
    },
    'row_cagr': {
        'en': 'CAGR',
        'pt': 'CAGR',
        'es': 'CAGR',
        'fr': 'CAGR',
        'de': 'CAGR',
        'ja': 'CAGR',
        'zh': 'CAGR（年复合增长率）',
        'ko': 'CAGR',
        'ar': 'معدل النمو السنوي المركب',
    },
    'row_sharpe': {
        'en': 'Sharpe',
        'pt': 'Sharpe',
        'es': 'Sharpe',
        'fr': 'Sharpe',
        'de': 'Sharpe',
        'ja': 'シャープレシオ',
        'zh': '夏普比率',
        'ko': '샤프 비율',
        'ar': 'نسبة شارب',
    },
    'row_maxdd': {
        'en': 'Max Drawdown',
        'pt': 'Max Drawdown',
        'es': 'Max Drawdown',
        'fr': 'Drawdown Max',
        'de': 'Max Drawdown',
        'ja': '最大ドローダウン',
        'zh': '最大回撤',
        'ko': '최대 낙폭',
        'ar': 'أقصى تراجع',
    },
    'row_ntrades': {
        'en': '# Trades',
        'pt': 'Nº Trades',
        'es': 'Nº Operaciones',
        'fr': 'Nb Trades',
        'de': 'Anzahl Trades',
        'ja': 'トレード数',
        'zh': '交易次数',
        'ko': '거래 수',
        'ar': 'عدد الصفقات',
    },
    'row_pct_active': {
        'en': '% Time Active',
        'pt': '% Tempo Ativo',
        'es': '% Tiempo Activo',
        'fr': '% Temps Actif',
        'de': '% Aktive Zeit',
        'ja': 'アクティブ時間の割合',
        'zh': '持仓时间百分比',
        'ko': '활성 시간 비율',
        'ar': '٪ الوقت النشط',
    },
    'trades_log_title': {
        'en': '📋 TRADE LOG',
        'pt': '📋 LOG DE TRADES',
        'es': '📋 REGISTRO DE OPERACIONES',
        'fr': '📋 JOURNAL DES TRADES',
        'de': '📋 TRADE-PROTOKOLL',
        'ja': '📋 トレードログ',
        'zh': '📋 交易记录',
        'ko': '📋 거래 기록',
        'ar': '📋 سجل الصفقات',
    },
    'tab_is_trades': {
        'en': 'In-Sample  ({n} trades)',
        'pt': 'In-Sample  ({n} trades)',
        'es': 'In-Sample  ({n} operaciones)',
        'fr': 'In-Sample  ({n} trades)',
        'de': 'In-Sample  ({n} Trades)',
        'ja': 'インサンプル  ({n}件)',
        'zh': '样本内  （{n}笔交易）',
        'ko': '인샘플  ({n}건)',
        'ar': 'العينة الداخلية ({n} صفقة)',
    },
    'tab_oos_trades': {
        'en': 'Out-of-Sample  ({n} trades)',
        'pt': 'Out-of-Sample  ({n} trades)',
        'es': 'Out-of-Sample  ({n} operaciones)',
        'fr': 'Out-of-Sample  ({n} trades)',
        'de': 'Out-of-Sample  ({n} Trades)',
        'ja': 'アウトオブサンプル  ({n}件)',
        'zh': '样本外  （{n}笔交易）',
        'ko': '아웃오브샘플  ({n}건)',
        'ar': 'العينة الخارجية ({n} صفقة)',
    },
    'info_no_trades': {
        'en': 'No trades in this period.',
        'pt': 'Nenhum trade neste periodo.',
        'es': 'No hay operaciones en este periodo.',
        'fr': 'Aucun trade sur cette periode.',
        'de': 'Keine Trades in diesem Zeitraum.',
        'ja': 'この期間にトレードはありません。',
        'zh': '此期间没有交易。',
        'ko': '이 기간에는 거래가 없습니다.',
        'ar': 'لا توجد صفقات في هذه الفترة.',
    },
    'col_entry': {
        'en': 'Entry',
        'pt': 'Entrada',
        'es': 'Entrada',
        'fr': 'Entree',
        'de': 'Einstieg',
        'ja': 'エントリー',
        'zh': '进场',
        'ko': '진입',
        'ar': 'الدخول',
    },
    'col_exit': {
        'en': 'Exit',
        'pt': 'Saida',
        'es': 'Salida',
        'fr': 'Sortie',
        'de': 'Ausstieg',
        'ja': 'エグジット',
        'zh': '出场',
        'ko': '청산',
        'ar': 'الخروج',
    },
    'col_days': {
        'en': 'Days',
        'pt': 'Dias',
        'es': 'Dias',
        'fr': 'Jours',
        'de': 'Tage',
        'ja': '日数',
        'zh': '天数',
        'ko': '일수',
        'ar': 'الأيام',
    },
    'col_side': {
        'en': 'Side',
        'pt': 'Lado',
        'es': 'Lado',
        'fr': 'Sens',
        'de': 'Seite',
        'ja': 'サイド',
        'zh': '方向',
        'ko': '포지션',
        'ar': 'الجانب',
    },
    'col_return': {
        'en': 'Return',
        'pt': 'Retorno',
        'es': 'Retorno',
        'fr': 'Rendement',
        'de': 'Rendite',
        'ja': 'リターン',
        'zh': '回报',
        'ko': '수익률',
        'ar': 'العائد',
    },
    'col_maxdd_trade': {
        'en': 'MaxDD Trade',
        'pt': 'MaxDD Trade',
        'es': 'MaxDD Operacion',
        'fr': 'MaxDD Trade',
        'de': 'MaxDD Trade',
        'ja': 'トレード最大DD',
        'zh': '交易最大回撤',
        'ko': '거래 최대낙폭',
        'ar': 'أقصى تراجع للصفقة',
    },
    'side_long': {
        'en': 'LONG',
        'pt': 'LONG',
        'es': 'LONG',
        'fr': 'LONG',
        'de': 'LONG',
        'ja': 'ロング',
        'zh': '做多',
        'ko': '롱',
        'ar': 'شراء',
    },
    'side_short': {
        'en': 'SHORT',
        'pt': 'SHORT',
        'es': 'SHORT',
        'fr': 'SHORT',
        'de': 'SHORT',
        'ja': 'ショート',
        'zh': '做空',
        'ko': '숏',
        'ar': 'بيع',
    },
    'caption_trades_summary': {
        'en': '{wins}/{n} positive ({pct}%)  ·  Avg return: {avg}  ·  Avg duration: {days} days',
        'pt': '{wins}/{n} positivos ({pct}%)  ·  Ret medio: {avg}  ·  Duracao media: {days} dias',
        'es': '{wins}/{n} positivos ({pct}%)  ·  Ret. promedio: {avg}  ·  Duracion promedio: {days} dias',
        'fr': '{wins}/{n} positifs ({pct}%)  ·  Rendement moyen : {avg}  ·  Duree moyenne : {days} jours',
        'de': '{wins}/{n} positiv ({pct}%)  ·  Durchschn. Rendite: {avg}  ·  Durchschn. Dauer: {days} Tage',
        'ja': '{wins}/{n} がポジティブ ({pct}%)  ・  平均リターン: {avg}  ・  平均期間: {days}日',
        'zh': '{wins}/{n} 为正（{pct}%）  ·  平均回报：{avg}  ·  平均持续时间：{days}天',
        'ko': '{wins}/{n} 양수 ({pct}%)  ·  평균 수익률: {avg}  ·  평균 기간: {days}일',
        'ar': '{wins}/{n} إيجابي ({pct}%)  ·  العائد المتوسط: {avg}  ·  المدة المتوسطة: {days} يومًا',
    },
    'consistency_title': {
        'en': 'CONSISTENCY TESTS',
        'pt': 'TESTES DE CONSISTENCIA',
        'es': 'PRUEBAS DE CONSISTENCIA',
        'fr': 'TESTS DE COHERENCE',
        'de': 'KONSISTENZPRUFUNGEN',
        'ja': '整合性テスト',
        'zh': '一致性测试',
        'ko': '일관성 테스트',
        'ar': 'اختبارات الاتساق',
    },
    'consistency_tooltip_label': {
        'en': 'What are these tests?',
        'pt': 'O que sao estes testes?',
        'es': 'Que son estas pruebas?',
        'fr': 'Que sont ces tests ?',
        'de': 'Was sind diese Tests?',
        'ja': 'これらのテストとは？',
        'zh': '这些测试是什么？',
        'ko': '이 테스트는 무엇인가요?',
        'ar': 'ما هي هذه الاختبارات؟',
    },
    'consistency_tooltip_text': {
        'en': '1. IS/OOS overlap: Error if IS ends after OOS starts (lookahead bias).\n2. IS/OOS gap: Warning if gap is greater than 5 days.\n3. Minimum trades: Warning if IS has fewer than 5 trades or OOS fewer than 3.\n4. Extreme return: Warning if daily return exceeds 30% (corrupted data?).\n5. Lookahead bias: OOS percentiles are calculated using only IS data.',
        'pt': '1. Sobreposicao IS/OOS: Erro se IS termina depois do OOS comecar (lookahead bias).\n2. Gap IS/OOS: Aviso se o gap for maior que 5 dias.\n3. Trades minimos: Aviso se IS tiver menos de 5 trades ou OOS menos de 3.\n4. Retorno extremo: Aviso se o retorno diario exceder 30% (dados corrompidos?).\n5. Lookahead bias: percentis do OOS sao calculados usando apenas dados do IS.',
        'es': '1. Superposicion IS/OOS: Error si el IS termina despues de que empiece el OOS (sesgo de anticipacion).\n2. Brecha IS/OOS: Aviso si la brecha es mayor a 5 dias.\n3. Operaciones minimas: Aviso si el IS tiene menos de 5 operaciones o el OOS menos de 3.\n4. Retorno extremo: Aviso si el retorno diario supera el 30% (datos corruptos?).\n5. Sesgo de anticipacion: los percentiles del OOS se calculan usando solo datos del IS.',
        'fr': "1. Chevauchement IS/OOS : Erreur si l'IS se termine apres le debut de l'OOS (biais d'anticipation).\n2. Ecart IS/OOS : Avertissement si l'ecart depasse 5 jours.\n3. Trades minimum : Avertissement si l'IS a moins de 5 trades ou l'OOS moins de 3.\n4. Rendement extreme : Avertissement si le rendement quotidien depasse 30 % (donnees corrompues ?).\n5. Biais d'anticipation : les percentiles de l'OOS sont calcules en utilisant uniquement les donnees de l'IS.",
        'de': '1. IS/OOS-Uberlappung: Fehler, wenn IS nach Beginn von OOS endet (Lookahead-Bias).\n2. IS/OOS-Lucke: Warnung, wenn die Lucke grosser als 5 Tage ist.\n3. Mindestanzahl Trades: Warnung, wenn IS weniger als 5 Trades oder OOS weniger als 3 hat.\n4. Extreme Rendite: Warnung, wenn die Tagesrendite 30% ubersteigt (beschadigte Daten?).\n5. Lookahead-Bias: OOS-Perzentile werden nur anhand von IS-Daten berechnet.',
        'ja': '1. IS/OOS重複：OOS開始後にISが終了する場合エラー（先読みバイアス）。\n2. IS/OOSギャップ：ギャップが5日を超える場合警告。\n3. 最小トレード数：ISが5件未満またはOOSが3件未満の場合警告。\n4. 極端なリターン：日次リターンが30%を超える場合警告（データ破損の可能性）。\n5. 先読みバイアス：OOSのパーセンタイルはISデータのみで計算されます。',
        'zh': '1. IS/OOS重叠：若IS在OOS开始后才结束，则报错（前视偏差）。\n2. IS/OOS间隔：若间隔超过5天，则警告。\n3. 最少交易数：若IS少于5笔或OOS少于3笔交易，则警告。\n4. 极端回报：若日回报超过30%，则警告（数据是否损坏？）。\n5. 前视偏差：OOS百分位数仅使用IS数据计算。',
        'ko': '1. IS/OOS 중복: OOS 시작 후 IS가 종료되면 오류(선행 편향).\n2. IS/OOS 간격: 간격이 5일을 초과하면 경고.\n3. 최소 거래 수: IS가 5건 미만 또는 OOS가 3건 미만이면 경고.\n4. 극단적 수익률: 일일 수익률이 30%를 초과하면 경고(데이터 손상 가능성).\n5. 선행 편향: OOS 백분위수는 IS 데이터만 사용하여 계산됩니다.',
        'ar': '1. تداخل IS/OOS: خطأ إذا انتهت العينة الداخلية بعد بدء العينة الخارجية (تحيز استباقي).\n2. فجوة IS/OOS: تحذير إذا كانت الفجوة أكبر من 5 أيام.\n3. الحد الأدنى للصفقات: تحذير إذا كانت العينة الداخلية أقل من 5 صفقات أو الخارجية أقل من 3.\n4. عائد متطرف: تحذير إذا تجاوز العائد اليومي 30% (بيانات تالفة؟).\n5. التحيز الاستباقي: تُحسب مئينات العينة الخارجية باستخدام بيانات العينة الداخلية فقط.',
    },
    'issue_overlap': {
        'en': 'IS and OOS overlap! IS ends {d1}, OOS starts {d2}',
        'pt': 'IS e OOS se sobrepoem! IS termina {d1}, OOS comeca {d2}',
        'es': 'IS y OOS se superponen! IS termina {d1}, OOS comienza {d2}',
        'fr': 'IS et OOS se chevauchent ! IS se termine le {d1}, OOS commence le {d2}',
        'de': 'IS und OOS uberlappen sich! IS endet {d1}, OOS beginnt {d2}',
        'ja': 'ISとOOSが重複しています！ISは{d1}に終了、OOSは{d2}に開始',
        'zh': 'IS和OOS重叠！IS于{d1}结束，OOS于{d2}开始',
        'ko': 'IS와 OOS가 겹칩니다! IS는 {d1}에 종료, OOS는 {d2}에 시작',
        'ar': 'تتداخل العينة الداخلية والخارجية! تنتهي IS في {d1}، وتبدأ OOS في {d2}',
    },
    'warning_gap': {
        'en': '{gap}-day gap between In-Sample and Out-of-Sample (normal on weekends/holidays)',
        'pt': 'Gap de {gap} dias entre In-Sample e Out-of-Sample (normal em fins de semana/feriados)',
        'es': 'Brecha de {gap} dias entre In-Sample y Out-of-Sample (normal en fines de semana/feriados)',
        'fr': 'Ecart de {gap} jours entre In-Sample et Out-of-Sample (normal les week-ends/jours feries)',
        'de': '{gap}-Tage-Lucke zwischen In-Sample und Out-of-Sample (normal an Wochenenden/Feiertagen)',
        'ja': 'インサンプルとアウトオブサンプルの間に{gap}日のギャップ（週末・祝日は正常）',
        'zh': '样本内与样本外之间存在{gap}天的间隔（周末/假期属正常现象）',
        'ko': '인샘플과 아웃오브샘플 사이에 {gap}일 간격 (주말/공휴일에는 정상)',
        'ar': 'فجوة {gap} يومًا بين العينة الداخلية والخارجية (طبيعي في عطلات نهاية الأسبوع/الأعياد)',
    },
    'warning_few_trades_is': {
        'en': 'IS: few trades ({n}). Increase entry percentiles.',
        'pt': 'IS: poucos trades ({n}). Aumentar percentis de entrada.',
        'es': 'IS: pocas operaciones ({n}). Aumentar percentiles de entrada.',
        'fr': "IS : peu de trades ({n}). Augmenter les percentiles d'entree.",
        'de': 'IS: wenige Trades ({n}). Einstiegsperzentile erhohen.',
        'ja': 'IS：トレード数が少ない（{n}件）。エントリーパーセンタイルを増やしてください。',
        'zh': 'IS：交易数较少（{n}笔）。请提高进场百分位数。',
        'ko': 'IS: 거래 수가 적음 ({n}건). 진입 백분위수를 높이세요.',
        'ar': 'العينة الداخلية: صفقات قليلة ({n}). زد مئينات الدخول.',
    },
    'warning_few_trades_oos': {
        'en': 'OOS: few trades ({n}). Result may not be representative.',
        'pt': 'OOS: poucos trades ({n}). Resultado pode nao ser representativo.',
        'es': 'OOS: pocas operaciones ({n}). El resultado puede no ser representativo.',
        'fr': 'OOS : peu de trades ({n}). Le resultat peut ne pas etre representatif.',
        'de': 'OOS: wenige Trades ({n}). Ergebnis moglicherweise nicht reprasentativ.',
        'ja': 'OOS：トレード数が少ない（{n}件）。結果が代表的でない可能性があります。',
        'zh': 'OOS：交易数较少（{n}笔）。结果可能不具代表性。',
        'ko': 'OOS: 거래 수가 적음 ({n}건). 결과가 대표성이 없을 수 있습니다.',
        'ar': 'العينة الخارجية: صفقات قليلة ({n}). قد لا تكون النتيجة ممثلة.',
    },
    'warning_extreme_return_is': {
        'en': 'In-Sample: extreme daily return of {pct} on {date} (with open position). Check the data.',
        'pt': 'In-Sample: retorno diario extremo de {pct} em {date} (com posicao aberta). Verificar dados.',
        'es': 'In-Sample: retorno diario extremo de {pct} en {date} (con posicion abierta). Verificar los datos.',
        'fr': 'In-Sample : rendement quotidien extreme de {pct} le {date} (avec position ouverte). Verifier les donnees.',
        'de': 'In-Sample: extreme Tagesrendite von {pct} am {date} (mit offener Position). Daten uberprufen.',
        'ja': 'インサンプル：{date}に極端な日次リターン{pct}（オープンポジションあり）。データを確認してください。',
        'zh': '样本内：{date}出现极端日回报{pct}（持有未平仓位）。请检查数据。',
        'ko': '인샘플: {date}에 극단적 일일 수익률 {pct} (포지션 보유 중). 데이터를 확인하세요.',
        'ar': 'العينة الداخلية: عائد يومي متطرف بنسبة {pct} في {date} (مع مركز مفتوح). تحقق من البيانات.',
    },
    'warning_extreme_return_oos': {
        'en': 'Out-of-Sample: extreme daily return of {pct} on {date} (with open position). Check the data.',
        'pt': 'Out-of-Sample: retorno diario extremo de {pct} em {date} (com posicao aberta). Verificar dados.',
        'es': 'Out-of-Sample: retorno diario extremo de {pct} en {date} (con posicion abierta). Verificar los datos.',
        'fr': 'Out-of-Sample : rendement quotidien extreme de {pct} le {date} (avec position ouverte). Verifier les donnees.',
        'de': 'Out-of-Sample: extreme Tagesrendite von {pct} am {date} (mit offener Position). Daten uberprufen.',
        'ja': 'アウトオブサンプル：{date}に極端な日次リターン{pct}（オープンポジションあり）。データを確認してください。',
        'zh': '样本外：{date}出现极端日回报{pct}（持有未平仓位）。请检查数据。',
        'ko': '아웃오브샘플: {date}에 극단적 일일 수익률 {pct} (포지션 보유 중). 데이터를 확인하세요.',
        'ar': 'العينة الخارجية: عائد يومي متطرف بنسبة {pct} في {date} (مع مركز مفتوح). تحقق من البيانات.',
    },
    'issue_lookahead': {
        'en': 'P{eh} OOS equals IS at every point — possible lookahead bias!',
        'pt': 'P{eh} OOS igual ao IS em todos os pontos — possivel lookahead bias!',
        'es': 'P{eh} OOS igual al IS en todos los puntos — posible sesgo de anticipacion!',
        'fr': "P{eh} OOS identique a l'IS en tout point — biais d'anticipation possible !",
        'de': 'P{eh} OOS entspricht IS an jedem Punkt — moglicher Lookahead-Bias!',
        'ja': 'P{eh} OOSがすべての点でISと一致 — 先読みバイアスの可能性！',
        'zh': 'P{eh} OOS在所有点上与IS相同 — 可能存在前视偏差！',
        'ko': 'P{eh} OOS가 모든 지점에서 IS와 동일함 — 선행 편향 가능성!',
        'ar': 'P{eh} العينة الخارجية تساوي الداخلية في كل نقطة — تحيز استباقي محتمل!',
    },
    'warning_low_invested': {
        'en': 'OOS: only {pct} of time with an open position. Percentiles too extreme?',
        'pt': 'OOS: apenas {pct} do tempo com posicao. Percentis muito extremos?',
        'es': 'OOS: solo {pct} del tiempo con posicion. Percentiles demasiado extremos?',
        'fr': 'OOS : seulement {pct} du temps avec une position ouverte. Percentiles trop extremes ?',
        'de': 'OOS: nur {pct} der Zeit mit offener Position. Perzentile zu extrem?',
        'ja': 'OOS：ポジションを保有している時間はわずか{pct}です。パーセンタイルが極端すぎますか？',
        'zh': 'OOS：仅{pct}的时间持有仓位。百分位数是否过于极端？',
        'ko': 'OOS: 포지션 보유 시간이 {pct}에 불과함. 백분위수가 너무 극단적인가요?',
        'ar': 'العينة الخارجية: فقط {pct} من الوقت بمركز مفتوح. هل المئينات متطرفة جدًا؟',
    },
    'metric_checks_ok': {
        'en': 'Checks OK',
        'pt': 'Verificacoes OK',
        'es': 'Verificaciones OK',
        'fr': 'Verifications OK',
        'de': 'Prufungen OK',
        'ja': 'チェックOK',
        'zh': '检查通过',
        'ko': '확인 완료',
        'ar': 'الفحوصات سليمة',
    },
    'metric_warnings': {
        'en': 'Warnings',
        'pt': 'Avisos',
        'es': 'Avisos',
        'fr': 'Avertissements',
        'de': 'Warnungen',
        'ja': '警告',
        'zh': '警告',
        'ko': '경고',
        'ar': 'تحذيرات',
    },
    'metric_errors': {
        'en': 'Errors',
        'pt': 'Erros',
        'es': 'Errores',
        'fr': 'Erreurs',
        'de': 'Fehler',
        'ja': 'エラー',
        'zh': '错误',
        'ko': '오류',
        'ar': 'أخطاء',
    },
    'label_error_prefix': {
        'en': 'ERROR: {msg}',
        'pt': 'ERRO: {msg}',
        'es': 'ERROR: {msg}',
        'fr': 'ERREUR : {msg}',
        'de': 'FEHLER: {msg}',
        'ja': 'エラー：{msg}',
        'zh': '错误：{msg}',
        'ko': '오류: {msg}',
        'ar': 'خطأ: {msg}',
    },
    'label_warning_prefix': {
        'en': 'Warning: {msg}',
        'pt': 'Aviso: {msg}',
        'es': 'Aviso: {msg}',
        'fr': 'Avertissement : {msg}',
        'de': 'Warnung: {msg}',
        'ja': '警告：{msg}',
        'zh': '警告：{msg}',
        'ko': '경고: {msg}',
        'ar': 'تحذير: {msg}',
    },
    'success_consistency': {
        'en': 'All consistency tests passed.',
        'pt': 'Todos os testes de consistencia passaram.',
        'es': 'Todas las pruebas de consistencia pasaron.',
        'fr': 'Tous les tests de coherence ont reussi.',
        'de': 'Alle Konsistenzprufungen wurden bestanden.',
        'ja': 'すべての整合性テストに合格しました。',
        'zh': '所有一致性测试均已通过。',
        'ko': '모든 일관성 테스트를 통과했습니다.',
        'ar': 'نجحت جميع اختبارات الاتساق.',
    },
    'error_ticker_not_found_short': {
        'en': "Ticker '{ticker}' not found.",
        'pt': "Ticker '{ticker}' nao encontrado.",
        'es': "Ticker '{ticker}' no encontrado.",
        'fr': "Symbole '{ticker}' introuvable.",
        'de': "Ticker '{ticker}' nicht gefunden.",
        'ja': "ティッカー '{ticker}' が見つかりません。",
        'zh': "未找到代码 '{ticker}'。",
        'ko': "티커 '{ticker}'를 찾을 수 없습니다.",
        'ar': "الرمز '{ticker}' غير موجود.",
    },
    'error_insufficient_years': {
        'en': 'Insufficient data ({years} years). Walk-forward requires >5 years.',
        'pt': 'Dados insuficientes ({anos} anos). Walk-forward exige >5 anos.',
        'es': 'Datos insuficientes ({anos} anos). Walk-forward requiere >5 anos.',
        'fr': 'Donnees insuffisantes ({anos} ans). Le walk-forward necessite >5 ans.',
        'de': 'Unzureichende Daten ({anos} Jahre). Walk-Forward erfordert >5 Jahre.',
        'ja': 'データが不足しています（{anos}年）。ウォークフォワードには5年以上必要です。',
        'zh': '数据不足（{anos}年）。前向滚动分析需要超过5年数据。',
        'ko': '데이터 부족 ({anos}년). 워크포워드는 5년 이상이 필요합니다.',
        'ar': 'بيانات غير كافية ({anos} سنوات). يتطلب Walk-Forward أكثر من 5 سنوات.',
    },
    'progress_starting': {
        'en': 'Starting walk-forward optimizer (576 combos x windows)...',
        'pt': 'Iniciando walk-forward optimizer (576 combos x janelas)...',
        'es': 'Iniciando optimizador walk-forward (576 combinaciones x ventanas)...',
        'fr': "Demarrage de l'optimiseur walk-forward (576 combinaisons x fenetres)...",
        'de': 'Starte Walk-Forward-Optimierer (576 Kombinationen x Fenster)...',
        'ja': 'ウォークフォワードオプティマイザを開始しています（576通り×ウィンドウ）...',
        'zh': '正在启动前向滚动优化器（576种组合×窗口）...',
        'ko': '워크포워드 옵티마이저 시작 중 (576개 조합 x 윈도우)...',
        'ar': 'بدء محسّن Walk-Forward (576 توليفة × نوافذ)...',
    },
    'progress_running': {
        'en': 'Optimizing... {done}/{total} combinations ({pct}%)',
        'pt': 'Otimizando... {done}/{total} combinacoes ({pct}%)',
        'es': 'Optimizando... {done}/{total} combinaciones ({pct}%)',
        'fr': 'Optimisation... {done}/{total} combinaisons ({pct}%)',
        'de': 'Optimiere... {done}/{total} Kombinationen ({pct}%)',
        'ja': '最適化中... {done}/{total} 組み合わせ ({pct}%)',
        'zh': '正在优化... {done}/{total} 种组合 ({pct}%)',
        'ko': '최적화 중... {done}/{total} 조합 ({pct}%)',
        'ar': 'التحسين... {done}/{total} توليفة ({pct}%)',
    },
    'progress_done': {
        'en': 'Done!',
        'pt': 'Concluido!',
        'es': 'Completado!',
        'fr': 'Termine !',
        'de': 'Fertig!',
        'ja': '完了！',
        'zh': '完成！',
        'ko': '완료!',
        'ar': 'اكتمل!',
    },
    'warning_insufficient_wf': {
        'en': 'Insufficient data for walk-forward.',
        'pt': 'Dados insuficientes para walk-forward.',
        'es': 'Datos insuficientes para walk-forward.',
        'fr': 'Donnees insuffisantes pour le walk-forward.',
        'de': 'Unzureichende Daten fur Walk-Forward.',
        'ja': 'ウォークフォワードに十分なデータがありません。',
        'zh': '前向滚动分析数据不足。',
        'ko': '워크포워드를 위한 데이터가 부족합니다.',
        'ar': 'بيانات غير كافية لـ Walk-Forward.',
    },
    'card_optimizer': {
        'en': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} windows &nbsp;|&nbsp; 576 combos (8x8 entry, 9 exits)',
        'pt': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} janelas &nbsp;|&nbsp; 576 combos (8x8 entrada, 9 saidas)',
        'es': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} ventanas &nbsp;|&nbsp; 576 combinaciones (8x8 entrada, 9 salidas)',
        'fr': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} fenetres &nbsp;|&nbsp; 576 combinaisons (8x8 entree, 9 sorties)',
        'de': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} Fenster &nbsp;|&nbsp; 576 Kombinationen (8x8 Einstieg, 9 Ausstiege)',
        'ja': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} ウィンドウ &nbsp;|&nbsp; 576通り (8x8エントリー、9エグジット)',
        'zh': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} 个窗口 &nbsp;|&nbsp; 576种组合 (8x8进场, 9种出场)',
        'ko': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} 윈도우 &nbsp;|&nbsp; 576개 조합 (8x8 진입, 9개 청산)',
        'ar': 'OPTIMIZER &nbsp;|&nbsp; {ticker} &nbsp;|&nbsp; Walk-Forward 4yr IS / 12m OOS &nbsp;|&nbsp; {n} نافذة &nbsp;|&nbsp; 576 توليفة (8×8 دخول، 9 خروج)',
    },
    'help_optimizer': {
        'en': 'Runs a walk-forward test: for each 4-year In-Sample window, tests all entry/exit percentile combinations of the indicator and measures the result in the next 12 months Out-of-Sample, rolling forward 6 months at a time. Ranks the 576 combos by 2 criteria: (1) highest median Sharpe across OOS windows; (2) lowest median Drawdown among combos with positive median return. Click a bar in the window chart below to inspect the OOS NAV and indicator for that period.',
        'pt': 'Roda um teste walk-forward: para cada janela de 4 anos In-Sample, testa todas as combinacoes de percentis de entrada/saida do indicador e mede o resultado nos 12 meses seguintes Out-of-Sample, avancando 6 em 6 meses. Ranqueia os 576 combos por 2 criterios: (1) maior Sharpe mediano nas janelas OOS; (2) menor Drawdown mediano entre os combos com retorno mediano positivo. Clique numa barra do grafico de janelas abaixo para ver a cota e o indicador daquele periodo.',
        'es': 'Ejecuta una prueba walk-forward: para cada ventana de 4 anos In-Sample, prueba todas las combinaciones de percentiles de entrada/salida del indicador y mide el resultado en los siguientes 12 meses Out-of-Sample, avanzando 6 meses a la vez. Clasifica las 576 combinaciones por 2 criterios: (1) mayor Sharpe mediano en las ventanas OOS; (2) menor Drawdown mediano entre las combinaciones con retorno mediano positivo. Haga clic en una barra del grafico de ventanas abajo para ver el NAV y el indicador OOS de ese periodo.',
        'fr': "Execute un test walk-forward : pour chaque fenetre In-Sample de 4 ans, teste toutes les combinaisons de percentiles d'entree/sortie de l'indicateur et mesure le resultat sur les 12 mois suivants Out-of-Sample, en avancant de 6 mois a la fois. Classe les 576 combinaisons selon 2 criteres : (1) le Sharpe median le plus eleve sur les fenetres OOS ; (2) le Drawdown median le plus faible parmi les combinaisons a rendement median positif. Cliquez sur une barre du graphique des fenetres ci-dessous pour voir la VL et l'indicateur OOS de cette periode.",
        'de': 'Fuhrt einen Walk-Forward-Test durch: Fur jedes 4-jaehrige In-Sample-Fenster werden alle Eintritts-/Austritts-Perzentil-Kombinationen des Indikators getestet und das Ergebnis in den folgenden 12 Monaten Out-of-Sample gemessen, wobei jeweils 6 Monate vorgeruckt wird. Die 576 Kombinationen werden nach 2 Kriterien eingestuft: (1) hoechster Median-Sharpe ueber die OOS-Fenster; (2) niedrigster Median-Drawdown unter den Kombinationen mit positivem Median-Ertrag. Klicken Sie auf einen Balken im Fenster-Diagramm unten, um den OOS-NAV und den Indikator fur diesen Zeitraum zu sehen.',
        'ja': '各4年間のIn-Sampleウィンドウについて、指標のすべてのエントリー/エグジットパーセンタイル組み合わせをテストし、その後の12か月間のOut-of-Sample結果を6か月ごとにローリングして測定するウォークフォワードテストを実行します。576通りの組み合わせを2つの基準でランク付けします: (1) OOSウィンドウ全体での中央値Sharpeが最も高い、(2) 中央値リターンが正の組み合わせの中で中央値Drawdownが最も低い。下のウィンドウチャートのバーをクリックすると、その期間のOOS NAVと指標を確認できます。',
        'zh': '运行一个滚动前进测试：对每个4年的样本内(In-Sample)窗口，测试指标的所有进场/出场百分位组合，并测量随后12个月样本外(Out-of-Sample)的结果，每次滚动前进6个月。按2个标准对576种组合进行排名：(1) 在OOS窗口中具有最高的中位数Sharpe；(2) 在中位数收益为正的组合中具有最低的中位数回撤。点击下方窗口图表中的柱形可查看该时段的OOS净值和指标。',
        'ko': '각 4년 In-Sample 윈도우에 대해 지표의 모든 진입/청산 백분위 조합을 테스트하고, 6개월씩 롤링하며 이후 12개월 Out-of-Sample 결과를 측정하는 워크포워드 테스트를 실행합니다. 576개 조합을 2가지 기준으로 순위를 매깁니다: (1) OOS 윈도우 전체에서 가장 높은 중간값 샤프 비율; (2) 중간값 수익률이 양수인 조합 중 가장 낮은 중간값 드로다운. 아래 윈도우 차트의 막대를 클릭하면 해당 기간의 OOS NAV와 지표를 확인할 수 있습니다.',
        'ar': 'يشغل اختبار walk-forward: لكل نافذة In-Sample مدتها 4 سنوات، يختبر جميع تركيبات النسب المئوية للدخول/الخروج للمؤشر ويقيس النتيجة في الأشهر الـ12 التالية Out-of-Sample، بالتقدم 6 أشهر في كل مرة. يصنف 576 تركيبة وفق معيارين: (1) أعلى متوسط Sharpe عبر نوافذ OOS؛ (2) أدنى متوسط Drawdown بين التركيبات ذات العائد المتوسط الإيجابي. انقر على شريط في مخطط النوافذ أدناه لمعاينة NAV والمؤشر OOS لتلك الفترة.',
    },
    'window_detail_title': {
        'en': 'Window {window} — OOS detail',
        'pt': 'Janela {window} — detalhe OOS',
        'es': 'Ventana {window} — detalle OOS',
        'fr': 'Fenetre {window} — detail OOS',
        'de': 'Fenster {window} — OOS-Detail',
        'ja': 'ウィンドウ {window} — OOS詳細',
        'zh': '窗口 {window} — OOS详情',
        'ko': '윈도우 {window} — OOS 상세',
        'ar': 'النافذة {window} — تفاصيل OOS',
    },
    'mini_chart_equity_title': {
        'en': 'OOS NAV (base 100)',
        'pt': 'Cota OOS (base 100)',
        'es': 'NAV OOS (base 100)',
        'fr': 'VL OOS (base 100)',
        'de': 'OOS-NAV (Basis 100)',
        'ja': 'OOS NAV（基準100）',
        'zh': 'OOS净值（基数100）',
        'ko': 'OOS NAV (기준 100)',
        'ar': 'NAV خارج العينة (الأساس 100)',
    },
    'mini_chart_indicator_title': {
        'en': 'Risk Appetite — entry/exit levels',
        'pt': 'Risk Appetite — niveis de entrada/saida',
        'es': 'Risk Appetite — niveles de entrada/salida',
        'fr': "Risk Appetite — niveaux d'entree/sortie",
        'de': 'Risk Appetite — Ein-/Ausstiegsniveaus',
        'ja': 'Risk Appetite — エントリー/エグジットレベル',
        'zh': 'Risk Appetite — 进出场水平',
        'ko': 'Risk Appetite — 진입/청산 레벨',
        'ar': 'Risk Appetite — مستويات الدخول/الخروج',
    },
    'mini_chart_entry_short': {
        'en': 'Short entry',
        'pt': 'Entrada short',
        'es': 'Entrada short',
        'fr': 'Entree short',
        'de': 'Short-Einstieg',
        'ja': 'ショートエントリー',
        'zh': '做空进场',
        'ko': '숏 진입',
        'ar': 'دخول بيع (Short)',
    },
    'mini_chart_entry_long': {
        'en': 'Long entry',
        'pt': 'Entrada long',
        'es': 'Entrada long',
        'fr': 'Entree long',
        'de': 'Long-Einstieg',
        'ja': 'ロングエントリー',
        'zh': '做多进场',
        'ko': '롱 진입',
        'ar': 'دخول شراء (Long)',
    },
    'mini_chart_exit': {
        'en': 'Exit',
        'pt': 'Saida',
        'es': 'Salida',
        'fr': 'Sortie',
        'de': 'Ausstieg',
        'ja': 'エグジット',
        'zh': '出场',
        'ko': '청산',
        'ar': 'خروج',
    },
    'caption_click_bar_detail': {
        'en': 'Click a bar below to see the OOS NAV and the indicator with entry/exit levels for that window.',
        'pt': 'Clique numa barra abaixo para ver a cota OOS e o indicador com os niveis de entrada/saida daquela janela.',
        'es': 'Haga clic en una barra abajo para ver el NAV OOS y el indicador con los niveles de entrada/salida de esa ventana.',
        'fr': "Cliquez sur une barre ci-dessous pour voir la VL OOS et l'indicateur avec les niveaux d'entree/sortie de cette fenetre.",
        'de': 'Klicken Sie unten auf einen Balken, um den OOS-NAV und den Indikator mit den Ein-/Ausstiegsniveaus fur dieses Fenster zu sehen.',
        'ja': '下のバーをクリックすると、そのウィンドウのOOS NAVとエントリー/エグジットレベル付きの指標を確認できます。',
        'zh': '点击下方的柱形可查看该窗口的OOS净值以及带有进出场水平的指标。',
        'ko': '아래 막대를 클릭하면 해당 윈도우의 OOS NAV와 진입/청산 레벨이 표시된 지표를 확인할 수 있습니다.',
        'ar': 'انقر على شريط أدناه لمعاينة NAV خارج العينة والمؤشر مع مستويات الدخول/الخروج لتلك النافذة.',
    },
    'button_view_chart': {
        'en': '👁 View',
        'pt': '👁 Ver',
        'es': '👁 Ver',
        'fr': '👁 Voir',
        'de': '👁 Ansehen',
        'ja': '👁 表示',
        'zh': '👁 查看',
        'ko': '👁 보기',
        'ar': '👁 عرض',
    },
    'viewing_rank_label': {
        'en': 'Showing detail for option #{rank}',
        'pt': 'Mostrando detalhe da opcao #{rank}',
        'es': 'Mostrando detalle de la opcion #{rank}',
        'fr': "Affichage du detail de l'option #{rank}",
        'de': 'Zeige Detail fur Option #{rank}',
        'ja': 'オプション #{rank} の詳細を表示中',
        'zh': '正在显示选项 #{rank} 的详情',
        'ko': '옵션 #{rank}의 상세 정보 표시 중',
        'ar': 'عرض تفاصيل الخيار #{rank}',
    },
    'criterio1_title': {
        'en': '🏆 CRITERION 1 — Maximum Sharpe (OOS median)',
        'pt': '🏆 CRITERIO 1 — Maximo Sharpe (mediana OOS)',
        'es': '🏆 CRITERIO 1 — Sharpe Maximo (mediana OOS)',
        'fr': '🏆 CRITERE 1 — Sharpe Maximum (mediane OOS)',
        'de': '🏆 KRITERIUM 1 — Maximaler Sharpe (OOS-Median)',
        'ja': '🏆 基準1 — 最大シャープレシオ（OOS中央値）',
        'zh': '🏆 标准1 — 最大夏普比率（OOS中位数）',
        'ko': '🏆 기준 1 — 최대 샤프 비율(OOS 중앙값)',
        'ar': '🏆 المعيار 1 — أقصى نسبة شارب (متوسط العينة الخارجية)',
    },
    'caption_trimmed_core': {
        'en': 'Trimmed core: median / min / max of the central 60% of windows (excluding the 20% extremes on each side)',
        'pt': 'Nucleo aparado: mediana / min / max dos 60% centrais das janelas (excluindo 20% extremos de cada lado)',
        'es': 'Nucleo recortado: mediana / min / max del 60% central de las ventanas (excluyendo el 20% extremo de cada lado)',
        'fr': 'Noyau elague : mediane / min / max des 60% centraux des fenetres (en excluant les 20% extremes de chaque cote)',
        'de': 'Getrimmter Kern: Median / Min / Max der zentralen 60% der Fenster (ohne die jeweils 20% Extreme an jeder Seite)',
        'ja': 'トリム済みコア：ウィンドウの中央60%の中央値・最小値・最大値（両端20%の極値を除外）',
        'zh': '修剪核心：窗口中心60%的中位数/最小值/最大值（排除两侧各20%的极端值）',
        'ko': '트리밍된 핵심: 윈도우 중심 60%의 중앙값/최소값/최대값(양쪽 20% 극값 제외)',
        'ar': 'النواة المشذبة: الوسيط / الأدنى / الأعلى لـ 60% الوسطى من النوافذ (باستثناء 20% المتطرفة من كل جانب)',
    },
    'row_rank': {
        'en': '#{rank}',
        'pt': '#{rank}',
        'es': '#{rank}',
        'fr': '#{rank}',
        'de': '#{rank}',
        'ja': '#{rank}',
        'zh': '#{rank}',
        'ko': '#{rank}',
        'ar': '#{rank}',
    },
    'row_entry': {
        'en': 'Entry: P{eh}/P{el}',
        'pt': 'Entrada: P{eh}/P{el}',
        'es': 'Entrada: P{eh}/P{el}',
        'fr': 'Entree : P{eh}/P{el}',
        'de': 'Einstieg: P{eh}/P{el}',
        'ja': 'エントリー: P{eh}/P{el}',
        'zh': '进场：P{eh}/P{el}',
        'ko': '진입: P{eh}/P{el}',
        'ar': 'الدخول: P{eh}/P{el}',
    },
    'row_exit': {
        'en': 'Exit: P{ex}',
        'pt': 'Saida: P{ex}',
        'es': 'Salida: P{ex}',
        'fr': 'Sortie : P{ex}',
        'de': 'Ausstieg: P{ex}',
        'ja': 'エグジット: P{ex}',
        'zh': '出场：P{ex}',
        'ko': '청산: P{ex}',
        'ar': 'الخروج: P{ex}',
    },
    'row_sharpe_median': {
        'en': 'Sharpe median: {v}',
        'pt': 'Sharpe mediana: {v}',
        'es': 'Sharpe mediana: {v}',
        'fr': 'Sharpe median : {v}',
        'de': 'Sharpe-Median: {v}',
        'ja': 'シャープ中央値: {v}',
        'zh': '夏普中位数：{v}',
        'ko': '샤프 중앙값: {v}',
        'ar': 'متوسط شارب: {v}',
    },
    'row_core60': {
        'en': '60% core: {med} [{min} / {max}]',
        'pt': 'Nucleo 60%: {med} [{min} / {max}]',
        'es': 'Nucleo 60%: {med} [{min} / {max}]',
        'fr': 'Noyau 60% : {med} [{min} / {max}]',
        'de': '60%-Kern: {med} [{min} / {max}]',
        'ja': '60%コア: {med} [{min} / {max}]',
        'zh': '60%核心：{med} [{min} / {max}]',
        'ko': '60% 핵심: {med} [{min} / {max}]',
        'ar': 'نواة 60%: {med} [{min} / {max}]',
    },
    'row_ret': {
        'en': 'Ret: {v}',
        'pt': 'Ret: {v}',
        'es': 'Ret: {v}',
        'fr': 'Rend : {v}',
        'de': 'Rendite: {v}',
        'ja': 'リターン: {v}',
        'zh': '回报：{v}',
        'ko': '수익률: {v}',
        'ar': 'العائد: {v}',
    },
    'row_dd': {
        'en': 'DD: {v}',
        'pt': 'DD: {v}',
        'es': 'DD: {v}',
        'fr': 'DD : {v}',
        'de': 'DD: {v}',
        'ja': 'DD: {v}',
        'zh': 'DD：{v}',
        'ko': 'DD: {v}',
        'ar': 'DD: {v}',
    },
    'row_win': {
        'en': 'Win: {v}',
        'pt': 'Win: {v}',
        'es': 'Win: {v}',
        'fr': 'Win : {v}',
        'de': 'Win: {v}',
        'ja': '勝率: {v}',
        'zh': '胜率：{v}',
        'ko': '승률: {v}',
        'ar': 'الفوز: {v}',
    },
    'button_use': {
        'en': 'Use',
        'pt': 'Usar',
        'es': 'Usar',
        'fr': 'Utiliser',
        'de': 'Verwenden',
        'ja': '使用',
        'zh': '使用',
        'ko': '사용',
        'ar': 'استخدام',
    },
    'chart_title_sharpe_wf': {
        'en': '#{rank} Walk-Forward OOS Sharpe — P{eh}/P{el} exit P{ex}',
        'pt': '#{rank} Walk-Forward OOS Sharpe — P{eh}/P{el} saida P{ex}',
        'es': '#{rank} Walk-Forward OOS Sharpe — P{eh}/P{el} salida P{ex}',
        'fr': '#{rank} Walk-Forward OOS Sharpe — P{eh}/P{el} sortie P{ex}',
        'de': '#{rank} Walk-Forward OOS Sharpe — P{eh}/P{el} Ausstieg P{ex}',
        'ja': '#{rank} ウォークフォワード OOS シャープ — P{eh}/P{el} エグジットP{ex}',
        'zh': '#{rank} 前向滚动 OOS 夏普 — P{eh}/P{el} 出场P{ex}',
        'ko': '#{rank} 워크포워드 OOS 샤프 — P{eh}/P{el} 청산 P{ex}',
        'ar': '#{rank} Walk-Forward OOS Sharpe — P{eh}/P{el} خروج P{ex}',
    },
    'criterio2_title': {
        'en': '🛡 CRITERION 2 — Minimum Drawdown (median return > 0)',
        'pt': '🛡 CRITERIO 2 — Minimo Drawdown (retorno mediana > 0)',
        'es': '🛡 CRITERIO 2 — Drawdown Minimo (retorno mediana > 0)',
        'fr': '🛡 CRITERE 2 — Drawdown Minimum (rendement median > 0)',
        'de': '🛡 KRITERIUM 2 — Minimaler Drawdown (Median-Rendite > 0)',
        'ja': '🛡 基準2 — 最小ドローダウン（中央値リターン > 0）',
        'zh': '🛡 标准2 — 最小回撤（中位数回报 > 0）',
        'ko': '🛡 기준 2 — 최소 낙폭(중앙값 수익률 > 0)',
        'ar': '🛡 المعيار 2 — أقل تراجع (الوسيط الموجب للعائد)',
    },
    'info_no_positive_combo': {
        'en': 'No combo with positive median return. Try another asset or period.',
        'pt': 'Nenhum combo com retorno mediana positivo. Tente outro ativo ou periodo.',
        'es': 'Ninguna combinacion con retorno mediana positivo. Pruebe otro activo o periodo.',
        'fr': 'Aucune combinaison avec un rendement median positif. Essayez un autre actif ou une autre periode.',
        'de': 'Keine Kombination mit positiver Median-Rendite. Versuchen Sie einen anderen Basiswert oder Zeitraum.',
        'ja': '中央値リターンが正の組み合わせはありません。別の資産または期間をお試しください。',
        'zh': '没有中位数回报为正的组合。请尝试其他资产或期间。',
        'ko': '중앙값 수익률이 양수인 조합이 없습니다. 다른 자산이나 기간을 시도하세요.',
        'ar': 'لا توجد توليفة بعائد وسيط موجب. حاول أصلًا أو فترة أخرى.',
    },
    'row_dd_median': {
        'en': 'DD median: {v}',
        'pt': 'DD mediana: {v}',
        'es': 'DD mediana: {v}',
        'fr': 'DD median : {v}',
        'de': 'DD-Median: {v}',
        'ja': 'DD中央値: {v}',
        'zh': 'DD中位数：{v}',
        'ko': 'DD 중앙값: {v}',
        'ar': 'وسيط DD: {v}',
    },
    'chart_title_dd_wf': {
        'en': '#{rank} Walk-Forward OOS MaxDD — P{eh}/P{el} exit P{ex}',
        'pt': '#{rank} Walk-Forward OOS MaxDD — P{eh}/P{el} saida P{ex}',
        'es': '#{rank} Walk-Forward OOS MaxDD — P{eh}/P{el} salida P{ex}',
        'fr': '#{rank} Walk-Forward OOS MaxDD — P{eh}/P{el} sortie P{ex}',
        'de': '#{rank} Walk-Forward OOS MaxDD — P{eh}/P{el} Ausstieg P{ex}',
        'ja': '#{rank} ウォークフォワード OOS 最大DD — P{eh}/P{el} エグジットP{ex}',
        'zh': '#{rank} 前向滚动 OOS 最大DD — P{eh}/P{el} 出场P{ex}',
        'ko': '#{rank} 워크포워드 OOS 최대DD — P{eh}/P{el} 청산 P{ex}',
        'ar': '#{rank} Walk-Forward OOS MaxDD — P{eh}/P{el} خروج P{ex}',
    },
    'caption_click_use': {
        'en': "Click 'Use' to apply the percentiles to the Backtest and run the full result.",
        'pt': "Clique 'Usar' para aplicar os percentis no Backtest e rodar o resultado completo.",
        'es': "Haga clic en 'Usar' para aplicar los percentiles al Backtest y ejecutar el resultado completo.",
        'fr': "Cliquez sur 'Utiliser' pour appliquer les percentiles au Backtest et obtenir le resultat complet.",
        'de': "Klicken Sie auf 'Verwenden', um die Perzentile auf den Backtest anzuwenden und das vollstandige Ergebnis auszufuhren.",
        'ja': '「使用」をクリックしてパーセンタイルをバックテストに適用し、完全な結果を実行します。',
        'zh': '点击「使用」将百分位数应用于回测并运行完整结果。',
        'ko': "'사용'을 클릭하여 백분위수를 백테스트에 적용하고 전체 결과를 실행하세요.",
        'ar': "انقر على 'استخدام' لتطبيق المئينات على الاختبار الخلفي وتشغيل النتيجة الكاملة.",
    },
    'instructions_title': {
        'en': '▶ INSTRUCTIONS',
        'pt': '▶ INSTRUCOES',
        'es': '▶ INSTRUCCIONES',
        'fr': '▶ INSTRUCTIONS',
        'de': '▶ ANLEITUNG',
        'ja': '▶ 使い方',
        'zh': '▶ 使用说明',
        'ko': '▶ 사용 방법',
        'ar': '▶ التعليمات',
    },
    'instructions_1': {
        'en': '1. Select the asset and configure the percentiles in the sidebar',
        'pt': '1. Selecione o ativo e configure os percentis na barra lateral',
        'es': '1. Seleccione el activo y configure los percentiles en la barra lateral',
        'fr': "1. Selectionnez l'actif et configurez les percentiles dans la barre laterale",
        'de': '1. Wahlen Sie den Basiswert und konfigurieren Sie die Perzentile in der Seitenleiste',
        'ja': '1. サイドバーで資産を選択し、パーセンタイルを設定します',
        'zh': '1. 在侧边栏选择资产并配置百分位数',
        'ko': '1. 사이드바에서 자산을 선택하고 백분위수를 설정하세요',
        'ar': '1. حدد الأصل وقم بضبط المئينات في الشريط الجانبي',
    },
    'instructions_2': {
        'en': '2. Click <b style="color:#FF7700">▶ RUN BACKTEST</b> for the full IS+OOS backtest',
        'pt': '2. Clique <b style="color:#FF7700">▶ RODAR BACKTEST</b> para o backtest completo IS+OOS',
        'es': '2. Haga clic en <b style="color:#FF7700">▶ EJECUTAR BACKTEST</b> para el backtest completo IS+OOS',
        'fr': '2. Cliquez sur <b style="color:#FF7700">▶ LANCER LE BACKTEST</b> pour le backtest complet IS+OOS',
        'de': '2. Klicken Sie auf <b style="color:#FF7700">▶ BACKTEST STARTEN</b> fur den vollstandigen IS+OOS-Backtest',
        'ja': '2. <b style="color:#FF7700">▶ バックテスト実行</b>をクリックしてIS+OOSの完全なバックテストを行います',
        'zh': '2. 点击<b style="color:#FF7700">▶ 运行回测</b>以执行完整的IS+OOS回测',
        'ko': '2. <b style="color:#FF7700">▶ 백테스트 실행</b>을 클릭하여 전체 IS+OOS 백테스트를 실행하세요',
        'ar': '2. انقر على <b style="color:#FF7700">▶ تشغيل الاختبار الخلفي</b> للاختبار الكامل IS+OOS',
    },
    'instructions_3': {
        'en': '3. Or click <b style="color:#FF7700">🔍 OPTIMIZE</b> for the walk-forward optimizer',
        'pt': '3. Ou clique <b style="color:#FF7700">🔍 OTIMIZAR</b> para o walk-forward optimizer',
        'es': '3. O haga clic en <b style="color:#FF7700">🔍 OPTIMIZAR</b> para el optimizador walk-forward',
        'fr': '3. Ou cliquez sur <b style="color:#FF7700">🔍 OPTIMISER</b> pour l\'optimiseur walk-forward',
        'de': '3. Oder klicken Sie auf <b style="color:#FF7700">🔍 OPTIMIEREN</b> fur den Walk-Forward-Optimierer',
        'ja': '3. または<b style="color:#FF7700">🔍 最適化</b>をクリックしてウォークフォワードオプティマイザを実行します',
        'zh': '3. 或点击<b style="color:#FF7700">🔍 优化</b>以运行前向滚动优化器',
        'ko': '3. 또는 <b style="color:#FF7700">🔍 최적화</b>를 클릭하여 워크포워드 옵티마이저를 실행하세요',
        'ar': '3. أو انقر على <b style="color:#FF7700">🔍 تحسين</b> لمحسّن Walk-Forward',
    },
    'instructions_4': {
        'en': '└ 576 combos (8x8 entry, 9 exits) · 4yr IS / 12m OOS windows',
        'pt': '└ 576 combos (8x8 entrada, 9 saidas) · Janelas 4yr IS / 12m OOS',
        'es': '└ 576 combinaciones (8x8 entrada, 9 salidas) · Ventanas 4yr IS / 12m OOS',
        'fr': '└ 576 combinaisons (8x8 entree, 9 sorties) · Fenetres 4yr IS / 12m OOS',
        'de': '└ 576 Kombinationen (8x8 Einstieg, 9 Ausstiege) · 4 Jahre IS / 12 Monate OOS Fenster',
        'ja': '└ 576通り（8x8エントリー、9エグジット） · 4年IS／12ヶ月OOSウィンドウ',
        'zh': '└ 576种组合（8x8进场，9种出场） · 4年IS / 12个月OOS窗口',
        'ko': '└ 576개 조합(8x8 진입, 9개 청산) · 4년 IS / 12개월 OOS 윈도우',
        'ar': '└ 576 توليفة (8×8 دخول، 9 خروج) · نوافذ 4 سنوات IS / 12 شهرًا OOS',
    },
    'instructions_5': {
        'en': '└ Criteria: max Sharpe and min DD · Click Use to apply',
        'pt': '└ Criterios: Sharpe max e DD minimo · Clique Usar para aplicar',
        'es': '└ Criterios: Sharpe maximo y DD minimo · Haga clic en Usar para aplicar',
        'fr': '└ Criteres : Sharpe max et DD min · Cliquez sur Utiliser pour appliquer',
        'de': '└ Kriterien: max. Sharpe und min. DD · Klicken Sie auf Verwenden, um anzuwenden',
        'ja': '└ 基準：最大シャープレシオと最小DD · 「使用」をクリックして適用',
        'zh': '└ 标准：最大夏普比率和最小DD · 点击「使用」以应用',
        'ko': '└ 기준: 최대 샤프 및 최소 DD · 적용하려면 사용 클릭',
        'ar': '└ المعايير: أقصى شارب وأقل DD · انقر على استخدام للتطبيق',
    },
    'instructions_footer': {
        'en': 'Master Quota: CDI as base + asset P&amp;L added on top via derivatives',
        'pt': 'Cota Master: CDI na base + P&amp;L do ativo adicionado por cima via derivativos',
        'es': 'Cuota Master: CDI como base + P&amp;L del activo agregado por encima via derivados',
        'fr': "Part Master : CDI en base + P&amp;L de l'actif ajoute par-dessus via des derives",
        'de': 'Master-Quote: CDI als Basis + Asset-P&amp;L oben drauf via Derivate',
        'ja': 'マスタークオータ：CDIをベースに、デリバティブで資産のP&amp;Lを上乗せ',
        'zh': '主份额：以CDI为基础 + 通过衍生品叠加资产盈亏',
        'ko': '마스터 쿼터: CDI를 기준으로 + 파생상품을 통해 자산 손익을 추가',
        'ar': 'الحصة الرئيسية: CDI كقاعدة + ربح وخسارة الأصل المضاف فوقها عبر المشتقات',
    },
}

def t(_key, **kwargs):
    _entry = TR.get(_key, {})
    _lang = st.session_state.get("lang", "en")
    _s = _entry.get(_lang) or _entry.get("en") or _key
    return _s.format(**kwargs) if kwargs else _s

# Language selector — placed early so every t() call below sees the
# current language on this run (Streamlit reruns top-to-bottom).
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"
_LANG_CODES = list(LANGUAGES.keys())
_LANG_NAMES = list(LANGUAGES.values())
_lang_idx = _LANG_CODES.index(st.session_state["lang"])
_lang_choice = st.sidebar.selectbox(
    "\U0001f310 " + t("language_label"), options=_LANG_NAMES, index=_lang_idx, key="_lang_select_widget",
)
st.session_state["lang"] = _LANG_CODES[_LANG_NAMES.index(_lang_choice)]

# Plotly Bloomberg template
BBG_LAYOUT = dict(
    paper_bgcolor="#000000",
    plot_bgcolor="#050505",
    font=dict(color="#C0C0C0", family="Courier New, monospace", size=11),
    xaxis=dict(gridcolor="#1a1a1a", zerolinecolor="#333333", tickfont=dict(color="#c0c0c0", size=11)),
    yaxis=dict(gridcolor="#1a1a1a", zerolinecolor="#333333", tickfont=dict(color="#c0c0c0", size=11)),
    margin=dict(t=60, b=40, l=50, r=50),
)

def render_autoscale_chart(fig, height=700):
    """Renderiza um Plotly figure via HTML/JS customizado com auto-rescale dos
    eixos Y (esquerda, direita e indicador) sempre que o usuario faz zoom no
    eixo X. O st.plotly_chart nativo nao reajusta a escala do Y ao dar zoom no
    X, o que dificulta a inspecao visual de janelas curtas."""
    fig_json = fig.to_json()
    html_template = """
    <div id="autoscale-chart-wrap" style="position:relative;width:100%;height:__HEIGHT__px;background:#000000;">
        <div id="autoscale-chart" style="width:100%;height:100%;background:#000000;"></div>
        <div id="autoscale-chart-loading" style="position:absolute;top:0;left:0;width:100%;height:100%;
             display:flex;align-items:center;justify-content:center;flex-direction:column;
             background:#000000;font-family:'Courier New',monospace;color:#FF7700;z-index:10;">
            <div style="border:3px solid #2a2a2a;border-top:3px solid #FF7700;border-radius:50%;
                 width:34px;height:34px;animation:spin-autoscale 0.8s linear infinite;"></div>
            <div style="margin-top:10px;font-size:0.8rem;letter-spacing:1px;">CARREGANDO GRAFICO...</div>
        </div>
    </div>
    <style>
        @keyframes spin-autoscale { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    </style>
    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
    <script>
    (function() {
        var figSpec = __FIG_JSON__;
        var gd = document.getElementById('autoscale-chart');
        var loadingEl = document.getElementById('autoscale-chart-loading');
        var isAdjusting = false;

        function axisKey(axisName) {
            return axisName === 'y' ? 'yaxis' : 'yaxis' + axisName.slice(1);
        }

        function computeRange(axisName, x0, x1) {
            var ymin = Infinity, ymax = -Infinity;
            gd.data.forEach(function(trace) {
                var ax = trace.yaxis || 'y';
                if (ax !== axisName) return;
                if (!trace.x || !trace.y) return;
                for (var i = 0; i < trace.x.length; i++) {
                    var xv = new Date(trace.x[i]).getTime();
                    if (xv >= x0 && xv <= x1) {
                        var yv = trace.y[i];
                        if (yv === null || yv === undefined || isNaN(yv)) continue;
                        if (yv < ymin) ymin = yv;
                        if (yv > ymax) ymax = yv;
                    }
                }
            });
            if (ymin === Infinity || ymax === -Infinity) return null;
            if (ymin === ymax) { ymin -= 1; ymax += 1; }
            var pad = (ymax - ymin) * 0.08;
            return [ymin - pad, ymax + pad];
        }

        function rescaleY(x0, x1) {
            var updates = {};
            ['y', 'y2', 'y3'].forEach(function(axisName) {
                var rng = computeRange(axisName, x0, x1);
                if (rng) { updates[axisKey(axisName) + '.range'] = rng; }
            });
            if (Object.keys(updates).length > 0) {
                isAdjusting = true;
                Plotly.relayout(gd, updates).then(function() { isAdjusting = false; });
            }
        }

        // Crosshair: shape de indice FIXO inserida ja no layout inicial (opacity 0).
        // Atualizamos apenas as propriedades x0/x1/opacity via relayout indexado
        // (Plotly.relayout(gd, {'shapes[N].x0': v, ...})), que e uma operacao leve
        // e independente do fluxo de rescale do eixo Y. Isso evita o bug em que o
        // flag isAdjusting (usado pelo rescale) ficava "preso" em true durante
        // hovers rapidos e fazia o crosshair parar de atualizar apos o 1o evento.
        var baseShapes = (figSpec.layout.shapes || []).slice();
        var crosshairIndex = baseShapes.length;
        // Usa uma data real existente nos dados (em vez do numero 0, que o
        // Plotly interpreta como epoch 1970-01-01 num eixo de datas e
        // corrompe o autorange inicial do eixo X — ver comentario acima).
        var firstX = null;
        for (var ti = 0; ti < figSpec.data.length; ti++) {
            if (figSpec.data[ti].x && figSpec.data[ti].x.length) { firstX = figSpec.data[ti].x[0]; break; }
        }
        var crosshairShape = {
            type: 'line', xref: 'x', yref: 'paper',
            x0: firstX, x1: firstX, y0: 0, y1: 1,
            opacity: 0,
            line: { color: '#999999', width: 1, dash: 'dot' }
        };
        figSpec.layout.shapes = baseShapes.concat([crosshairShape]);

        function setCrosshair(xval) {
            var upd = {};
            upd['shapes[' + crosshairIndex + '].x0'] = xval;
            upd['shapes[' + crosshairIndex + '].x1'] = xval;
            upd['shapes[' + crosshairIndex + '].opacity'] = 1;
            Plotly.relayout(gd, upd);
        }

        function clearCrosshair() {
            var upd = {};
            upd['shapes[' + crosshairIndex + '].opacity'] = 0;
            Plotly.relayout(gd, upd);
        }

        Plotly.newPlot(gd, figSpec.data, figSpec.layout, {responsive: true, displaylogo: false}).then(function() {
            if (loadingEl) { loadingEl.style.display = 'none'; }
            gd.on('plotly_relayout', function(eventdata) {
                if (isAdjusting) return;
                if (eventdata['xaxis.range[0]'] !== undefined && eventdata['xaxis.range[1]'] !== undefined) {
                    var x0 = new Date(eventdata['xaxis.range[0]']).getTime();
                    var x1 = new Date(eventdata['xaxis.range[1]']).getTime();
                    rescaleY(x0, x1);
                } else if (eventdata['xaxis.autorange'] === true || eventdata['xaxis2.autorange'] === true) {
                    isAdjusting = true;
                    Plotly.relayout(gd, {'yaxis.autorange': true, 'yaxis2.autorange': true, 'yaxis3.autorange': true}).then(function() { isAdjusting = false; });
                }
            });
            gd.on('plotly_hover', function(eventdata) {
                if (!eventdata.points || !eventdata.points.length) return;
                setCrosshair(eventdata.points[0].x);
            });
            gd.on('plotly_unhover', function() {
                clearCrosshair();
            });
        });
    })();
    </script>
    """
    html_out = html_template.replace("__HEIGHT__", str(height)).replace("__FIG_JSON__", fig_json)
    components.html(html_out, height=height + 30, scrolling=False)


# ─────────────────────────────────────────────────────────────────────────────
# LISTA DE ATIVOS POR FONTE
# ─────────────────────────────────────────────────────────────────────────────

# ── Yahoo Finance ────────────────────────────────────────────────────────────
# ── Futuros Yahoo Finance (sufixo =F = front-month continuo) ─────────────────
ASSETS_FUTUROS = [
    # ── Indices EUA (CME) ──
    ("ES=F",    "S&P 500 E-mini — CME"),
    ("MES=F",   "S&P 500 Micro E-mini — CME"),
    ("NQ=F",    "Nasdaq 100 E-mini — CME"),
    ("MNQ=F",   "Nasdaq 100 Micro E-mini — CME"),
    ("YM=F",    "Dow Jones E-mini — CME"),
    ("RTY=F",   "Russell 2000 E-mini — CME"),
    # ── Renda Fixa EUA — PU (sobe quando juros caem) ──
    ("ZT=F",      "UST 2Y PU — CME (sobe c/ juro cai)"),
    ("ZF=F",      "UST 5Y PU — CME (sobe c/ juro cai)"),
    ("ZN=F",      "UST 10Y PU — CME (sobe c/ juro cai)"),
    ("ZB=F",      "UST 30Y PU — CME (sobe c/ juro cai)"),
    ("UB=F",      "Ultra Bond PU — CME (sobe c/ juro cai)"),
    # ── Renda Fixa EUA — Yield proxy [inv] (sobe quando juros sobem) ──
    ("ZT=F~inv",  "UST 2Y Yield proxy [inv] (sobe c/ juro sobe)"),
    ("ZF=F~inv",  "UST 5Y Yield proxy [inv] (sobe c/ juro sobe)"),
    ("ZN=F~inv",  "UST 10Y Yield proxy [inv] (sobe c/ juro sobe)"),
    ("ZB=F~inv",  "UST 30Y Yield proxy [inv] (sobe c/ juro sobe)"),
    ("UB=F~inv",  "Ultra Bond Yield proxy [inv] (sobe c/ juro sobe)"),
    # ── Metais Preciosos — perspectiva metal (sobe c/ metal sobe) ──
    ("GC=F",      "Ouro (Gold) — COMEX (sobe c/ ouro sobe)"),
    ("SI=F",      "Prata (Silver) — COMEX (sobe c/ prata sobe)"),
    ("PL=F",      "Platina — COMEX"),
    ("PA=F",      "Paladio — COMEX"),
    # ── Metais Preciosos — perspectiva USD [inv] (sobe c/ USD forte) ──
    ("GC=F~inv",  "USD/Ouro [inv] (sobe c/ USD forte/ouro cai)"),
    ("SI=F~inv",  "USD/Prata [inv] (sobe c/ USD forte/prata cai)"),
    # ── Metais Industriais ──
    ("HG=F",      "Cobre (Copper) — COMEX"),
    # ── Energia (NYMEX/ICE) ──
    ("CL=F",      "Petroleo WTI — NYMEX"),
    ("BZ=F",      "Petroleo Brent — ICE"),
    ("NG=F",      "Gas Natural — NYMEX"),
    ("RB=F",      "Gasolina (RBOB) — NYMEX"),
    # ── Agricolas (CBOT/ICE) ──
    ("ZC=F",      "Milho (Corn) — CBOT"),
    ("ZW=F",      "Trigo (Wheat) — CBOT"),
    ("ZS=F",      "Soja (Soybeans) — CBOT"),
    ("ZL=F",      "Oleo de Soja — CBOT"),
    ("ZM=F",      "Farelo de Soja — CBOT"),
    ("KC=F",      "Cafe (Coffee) — ICE"),
    ("CT=F",      "Algodao (Cotton) — ICE"),
    ("SB=F",      "Acucar (Sugar 11) — ICE"),
    ("CC=F",      "Cacau (Cocoa) — ICE"),
    ("OJ=F",      "Suco de Laranja — ICE"),
    ("LE=F",      "Boi Gordo (Live Cattle) — CME"),
    ("HE=F",      "Suinos (Lean Hogs) — CME"),
    ("GF=F",      "Bezerro (Feeder Cattle) — CME"),
    # ── FX Futuros CME — perspectiva moeda (sobe c/ moeda forte vs USD) ──
    ("6E=F",      "EUR/USD futuro — CME (sobe c/ EUR forte)"),
    ("6J=F",      "JPY/USD futuro — CME (sobe c/ JPY forte)"),
    ("6B=F",      "GBP/USD futuro — CME (sobe c/ GBP forte)"),
    ("6A=F",      "AUD/USD futuro — CME (sobe c/ AUD forte)"),
    ("6C=F",      "CAD/USD futuro — CME (sobe c/ CAD forte)"),
    ("6S=F",      "CHF/USD futuro — CME (sobe c/ CHF forte)"),
    ("6N=F",      "NZD/USD futuro — CME (sobe c/ NZD forte)"),
    ("6M=F",      "MXN/USD futuro — CME (sobe c/ MXN forte)"),
    # ── FX Futuros CME — perspectiva USD [inv] (sobe c/ USD forte) ──
    ("6E=F~inv",  "USD/EUR [inv] — CME (sobe c/ USD forte/EUR fraco)"),
    ("6J=F~inv",  "USD/JPY [inv] — CME (sobe c/ USD forte/JPY fraco)"),
    ("6B=F~inv",  "USD/GBP [inv] — CME (sobe c/ USD forte/GBP fraco)"),
    ("6A=F~inv",  "USD/AUD [inv] — CME (sobe c/ USD forte/AUD fraco)"),
    ("6C=F~inv",  "USD/CAD [inv] — CME (sobe c/ USD forte/CAD fraco)"),
    ("6S=F~inv",  "USD/CHF [inv] — CME (sobe c/ USD forte/CHF fraco)"),
    ("6N=F~inv",  "USD/NZD [inv] — CME (sobe c/ USD forte/NZD fraco)"),
    ("6M=F~inv",  "USD/MXN [inv] — CME (sobe c/ USD forte/MXN fraco)"),
    # ── FX Spot / NDF — perspectiva USD (sobe c/ USD forte) ──
    ("USDBRL=X",    "USD/BRL Spot — NDF (sobe c/ USD forte)"),
    ("USDKRW=X",    "USD/KRW Spot — NDF (sobe c/ USD forte)"),
    ("USDINR=X",    "USD/INR Spot — NDF (sobe c/ USD forte)"),
    ("USDMXN=X",    "USD/MXN Spot (sobe c/ USD forte)"),
    ("USDZAR=X",    "USD/ZAR Spot (sobe c/ USD forte)"),
    ("USDTRY=X",    "USD/TRY Spot (sobe c/ USD forte)"),
    ("USDCNY=X",    "USD/CNY Spot (sobe c/ USD forte)"),
    ("DX-Y.NYB",    "Indice Dolar DXY — ICE"),
    # ── FX Spot / NDF — perspectiva moeda local [inv] (sobe c/ moeda local forte) ──
    ("USDBRL=X~inv","BRL/USD [inv] (sobe c/ BRL forte)"),
    ("USDKRW=X~inv","KRW/USD [inv] (sobe c/ KRW forte)"),
    ("USDINR=X~inv","INR/USD [inv] (sobe c/ INR forte)"),
    ("USDMXN=X~inv","MXN/USD [inv] (sobe c/ MXN forte)"),
    ("USDZAR=X~inv","ZAR/USD [inv] (sobe c/ ZAR forte)"),
    ("USDTRY=X~inv","TRY/USD [inv] (sobe c/ TRY forte)"),
    # ── Volatilidade ──
    ("^VIX",    "VIX — CBOE Volatility Index"),
    ("VX=F",    "VIX Futures — CBOE"),
]

# ── ETFs Yahoo Finance (cash, preco ajustado) ─────────────────────────────────
ASSETS_ETFS = [
    # ── Acoes EUA ──
    ("SPY",  "S&P 500 — SPDR ETF"),
    ("QQQ",  "Nasdaq 100 — Invesco ETF"),
    ("IWM",  "Russell 2000 — iShares ETF"),
    ("DIA",  "Dow Jones — SPDR ETF"),
    # ── Acoes Globais ──
    ("EWZ",  "Brasil MSCI — iShares ETF"),
    ("EEM",  "Emerging Markets — iShares ETF"),
    ("EFA",  "Developed ex-EUA — iShares ETF"),
    ("FXI",  "China Large Cap — iShares ETF"),
    ("EWJ",  "Japao — iShares ETF"),
    ("EZU",  "Eurozona — iShares ETF"),
    ("EWG",  "Alemanha — iShares ETF"),
    ("EWY",  "Coreia do Sul — iShares ETF"),
    # ── Renda Fixa EUA ──
    ("TLT",  "US Treasury 20+ anos — iShares ETF"),
    ("IEF",  "US Treasury 7-10 anos — iShares ETF"),
    ("SHY",  "US Treasury 1-3 anos — iShares ETF"),
    ("HYG",  "High Yield Corp — iShares ETF"),
    ("LQD",  "IG Corp — iShares ETF"),
    ("EMB",  "EM Bonds USD — iShares ETF"),
    # ── Commodities ──
    ("GLD",  "Ouro — SPDR Gold ETF"),
    ("IAU",  "Ouro — iShares Gold ETF"),
    ("SLV",  "Prata — iShares ETF"),
    ("DBC",  "Commodities Amplas — Invesco ETF"),
    ("USO",  "Petroleo WTI — US Oil Fund"),
    ("PDBC", "Commodities Otimizadas — Invesco ETF"),
    # ── Volatilidade ──
    ("UVXY", "VIX 1.5x — ProShares ETF"),
    ("SVXY", "VIX Inverso — ProShares ETF"),
    # ── Setoriais EUA ──
    ("XLF",  "Financials — SPDR ETF"),
    ("XLE",  "Energy — SPDR ETF"),
    ("XLK",  "Technology — SPDR ETF"),
    ("XLU",  "Utilities — SPDR ETF"),
    ("XLV",  "Health Care — SPDR ETF"),
]

def get_asset_list(tipo):
    return ASSETS_FUTUROS if tipo == "Futuros" else ASSETS_ETFS

def get_all_assets():
    return ASSETS_FUTUROS + ASSETS_ETFS

# Lookup global para benchmark selectbox
_ALL = get_all_assets()
ASSET_LABELS      = [f"{t} | {d}" for t, d in _ALL]
TICKER_FROM_LABEL = {f"{t} | {d}": t for t, d in _ALL}




# ─────────────────────────────────────────────────────────────────────────────
# TAXAS DE JUROS (Fed Funds e CDI/SELIC)
# ─────────────────────────────────────────────────────────────────────────────
FOMC = [
    ("2007-06-13",5.25),("2007-09-18",4.75),("2007-10-31",4.50),
    ("2007-12-11",4.25),("2008-01-22",3.50),("2008-01-30",3.00),
    ("2008-03-18",2.25),("2008-04-30",2.00),("2008-10-08",1.50),
    ("2008-10-29",1.00),("2008-12-16",0.25),("2015-12-17",0.50),
    ("2016-12-15",0.75),("2017-03-16",1.00),("2017-06-15",1.25),
    ("2017-12-14",1.50),("2018-03-22",1.75),("2018-06-14",2.00),
    ("2018-09-27",2.25),("2018-12-20",2.50),("2019-08-01",2.25),
    ("2019-09-19",2.00),("2019-10-31",1.75),("2020-03-03",1.25),
    ("2020-03-16",0.25),("2022-03-17",0.50),("2022-05-05",1.00),
    ("2022-06-16",1.75),("2022-07-28",2.50),("2022-09-22",3.25),
    ("2022-11-03",4.00),("2022-12-15",4.50),("2023-02-02",4.75),
    ("2023-03-23",5.00),("2023-05-04",5.25),("2023-07-27",5.50),
    ("2024-09-19",5.00),("2024-11-08",4.75),("2024-12-19",4.50),
    ("2025-09-17",4.00),("2025-10-29",3.75),("2025-12-10",3.50),
    ("2026-12-31",3.50),
]

COPOM = [
    ("2007-06-13",12.00),("2007-09-05",11.25),("2008-04-16",11.75),
    ("2008-06-04",12.25),("2008-07-23",13.00),("2008-09-10",13.75),
    ("2009-01-21",12.75),("2009-03-11",11.25),("2009-04-29",10.25),
    ("2009-06-10",9.25), ("2009-07-22",8.75), ("2010-04-28",9.50),
    ("2010-06-09",10.25),("2011-01-19",11.25),("2011-03-02",11.75),
    ("2011-04-20",12.00),("2011-07-20",12.50),("2012-08-29",7.50),
    ("2012-10-10",7.25), ("2013-04-17",7.50), ("2013-05-29",8.00),
    ("2013-07-10",8.50), ("2013-08-28",9.00), ("2013-10-09",9.50),
    ("2013-11-27",10.00),("2014-01-15",10.50),("2014-04-02",11.00),
    ("2014-10-29",11.25),("2014-12-03",11.75),("2015-01-21",12.25),
    ("2015-03-04",12.75),("2015-04-29",13.25),("2015-06-03",13.75),
    ("2015-07-29",14.25),("2016-10-19",14.00),("2016-11-30",13.75),
    ("2017-01-11",13.00),("2017-02-22",12.25),("2017-04-12",11.25),
    ("2017-05-31",10.25),("2017-07-26",9.25), ("2017-09-06",8.25),
    ("2017-10-25",7.50), ("2017-12-06",7.00), ("2018-02-07",6.75),
    ("2018-03-21",6.50), ("2018-12-12",6.50), ("2019-07-31",6.00),
    ("2019-09-18",5.50), ("2019-10-30",5.00), ("2019-12-11",4.50),
    ("2020-02-05",4.25), ("2020-03-18",3.75), ("2020-05-06",3.00),
    ("2020-06-17",2.25), ("2020-08-05",2.00), ("2021-03-17",2.75),
    ("2021-05-05",3.50), ("2021-06-16",4.25), ("2021-08-04",5.25),
    ("2021-09-22",6.25), ("2021-10-27",7.75), ("2021-12-08",9.25),
    ("2022-02-02",10.75),("2022-03-16",11.75),("2022-05-04",12.75),
    ("2022-06-15",13.25),("2022-08-03",13.75),("2022-12-07",13.75),
    ("2023-06-21",13.25),("2023-08-02",12.75),("2023-09-20",12.25),
    ("2023-11-01",11.75),("2023-12-13",11.25),("2024-01-31",11.25),
    ("2024-03-20",10.75),("2024-05-08",10.50),("2024-09-18",10.75),
    ("2024-10-30",11.25),("2024-12-11",12.25),("2025-01-29",13.25),
    ("2025-03-19",14.25),("2026-12-31",14.25),
]

def build_rate_series(decisions, index):
    dec_ts    = np.array([pd.Timestamp(d).value for d,_ in decisions], dtype=np.int64)
    dec_rates = np.array([r for _,r in decisions], dtype=np.float64)
    idx_vals  = np.array([pd.Timestamp(t).value for t in index], dtype=np.int64)
    pos = np.searchsorted(dec_ts, idx_vals, side="right") - 1
    pos = np.clip(pos, 0, len(dec_rates)-1)
    return dec_rates[pos] / 100.0 / 252.0

# ─────────────────────────────────────────────────────────────────────────────
# DADOS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_risk_appetite():
    path = Path(__file__).parent / "Inputs_backtesting_riskapp.xlsx"
    df = pd.read_excel(path, index_col=0, parse_dates=True).sort_index().dropna()
    df.columns = ["indicator","spx"]
    return df

@st.cache_data
def download_asset(ticker, start, end):
    try:
        real_ticker = ticker.replace("~inv", "")
        data = yf.download(real_ticker, start=start, end=end, progress=False, auto_adjust=True)
        if data.empty: return None
        close = data[["Close"]].copy(); close.columns = ["asset"]
        close.index = pd.to_datetime(close.index)
        if hasattr(close.index,"tz") and close.index.tz is not None:
            close.index = close.index.tz_localize(None)
        return close
    except Exception as e:
        st.error(t("error_download_failed", ticker=ticker, err=e)); return None

# ─────────────────────────────────────────────────────────────────────────────
# BACKTEST
# ─────────────────────────────────────────────────────────────────────────────
def calc_metrics(strat_ret, position, index):
    cum = np.cumprod(1 + strat_ret)
    total_return = float(cum[-1]-1)
    n_years = (index[-1]-index[0]).days/365.25
    cagr = float((1+total_return)**(1/max(n_years,0.01))-1)
    vol = float(np.std(strat_ret)*np.sqrt(252))
    sharpe = float(np.mean(strat_ret)*252/vol) if vol>0 else 0.0
    rm = np.maximum.accumulate(cum)
    max_dd = float((cum/rm-1).min())
    return dict(
        total_return=round(total_return,4), cagr=round(cagr,4),
        sharpe=round(sharpe,3), max_dd=round(max_dd,4),
        n_trades=int(np.sum(np.diff(position)!=0)),
        pct_invested=round(float(np.mean(position!=0)),3),
        cum_series=pd.Series(cum, index=index),
    )

def build_trade(df, ei, xi, side, ep, xp):
    seg=df["asset"].values[ei:xi+1]; edate,xdate=df.index[ei],df.index[xi]
    tret=(xp-ep)/ep if side==1 else (ep-xp)/ep
    cum=(seg/seg[0]) if side==1 else (2*ep-seg)/ep
    rm=np.maximum.accumulate(cum)
    return {"Entrada":edate.strftime("%Y-%m-%d"),"Saída":xdate.strftime("%Y-%m-%d"),
            "Dias":(xdate-edate).days,"Lado":"LONG" if side==1 else "SHORT",
            "Retorno":round(tret,4),"MaxDD Trade":round(float((cum/rm-1).min()),4)}

def get_signals_is(df, eh, el, ex, direction, calib_df=None, excl_mask=None):
    # calib_df: dataset para calibrar percentis (ex: IS sem crises). Se None, usa df.
    cal = calib_df if calib_df is not None else df
    tH=np.percentile(cal["indicator"].dropna(),eh); tL=np.percentile(cal["indicator"].dropna(),el)
    tM=np.percentile(cal["indicator"].dropna(),ex) if ex!="opposite" else None
    ind,prices=df["indicator"].values,df["asset"].values; n=len(df)
    pos=np.zeros(n); cp=0; ei=None; ep=None; trades=[]
    _excl = excl_mask if excl_mask is not None else np.zeros(n, dtype=bool)
    # ghost_cp: sinal virtual que rastreia sinais nascidos/ativos durante exclusao.
    # O modelo so pode abrir posicoes reais apos o ghost fechar naturalmente (P50).
    ghost_cp = 0
    for i in range(1,n):
        v=ind[i]
        if _excl[i]:
            # Converter posicao real aberta em ghost (sem registrar trade)
            if cp != 0:
                ghost_cp=cp; cp=0; ei=None; ep=None
            pos[i]=0
            # Rodar logica de entrada/saida do ghost durante exclusao
            if ghost_cp==0:
                if direction=="contrarian":
                    if v<=tL: ghost_cp=1
                    elif v>=tH: ghost_cp=-1
                else:
                    if v>=tH: ghost_cp=1
                    elif v<=tL: ghost_cp=-1
            elif ghost_cp==1:
                if (tM is not None and v>=tM) or (tM is None and v>=tH): ghost_cp=0
            elif ghost_cp==-1:
                if (tM is not None and v<=tM) or (tM is None and v<=tL): ghost_cp=0
            continue
        # Fora da exclusao: se ghost ainda ativo, permanecer flat ate sair naturalmente
        if ghost_cp != 0:
            pos[i]=0
            if ghost_cp==1:
                if (tM is not None and v>=tM) or (tM is None and v>=tH): ghost_cp=0
            elif ghost_cp==-1:
                if (tM is not None and v<=tM) or (tM is None and v<=tL): ghost_cp=0
            continue
        # Modo normal: gerar posicoes reais
        if cp==0:
            if direction=="contrarian":
                if v<=tL: cp=1;ei=i;ep=prices[i]
                elif v>=tH: cp=-1;ei=i;ep=prices[i]
            else:
                if v>=tH: cp=1;ei=i;ep=prices[i]
                elif v<=tL: cp=-1;ei=i;ep=prices[i]
        elif cp==1:
            if (tM is not None and v>=tM) or (tM is None and v>=tH) or i==n-1:
                trades.append(build_trade(df,ei,i,cp,ep,prices[i])); cp=0;ei=None;ep=None
        elif cp==-1:
            if (tM is not None and v<=tM) or (tM is None and v<=tL) or i==n-1:
                trades.append(build_trade(df,ei,i,cp,ep,prices[i])); cp=0;ei=None;ep=None
        pos[i]=cp
    return pos,(pd.DataFrame(trades) if trades else pd.DataFrame())

def precompute_expanding_pcts(df_in, df_out, pct_levels):
    full=np.concatenate([df_in["indicator"].values,df_out["indicator"].values])
    n_in,n_oos=len(df_in),len(df_out)
    lookup={p:np.empty(n_oos) for p in pct_levels}
    for i in range(n_oos):
        sl=np.sort(full[:n_in+i]); n=len(sl)
        for p in pct_levels:
            idx=(p/100)*(n-1); lo=int(idx); hi=min(lo+1,n-1)
            lookup[p][i]=sl[lo]+(idx-lo)*(sl[hi]-sl[lo])
    return lookup

def get_signals_oos(df_out, eh, el, ex, direction, lookup):
    tH_arr,tL_arr=lookup[eh],lookup[el]
    tM_arr=lookup[ex] if ex!="opposite" else None
    ind,prices=df_out["indicator"].values,df_out["asset"].values; n=len(df_out)
    pos=np.zeros(n); cp=0; ei=None; ep=None; trades=[]
    for i in range(1,n):
        v=ind[i]; tH=tH_arr[i]; tL=tL_arr[i]
        tM=tM_arr[i] if tM_arr is not None else None
        if cp==0:
            if direction=="contrarian":
                if v<=tL: cp=1;ei=i;ep=prices[i]
                elif v>=tH: cp=-1;ei=i;ep=prices[i]
            else:
                if v>=tH: cp=1;ei=i;ep=prices[i]
                elif v<=tL: cp=-1;ei=i;ep=prices[i]
        elif cp==1:
            if (tM is not None and v>=tM) or (tM is None and v>=tH) or i==n-1:
                trades.append(build_trade(df_out,ei,i,cp,ep,prices[i])); cp=0;ei=None;ep=None
        elif cp==-1:
            if (tM is not None and v<=tM) or (tM is None and v<=tL) or i==n-1:
                trades.append(build_trade(df_out,ei,i,cp,ep,prices[i])); cp=0;ei=None;ep=None
        pos[i]=cp
    return pos,(pd.DataFrame(trades) if trades else pd.DataFrame())

def compute_br_fund_cota(pos, asset_ret, base_rate, long_only=False,
                         hedge_spread_daily=0.0):
    """
    Cota Master de fundo (sem taxa de administracao).

    base_rate: taxa de carrego do fundo no periodo flat
      - CDI / SELIC: fundo brasileiro
      - Fed Funds: fundo USD
      - BH do ativo: passivo no ativo (sempre comprado na base)

      Cota = base_rate + pos * r_ativo - |pos| * spread

    hedge_spread_daily = (Cupom_Cambial_1M - SOFR_1M) / 252
    """
    rp = np.roll(pos, 1); rp[0] = 0

    if long_only:
        pos_scaled = np.where(rp == 1, 1.5, np.where(rp == -1, 0.5, 1.0))
        lev = np.maximum(0.0, pos_scaled - 1.0)
        cota_ret = (base_rate * (1.0 - lev)
                    + pos_scaled * asset_ret
                    - pos_scaled * hedge_spread_daily)
    else:
        cota_ret = (base_rate
                    + rp * asset_ret
                    - np.abs(rp) * hedge_spread_daily)

    cota_ret[0] = 0.0
    return cota_ret

def compute_alpha_only(pos, asset_ret, long_only=False, hedge_spread_daily=0.0):
    """
    Alpha puro da estrategia: apenas o P&L direcional das posicoes, sem CDI.
    FLAT = 0%, LONG = +asset_ret, SHORT = -asset_ret.
    Util para isolar o valor gerado pelo sinal de timing.
    hedge_spread_daily: custo do hedge cambial (bps/252), deduzido quando em posicao.
    """
    rp = np.roll(pos, 1); rp[0] = 0
    if long_only:
        pos_scaled = np.where(rp == 1, 1.5, np.where(rp == -1, 0.5, 1.0))
        sr = (pos_scaled - 1.0) * asset_ret - np.abs(pos_scaled - 1.0) * hedge_spread_daily
    else:
        sr = rp * asset_ret - np.abs(rp) * hedge_spread_daily
    sr[0] = 0.0
    return sr

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="border-bottom:2px solid #FF7700;padding-bottom:8px;margin-bottom:4px;">
<span style="color:#FF7700;font-size:1.5rem;font-weight:bold;letter-spacing:3px;font-family:'Courier New';">
▶ RISK APPETITE BACKTESTER
</span>
<span style="color:#606060;font-size:0.75rem;margin-left:16px;font-family:'Courier New';">
{t("header_indicator_label")}: DIEGO DONADIO | {t("header_data_label")}: YAHOO FINANCE
</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
# ── Walk-Forward Optimizer helpers ─────────────────────────────────────────

def build_excl_mask_arr(idx, excl_gfc, excl_covid, excl_custom, excl_start_ts, excl_end_ts):
    mask = np.zeros(len(idx), dtype=bool)
    if excl_gfc:
        mask |= (idx >= pd.Timestamp("2008-09-01")) & (idx <= pd.Timestamp("2009-04-30"))
    if excl_covid:
        mask |= (idx >= pd.Timestamp("2020-02-28")) & (idx <= pd.Timestamp("2020-11-30"))
    if excl_custom and excl_start_ts is not None and excl_end_ts is not None:
        mask |= (idx >= pd.Timestamp(excl_start_ts)) & (idx <= pd.Timestamp(excl_end_ts))
    return mask


def get_signals_oos_static(df, tH, tL, tM, excl_mask=None):
    """Contrarian signals with fixed IS-calibrated thresholds + ghost signal."""
    ind = df["indicator"].values
    n = len(df)
    pos = np.zeros(n)
    cp = 0
    _excl = excl_mask if excl_mask is not None else np.zeros(n, dtype=bool)
    ghost_cp = 0
    for i in range(1, n):
        v = ind[i]
        if _excl[i]:
            if cp != 0:
                ghost_cp = cp
                cp = 0
            pos[i] = 0
            if ghost_cp == 0:
                if v <= tL:
                    ghost_cp = 1
                elif v >= tH:
                    ghost_cp = -1
            elif ghost_cp == 1:
                if v >= tM:
                    ghost_cp = 0
            elif ghost_cp == -1:
                if v <= tM:
                    ghost_cp = 0
            continue
        if ghost_cp != 0:
            pos[i] = 0
            if ghost_cp == 1:
                if v >= tM:
                    ghost_cp = 0
            elif ghost_cp == -1:
                if v <= tM:
                    ghost_cp = 0
            continue
        if cp == 0:
            if v <= tL:
                cp = 1
            elif v >= tH:
                cp = -1
        elif cp == 1:
            if v >= tM or i == n - 1:
                cp = 0
        elif cp == -1:
            if v <= tM or i == n - 1:
                cp = 0
        pos[i] = cp
    return pos


def build_walkforward_windows(idx, is_years=4, oos_months=12, step_months=6):
    """Constroi as janelas rolantes (IS de is_years anos, OOS de oos_months meses,
    avancando step_months meses por iteracao) usadas pelo walk-forward optimizer.
    Extraido para funcao propria para poder ser reutilizado tanto no grid-search
    quanto no recalculo de series detalhadas (cota/indicador) de um combo especifico."""
    windows = []
    start_date = idx[0]
    end_date = idx[-1]
    cur = start_date
    while True:
        is_end = cur + pd.DateOffset(years=is_years) - pd.DateOffset(days=1)
        oos_start = is_end + pd.DateOffset(days=1)
        oos_end = oos_start + pd.DateOffset(months=oos_months) - pd.DateOffset(days=1)
        if oos_end > end_date:
            break
        is_mask_idx  = (idx >= cur) & (idx <= is_end)
        oos_mask_idx = (idx >= oos_start) & (idx <= oos_end)
        if is_mask_idx.sum() < 200 or oos_mask_idx.sum() < 20:
            cur += pd.DateOffset(months=step_months)
            continue
        windows.append({
            "label": oos_start.strftime("%Y-%m"),
            "is_idx": is_mask_idx,
            "oos_idx": oos_mask_idx,
        })
        cur += pd.DateOffset(months=step_months)
    return windows


def run_walkforward_optimizer(combined, excl_gfc, excl_covid, excl_custom,
                               excl_start, excl_end, invert_ativo, long_only,
                               flat_mode_label, progress_bar=None):
    """Rolling 4yr IS / 12m OOS walk-forward optimizer. Contrarian only."""
    entry_highs = [80.0, 82.5, 85.0, 87.5, 90.0, 92.5, 95.0, 97.5]
    entry_lows  = [2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0]
    exit_levels = [40.0, 42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5, 60.0]
    combos = [(eh, el, ex) for eh in entry_highs for el in entry_lows for ex in exit_levels]
    n_combos = len(combos)  # 576

    idx = combined.index
    windows = build_walkforward_windows(idx)
    if not windows:
        return None, []

    n_wins = len(windows)

    # Full-series exclusion mask
    full_excl = build_excl_mask_arr(idx, excl_gfc, excl_covid, excl_custom, excl_start, excl_end)

    combo_windows = {c: [] for c in combos}
    total_iters = n_combos * n_wins
    done = 0

    pct_keys = [2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0,
                40.0, 42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5, 60.0,
                80.0, 82.5, 85.0, 87.5, 90.0, 92.5, 95.0, 97.5]

    for win in windows:
        is_m  = win["is_idx"]
        oos_m = win["oos_idx"]
        df_is  = combined[is_m].copy()
        df_oos = combined[oos_m].copy()
        excl_is  = full_excl[np.where(is_m)[0]]
        excl_oos = full_excl[np.where(oos_m)[0]]

        # Asset returns OOS
        if "asset" in df_oos.columns:
            asset_oos = df_oos["asset"].pct_change().fillna(0).values
        else:
            asset_oos = np.zeros(len(df_oos))
        if invert_ativo:
            asset_oos = -asset_oos

        # IS percentile cache
        ind_is_clean = df_is["indicator"].dropna().values
        pct_cache = {p: float(np.percentile(ind_is_clean, p)) for p in pct_keys}

        for (eh, el, ex) in combos:
            tH = pct_cache[eh]
            tL = pct_cache[el]
            tM = pct_cache[ex]

            pos_oos = get_signals_oos_static(df_oos, tH, tL, tM, excl_mask=excl_oos)
            if long_only:
                pos_oos = np.maximum(pos_oos, 0)

            strat_ret = pos_oos[:-1] * asset_oos[1:]

            if len(strat_ret) == 0 or np.all(strat_ret == 0):
                combo_windows[(eh, el, ex)].append(
                    {"sharpe": np.nan, "ret": np.nan, "dd": np.nan, "pct_pos": np.nan}
                )
                done += 1
                continue

            ann = 252
            avg_r = float(np.mean(strat_ret) * ann)
            std_r = float(np.std(strat_ret) * np.sqrt(ann))
            sharpe = avg_r / std_r if std_r > 1e-9 else np.nan

            curve = np.cumprod(1 + strat_ret)
            peak = np.maximum.accumulate(curve)
            max_dd = float(np.min((curve - peak) / peak))
            pct_pos = np.nan  # calculated per-combo after aggregation

            combo_windows[(eh, el, ex)].append(
                {"sharpe": sharpe, "ret": avg_r, "dd": max_dd, "pct_pos": pct_pos}
            )
            done += 1
            if progress_bar is not None and done % 500 == 0:
                pct = int(done / total_iters * 100)
                progress_bar.progress(pct, text=t("progress_running", done=done, total=total_iters, pct=pct))

    if progress_bar is not None:
        progress_bar.progress(100, text=t("progress_done"))

    # Aggregate
    rows = []
    detail_list = []
    def _trimmed(arr, trim=0.20):
        """Remove trim% piores e trim% melhores. Retorna (mediana, min, max) do nucleo."""
        s = sorted(arr)
        n = len(s)
        if n < 5:
            return (float(np.median(s)), float(s[0]), float(s[-1]))
        cut = max(1, int(round(n * trim)))
        core = s[cut: n - cut]
        if not core:
            core = s
        return (float(np.median(core)), float(core[0]), float(core[-1]))

    for (eh, el, ex), win_data in combo_windows.items():
        sharpes = [w["sharpe"] for w in win_data if w["sharpe"] is not None and not np.isnan(w["sharpe"])]
        rets    = [w["ret"]    for w in win_data if w["ret"]    is not None and not np.isnan(w["ret"])]
        dds     = [w["dd"]     for w in win_data if w["dd"]     is not None and not np.isnan(w["dd"])]
        if not sharpes:
            continue
        pct_win = float(np.mean([s > 0 for s in sharpes]))  # % janelas com Sharpe > 0

        sh_trim_med, sh_trim_min, sh_trim_max = _trimmed(sharpes)
        dd_trim_med, dd_trim_min, dd_trim_max = _trimmed(dds) if dds else (np.nan, np.nan, np.nan)
        rt_trim_med, rt_trim_min, rt_trim_max = _trimmed(rets) if rets else (np.nan, np.nan, np.nan)

        rows.append({
            "eh": eh, "el": el, "ex": ex,
            # mediana global (para ordenação)
            "avg_sharpe": float(np.median(sharpes)),
            "avg_ret":    float(np.median(rets)) if rets else np.nan,
            "avg_dd":     float(np.median(dds))  if dds  else np.nan,
            # nucleo aparado 60%
            "sh_trim_med": sh_trim_med, "sh_trim_min": sh_trim_min, "sh_trim_max": sh_trim_max,
            "dd_trim_med": dd_trim_med, "dd_trim_min": dd_trim_min, "dd_trim_max": dd_trim_max,
            "rt_trim_med": rt_trim_med, "rt_trim_min": rt_trim_min, "rt_trim_max": rt_trim_max,
            "pct_win":    pct_win,
            "n_windows":  n_wins,
        })
        win_detail = []
        for winfo, wmetric in zip(windows, win_data):
            win_detail.append({
                "window": winfo["label"],
                "sharpe": 0.0 if wmetric["sharpe"] is None or np.isnan(wmetric["sharpe"]) else wmetric["sharpe"],
                "ret":    0.0 if wmetric["ret"]    is None or np.isnan(wmetric["ret"])    else wmetric["ret"],
                "dd":     0.0 if wmetric["dd"]     is None or np.isnan(wmetric["dd"])     else wmetric["dd"],
            })
        detail_list.append({"eh": eh, "el": el, "ex": ex, "windows": win_detail})

    agg_df = pd.DataFrame(rows)
    return agg_df, detail_list


def compute_window_series(combined, eh, el, ex, excl_gfc, excl_covid, excl_custom,
                           excl_start, excl_end, invert_ativo, long_only):
    """Recalcula, para um combo (eh, el, ex) ja escolhido, a serie OOS detalhada de
    cada janela walk-forward: datas, cota (rebasada em 100), indicador, e os niveis
    reais (tH/tL/tM) calibrados naquela janela IS. Usado para o popup de due diligence
    visual ao clicar numa barra do grafico do optimizer — nao precisa ser calculado
    para os 576 combos do grid-search, so para o melhor combo de cada criterio."""
    idx = combined.index
    windows = build_walkforward_windows(idx)
    full_excl = build_excl_mask_arr(idx, excl_gfc, excl_covid, excl_custom, excl_start, excl_end)
    out = []
    for win in windows:
        is_m, oos_m = win["is_idx"], win["oos_idx"]
        df_is  = combined[is_m]
        df_oos = combined[oos_m].copy()
        excl_oos = full_excl[np.where(oos_m)[0]]

        ind_is_clean = df_is["indicator"].dropna().values
        tH = float(np.percentile(ind_is_clean, eh))
        tL = float(np.percentile(ind_is_clean, el))
        tM = float(np.percentile(ind_is_clean, ex))

        if "asset" in df_oos.columns:
            asset_oos = df_oos["asset"].pct_change().fillna(0).values
        else:
            asset_oos = np.zeros(len(df_oos))
        if invert_ativo:
            asset_oos = -asset_oos

        pos_oos = get_signals_oos_static(df_oos, tH, tL, tM, excl_mask=excl_oos)
        if long_only:
            pos_oos = np.maximum(pos_oos, 0)

        strat_ret = pos_oos[:-1] * asset_oos[1:]
        curve = np.concatenate([[1.0], np.cumprod(1 + strat_ret)]) * 100.0

        out.append({
            "window": win["label"],
            "dates": df_oos.index.strftime("%Y-%m-%d").tolist(),
            "curve": curve.tolist(),
            "indicator": df_oos["indicator"].tolist(),
            "tH": tH, "tL": tL, "tM": tM,
        })
    return out


with st.sidebar:
    st.markdown(f"<span style='color:#FF7700;font-size:1rem;font-weight:bold;letter-spacing:2px;'>⚙ {t('sidebar_params')}</span>", unsafe_allow_html=True)

    st.markdown(f"<span style='color:#FF7700;font-size:0.8rem;'>{t('asset_type_label')}</span>", unsafe_allow_html=True)
    _tipo_opts = [t("opt_futuros"), t("opt_etfs")]
    tipo_ativo_label = st.radio(
        "Tipo", options=_tipo_opts, index=0,
        label_visibility="collapsed",
        help=t("help_tipo_ativo"),
    )
    tipo_ativo = "Futuros" if tipo_ativo_label == t("opt_futuros") else "ETFs"
    if tipo_ativo == "Futuros":
        st.caption(t("caption_futuros"))
    else:
        st.caption(t("caption_etfs"))

    assets_list   = get_asset_list(tipo_ativo)
    asset_labels  = [f"{t_} | {d}" for t_, d in assets_list]
    ticker_from_label = {f"{t_} | {d}": t_ for t_, d in assets_list}

    st.divider()
    st.markdown(f"<span style='color:#FF7700;font-size:0.8rem;'>{t('asset_label')}</span>", unsafe_allow_html=True)
    selected_label = st.selectbox(
        "Ativo", options=asset_labels, index=0,
        help=t("help_ativo"),
        label_visibility="collapsed",
    )
    ticker = ticker_from_label[selected_label]
    st.caption(t("caption_selected", ticker=ticker))

    st.divider()
    st.markdown(f"<span style='color:#FF7700;font-size:0.8rem;'>{t('period_label')}</span>", unsafe_allow_html=True)
    is_start = st.date_input(t("is_start_label"), value=pd.Timestamp("2007-06-13"),
                              label_visibility="visible",
                              help=t("help_is_start"))
    is_end   = st.date_input(t("is_end_label"),    value=pd.Timestamp("2016-12-31"),
                              label_visibility="visible")
    st.caption(t("caption_oos", date=(pd.Timestamp(is_end)+pd.offsets.BDay(1)).strftime('%Y-%m-%d')))

    st.markdown(f"<span style='color:#FF7700;font-size:0.8rem;'>{t('exclude_periods_label')}</span>", unsafe_allow_html=True)
    excl_gfc = st.checkbox(t("excl_gfc_label"), value=False,
                            help=t("help_excl_gfc"))
    excl_covid = st.checkbox(t("excl_covid_label"), value=False,
                              help=t("help_excl_covid"))
    excl_custom = st.checkbox(t("excl_custom_label"), value=False)
    excl_start = excl_end = None
    if excl_custom:
        excl_col1, excl_col2 = st.columns(2)
        excl_start = excl_col1.date_input(t("from_label"), value=pd.Timestamp("2020-02-01"), label_visibility="visible")
        excl_end   = excl_col2.date_input(t("to_label"), value=pd.Timestamp("2020-11-30"), label_visibility="visible")

    st.divider()
    st.markdown(f"<span style='color:#FF7700;font-size:0.8rem;'>{t('strategy_label')}</span>", unsafe_allow_html=True)
    direction = "contrarian"
    invert_signal = False
    st.caption(t("caption_strategy"))

    # Session state para botão 'Usar este combo' do Optimizer
    for _k, _v in [("sel_eh", 90.0), ("sel_el", 10.0), ("sel_ex", 50.0)]:
        if _k not in st.session_state:
            st.session_state[_k] = _v
    if "run_after_usar" not in st.session_state:
        st.session_state["run_after_usar"] = False
    # Transferir valores pendentes do "Usar" ANTES de criar os sliders
    for _src_k, _dst_k in [("_new_eh", "sel_eh"), ("_new_el", "sel_el"), ("_new_ex", "sel_ex")]:
        if _src_k in st.session_state:
            st.session_state[_dst_k] = st.session_state.pop(_src_k)

    _eh_opts = [80.0, 82.5, 85.0, 87.5, 90.0, 92.5, 95.0, 97.5]
    _el_opts = [2.5, 5.0, 7.5, 10.0, 12.5, 15.0, 17.5, 20.0]
    _ex_opts = [40.0, 42.5, 45.0, 47.5, 50.0, 52.5, 55.0, 57.5, 60.0]
    entry_high = st.select_slider(t("entry_euphoria_label"),
                                   options=_eh_opts, key="sel_eh",
                                   format_func=lambda x: f"P{x:g}")
    entry_low  = st.select_slider(t("entry_panic_label"),
                                   options=_el_opts, key="sel_el",
                                   format_func=lambda x: f"P{x:g}")
    exit_rule  = st.select_slider(t("exit_label_slider"),
                                   options=_ex_opts, key="sel_ex",
                                   format_func=lambda x: f"P{x:g}")
    exit_label = f"P{exit_rule:g}"

    st.divider()
    st.markdown(f"<span style='color:#FF7700;font-size:0.8rem;'>{t('leverage_label')}</span>", unsafe_allow_html=True)
    long_only = st.checkbox(t("long_only_label"), value=False,
                             help=t("help_long_only"))

    st.divider()
    st.markdown(f"<span style='color:#FF7700;font-size:0.8rem;'>{t('hedge_cost_label')}</span>",
                unsafe_allow_html=True)
    st.caption(t("caption_hedge"))
    hedge_spread_bps = st.slider(
        t("hedge_slider_label"), min_value=0, max_value=300, value=0, step=5,
        label_visibility="collapsed",
        help=t("help_hedge_slider"),
    )
    hedge_spread_daily = hedge_spread_bps / 10_000 / 252

    st.divider()
    st.markdown(f"<span style='color:#FF7700;font-size:0.8rem;'>{t('benchmark_label')}</span>",
                unsafe_allow_html=True)
    st.caption(t("caption_benchmark"))
    flat_mode_label = st.radio(
        "Benchmark",
        options=["zero","cdi","fed_funds","passivo_longo","benchmark"],
        format_func=lambda x: {
            "zero":         t("bench_opt_zero"),
            "cdi":          t("bench_opt_cdi"),
            "fed_funds":    t("bench_opt_fed"),
            "passivo_longo":t("bench_opt_passive"),
            "benchmark":    t("bench_opt_other"),
        }[x],
        index=0, label_visibility="collapsed",
    )
    bench_ticker = None
    if flat_mode_label == "benchmark":
        bench_lbl = st.selectbox(t("benchmark_ticker_label"), options=ASSET_LABELS, index=0)
        bench_ticker = TICKER_FROM_LABEL[bench_lbl]

        # ── Validacao de cobertura historica ANTES de rodar o backtest ──
        # Garante que o ticker escolhido como benchmark tem dados suficientes
        # para o periodo necessario, evitando resultados enganosos ou erros.
        _ra_preview = load_risk_appetite()
        with st.spinner(t("benchmark_check_spinner", ticker=bench_ticker)):
            _bd_check = download_asset(
                bench_ticker, str(pd.Timestamp(is_start).date()), str(_ra_preview.index[-1].date())
            )
        if _bd_check is None or _bd_check.empty:
            st.error(t("benchmark_coverage_not_found", ticker=bench_ticker))
        else:
            _gap_start = (pd.Timestamp(_bd_check.index[0]) - pd.Timestamp(is_start)).days
            _gap_end   = (pd.Timestamp(_ra_preview.index[-1]) - pd.Timestamp(_bd_check.index[-1])).days
            if _gap_start > 30:
                st.warning(t("benchmark_coverage_late_start",
                              ticker=bench_ticker,
                              start=pd.Timestamp(_bd_check.index[0]).strftime("%Y-%m-%d"),
                              is_start=pd.Timestamp(is_start).strftime("%Y-%m-%d")))
            elif _gap_end > 30:
                st.warning(t("benchmark_coverage_stale_end",
                              ticker=bench_ticker,
                              end=pd.Timestamp(_bd_check.index[-1]).strftime("%Y-%m-%d"),
                              days=_gap_end))
            else:
                st.caption("✓ " + t("benchmark_coverage_ok",
                              ticker=bench_ticker,
                              start=pd.Timestamp(_bd_check.index[0]).strftime("%Y-%m-%d")))

    st.divider()
    run_btn = st.button(t("run_button"), type="primary", use_container_width=True)
    st.divider()
    opt_btn = st.button(t("optimize_button"), type="secondary", use_container_width=True, help=t("help_optimizer"))

    st.markdown(
        f"<div style='text-align:center;color:#3a3a3a;font-size:0.6rem;margin-top:8px;'>"
        f"Streamlit v{st.__version__}</div>",
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO
# ─────────────────────────────────────────────────────────────────────────────
# Usar no optimizer => rodar backtest automaticamente com combo selecionado
if st.session_state.get("run_after_usar") and not run_btn:
    st.session_state["run_after_usar"] = False
    run_btn = True

if run_btn:
    ra = load_risk_appetite()

    # Definir antes do spinner para usar no label
    invert_ativo = ticker.endswith("~inv")
    ticker_display = ticker.replace("~inv", "") + (" [inv]" if invert_ativo else "")

    with st.spinner(t("spinner_loading_asset", ticker=ticker_display)):
        asset = download_asset(ticker, str(ra.index[0].date()), str(ra.index[-1].date()))

    if asset is None or asset.empty:
        st.error(t("error_ticker_not_found", ticker=ticker)); st.stop()

    combined = ra[["indicator"]].join(asset, how="inner").dropna()
    if len(combined) < 100:
        st.error(t("error_insufficient_data_align", n=len(combined))); st.stop()

    is_start_ts = pd.Timestamp(is_start)
    is_end_ts   = pd.Timestamp(is_end)

    # Excluir periodos do IS
    # IS completo (sem remover datas — evita gap de pct_change)
    combined_is_full = combined[(combined.index >= is_start_ts) & (combined.index <= is_end_ts)]
    df_in  = combined_is_full
    df_out = combined[combined.index > is_end_ts]

    # Mascara de exclusao calculada DIRETAMENTE sobre df_in.index (evita desalinhamento)
    _idx = df_in.index
    excl_mask_is = pd.Series(False, index=_idx)
    if excl_gfc:
        excl_mask_is |= ((_idx >= pd.Timestamp("2008-09-01")) & (_idx <= pd.Timestamp("2009-04-30")))
    if excl_covid:
        excl_mask_is |= ((_idx >= pd.Timestamp("2020-02-28")) & (_idx <= pd.Timestamp("2020-11-30")))
    if excl_custom and excl_start and excl_end:
        excl_mask_is |= ((_idx >= pd.Timestamp(excl_start)) & (_idx <= pd.Timestamp(excl_end)))
    excl_mask_is = excl_mask_is.values  # numpy bool array

    # calib_df: IS sem periodos excluidos — para calibrar percentis sem crises
    combined_is_calib = df_in[~excl_mask_is]
    if len(combined_is_calib) < 30:
        combined_is_calib = df_in  # fallback se sobrar muito pouco
        st.warning(t("warning_few_data_excl"))

    if len(df_in) < 50:  st.error(t("error_is_too_short")); st.stop()
    if len(df_out) < 10: st.error(t("error_oos_too_short")); st.stop()

    # Retornos diários do ativo
    bh_ret_in  = df_in["asset"].pct_change().fillna(0).values
    bh_ret_out = df_out["asset"].pct_change().fillna(0).values
    if invert_ativo:
        bh_ret_in  = -bh_ret_in
        bh_ret_out = -bh_ret_out

    # CDI sempre computado — é a base da cota Master
    cdi_is  = build_rate_series(COPOM, df_in.index)
    cdi_oos = build_rate_series(COPOM, df_out.index)

    # Benchmark para o gráfico (só linha comparativa) — calculado ANTES da
    # taxa base do fundo, pois o modo "benchmark" reaproveita esses valores.
    bench_ret_is = bench_ret_oos = None

    if flat_mode_label == "zero":
        bench_ret_is  = np.zeros(len(df_in))
        bench_ret_oos = np.zeros(len(df_out))
        bench_name    = t("bench_name_alpha")

    elif flat_mode_label == "fed_funds":
        bench_ret_is  = build_rate_series(FOMC, df_in.index)
        bench_ret_oos = build_rate_series(FOMC, df_out.index)
        bench_name    = t("bench_name_fed")

    elif flat_mode_label == "cdi":
        bench_ret_is  = cdi_is
        bench_ret_oos = cdi_oos
        bench_name    = t("bench_name_cdi")

    elif flat_mode_label == "passivo_longo":
        bench_ret_is  = bh_ret_in
        bench_ret_oos = bh_ret_out
        bench_name    = t("bench_name_passive", ticker=ticker)

    elif flat_mode_label == "benchmark" and bench_ticker:
        with st.spinner(t("spinner_loading_benchmark", ticker=bench_ticker)):
            bd = download_asset(bench_ticker, str(combined.index[0].date()), str(combined.index[-1].date()))
        if bd is not None and not bd.empty:
            # Transparencia sobre cobertura: avisa se faltar historico no inicio
            # ou no fim, em vez de deixar o ffill/fillna mascarar silenciosamente.
            _gap_start = (bd.index[0] - combined.index[0]).days
            _gap_end   = (combined.index[-1] - bd.index[-1]).days
            if _gap_start > 30:
                st.warning(t("benchmark_coverage_late_start",
                              ticker=bench_ticker,
                              start=bd.index[0].strftime("%Y-%m-%d"),
                              is_start=combined.index[0].strftime("%Y-%m-%d")))
            if _gap_end > 30:
                st.warning(t("benchmark_coverage_stale_end",
                              ticker=bench_ticker,
                              end=bd.index[-1].strftime("%Y-%m-%d"),
                              days=_gap_end))
            bench_ret_is  = bd.reindex(df_in.index,  method="ffill")["asset"].pct_change().fillna(0).values
            bench_ret_oos = bd.reindex(df_out.index, method="ffill")["asset"].pct_change().fillna(0).values
            bench_name    = bench_ticker
        else:
            st.warning(t("warning_benchmark_not_found"))
            bench_ret_is  = cdi_is
            bench_ret_oos = cdi_oos
            bench_name    = t("bench_name_cdi")
    else:
        bench_ret_is  = cdi_is
        bench_ret_oos = cdi_oos
        bench_name    = t("bench_name_cdi")

    # Taxa base do fundo — varia conforme seleção do usuário
    if flat_mode_label == "zero":
        base_rate_is  = np.zeros(len(df_in))
        base_rate_oos = np.zeros(len(df_out))
    elif flat_mode_label == "fed_funds":
        base_rate_is  = build_rate_series(FOMC, df_in.index)
        base_rate_oos = build_rate_series(FOMC, df_out.index)
    elif flat_mode_label == "passivo_longo":
        base_rate_is  = bh_ret_in.copy()
        base_rate_oos = bh_ret_out.copy()
    elif flat_mode_label == "benchmark" and bench_ticker is not None:
        base_rate_is  = bench_ret_is  if bench_ret_is  is not None else cdi_is
        base_rate_oos = bench_ret_oos if bench_ret_oos is not None else cdi_oos
    else:  # cdi (default)
        base_rate_is  = cdi_is
        base_rate_oos = cdi_oos

    # Sinais e retornos (modelo Cota Master)
    pct_levels = [2.5,5.0,7.5,10.0,12.5,15.0,17.5,20.0,40.0,42.5,45.0,47.5,50.0,52.5,55.0,57.5,60.0,80.0,82.5,85.0,87.5,90.0,92.5,95.0,97.5]

    with st.spinner(t("spinner_running_is")):
        # excl_mask passado para dentro do loop: cp=0 em dias excluidos
        # garante que sinais nascidos no GFC/COVID nao vazam para apos o periodo
        pos_is, trades_is = get_signals_is(df_in, entry_high, entry_low, exit_rule, direction,
                                              calib_df=combined_is_calib,
                                              excl_mask=excl_mask_is)

        # Calcular retornos (bh_ret_in ja tem invert_ativo aplicado — nao redefinir aqui)
        if flat_mode_label == "zero":
            sr_is = compute_alpha_only(pos_is, bh_ret_in, long_only, hedge_spread_daily)
        else:
            sr_is = compute_br_fund_cota(pos_is, bh_ret_in, base_rate_is, long_only, hedge_spread_daily)

        # Override direto dos retornos nos dias excluidos — elimina qualquer vazamento
        # de np.roll ou posicao remanescente na borda do periodo
        if excl_mask_is.any():
            if flat_mode_label == "zero":
                sr_is[excl_mask_is] = 0.0
            else:
                sr_is[excl_mask_is] = base_rate_is[excl_mask_is]   # taxa base nos dias excluidos

        m_is  = calc_metrics(sr_is, pos_is, df_in.index)

    with st.spinner(t("spinner_expanding_pct")):
        lookup = precompute_expanding_pcts(df_in, df_out, sorted(set(pct_levels)))

    with st.spinner(t("spinner_running_oos")):
        pos_oos, trades_oos = get_signals_oos(df_out, entry_high, entry_low, exit_rule, direction, lookup)
        if flat_mode_label == "zero":
            sr_oos = compute_alpha_only(pos_oos, bh_ret_out, long_only, hedge_spread_daily)
        else:
            sr_oos = compute_br_fund_cota(pos_oos, bh_ret_out, base_rate_oos, long_only, hedge_spread_daily)
        m_oos  = calc_metrics(sr_oos, pos_oos, df_out.index)

    # Benchmark para gráfico (cumulativo IS+OOS encadeado)
    bench_cum_is  = pd.Series(np.cumprod(1+bench_ret_is)*100,   index=df_in.index)
    bench_is_end  = float(bench_cum_is.iloc[-1])
    bench_cum_oos = pd.Series(np.cumprod(1+bench_ret_oos)*bench_is_end, index=df_out.index)

    # Métricas do benchmark
    bm_is  = calc_metrics(bench_ret_is,  np.ones(len(df_in)),  df_in.index)
    bm_oos = calc_metrics(bench_ret_oos, np.ones(len(df_out)), df_out.index)

    # ── CARDS DE MÉTRICAS ─────────────────────────────────────────────────
    mode_lbl = t("mode_long_only") if long_only else t("mode_contrarian")
    st.markdown(f"""
    <div style="background:#0d0d0d;border:1px solid #2a2a2a;padding:6px 12px;margin-bottom:12px;
                font-family:'Courier New';font-size:0.75rem;color:#808080;">
    {ticker} &nbsp;|&nbsp; {mode_lbl} &nbsp;|&nbsp;
    P{entry_high:g}/P{entry_low:g} &nbsp;|&nbsp; {t("col_exit")}: {exit_label} &nbsp;|&nbsp;
    {t("label_model_master_quota")} | Spread hedge: {hedge_spread_bps} bps &nbsp;|&nbsp; Benchmark: {bench_name}
    </div>
    """, unsafe_allow_html=True)

    def _delta_html(strat_ret, bm_ret, label):
        # Alpha geometrico (correto): (1+estrategia)/(1+benchmark) - 1
        # Nunca subtracao aritmetica simples entre percentuais acumulados.
        diff = (1.0 + strat_ret) / (1.0 + bm_ret) - 1.0
        if diff > 0.01:
            clr, bg, arrow = "#00C805", "rgba(0,200,5,0.18)", "▲"
        elif diff < -0.01:
            clr, bg, arrow = "#FF4444", "rgba(255,68,68,0.18)", "▼"
        else:
            clr, bg, arrow = "#FFB800", "rgba(255,184,0,0.18)", "►"
        sign = "+" if diff >= 0 else ""
        return (f'<span style="background:{bg};color:{clr};font-size:0.72rem;'
                f'padding:1px 6px;border-radius:3px;font-family:Courier New;">'
                f'{arrow} {t("delta_vs_buyhold")}: {sign}{diff:.1%}</span>')

    c1,c2,c3,c4 = st.columns(4)
    c1.metric(t("metric_quota_is"),       f"{m_is['total_return']:.1%}")
    c1.markdown(_delta_html(m_is['total_return'], bm_is['total_return'], "IS"),
                unsafe_allow_html=True)
    c2.metric(t("metric_quota_oos"),  f"{m_oos['total_return']:.1%}")
    c2.markdown(_delta_html(m_oos['total_return'], bm_oos['total_return'], "OOS"),
                unsafe_allow_html=True)
    c3.metric(t("metric_sharpe"), f"{m_is['sharpe']:.2f}  /  {m_oos['sharpe']:.2f}")
    c4.metric(t("metric_maxdd"), f"{m_is['max_dd']:.1%}  /  {m_oos['max_dd']:.1%}")

    st.divider()

    # ── GRÁFICO ───────────────────────────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.48,0.52], vertical_spacing=0.22,
        subplot_titles=[t("chart_title_capital"), t("chart_title_riskapp")],
        specs=[[{"secondary_y": True}], [{"secondary_y": False}]],
    )

    # IS strategy — Cota Master (laranja Bloomberg)
    # Rebase: cota = 100 no ULTIMO dia do IS (nao no primeiro) — assim o OOS
    # comeca sempre em 100 e fica visualmente claro o desempenho fora da amostra.
    curve_label = t("curve_label_alpha_is") if flat_mode_label == "zero" else t("curve_label_quota_is")
    curve_label_oos = t("curve_label_alpha_oos") if flat_mode_label == "zero" else t("curve_label_quota_oos")
    _is_raw    = m_is["cum_series"]
    is_curve   = _is_raw / float(_is_raw.iloc[-1]) * 100
    fig.add_trace(go.Scatter(
        x=is_curve.index, y=is_curve.values,
        name=curve_label,
        line=dict(color="#FF7700", width=2.5),
    ), row=1, col=1)

    # OOS strategy — Cota Master (laranja pontilhado — continua do IS, que termina em 100)
    is_end_val = float(is_curve.iloc[-1])  # sempre 100.0
    oos_curve  = m_oos["cum_series"] * is_end_val
    fig.add_trace(go.Scatter(
        x=oos_curve.index, y=oos_curve.values,
        name=curve_label_oos,
        line=dict(color="#FF7700", width=2.5, dash="dot"),
    ), row=1, col=1)

    # Benchmark IS (cinza claro) — mesmo rebase: 100 no ultimo dia do IS
    _bench_is_raw = bench_cum_is / 100.0  # volta para fator cumulativo puro
    bench_cum_is_rebased = _bench_is_raw / float(_bench_is_raw.iloc[-1]) * 100
    fig.add_trace(go.Scatter(
        x=bench_cum_is_rebased.index, y=bench_cum_is_rebased.values,
        name=t("trace_buyhold_is", bench=bench_name),
        line=dict(color="#4A90D9", width=1.5, dash="dash"),
    ), row=1, col=1)

    # Benchmark OOS (continua do IS, que agora termina em 100)
    bench_is_end_rebased = float(bench_cum_is_rebased.iloc[-1])  # sempre 100.0
    bench_cum_oos_rebased = pd.Series(np.cumprod(1+bench_ret_oos) * bench_is_end_rebased, index=df_out.index)
    fig.add_trace(go.Scatter(
        x=bench_cum_oos_rebased.index, y=bench_cum_oos_rebased.values,
        name=t("trace_buyhold_oos", bench=bench_name),
        line=dict(color="#4A90D9", width=1.5),
    ), row=1, col=1)

    # Linha divisória IS | OOS
    _x_iso = is_end_ts.isoformat()
    fig.add_shape(
        type="line", xref="x", yref="paper",
        x0=_x_iso, x1=_x_iso, y0=0, y1=1,
        line=dict(dash="dash", color="#555555", width=1),
    )
    # Label "In-Sample" no ponto médio do IS
    _is_mid = (is_start_ts + (is_end_ts - is_start_ts) / 2).isoformat()
    fig.add_annotation(
        xref="x", yref="paper",
        x=_is_mid, y=1.0,
        text=t("annotation_is"),
        font=dict(color="#666666", size=10, family="Courier New"),
        showarrow=False,
        xanchor="center", yanchor="bottom",
    )
    # Label "Out-of-Sample" no ponto médio do OOS
    _oos_start = df_out.index[0]
    _oos_end   = df_out.index[-1]
    _oos_mid   = (_oos_start + (_oos_end - _oos_start) / 2).isoformat()
    fig.add_annotation(
        xref="x", yref="paper",
        x=_oos_mid, y=1.0,
        text=t("annotation_oos"),
        font=dict(color="#666666", size=10, family="Courier New"),
        showarrow=False,
        xanchor="center", yanchor="bottom",
    )

    # Risk Appetite indicator
    fig.add_trace(go.Scatter(
        x=combined.index, y=combined["indicator"],
        name=t("label_risk_appetite"),
        line=dict(color="#00BFFF", width=1),
        fill="tozeroy", fillcolor="rgba(0,191,255,0.05)",
        legend="legend2",
        hovertemplate=t("label_risk_appetite") + ": %{y:.3f}<extra></extra>",
    ), row=2, col=1)

    # Ativo selecionado — eixo direito do grafico de cotas
    _asset_prices = combined["asset"].copy()
    if invert_ativo:
        _asset_prices = 1.0 / _asset_prices  # perspectiva invertida (ex: ZAR/USD)
    fig.add_trace(go.Scatter(
        x=_asset_prices.index, y=_asset_prices.values,
        name=f"{ticker_display} " + t("label_rhs"),
        line=dict(color="#FFD700", width=1, dash="dot"),
        opacity=0.7,
    ), row=1, col=1, secondary_y=True)

    # Thresholds — IS: linha fixa | OOS: percentil expansivo dinâmico
    tH_is = float(np.percentile(df_in["indicator"].dropna(), entry_high))
    tL_is = float(np.percentile(df_in["indicator"].dropna(), entry_low))
    tM_is = float(np.percentile(df_in["indicator"].dropna(), exit_rule))
    for is_val, oos_arr, tag, clr in [
        (tH_is, lookup[entry_high], f"P{entry_high:g}", "#FF4444"),
        (tL_is, lookup[entry_low],  f"P{entry_low:g}",  "#44FF44"),
        (tM_is, lookup[exit_rule],  f"P{exit_rule:g} " + t("label_exit_suffix"), "#FFD700"),
    ]:
        # IS: linha horizontal fixa (sem legenda — OOS representa) — hover ativo
        fig.add_trace(go.Scatter(
            x=df_in.index, y=np.full(len(df_in), is_val),
            name=tag, line=dict(color=clr, width=1, dash="dot"),
            showlegend=False,
            hovertemplate=f"{tag} " + t("label_is_suffix") + ": " + "%{y:.2f}<extra></extra>",
        ), row=2, col=1)
        # OOS: percentil expansivo — aparece na legend2 — hover ativo
        fig.add_trace(go.Scatter(
            x=df_out.index, y=oos_arr,
            name=tag, line=dict(color=clr, width=1, dash="dot"),
            showlegend=True, legend="legend2",
            hovertemplate=f"{tag} " + t("label_oos_suffix") + ": " + "%{y:.2f}<extra></extra>",
        ), row=2, col=1)
        # Sem anotacao fixa no grafico — valor aparece via hover ao passar o mouse

    # Layout Bloomberg
    fig.update_layout(
        height=950, hovermode="x unified",
        margin=dict(t=90, b=120, l=50, r=70),
        legend=dict(
            orientation="h", x=0, y=0.46, yref="paper",
            font=dict(size=11, color="#c0c0c0", family="Courier New"),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        legend2=dict(
            orientation="h", x=0, y=-0.10, yref="paper",
            font=dict(size=11, color="#c0c0c0", family="Courier New"),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        **{k: v for k, v in BBG_LAYOUT.items() if k != "margin"},
    )
    fig.update_xaxes(**dict(gridcolor="#1a1a1a", zerolinecolor="#333"))
    fig.update_yaxes(row=1, col=1, title_text=t("yaxis_base100"),
                     gridcolor="#1a1a1a", tickfont=dict(color="#c0c0c0", size=11))
    fig.update_yaxes(row=2, col=1, title_text=t("yaxis_indicator"),
                     gridcolor="#1a1a1a", tickfont=dict(color="#c0c0c0", size=11))
    _ap = _asset_prices.dropna()
    _ap_min = float(_ap.min()); _ap_max = float(_ap.max())
    _ap_pad = (_ap_max - _ap_min) * 0.08
    fig.update_yaxes(row=1, col=1, secondary_y=True,
                     title_text=ticker_display,
                     tickfont=dict(color="#FFD700", size=10),
                     tickformat=".2f",
                     range=[_ap_min - _ap_pad, _ap_max + _ap_pad],
                     showgrid=False, zeroline=False)
    # Títulos dos subplots em laranja (ignorar anotação IS|OOS)
    for ann in fig.layout.annotations:
        if ann.text and "IS" in ann.text and "OOS" in ann.text:
            continue  # ja estilizado via add_annotation
        ann.font.color  = "#FF7700"
        ann.font.size   = 12
        ann.font.family = "Courier New"
        ann.y = ann.y + 0.04 if ann.y is not None else ann.y  # empurra titulo pra cima

    render_autoscale_chart(fig, height=950)

    # ── TABELA DE MÉTRICAS ────────────────────────────────────────────────
    st.markdown(f"<span style='color:#FF7700;font-size:0.9rem;font-weight:bold;'>{t('metrics_table_title')}</span>",
                unsafe_allow_html=True)

    tab_m = pd.DataFrame({
        t("col_metric"): [t("row_total_return"),t("row_cagr"),t("row_sharpe"),t("row_maxdd"),t("row_ntrades"),t("row_pct_active")],
        t("col_is_strategy"): [
            f"{m_is['total_return']:.1%}", f"{m_is['cagr']:.1%}",
            f"{m_is['sharpe']:.3f}",       f"{m_is['max_dd']:.1%}",
            m_is["n_trades"],              f"{m_is['pct_invested']:.0%}",
        ],
        t("col_is_buyhold", bench=bench_name): [
            f"{bm_is['total_return']:.1%}", f"{bm_is['cagr']:.1%}",
            f"{bm_is['sharpe']:.3f}",       f"{bm_is['max_dd']:.1%}",
            "—", "100%",
        ],
        t("col_oos_strategy"): [
            f"{m_oos['total_return']:.1%}", f"{m_oos['cagr']:.1%}",
            f"{m_oos['sharpe']:.3f}",       f"{m_oos['max_dd']:.1%}",
            m_oos["n_trades"],              f"{m_oos['pct_invested']:.0%}",
        ],
        t("col_oos_buyhold", bench=bench_name): [
            f"{bm_oos['total_return']:.1%}", f"{bm_oos['cagr']:.1%}",
            f"{bm_oos['sharpe']:.3f}",       f"{bm_oos['max_dd']:.1%}",
            "—", "100%",
        ],
    })
    st.dataframe(tab_m, use_container_width=True, hide_index=True)

    # ── LOG DE TRADES ──────────────────────────────────────────────────────
    st.markdown(f"<span style='color:#FF7700;font-size:0.9rem;font-weight:bold;'>{t('trades_log_title')}</span>",
                unsafe_allow_html=True)
    t_is, t_oos = st.tabs([
        t("tab_is_trades", n=len(trades_is)),
        t("tab_oos_trades", n=len(trades_oos)),
    ])
    _COL_RENAME = {
        "Entrada": t("col_entry"), "Saída": t("col_exit"), "Dias": t("col_days"),
        "Lado": t("col_side"), "Retorno": t("col_return"), "MaxDD Trade": t("col_maxdd_trade"),
    }
    _COL_RET, _COL_DD, _COL_SIDE, _COL_DAYS = t("col_return"), t("col_maxdd_trade"), t("col_side"), t("col_days")
    for tab, tdf in [(t_is, trades_is), (t_oos, trades_oos)]:
        with tab:
            if tdf.empty:
                st.info(t("info_no_trades"))
            else:
                def style_trades(df):
                    df = df.rename(columns=_COL_RENAME)
                    df[_COL_SIDE] = df[_COL_SIDE].map({"LONG": t("side_long"), "SHORT": t("side_short")}).fillna(df[_COL_SIDE])
                    def rc(row):
                        c = "#1a3a1a" if row[_COL_RET]>0 else ("#3a1a1a" if row[_COL_RET]<0 else "")
                        return [f"background-color:{c};color:#d0d0d0"] * len(row)
                    return df.style.apply(rc,axis=1).format({_COL_RET:"{:.2%}",_COL_DD:"{:.1%}"})
                st.dataframe(style_trades(tdf.copy()), use_container_width=True, hide_index=True)
                wins = int((tdf["Retorno"]>0).sum())
                st.caption(t("caption_trades_summary",
                              wins=wins, n=len(tdf), pct=wins*100//len(tdf),
                              avg=f"{tdf['Retorno'].mean():.2%}", days=f"{tdf['Dias'].mean():.0f}"))


    # ── TESTES DE CONSISTENCIA ────────────────────────────────────────────
    st.markdown(f"<span style='color:#FF7700;font-size:0.9rem;font-weight:bold;'>{t('consistency_title')}</span>",
                unsafe_allow_html=True)
    st.markdown(
        '<span title="' + t("consistency_tooltip_text").replace("\n", "&#10;") +
        '" style="color:#FF7700;font-size:0.75rem;font-family:Courier New;'
        'border-bottom:1px dotted #FF7700;cursor:help;">' + t("consistency_tooltip_label") + '</span>',
        unsafe_allow_html=True
    )
    issues = []
    warnings_list = []

    # 1. Datas nao se sobrepoe
    if df_in.index[-1] >= df_out.index[0]:
        issues.append(t("issue_overlap", d1=df_in.index[-1].date(), d2=df_out.index[0].date()))
    else:
        gap = (df_out.index[0] - df_in.index[-1]).days
        if gap > 5:
            warnings_list.append(t("warning_gap", gap=gap))

    # 2. Numero minimo de trades
    if len(trades_is) < 5:
        warnings_list.append(t("warning_few_trades_is", n=len(trades_is)))
    if len(trades_oos) < 3:
        warnings_list.append(t("warning_few_trades_oos", n=len(trades_oos)))

    # 3. Retornos extremos (possivel erro de dados)
    # Retornos extremos — apenas dias com posicao aberta (pos != 0)
    # pos_is e pos_oos: sinal do dia anterior aplicado ao retorno do dia
    _pos_is_shifted  = np.roll(pos_is,  1); _pos_is_shifted[0]  = 0
    _pos_oos_shifted = np.roll(pos_oos, 1); _pos_oos_shifted[0] = 0
    _invested_is  = (_pos_is_shifted  != 0)
    _invested_oos = (_pos_oos_shifted != 0)

    abs_ret_is  = np.abs(bh_ret_in).copy()
    abs_ret_is[~_invested_is]  = 0.0   # so dias posicionados
    abs_ret_oos = np.abs(bh_ret_out).copy()
    abs_ret_oos[~_invested_oos] = 0.0  # so dias posicionados
    max_1d_is   = float(abs_ret_is.max())
    max_1d_oos  = float(abs_ret_oos.max())
    if max_1d_is > 0.30:
        _dt_is = pd.Series(abs_ret_is, index=df_in.index).idxmax().strftime("%d/%m/%Y")
        warnings_list.append(t("warning_extreme_return_is", pct=f"{max_1d_is:.1%}", date=_dt_is))
    if max_1d_oos > 0.30:
        _dt_oos = pd.Series(abs_ret_oos, index=df_out.index).idxmax().strftime("%d/%m/%Y")
        warnings_list.append(t("warning_extreme_return_oos", pct=f"{max_1d_oos:.1%}", date=_dt_oos))

    # 4. IS nao pode ter lookahead (percentis OOS calculados corretamente)
    pct_final_oos = float(lookup[entry_high][-1])
    pct_is_val    = float(np.percentile(df_in["indicator"].dropna(), entry_high))
    if abs(pct_final_oos - pct_is_val) < 1e-6 and len(df_out) > 50:
        issues.append(t("issue_lookahead", eh=f"{entry_high:g}"))

    # 5. Porcentagem de tempo ativo
    if m_oos["pct_invested"] < 0.05:
        warnings_list.append(t("warning_low_invested", pct=f"{m_oos['pct_invested']:.0%}"))

    col_ok, col_warn, col_err = st.columns(3)
    ok_count = max(0, 5 - len(issues) - len(warnings_list))
    col_ok.metric(t("metric_checks_ok"), ok_count)
    col_warn.metric(t("metric_warnings"), len(warnings_list))
    col_err.metric(t("metric_errors"), len(issues))

    if issues:
        for msg in issues:
            st.error(t("label_error_prefix", msg=msg))
    if warnings_list:
        for msg in warnings_list:
            st.warning(t("label_warning_prefix", msg=msg))
    if not issues and not warnings_list:
        st.success(t("success_consistency"))

elif opt_btn or (not run_btn and st.session_state.get('opt_agg') is not None):
    if opt_btn:
        ra2 = load_risk_appetite()
        invert_ativo2   = ticker.endswith("~inv")
        ticker_display2 = ticker.replace("~inv", "") + (" [inv]" if invert_ativo2 else "")
        with st.spinner(t("spinner_loading_asset", ticker=ticker_display2)):
            asset2 = download_asset(ticker, str(ra2.index[0].date()), str(ra2.index[-1].date()))
        if asset2 is None or asset2.empty:
            st.error(t("error_ticker_not_found_short", ticker=ticker)); st.stop()
        combined2 = ra2[["indicator"]].join(asset2, how="inner").dropna()
        n_anos2 = (combined2.index[-1] - combined2.index[0]).days / 365.25
        if n_anos2 < 5.5:
            st.error(t("error_insufficient_years", years=f"{n_anos2:.1f}", anos=f"{n_anos2:.1f}")); st.stop()
        prog = st.progress(0, text=t("progress_starting"))
        agg_df, detail_list = run_walkforward_optimizer(
            combined=combined2,
            excl_gfc=excl_gfc, excl_covid=excl_covid,
            excl_custom=excl_custom, excl_start=excl_start, excl_end=excl_end,
            invert_ativo=invert_ativo2, long_only=long_only,
            flat_mode_label=flat_mode_label,
            progress_bar=prog,
        )
        prog.empty()
        if agg_df is None or agg_df.empty:
            st.warning(t("warning_insufficient_wf")); st.stop()
        st.session_state["opt_agg"]      = agg_df
        st.session_state["opt_detail"]   = detail_list
        st.session_state["opt_ticker"]   = ticker_display2
        st.session_state["opt_combined"] = combined2
        st.session_state["opt_invert"]   = invert_ativo2
        ticker_display = ticker_display2
    else:
        agg_df         = st.session_state["opt_agg"]
        detail_list    = st.session_state["opt_detail"]
        ticker_display = st.session_state.get("opt_ticker", ticker)
        combined2      = st.session_state.get("opt_combined")
        invert_ativo2  = st.session_state.get("opt_invert", ticker.endswith("~inv"))

    if agg_df is None or agg_df.empty:
        st.warning(t("warning_insufficient_wf")); st.stop()

    n_wins = int(agg_df["n_windows"].iloc[0])

    st.markdown(
        f'<div style="background:#0d0d0d;border:1px solid #2a2a2a;padding:6px 12px;'
        f'margin-bottom:12px;font-family:Courier New;font-size:0.75rem;color:#808080;">'
        + t("card_optimizer", ticker=ticker_display, n=n_wins) +
        '</div>',
        unsafe_allow_html=True
    )

    def _get_detail(eh, el, ex):
        for d in detail_list:
            if d["eh"] == eh and d["el"] == el and d["ex"] == ex:
                return d
        return None

    def _render_window_popup(ws, chart_key):
        with st.container(border=True):
            st.markdown(
                f"<span style='color:#FF7700;font-size:0.82rem;font-weight:bold;'>"
                f"{t('window_detail_title', window=ws['window'])}</span>",
                unsafe_allow_html=True
            )
            dates = pd.to_datetime(ws["dates"])
            mini_layout = {**BBG_LAYOUT, "margin": dict(t=30, b=20, l=35, r=10)}
            c_eq, c_ind = st.columns(2)
            with c_eq:
                fig_eq = go.Figure()
                fig_eq.add_trace(go.Scatter(x=dates, y=ws["curve"], mode="lines",
                                             line=dict(color="#FF7700", width=1.5)))
                fig_eq.update_layout(height=220, title=t("mini_chart_equity_title"),
                                      showlegend=False, **mini_layout)
                st.plotly_chart(fig_eq, use_container_width=True, theme=None, key=f"mini_eq_{chart_key}_{ws['window']}")
            with c_ind:
                fig_ind = go.Figure()
                fig_ind.add_trace(go.Scatter(x=dates, y=ws["indicator"], mode="lines",
                                              line=dict(color="#4A90D9", width=1.2)))
                fig_ind.add_hline(y=ws["tH"], line_dash="dot", line_color="#CC4444",
                                   annotation_text=t("mini_chart_entry_short"), annotation_font_size=9)
                fig_ind.add_hline(y=ws["tL"], line_dash="dot", line_color="#4ABF4A",
                                   annotation_text=t("mini_chart_entry_long"), annotation_font_size=9)
                fig_ind.add_hline(y=ws["tM"], line_dash="dash", line_color="#999999",
                                   annotation_text=t("mini_chart_exit"), annotation_font_size=9)
                fig_ind.update_layout(height=220, title=t("mini_chart_indicator_title"),
                                       showlegend=False, **mini_layout)
                st.plotly_chart(fig_ind, use_container_width=True, theme=None, key=f"mini_ind_{chart_key}_{ws['window']}")

    def _wf_bar(detail, metric, title, col_pos="#FF7700", col_neg="#CC4444",
                series_data=None, chart_key="wf_bar"):
        wdf = pd.DataFrame(detail["windows"])
        vals = wdf[metric].tolist()
        colors = [col_pos if v >= 0 else col_neg for v in vals]
        fig_w = go.Figure()
        fig_w.add_trace(go.Bar(x=wdf["window"].tolist(), y=vals, marker_color=colors))
        fig_w.add_hline(y=0, line_color="#555555")
        layout_wf = {**BBG_LAYOUT, "margin": dict(t=36, b=20, l=20, r=20)}
        fig_w.update_layout(height=200, title=title, showlegend=False, **layout_wf)
        fig_w.update_xaxes(tickangle=-45, tickfont=dict(size=9))
        if series_data is not None:
            event = st.plotly_chart(fig_w, use_container_width=True, theme=None, on_select="rerun",
                                     selection_mode="points", key=chart_key)
            pts = (event or {}).get("selection", {}).get("points", [])
            if pts:
                pidx = pts[0].get("point_index")
                if pidx is not None and 0 <= pidx < len(series_data):
                    _render_window_popup(series_data[pidx], chart_key)
        else:
            st.plotly_chart(fig_w, use_container_width=True, theme=None)

    # ── CRITERIO 1: Maximo Sharpe ─────────────────────────────────────────
    st.markdown(
        "<span style='color:#FF7700;font-size:0.9rem;font-weight:bold;'>"
        + t("criterio1_title") + "</span>",
        unsafe_allow_html=True
    )
    st.caption(t("caption_trimmed_core"))
    top_sh = agg_df.sort_values("avg_sharpe", ascending=False).head(5).reset_index(drop=True)
    for rank, row in top_sh.iterrows():
        c_info, c_btn, c_view = st.columns([5, 1, 1])
        _eh_s, _el_s, _ex_s = f"{row['eh']:g}", f"{row['el']:g}", f"{row['ex']:g}"
        _sh_s = f"{row['avg_sharpe']:.3f}"
        _core60_sh = t('row_core60', med=f"{row['sh_trim_med']:.3f}", min=f"{row['sh_trim_min']:.3f}", max=f"{row['sh_trim_max']:.3f}")
        _ret_s, _dd_s, _win_s = f"{row['avg_ret']:.1%}", f"{row['avg_dd']:.1%}", f"{row['pct_win']:.0%}"
        c_info.markdown(
            "<span style='font-size:0.78rem;'>"
            f"**{t('row_rank', rank=rank+1)}** &nbsp; "
            f"**{t('row_entry', eh=_eh_s, el=_el_s)}** &nbsp;|&nbsp; "
            f"**{t('row_exit', ex=_ex_s)}** &nbsp;|&nbsp; "
            f"**{t('row_sharpe_median', v=_sh_s)}** &nbsp;|&nbsp; "
            f"{_core60_sh} &nbsp;|&nbsp; "
            f"{t('row_ret', v=_ret_s)} &nbsp;|&nbsp; "
            f"{t('row_dd', v=_dd_s)} &nbsp;|&nbsp; "
            f"{t('row_win', v=_win_s)}</span>",
            unsafe_allow_html=True
        )
        if c_btn.button(t("button_use"), key=f"sh_{rank}"):
            st.session_state["_new_eh"] = float(row["eh"])
            st.session_state["_new_el"] = float(row["el"])
            st.session_state["_new_ex"] = float(row["ex"])
            st.session_state["run_after_usar"] = True
            st.rerun()
        if c_view.button(t("button_view_chart"), key=f"view_sh_{rank}"):
            st.session_state["wf_view_rank_sh"] = rank

    sel_rank_sh = min(st.session_state.get("wf_view_rank_sh", 0), len(top_sh) - 1)
    best_sh = top_sh.iloc[sel_rank_sh]
    det_sh  = _get_detail(best_sh["eh"], best_sh["el"], best_sh["ex"])
    if det_sh:
        series_sh = compute_window_series(
            combined2, best_sh["eh"], best_sh["el"], best_sh["ex"],
            excl_gfc, excl_covid, excl_custom, excl_start, excl_end,
            invert_ativo2, long_only,
        )
        st.caption(t("viewing_rank_label", rank=sel_rank_sh + 1))
        st.caption(t("caption_click_bar_detail"))
        _wf_bar(det_sh, "sharpe",
                t("chart_title_sharpe_wf", rank=sel_rank_sh + 1, eh=f"{best_sh['eh']:g}", el=f"{best_sh['el']:g}", ex=f"{best_sh['ex']:g}"),
                series_data=series_sh, chart_key=f"wf_bar_sharpe_r{sel_rank_sh}")

    st.divider()

    # ── CRITERIO 2: Minimo Drawdown com retorno positivo ──────────────────
    st.markdown(
        "<span style='color:#FF7700;font-size:0.9rem;font-weight:bold;'>"
        + t("criterio2_title") + "</span>",
        unsafe_allow_html=True
    )
    st.caption(t("caption_trimmed_core"))
    agg_pos = agg_df[agg_df["avg_ret"] > 0].copy()
    if agg_pos.empty:
        st.info(t("info_no_positive_combo"))
    else:
        top_dd = agg_pos.sort_values("avg_dd", ascending=False).head(5).reset_index(drop=True)
        for rank, row in top_dd.iterrows():
            c_info, c_btn, c_view = st.columns([5, 1, 1])
            _eh_s, _el_s, _ex_s = f"{row['eh']:g}", f"{row['el']:g}", f"{row['ex']:g}"
            _dd_s = f"{row['avg_dd']:.1%}"
            _core60_dd = t('row_core60', med=f"{row['dd_trim_med']:.1%}", min=f"{row['dd_trim_min']:.1%}", max=f"{row['dd_trim_max']:.1%}")
            _sh_s, _ret_s, _win_s = f"{row['avg_sharpe']:.3f}", f"{row['avg_ret']:.1%}", f"{row['pct_win']:.0%}"
            c_info.markdown(
                "<span style='font-size:0.78rem;'>"
                f"**{t('row_rank', rank=rank+1)}** &nbsp; "
                f"**{t('row_entry', eh=_eh_s, el=_el_s)}** &nbsp;|&nbsp; "
                f"**{t('row_exit', ex=_ex_s)}** &nbsp;|&nbsp; "
                f"**{t('row_dd_median', v=_dd_s)}** &nbsp;|&nbsp; "
                f"{_core60_dd} &nbsp;|&nbsp; "
                f"{t('row_sharpe_median', v=_sh_s)} &nbsp;|&nbsp; "
                f"{t('row_ret', v=_ret_s)} &nbsp;|&nbsp; "
                f"{t('row_win', v=_win_s)}</span>",
                unsafe_allow_html=True
            )
            if c_btn.button(t("button_use"), key=f"dd_{rank}"):
                st.session_state["_new_eh"] = float(row["eh"])
                st.session_state["_new_el"] = float(row["el"])
                st.session_state["_new_ex"] = float(row["ex"])
                st.session_state["run_after_usar"] = True
                st.rerun()
            if c_view.button(t("button_view_chart"), key=f"view_dd_{rank}"):
                st.session_state["wf_view_rank_dd"] = rank

        sel_rank_dd = min(st.session_state.get("wf_view_rank_dd", 0), len(top_dd) - 1)
        best_dd = top_dd.iloc[sel_rank_dd]
        det_dd  = _get_detail(best_dd["eh"], best_dd["el"], best_dd["ex"])
        if det_dd:
            series_dd = compute_window_series(
                combined2, best_dd["eh"], best_dd["el"], best_dd["ex"],
                excl_gfc, excl_covid, excl_custom, excl_start, excl_end,
                invert_ativo2, long_only,
            )
            st.caption(t("viewing_rank_label", rank=sel_rank_dd + 1))
            st.caption(t("caption_click_bar_detail"))
            _wf_bar(det_dd, "dd",
                    t("chart_title_dd_wf", rank=sel_rank_dd + 1, eh=f"{best_dd['eh']:g}", el=f"{best_dd['el']:g}", ex=f"{best_dd['ex']:g}"),
                    col_pos="#4A90D9", col_neg="#4A90D9",
                    series_data=series_dd, chart_key=f"wf_bar_dd_r{sel_rank_dd}")

    st.caption(t("caption_click_use"))

else:
    st.markdown(f"""
    <div style="border:1px solid #2a2a2a;padding:20px;background:#0a0a0a;font-family:'Courier New';color:#606060;">
    <div style="color:#FF7700;font-size:0.85rem;margin-bottom:12px;">{t("instructions_title")}</div>
    {t("instructions_1")}<br>
    {t("instructions_2")}<br>
    {t("instructions_3")}<br>
    &nbsp;&nbsp;&nbsp;└ {t("instructions_4")}<br>
    &nbsp;&nbsp;&nbsp;└ {t("instructions_5")}<br>
    <br>
    <span style="color:#606060;font-size:0.7rem;">
    {t("instructions_footer")}
    </span>
    </div>
    """, unsafe_allow_html=True)
