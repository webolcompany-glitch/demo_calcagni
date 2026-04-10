import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="Fuel Manager", layout="wide")

# =========================
# MULTI AZIENDA
# =========================
azienda = st.query_params.get("azienda", "demo")
FILE = f"clienti_{azienda}.csv"

st.markdown(f"## 🏢 Azienda: {azienda.upper()}")

# =========================
# EMAIL CONFIG
# =========================
EMAIL_MITTENTE = "tuaemail@gmail.com"
PASSWORD_APP = "password_app"

def invia_email(destinatario, prezzo):
    try:
        msg = MIMEText(f"""Buongiorno,

il prezzo aggiornato di oggi è:
⛽ {prezzo:.3f} €/L

Grazie""")

        msg["Subject"] = "Prezzo carburante aggiornato"
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

if "clienti" not in st.session_state:
    st.session_state.clienti = load_data()

df = st.session_state.clienti

# =========================
# NAVIGATION (mobile friendly)
# =========================
c1, c2, c3 = st.columns(3)

with c1:
    if st.button("📊 Home", use_container_width=True):
        st.session_state.page = "dashboard"

with c2:
    if st.button("👤 Clienti", use_container_width=True):
        st.session_state.page = "clienti"

with c3:
    if st.button("➕ Nuovo", use_container_width=True):
        st.session_state.page = "cliente"

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

st.divider()

# =========================================================
# DASHBOARD
# =========================================================
if st.session_state.page == "dashboard":

    st.subheader("📊 Dashboard operativa")

    prezzo_base = st.number_input("⛽ Prezzo base", value=1.000, step=0.001, format="%.3f")

    if not df.empty:
        guadagno_tot = df["Margine"].sum()
        margine_medio = df["Margine"].mean()
        prezzo_medio = (prezzo_base + df["Margine"] + df["Trasporto"]).mean()
    else:
        guadagno_tot = margine_medio = 0
        prezzo_medio = prezzo_base

    # =========================
    # KPI CARDS MOBILE FRIENDLY
    # =========================
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)

    with c1:
        st.metric("⛽ Prezzo base", f"{prezzo_base:.3f} €")

    with c2:
        st.metric("👥 Clienti", len(df))

    with c3:
        st.metric("💰 Guadagno medio €/L", f"{margine_medio:.3f}")

    with c4:
        st.metric("⛽ Prezzo medio clienti", f"{prezzo_medio:.3f}")

    st.metric("💵 Guadagno totale stimato", f"{guadagno_tot:.2f} €")

    # =========================
    # INVIA A TUTTI
    # =========================
    st.markdown("### 🚀 Azioni rapide")

    if st.button("📧 Invia prezzo a tutti i clienti", use_container_width=True):

        count = 0

        for _, c in df.iterrows():
            if pd.notna(c["Email"]):
                prezzo = prezzo_base + c["Margine"] + c["Trasporto"]
                invia_email(c["Email"], prezzo)
                count += 1

        st.success(f"Inviate {count} email")

    st.divider()

    # =========================
    # CLIENT LIST (mobile cards)
    # =========================
    st.subheader("👤 Clienti")

    for _, c in df.iterrows():

        prezzo = prezzo_base + c["Margine"] + c["Trasporto"]

        st.markdown(f"""
        ### 👤 {c['Nome']}

        ⛽ **Prezzo finale:** `{prezzo:.3f} €/L`

        📊 Margine: `{c['Margine']:.3f}` | Trasporto: `{c['Trasporto']:.3f}`

        📞 {c['Telefono']}  
        📧 {c['Email'] if pd.notna(c['Email']) else '-'}
        """)

        # WhatsApp
        msg = f"Prezzo oggi {prezzo:.3f} €/L"
        wa_link = f"https://wa.me/{c['Telefono']}?text={msg.replace(' ', '%20')}"

        b1, b2, b3 = st.columns(3)

        with b1:
            st.markdown(f"[📲 WhatsApp]({wa_link})")

        with b2:
            if pd.notna(c["Email"]):
                if st.button("📧 Email", key=f"mail_{c['ID']}"):
                    invia_email(c["Email"], prezzo)
                    st.success("Inviata")

        with b3:
            if st.button("🗑️ Elimina", key=f"del_{c['ID']}"):
                st.session_state.clienti = df[df["ID"] != c["ID"]]
                save_data(st.session_state.clienti)
                st.rerun()

        st.divider()

# =========================================================
# CLIENTI PAGE
# =========================================================
elif st.session_state.page == "clienti":

    st.subheader("👤 Lista clienti")

    for _, c in df.iterrows():

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"👤 {c['Nome']}")

        with col2:
            if st.button("✏️ Modifica", key=f"edit_{c['ID']}"):
                st.session_state.edit_id = c["ID"]
                st.session_state.page = "cliente"

            if st.button("🗑️ Elimina", key=f"del_list_{c['ID']}"):
                st.session_state.clienti = df[df["ID"] != c["ID"]]
                save_data(st.session_state.clienti)
                st.rerun()

        st.divider()

# =========================================================
# CREATE / EDIT CLIENT
# =========================================================
elif st.session_state.page == "cliente":

    st.subheader("➕ Cliente")

    editing = "edit_id" in st.session_state

    if editing and st.session_state.get("edit_id") is not None:
        c = df[df["ID"] == st.session_state.edit_id]
        if c.empty:
            st.stop()
        c = c.iloc[0]
    else:
        c = {"Nome":"","PIVA":"","Telefono":"","Email":"","Margine":0.0,"Trasporto":0.0}

    nome = st.text_input("Nome", c["Nome"])
    piva = st.text_input("P.IVA", c["PIVA"])
    tel = st.text_input("Telefono", c["Telefono"])
    email = st.text_input("Email", c.get("Email",""))

    margine = st.number_input("Margine", value=float(c["Margine"]), step=0.001, format="%.3f")
    trasporto = st.number_input("Trasporto", value=float(c["Trasporto"]), step=0.001, format="%.3f")

    if st.button("💾 Salva", use_container_width=True):

        if editing and st.session_state.edit_id is not None:

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

            st.session_state.clienti = pd.concat([df, new], ignore_index=True)

        save_data(st.session_state.clienti)

        st.success("Salvato")
        st.session_state.page = "clienti"
        st.rerun()
