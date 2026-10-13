"""
Clean SaaS Stylesheet for Retail Customer Intelligence Platform
Provides typography (Inter), calm off-white background, custom sidebar button styling,
and polished button states.
"""

SAAS_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        color: #0F172A;
    }

    .stApp {
        background-color: #F8FAFC !important;
    }

    /* Hide Default Streamlit Chrome */
    #MainMenu, header, footer, [data-testid="stToolbar"] {
        display: none !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2.25rem !important;
        padding-right: 2.25rem !important;
        max-width: 1220px !important;
    }

    /* -------------------------------------------------------------
       SIDEBAR STYLING
       ------------------------------------------------------------- */
    [data-testid="stSidebar"] {
        min-width: 235px !important;
        max-width: 235px !important;
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.25rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
        padding-bottom: 1.5rem !important;
    }

    /* Sidebar Nav Buttons (No radio buttons, no circles) */
    [data-testid="stSidebar"] div.stButton {
        margin-bottom: 0.2rem !important;
    }
    [data-testid="stSidebar"] div.stButton > button {
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
        text-align: left !important;
        width: 100% !important;
        padding: 0.5rem 0.85rem !important;
        border-radius: 6px !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.01em !important;
        transition: all 0.15s ease !important;
    }

    /* Active Nav Button */
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {
        background-color: #EFF6FF !important;
        color: #2563EB !important;
        border: 1px solid #BFDBFE !important;
        font-weight: 600 !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover {
        background-color: #DBEAFE !important;
        border-color: #93C5FD !important;
        color: #1D4ED8 !important;
    }

    /* Inactive Nav Button */
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"],
    [data-testid="stSidebar"] div.stButton > button:not([kind="primary"]) {
        background-color: transparent !important;
        color: #475569 !important;
        border: 1px solid transparent !important;
        font-weight: 500 !important;
        box-shadow: none !important;
    }
    [data-testid="stSidebar"] div.stButton > button[kind="secondary"]:hover,
    [data-testid="stSidebar"] div.stButton > button:not([kind="primary"]):hover {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border-color: #E2E8F0 !important;
    }

    /* -------------------------------------------------------------
       MAIN CONTENT BUTTONS
       ------------------------------------------------------------- */
    section.main button[kind="primary"],
    div[data-testid="stMain"] button[kind="primary"] {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: 1px solid #2563EB !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.15rem !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 2px rgba(37, 99, 235, 0.15) !important;
        transition: all 0.15s ease !important;
    }
    section.main button[kind="primary"]:hover,
    div[data-testid="stMain"] button[kind="primary"]:hover {
        background-color: #1D4ED8 !important;
        border-color: #1D4ED8 !important;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.25) !important;
    }

    section.main button[kind="secondary"],
    section.main button:not([kind="primary"]),
    div[data-testid="stMain"] button[kind="secondary"],
    div[data-testid="stMain"] button:not([kind="primary"]) {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.15rem !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
        transition: all 0.15s ease !important;
    }
    section.main button[kind="secondary"]:hover,
    section.main button:not([kind="primary"]):hover,
    div[data-testid="stMain"] button[kind="secondary"]:hover,
    div[data-testid="stMain"] button:not([kind="primary"]):hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
    }

    /* Clean Dataframe Container */
    div[data-testid="stDataFrame"] {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
        background: #FFFFFF;
    }
</style>
"""
