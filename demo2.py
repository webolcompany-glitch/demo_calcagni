import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="Fuel SaaS", layout="wide")

# =========================
# 🏢 AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
if isinstance(azienda, list):
    azienda = azienda[0]

FILE = f"clienti_{azienda}.csv"

st.markdown(f"## 🏢 Azienda: {azienda.upper()}")

# =========================
# 📧 EMAIL
# =========================
EMAIL_MITTENTE = "webolcompany@gmail.com"
PASSWORD_APP = "YOUR_APP_PASSWORD"

def invia_email(destinatario, prezzo):
    try:
        msg = MIMEText(f"Buongiorno,\n\nIl prezzo di oggi è {prezzo:.3f} €/L\n\nGrazie")
        msg["Subject"] = "Prezzo carburante"
        msg["From"] = EMAIL_MITTENTE
        msg["To"] = destinatario

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_MITTENTE, PASSWORD_APP)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error(f"Errore email: {e}")

# =========================
# 🔒 FORMAT SICURO
# =========================
def format_euro(x):
    if x is None or pd.isna(x):
        return "0,000"
    return f"{round(float(x), 3):.3f}".replace(".", ",")

def calc_price(base, margine, trasporto):
    return round(float(base) + float(margine) + float(trasporto), 3)

# =========================
# 💾 DATA
# =========================
def load_data():
    if os.path.exists(FILE):
        df = pd.read_csv(FILE)
        if "UltimoPrezzo" not in df.columns:
            df["UltimoPrezzo"] = None
        return df

    return pd.DataFrame(columns=[
        "ID","Nome","PIVA","Telefono","Email",
        "Margine","Trasporto","UltimoPrezzo"
    ])

def save_data(df):
    df.to_csv(FILE, index=False)

# =========================
# INIT
# =========================
if "clienti" not in st.session_state:
    st.session_state.clienti = load_data()

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

if "prezzo_base" not in st.session_state:
    st.session_state.prezzo_base = 1.000

df = st.session_state.clienti

# =========================
# NAV
# =========================
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"

with c2:
    if st.button("👤 Clienti", use_container_width=True):
        st.session_state.page = "clienti"

with c3:
    if st.button("➕ Nuovo", use_container_width=True):
        st.session_state.page = "cliente"

st.divider()

# =========================
# CARD
# =========================
def card(title, value):
    return f"""
    <div style="padding:14px;border-radius:14px;background:#111827;
    color:white;text-align:center;margin:6px 0;">
        <div style="font-size:12px;opacity:0.7;">{title}</div>
        <div style="font-size:20px;font-weight:600">{value}</div>
    </div>
    """

# =========================================================
# 📊 DASHBOARD
# =========================================================
if st.session_state.page == "dashboard":

    st.markdown("## ⛽ Dashboard operativa")

    prezzo_base = st.number_input(
        "⛽ Prezzo base giornaliero",
        value=float(st.session_state.prezzo_base),
        step=0.001,
        format="%.3f"
    )

    st.session_state.prezzo_base = prezzo_base

    clienti_count = len(df)

    media_margine = round(df["Margine"].astype(float).mean(), 3) if not df.empty else 0

    prezzo_medio = (
        calc_price(prezzo_base, df["Margine"].astype(float).mean(), df["Trasporto"].astype(float).mean())
        if not df.empty else prezzo_base
    )

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    with c1:
        st.markdown(card("⛽ Prezzo base giornaliero", format_euro(prezzo_base)), unsafe_allow_html=True)

    with c2:
        st.markdown(card("👤 Clienti attivi", clienti_count), unsafe_allow_html=True)

    with c3:
        st.markdown(card("📊 Margine medio per litro", format_euro(media_margine)), unsafe_allow_html=True)

    with c4:
        st.markdown(card("💰 Prezzo medio di vendita", format_euro(prezzo_medio)), unsafe_allow_html=True)

    st.divider()

    # =========================
    # 🚀 INVIO MASSIVO EMAIL
    # =========================
    if st.button("📧 Invia email a tutti i clienti in un click"):

        count = 0

        for _, c in df.iterrows():

            if c["Email"] and pd.notna(c["Email"]):

                prezzo = calc_price(prezzo_base, c["Margine"], c["Trasporto"])

                invia_email(c["Email"], prezzo)

                st.session_state.clienti.loc[
                    st.session_state.clienti["ID"] == c["ID"],
                    "UltimoPrezzo"
                ] = prezzo

                count += 1

        save_data(st.session_state.clienti)
        st.success(f"📧 Email inviate a {count} clienti")

# =========================================================
# 👤 CLIENTI PAGE
# =========================================================
elif st.session_state.page == "clienti":

    st.markdown("## 👤 Clienti attivi")

    search = st.text_input("🔍 Cerca cliente")

    if search:
        df_view = df[
            df["Nome"].astype(str).str.contains(search, case=False, na=False) |
            df["PIVA"].astype(str).str.contains(search, case=False, na=False) |
            df["Telefono"].astype(str).str.contains(search, case=False, na=False)
        ]
    else:
        df_view = df

    for _, c in df_view.iterrows():

        ultimo_txt = "Nessun invio" if pd.isna(c.get("UltimoPrezzo")) else format_euro(c["UltimoPrezzo"]) + " €/L"

        st.markdown(f"""
        ### 👤 {c['Nome']}
        📄 {c['PIVA']}  
        📞 {c['Telefono']}  
        💰 Ultimo prezzo: {ultimo_txt}
        """)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("✏️ Modifica", key=f"edit_{c['ID']}"):
                st.session_state.edit_id = c["ID"]
                st.session_state.page = "cliente"

        with col2:
            if st.button("🗑️ Elimina", key=f"del_{c['ID']}"):
                st.session_state.clienti = df[df["ID"] != c["ID"]]
                save_data(st.session_state.clienti)
                st.rerun()

        st.divider()

# =========================================================
# ➕ CLIENTE
# =========================================================
elif st.session_state.page == "cliente":

    st.markdown("## ➕ Cliente")

    editing = st.session_state.edit_id is not None

    if editing:
        c = df[df["ID"] == st.session_state.edit_id]
        if c.empty:
            st.stop()
        c = c.iloc[0]
    else:
        c = {"Nome":"","PIVA":"","Telefono":"","Email":"","Margine":0.0,"Trasporto":0.0}

    nome = st.text_input("Nome", value=c["Nome"])
    piva = st.text_input("P.IVA", value=c["PIVA"])
    tel = st.text_input("Telefono", value=c["Telefono"])
    email = st.text_input("Email", value=c["Email"])

    margine = st.number_input("Margine", value=float(c["Margine"]), step=0.001, format="%.3f")
    trasporto = st.number_input("Trasporto", value=float(c["Trasporto"]), step=0.001, format="%.3f")

    if st.button("💾 Salva"):

        margine = round(float(margine), 3)
        trasporto = round(float(trasporto), 3)

        if editing:
            st.session_state.clienti.loc[
                st.session_state.clienti["ID"] == st.session_state.edit_id,
                ["Nome","PIVA","Telefono","Email","Margine","Trasporto"]
            ] = [nome,piva,tel,email,margine,trasporto]

            st.session_state.edit_id = None

        else:
            new_id = 1 if df.empty else int(df["ID"].max()) + 1

            new = pd.DataFrame([{
                "ID": new_id,
                "Nome": nome,
                "PIVA": piva,
                "Telefono": tel,
                "Email": email,
                "Margine": margine,
                "Trasporto": trasporto,
                "UltimoPrezzo": None
            }])

            st.session_state.clienti = pd.concat([df, new], ignore_index=True)

        save_data(st.session_state.clienti)
        st.success("Salvato")
        st.session_state.page = "clienti"
        st.rerun()
