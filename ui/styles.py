"""SWAYAMYAN UI Design System & Global CSS Styling.

Refined global design system featuring:
1. Sharp 90-degree rectangular geometry (0px border-radius throughout all components).
2. Complementary typography pair:
   - Headings: DM Serif Display (for elegant editorial headlines and major titles).
   - Body & Interface: Inter (for clean, modern readability across paragraphs, navigation,
     tables, inputs, buttons, and scientific data).
3. White-dominant backgrounds, near-black typography, and teal accents with subtle glassmorphism.
"""

def get_custom_css():
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --sw-bg: #FFFFFF;
        --sw-bg-alt: #F4F8F8;
        --sw-border: #DCE6E8;
        --sw-text-main: #0A1F2C;
        --sw-text-muted: #52677A;
        --sw-text-subtle: #7A8DA0;
        --sw-teal: #0B6E6E;
        --sw-teal-dark: #095858;
        --sw-aqua: #5CC8C0;
        --sw-accent: #F2994A;
        --sw-banner: #0A3D42;
        --sw-teal-light: #F4F8F8;
        --sw-teal-border: rgba(11, 110, 110, 0.22);
        --sw-teal-glow: rgba(11, 110, 110, 0.12);
        --sw-font-display: 'DM Serif Display', Georgia, 'Times New Roman', serif;
        --sw-font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --sw-surface: rgba(255, 255, 255, 0.95);
        --sw-surface-glass: rgba(255, 255, 255, 0.88);
        --sw-border-dark: #0A1F2C;
        --sw-radius-sm: 0px;
        --sw-radius-md: 0px;
        --sw-radius-lg: 0px;
        --sw-radius-full: 0px;
        --sw-shadow-card: 0 4px 20px -4px rgba(10, 31, 44, 0.05), 0 0 0 1px rgba(10, 31, 44, 0.04);
        --sw-shadow-hover: 0 10px 28px -6px rgba(11, 110, 110, 0.16), 0 0 0 1px rgba(11, 110, 110, 0.28);
    }

    /* GLOBAL MANDATORY SHARP 90-DEGREE GEOMETRY */
    *, *::before, *::after {
        border-radius: 0px !important;
    }

    /* Staggered Hero Fade-Up Animations */
    @keyframes heroFadeUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .sw-hero-tag {
        animation: heroFadeUp 400ms ease-out 0ms both;
    }
    .sw-hero-h1 {
        animation: heroFadeUp 400ms ease-out 80ms both;
    }
    .sw-hero-subhead {
        animation: heroFadeUp 400ms ease-out 160ms both;
    }
    .sw-hero-btns {
        animation: heroFadeUp 400ms ease-out 240ms both;
    }

    /* Base Body & App Font: Inter */
    .stApp {
        background-color: var(--sw-bg) !important;
        font-family: var(--sw-font-sans) !important;
        color: var(--sw-text-main) !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Top navigation / header */
    header[data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(14px) !important;
        border-bottom: 1px solid var(--sw-border) !important;
        border-radius: 0px !important;
    }

    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 5rem !important;
        max-width: 1240px !important;
    }

    /* Major section headings: bold or medium-weight Inter */
    h1, h2, h3, h4, h5, h6 {
        font-family: var(--sw-font-sans) !important;
        color: var(--sw-text-main) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.2 !important;
    }

    .sw-hero-h1 {
        font-family: var(--sw-font-display) !important;
        font-weight: 400 !important;
        letter-spacing: -0.01em !important;
        line-height: 1.08 !important;
    }

    .sw-hero-h1 em {
        font-family: var(--sw-font-display) !important;
        font-style: italic !important;
        font-weight: 400 !important;
    }

    html {
        scroll-behavior: smooth;
    }

    #platform, #method, #datasets {
        scroll-margin-top: 80px;
    }

    h1 {
        font-size: 2.4rem !important;
    }

    h2 {
        font-size: 1.85rem !important;
    }

    h3 {
        font-size: 1.35rem !important;
        font-weight: 600 !important;
    }

    h4, h5, h6 {
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        line-height: 1.25 !important;
    }

    /* Body text, UI labels, links: Inter */
    p, label, li, a {
        font-family: var(--sw-font-sans);
        line-height: 1.6;
    }

    /* Selective editorial serif styling */
    .sw-editorial, .sw-serif-emphasis {
        font-family: var(--sw-font-display) !important;
        font-style: italic !important;
        font-weight: 400 !important;
        color: var(--sw-text-main) !important;
    }

    .sw-label-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-family: var(--sw-font-sans) !important;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--sw-teal-dark);
        background: var(--sw-teal-light);
        border: 1px solid var(--sw-teal-border);
        border-radius: 0px !important;
        padding: 5px 12px;
    }

    .sw-section-tag {
        font-family: var(--sw-font-sans) !important;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--sw-teal);
        margin-bottom: 0.5rem;
        display: block;
    }

    /* Sharp Rectangular Glass Cards */
    .sw-card {
        background: var(--sw-surface-glass);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid var(--sw-border);
        border-radius: 0px !important;
        padding: 28px 32px;
        box-shadow: var(--sw-shadow-card);
        transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.22s ease;
    }

    .sw-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--sw-shadow-hover);
        border-color: var(--sw-teal);
    }

    /* Floating Metric Panel */
    .sw-floating-metric {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(16px);
        border: 1px solid var(--sw-border);
        border-radius: 0px !important;
        padding: 16px 22px;
        box-shadow: 0 10px 24px -6px rgba(0, 0, 0, 0.06);
    }

    .st-key-cta, .sw-cta-banner {
        background: var(--sw-banner) !important;
        background-image: none !important;
        border: 1px solid var(--sw-teal-dark) !important;
        border-radius: 0px !important;
        padding: 52px 48px !important;
        color: #ffffff !important;
        box-shadow: 0 18px 40px -10px rgba(10, 61, 66, 0.28);
    }

    /* Target the inner vertical block that Streamlit nests inside st.container(key=) */
    .st-key-cta > div[data-testid="stVerticalBlockBorderWrapper"],
    .st-key-cta > div[data-testid="stVerticalBlock"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }

    .sw-cta-banner h2, .st-key-cta h2 {
        color: #ffffff !important;
        font-family: var(--sw-font-display) !important;
        font-weight: 400 !important;
    }

    .st-key-cta p, .sw-cta-banner p {
        color: #d1fae5 !important;
    }

    .st-key-cta div.stButton > button {
        background-color: var(--sw-aqua) !important;
        border-color: var(--sw-aqua) !important;
        color: #0A1F2C !important;
        font-weight: 700 !important;
        padding: 0.65rem 1.6rem !important;
    }

    .st-key-cta div.stButton > button:hover {
        background-color: #ffffff !important;
        border-color: #ffffff !important;
        color: var(--sw-teal) !important;
    }

    /* Sharp Rectangular Buttons (Inter) */
    div.stButton > button {
        border-radius: 0px !important;
        font-family: var(--sw-font-sans) !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        letter-spacing: -0.01em !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
        border: 1px solid var(--sw-border-dark) !important;
        background-color: #ffffff !important;
        color: var(--sw-text-main) !important;
        box-shadow: none !important;
    }

    div.stButton > button:hover {
        border-color: var(--sw-teal) !important;
        color: var(--sw-teal) !important;
        background-color: var(--sw-teal-light) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px var(--sw-teal-glow) !important;
    }

    div.stButton > button[kind="primary"] {
        background-color: var(--sw-teal) !important;
        border-color: var(--sw-teal) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 14px var(--sw-teal-glow) !important;
    }

    div.stButton > button[kind="primary"]:hover {
        background-color: var(--sw-teal-dark) !important;
        border-color: var(--sw-teal-dark) !important;
        color: #ffffff !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 18px rgba(11, 110, 110, 0.3) !important;
    }

    div.stDownloadButton > button {
        border-radius: 0px !important;
        font-family: var(--sw-font-sans) !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        letter-spacing: -0.01em !important;
        padding: 0.55rem 1.3rem !important;
        background-color: var(--sw-teal-light) !important;
        color: var(--sw-teal-dark) !important;
        border: 1px solid var(--sw-teal-border) !important;
        transition: all 0.2s ease !important;
    }

    div.stDownloadButton > button:hover {
        background-color: var(--sw-teal) !important;
        color: #ffffff !important;
        border-color: var(--sw-teal) !important;
        box-shadow: 0 4px 14px var(--sw-teal-glow) !important;
    }

    /* Metric Panels (Inter) */
    div[data-testid="stMetric"] {
        background: var(--sw-surface-glass);
        backdrop-filter: blur(10px);
        border: 1px solid var(--sw-teal-border);
        border-radius: 0px !important;
        padding: 18px 24px;
        box-shadow: var(--sw-shadow-card);
    }

    div[data-testid="stMetricLabel"] {
        font-family: var(--sw-font-sans) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: var(--sw-text-muted) !important;
        font-weight: 600 !important;
    }

    div[data-testid="stMetricValue"] {
        font-family: var(--sw-font-sans) !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        letter-spacing: -0.025em !important;
        color: var(--sw-text-main) !important;
        line-height: 1.15 !important;
    }

    /* Sharp Stepper Navigation (Inter) */
    .sw-stepper-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #ffffff;
        border: 1px solid var(--sw-border);
        border-radius: 0px !important;
        padding: 12px 22px;
        margin-bottom: 26px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
    }

    .sw-step-item {
        display: flex;
        align-items: center;
        gap: 10px;
        color: var(--sw-text-muted);
        font-size: 0.92rem;
        font-weight: 500;
        font-family: var(--sw-font-sans) !important;
    }

    .sw-step-item.active {
        color: var(--sw-teal-dark);
        font-weight: 700;
    }

    .sw-step-item.completed {
        color: var(--sw-text-main);
    }

    .sw-step-badge {
        width: 26px;
        height: 26px;
        border-radius: 0px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 700;
        background: #f1f5f9;
        color: var(--sw-text-subtle);
        border: 1px solid var(--sw-border);
        font-family: var(--sw-font-sans) !important;
    }

    .sw-step-item.active .sw-step-badge {
        background: var(--sw-teal);
        color: #ffffff;
        border-color: var(--sw-teal);
    }

    .sw-step-item.completed .sw-step-badge {
        background: var(--sw-teal-light);
        color: var(--sw-teal-dark);
        border-color: var(--sw-teal-border);
    }

    .sw-step-divider {
        flex: 1;
        height: 1px;
        background: var(--sw-border);
        margin: 0 16px;
    }

    .sw-step-divider.active {
        background: var(--sw-teal);
    }

    /* Form Inputs and Selects (Inter, Sharp 90-degree) */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] [role="combobox"],
    input, select, textarea {
        border-radius: 0px !important;
        font-family: var(--sw-font-sans) !important;
        font-size: 0.92rem !important;
    }

    div[data-baseweb="input"],
    div[data-baseweb="select"] {
        border-radius: 0px !important;
    }

    div[data-baseweb="input"] {
        border: 1px solid var(--sw-border) !important;
    }

    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: var(--sw-teal) !important;
        box-shadow: 0 0 0 1px var(--sw-teal) !important;
    }

    /* Tables & DataFrames (Inter, sharp, legible, zero clipping) */
    table, th, td {
        font-family: var(--sw-font-sans) !important;
        font-size: 0.88rem !important;
        border-radius: 0px !important;
    }

    th {
        font-weight: 600 !important;
        color: var(--sw-text-main) !important;
        background-color: #f8fafc !important;
        letter-spacing: 0.03em !important;
    }

    td {
        color: var(--sw-text-main) !important;
    }

    /* Bordered containers: sharp corners only */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 0 !important;
    }

    /* Expanders: sharp, clean */
    div[data-testid="stExpander"] details {
        border: 1px solid var(--sw-border) !important;
        border-radius: 0 !important;
        background: #fff !important;
    }

    div[data-testid="stExpander"] summary p {
        font-family: var(--sw-font-sans) !important;
        font-weight: 600 !important;
        margin: 0 !important;
    }

    div[data-testid="stAlert"] {
        border-radius: 0px !important;
        border: 1px solid var(--sw-teal-border) !important;
        background-color: var(--sw-teal-light) !important;
        color: var(--sw-teal-dark) !important;
        font-family: var(--sw-font-sans) !important;
    }

    /* Radio and Checkbox alignment */
    div[data-testid="stRadio"] label, div[data-testid="stCheckbox"] label {
        font-family: var(--sw-font-sans) !important;
        font-size: 0.92rem !important;
    }

    /* Responsive adjustments */
    @media (max-width: 768px) {
        .sw-cta-banner {
            padding: 40px 24px;
        }
        .sw-stepper-container {
            flex-direction: column;
            align-items: flex-start;
            gap: 12px;
        }
        .sw-step-divider {
            display: none;
        }
    }

    /* Reduced motion preference */
    @media (prefers-reduced-motion: reduce) {
        *, ::before, ::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
        }
        .sw-hero-tag, .sw-hero-h1, .sw-hero-subhead, .sw-hero-btns {
            animation: none !important;
            transform: none !important;
            opacity: 1 !important;
        }
    }
    </style>
    """
