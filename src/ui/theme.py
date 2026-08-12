import streamlit as st

DISCLAIMER = "Educational execution simulation using synthetic data. Not investment advice. No real orders are placed. Independent portfolio project—not affiliated with Nubra or any broker."


def inject_theme():
    st.markdown(
        """<style>
    .stApp{background:#08111f;color:#dbe7f3}.block-container{max-width:1440px;padding-top:1.4rem;padding-bottom:4rem}
    [data-testid="stSidebar"]{background:#0c1728;border-right:1px solid #20324a}
    h1,h2,h3{font-family:Inter,system-ui;color:#f4f8fc;letter-spacing:-.02em}h1{font-size:2rem!important}
    .eyebrow{color:#47d7ac;font:600 .72rem ui-monospace;letter-spacing:.14em;text-transform:uppercase}
    .panel{border:1px solid #20324a;background:#0d1a2c;border-radius:10px;padding:14px 16px;margin:6px 0}
    .status{font:700 .75rem ui-monospace;padding:4px 8px;border-radius:4px;background:#14243a}
    [data-testid="stMetric"]{background:#0d1a2c;border:1px solid #20324a;border-radius:8px;padding:12px}
    [data-testid="stMetricValue"]{font-family:ui-monospace;color:#f4f8fc;font-size:1.55rem}
    .disclaimer{position:relative;margin-top:2rem;padding:10px;border-top:1px solid #20324a;color:#8498ad;font-size:.72rem}
    .stButton>button{background:#19b785;color:#06120f;border:0;font-weight:700;border-radius:6px;height:42px}
    .stButton>button:hover{background:#47d7ac;color:#06120f}.stDataFrame{border:1px solid #20324a;border-radius:8px}
    code{color:#78d9ff}.legend{color:#8fa5ba;font-size:.8rem}.green{color:#47d7ac}.amber{color:#f5b942}.red{color:#ff6b79}
    </style>""",
        unsafe_allow_html=True,
    )


def header(kicker, title, subtitle):
    st.markdown(
        f'<div class="eyebrow">{kicker}</div><h1>{title}</h1><p class="legend">{subtitle}</p>',
        unsafe_allow_html=True,
    )


def disclaimer():
    st.markdown(f'<div class="disclaimer">{DISCLAIMER}</div>', unsafe_allow_html=True)
