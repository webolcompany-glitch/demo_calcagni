import streamlit as st
import pandas as pd
import os
import smtplib
from decimal import Decimal, ROUND_DOWN
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
# 🔒 DECIMALI SICURI
# =========================
def to_float(x):
    try:
        return float(
            Decimal(str(x).replace(",", "."))
            .quantize(Decimal("0.001"), rounding=ROUND_DOWN)
        )
    except:
        return 0.0

def format_euro(x):
    return f"{to_float(x):.3f}".replace(".", ",")

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
# SEARCH SAFE
# =========================
def filtra_clienti(df, search):
    if not search:
        return df

    return df[
        df["Nome"].astype(str).str.contains(search, case=False, na=False) |
        df["PIVA"].astype(str).str.contains(search, case=False, na=False) |
        df["Telefono"].astype(str).str.contains(search, case=False, na=False)
    ]

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
# CARD UI
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

    st.markdown("## ⛽ Dashboard")

    prezzo_base = st.number_input(
        "⛽ Prezzo base giornaliero",
        value=float(st.session_state.prezzo_base),
        step=0.001,
        format="%.3f"
    )

    st.session_state.prezzo_base = prezzo_base

    st.divider()

    # SEARCH
    search = st.text_input("🔍 Cerca cliente")
    filtered = filtra_clienti(df, search)

    st.markdown("### 👤 Clienti")

    for _, c in filtered.iterrows():

        prezzo = to_float(prezzo_base + float(c["Margine"]) + float(c["Trasporto"]))

        ultimo = c.get("UltimoPrezzo", None)
        ultimo_txt = "Nessun invio" if pd.isna(ultimo) else format_euro(ultimo) + " €/L"

        st.markdown(f"""
        ### 👤 {c['Nome']}
        📄 P.IVA: {c['PIVA']}  
        💰 Prezzo: {format_euro(prezzo)} €/L  
        📌 Ultimo invio: {ultimo_txt}
        """)

        col1, col2, col3 = st.columns(3)

        with col1:
            tel = str(c["Telefono"])
            msg = f"Prezzo oggi {format_euro(prezzo)} €/L"
            wa = f"https://wa.me/{tel}?text={msg.replace(' ', '%20')}"

            st.markdown(f"[💬 WhatsApp]({wa})")

        with col2:
            if st.button("📧 Email", key=f"mail_{c['ID']}"):

                invia_email(c["Email"], prezzo)

                idx = st.session_state.clienti["ID"] == c["ID"]
                st.session_state.clienti.loc[idx, "UltimoPrezzo"] = float(prezzo)

                save_data(st.session_state.clienti)
                st.success("Email inviata")

        with col3:
            if st.button("🗑️ Elimina", key=f"del_{c['ID']}"):
                st.session_state.clienti = df[df["ID"] != c["ID"]]
                save_data(st.session_state.clienti)
                st.rerun()

# =========================================================
# 👤 CLIENTI
# =========================================================
elif st.session_state.page == "clienti":

    st.markdown("## 👤 Clienti")

    search = st.text_input("🔍 Cerca cliente")
    filtered = filtra_clienti(df, search)

    for _, c in filtered.iterrows():

        ultimo = c.get("UltimoPrezzo", None)
        ultimo_txt = "Nessun invio" if pd.isna(ultimo) else format_euro(ultimo) + " €/L"

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
            if st.button("🗑️ Elimina", key=f"del_list_{c['ID']}"):
                st.session_state.clienti = df[df["ID"] != c["ID"]]
                save_data(st.session_state.clienti)
                st.rerun()

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
    piva = st.text_input("PIVA", value=c["PIVA"])
    tel = st.text_input("Telefono", value=c["Telefono"])
    email = st.text_input("Email", value=c["Email"])

    # 🔥 FIX DEFINITIVO (NO LOC MULTICOLONNA)
    margine = to_float(st.text_input("Margine", value=str(c["Margine"])))
    trasporto = to_float(st.text_input("Trasporto", value=str(c["Trasporto"])))

    if st.button("💾 Salva"):

        if editing:

            idx = st.session_state.clienti["ID"] == st.session_state.edit_id

            st.session_state.clienti.loc[idx, "Nome"] = str(nome)
            st.session_state.clienti.loc[idx, "PIVA"] = str(piva)
            st.session_state.clienti.loc[idx, "Telefono"] = str(tel)
            st.session_state.clienti.loc[idx, "Email"] = str(email)

            st.session_state.clienti.loc[idx, "Margine"] = float(margine)
            st.session_state.clienti.loc[idx, "Trasporto"] = float(trasporto)

            st.session_state.edit_id = None

        else:

            new_id = 1 if df.empty else int(df["ID"].max()) + 1

            new = pd.DataFrame([{
                "ID": new_id,
                "Nome": nome,
                "PIVA": piva,
                "Telefono": tel,
                "Email": email,
                "Margine": float(margine),
                "Trasporto": float(trasporto),
                "UltimoPrezzo": None
            }])

            st.session_state.clienti = pd.concat([df, new], ignore_index=True)

        save_data(st.session_state.clienti)
        st.success("Salvato")
        st.session_state.page = "clienti"
        st.rerun()
