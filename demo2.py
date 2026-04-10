import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="Fuel SaaS", layout="wide")

# =========================
# MULTI AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
FILE = f"clienti_{azienda}.csv"

st.markdown(f"### 🏢 Azienda: {azienda.upper()}")

# =========================
# CONFIG EMAIL
# =========================
EMAIL_MITTENTE = "webolcompany@gmail.com"
PASSWORD_APP = "neqr ewtb bdkr lmca"

def invia_email(destinatario, prezzo):
    msg = MIMEText(f"Buongiorno,\n\nIl prezzo di oggi è {prezzo:.3f} €/L\n\nGrazie")
    msg["Subject"] = "Prezzo carburante"
    msg["From"] = EMAIL_MITTENTE
    msg["To"] = destinatario

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_MITTENTE, PASSWORD_APP)
    server.send_message(msg)
    server.quit()

# =========================
# LOAD / SAVE
# =========================
def load_data():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)
    return pd.DataFrame(columns=[
        "ID","Nome","PIVA","Telefono","Email","Margine","Trasporto"
    ])

def save_data(df):
    df.to_csv(FILE, index=False)

# =========================
# INIT
# =========================
if "clienti" not in st.session_state:
    st.session_state.clienti = load_data()

if "prezzo_base" not in st.session_state:
    st.session_state.prezzo_base = 1.000

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "edit_id" not in st.session_state:
    st.session_state.edit_id = None

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

# =========================================================
# DASHBOARD
# =========================================================
if st.session_state.page == "dashboard":

    st.markdown("## ⛽ Dashboard")

    prezzo_base = st.number_input("Prezzo base", value=float(st.session_state.prezzo_base), step=0.001, format="%.3f")
    st.session_state.prezzo_base = prezzo_base

    media_margine = df["Margine"].mean() if not df.empty else 0
    clienti_count = len(df)
    prezzo_medio = (prezzo_base + df["Margine"] + df["Trasporto"]).mean() if not df.empty else prezzo_base

    st.markdown("### 📊 Riepilogo")

    def card(label, value):
        return f"""
        <div style="padding:14px;border-radius:12px;background:#111827;color:white;text-align:center;margin:6px 0;">
        <div style="font-size:12px;opacity:0.7;">{label}</div>
        <div style="font-size:20px;font-weight:600">{value}</div>
        </div>
        """

    k1,k2 = st.columns(2)
    k3,k4 = st.columns(2)

    with k1: st.markdown(card("Base", f"{prezzo_base:.3f} €"), unsafe_allow_html=True)
    with k2: st.markdown(card("Clienti", clienti_count), unsafe_allow_html=True)
    with k3: st.markdown(card("Margine medio", f"{media_margine:.3f}"), unsafe_allow_html=True)
    with k4: st.markdown(card("Prezzo medio", f"{prezzo_medio:.3f}"), unsafe_allow_html=True)

    # 🔥 INVIA A TUTTI
    st.markdown("### 🚀 Invio massivo")

    if st.button("📧 Invia prezzo a tutti i clienti"):

        count = 0

        for _, c in df.iterrows():
            if pd.notna(c["Email"]):
                prezzo = prezzo_base + c["Margine"] + c["Trasporto"]
                invia_email(c["Email"], prezzo)
                count += 1

        st.success(f"Inviate {count} email")

    st.divider()

    # CLIENTI
    for _, c in df.iterrows():

        prezzo = prezzo_base + c["Margine"] + c["Trasporto"]

        st.markdown(f"### 👤 {c['Nome']}")
        st.write(f"P.IVA: {c['PIVA']}")
        st.write(f"💰 {prezzo:.3f} €/L")

        col1, col2, col3 = st.columns(3)

        with col1:
            msg = f"Prezzo oggi {prezzo:.3f} €/L"
            link = f"https://wa.me/{c['Telefono']}?text={msg.replace(' ', '%20')}"
            st.markdown(f"[📲 WhatsApp]({link})")

        with col2:
            if pd.notna(c["Email"]):
                if st.button("📧 Email", key=f"mail_{c['ID']}"):
                    invia_email(c["Email"], prezzo)
                    st.success("Inviata")

        with col3:
            if st.button("🗑️ Elimina", key=f"del_{c['ID']}"):
                st.session_state.clienti = df[df["ID"] != c["ID"]]
                save_data(st.session_state.clienti)
                st.rerun()

        st.divider()

# =========================================================
# CLIENTI
# =========================================================
elif st.session_state.page == "clienti":

    st.markdown("## 👤 Clienti")

    for _, c in df.iterrows():

        st.markdown(f"### {c['Nome']}")

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
# NUOVO / MODIFICA
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
    email = st.text_input("Email", value=c.get("Email",""))

    margine = st.number_input("Margine", value=float(c["Margine"]), step=0.001, format="%.3f")
    trasporto = st.number_input("Trasporto", value=float(c["Trasporto"]), step=0.001, format="%.3f")

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
                "Trasporto": trasporto
            }])

            st.session_state.clienti = pd.concat([df,new], ignore_index=True)

        save_data(st.session_state.clienti)

        st.success("Salvato")
        st.session_state.page = "clienti"
        st.rerun()