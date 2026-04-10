import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="Fuel SaaS", layout="wide")

# =========================
# 🏢 MULTI AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
if isinstance(azienda, list):
    azienda = azienda[0]

FILE = f"clienti_{azienda}.csv"

st.markdown(f"## 🏢 Azienda: {azienda.upper()}")

# =========================
# 📧 EMAIL CONFIG
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
# 💾 LOAD / SAVE (SAFE)
# =========================
def load_data():
    if os.path.exists(FILE):
        df = pd.read_csv(FILE)

        required_cols = [
            "ID","Nome","PIVA","Telefono","Email",
            "Margine","Trasporto","UltimoPrezzo"
        ]

        for col in required_cols:
            if col not in df.columns:
                df[col] = None

        return df[required_cols]

    return pd.DataFrame(columns=[
        "ID","Nome","PIVA","Telefono","Email",
        "Margine","Trasporto","UltimoPrezzo"
    ])

def save_data(df):
    df.to_csv(FILE, index=False)

# =========================
# 🔎 SEARCH
# =========================
def filtra_clienti(df, search):
    if not search:
        return df

    return df[
        df["Nome"].str.contains(search, case=False, na=False) |
        df["PIVA"].str.contains(search, case=False, na=False) |
        df["Telefono"].astype(str).str.contains(search, na=False)
    ]

# =========================
# INIT STATE
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
# NAVIGATION
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
    <div style="
        padding:14px;
        border-radius:14px;
        background:#111827;
        color:white;
        text-align:center;
        margin:6px 0;
    ">
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

    # SEARCH
    search = st.text_input("🔍 Cerca cliente")
    filtered_df = filtra_clienti(df, search)

    # KPI
    clienti_count = len(df)
    media_margine = df["Margine"].mean() if not df.empty else 0
    prezzo_medio = (df["Margine"] + df["Trasporto"]).add(prezzo_base).mean() if not df.empty else prezzo_base

    # CARDS
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    with c1:
        st.markdown(card("⛽ Prezzo base giornaliero", f"{prezzo_base:.3f} €"), unsafe_allow_html=True)

    with c2:
        st.markdown(card("👤 Clienti attivi", clienti_count), unsafe_allow_html=True)

    with c3:
        st.markdown(card("📊 Margine medio per litro", f"{media_margine:.3f}"), unsafe_allow_html=True)

    with c4:
        st.markdown(card("💰 Prezzo medio di vendita", f"{prezzo_medio:.3f}"), unsafe_allow_html=True)

    st.divider()

    # MASS EMAIL
    st.markdown("### 🚀 Invio prezzi")

    if st.button("📧 Invia email a tutti i clienti in un click", use_container_width=True):

        count = 0

        for _, c in df.iterrows():
            if c["Email"] and pd.notna(c["Email"]):

                prezzo = prezzo_base + c["Margine"] + c["Trasporto"]
                invia_email(c["Email"], prezzo)

                st.session_state.clienti.loc[
                    st.session_state.clienti["ID"] == c["ID"],
                    "UltimoPrezzo"
                ] = prezzo

                count += 1

        save_data(st.session_state.clienti)
        st.success(f"Inviate {count} email")

    st.divider()

    # CLIENT LIST
    for _, c in filtered_df.iterrows():

        prezzo = prezzo_base + c["Margine"] + c["Trasporto"]
        ultimo = c.get("UltimoPrezzo", None)

        if pd.isna(ultimo) or ultimo is None:
            ultimo_txt = "Nessun invio"
        else:
            ultimo_txt = f"{float(ultimo):.3f} €/L"

        st.markdown(f"""
        ### 👤 {c['Nome']}
        📄 P.IVA: {c['PIVA']}  
        💰 **{prezzo:.3f} €/L**

        📌 Ultimo prezzo inviato: **{ultimo_txt}**
        """)

        col1, col2, col3 = st.columns(3)

        with col1:
            tel = str(c["Telefono"]).replace("+", "").replace(" ", "")
            msg = f"Prezzo oggi {prezzo:.3f} €/L"
            wa = f"https://wa.me/{tel}?text={msg.replace(' ', '%20')}"

            st.markdown(
                f"""<a href="{wa}" target="_blank"
                style="display:block;padding:8px;background:#22c55e;color:white;
                text-align:center;border-radius:10px;text-decoration:none;">
                💬 Invia messaggio</a>""",
                unsafe_allow_html=True
            )

        with col2:
            if c["Email"] and pd.notna(c["Email"]):
                if st.button("📧 Invia email", key=f"mail_{c['ID']}"):

                    invia_email(c["Email"], prezzo)

                    st.session_state.clienti.loc[
                        st.session_state.clienti["ID"] == c["ID"],
                        "UltimoPrezzo"
                    ] = prezzo

                    save_data(st.session_state.clienti)
                    st.success("Inviata")

        with col3:
            if st.button("🗑️ Elimina", key=f"del_{c['ID']}"):
                st.session_state.clienti = df[df["ID"] != c["ID"]]
                save_data(st.session_state.clienti)
                st.rerun()

        st.divider()

# =========================================================
# 👤 CLIENTI
# =========================================================
elif st.session_state.page == "clienti":

    st.markdown("## 👤 Clienti attivi")

    search = st.text_input("🔍 Cerca cliente")
    filtered_df = filtra_clienti(df, search)

    for _, c in filtered_df.iterrows():

        ultimo = c.get("UltimoPrezzo", None)
        ultimo_txt = "Nessun invio" if pd.isna(ultimo) or ultimo is None else f"{float(ultimo):.3f} €/L"

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

        st.divider()

# =========================================================
# ➕ CLIENTE FORM
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

    margine = st.number_input("Margine", value=float(c["Margine"]), step=0.001)
    trasporto = st.number_input("Trasporto", value=float(c["Trasporto"]), step=0.001)

    if st.button("💾 Salva"):

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
