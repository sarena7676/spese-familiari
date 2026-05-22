import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# ============================================
# PROTEZIONE CON PASSWORD
# ============================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔒 Accesso Protetto")
        st.write("App Gestione Spese Familiari")
        
        with st.form("login_form"):
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Accedi")
            
            if submitted:
                if password == "famiglia2024":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Password errata!")
        
        return False
    return True

if not check_password():
    st.stop()

# ============================================
# CONFIGURAZIONE DATABASE
# ============================================
def init_db():
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS carte
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  data TEXT,
                  descrizione TEXT,
                  importo REAL,
                  quota_seba REAL,
                  quota_gio REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS fisse
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  data TEXT,
                  descrizione TEXT,
                  importo REAL)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS saldi_iniziali
                 (mese TEXT PRIMARY KEY,
                  importo REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stipendi
                 (mese TEXT PRIMARY KEY,
                  importo REAL)''')
    
    conn.commit()
    conn.close()

def load_carte():
    conn = sqlite3.connect('spese_familiari.db')
    df = pd.read_sql("SELECT * FROM carte", conn)
    conn.close()
    return df

def add_carta(descrizione, importo, quota_seba):
    if descrizione == 'UNICREDIT':
        quota_gio = importo / 2
    else:
        quota_gio = importo - quota_seba
    
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("INSERT INTO carte (data, descrizione, importo, quota_seba, quota_gio) VALUES (?, ?, ?, ?, ?)",
              (date.today().isoformat(), descrizione, importo, quota_seba, quota_gio))
    conn.commit()
    conn.close()

def update_carta(id, field, value):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    if field == 'descrizione':
        c.execute("SELECT importo, quota_seba FROM carte WHERE id = ?", (id,))
        importo, quota_seba = c.fetchone()
        if value == 'UNICREDIT':
            quota_gio = importo / 2
        else:
            quota_gio = importo - quota_seba
        c.execute("UPDATE carte SET descrizione = ?, quota_gio = ?, data = ? WHERE id = ?", 
                  (value, quota_gio, date.today().isoformat(), id))
    elif field == 'importo':
        c.execute("SELECT descrizione, quota_seba FROM carte WHERE id = ?", (id,))
        descrizione, quota_seba = c.fetchone()
        if descrizione == 'UNICREDIT':
            quota_gio = value / 2
        else:
            quota_gio = value - quota_seba
        c.execute("UPDATE carte SET importo = ?, quota_gio = ?, data = ? WHERE id = ?", 
                  (value, quota_gio, date.today().isoformat(), id))
    elif field == 'quota_seba':
        c.execute("SELECT descrizione, importo FROM carte WHERE id = ?", (id,))
        descrizione, importo = c.fetchone()
        if descrizione == 'UNICREDIT':
            quota_gio = importo / 2
        else:
            quota_gio = importo - value
        c.execute("UPDATE carte SET quota_seba = ?, quota_gio = ?, data = ? WHERE id = ?", 
                  (value, quota_gio, date.today().isoformat(), id))
    conn.commit()
    conn.close()

def delete_carta(id):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("DELETE FROM carte WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def load_fisse():
    conn = sqlite3.connect('spese_familiari.db')
    df = pd.read_sql("SELECT * FROM fisse", conn)
    conn.close()
    return df

def add_fissa(descrizione, importo, data_saldo):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("INSERT INTO fisse (data, descrizione, importo) VALUES (?, ?, ?)",
              (data_saldo.isoformat(), descrizione, importo))
    conn.commit()
    conn.close()

def update_fissa(id, importo):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("UPDATE fisse SET importo = ? WHERE id = ?", (importo, id))
    conn.commit()
    conn.close()

def delete_fissa(id):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("DELETE FROM fisse WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def save_stipendio(mese, importo):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO stipendi (mese, importo) VALUES (?, ?)",
              (mese, importo))
    conn.commit()
    conn.close()

def load_stipendio(mese):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("SELECT importo FROM stipendi WHERE mese = ?", (mese,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0.0

def save_saldo_iniziale(mese, importo):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO saldi_iniziali (mese, importo) VALUES (?, ?)",
              (mese, importo))
    conn.commit()
    conn.close()

def load_saldo_iniziale(mese):
    conn = sqlite3.connect('spese_familiari.db')
    c = conn.cursor()
    c.execute("SELECT importo FROM saldi_iniziali WHERE mese = ?", (mese,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0.0

# Inizializza database
init_db()

# ============================================
# INTERFACCIA PRINCIPALE
# ============================================
st.set_page_config(
    page_title="Spese Familiari",
    page_icon="💰",
    layout="wide"
)

# CSS responsive + mobile-style cards
st.markdown("""
    <style>
    /* Layout generale */
    .block-container { padding-top: 1rem !important; }
    
    /* Righe lista stile app mobile */
    .row-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.07);
        background: rgba(255,255,255,0.03);
        border-radius: 6px;
        margin-bottom: 2px;
    }
    .row-desc { font-size: 0.92rem; font-weight: 500; flex: 2; }
    .row-val  { font-size: 0.92rem; color: #aaa; flex: 1; text-align: right; }
    
    /* Riduce spazio verticale tra colonne streamlit */
    .stColumn { padding: 0 4px !important; }
    div[data-testid="column"] { padding: 0 3px !important; }
    
    /* Input più compatti */
    .stNumberInput > div > div > input { 
        padding: 4px 8px !important; 
        font-size: 0.88rem !important;
        height: 36px !important;
    }
    .stSelectbox > div > div {
        padding: 2px 6px !important;
        font-size: 0.88rem !important;
        min-height: 36px !important;
    }
    
    /* Bottoni icona compatti */
    .stButton > button {
        padding: 4px 10px !important;
        font-size: 0.85rem !important;
        height: 36px !important;
        min-width: 36px !important;
        border-radius: 6px !important;
    }
    
    /* Riduce gap tra righe */
    .element-container { margin-bottom: 2px !important; }
    div[data-testid="stHorizontalBlock"] { 
        gap: 4px !important; 
        align-items: center !important;
        margin-bottom: 2px !important;
    }
    
    /* Separatori sottili */
    hr { margin: 6px 0 !important; opacity: 0.15 !important; }

    /* Header sezioni */
    .section-header {
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #888;
        padding: 4px 0 2px 2px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 4px;
    }

    @media (max-width: 768px) {
        h1 { font-size: 1.2rem !important; }
        h2 { font-size: 1rem !important; }
        h3 { font-size: 0.88rem !important; }
    }
    </style>
""", unsafe_allow_html=True)

# Logout button
col1, col2 = st.columns([6, 1])
with col1:
    st.title("💰 GESTIONE SPESE")
with col2:
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# Menu navigazione
tab1, tab2, tab3, tab4 = st.tabs(["📋 CARTE", "📊 SPESE FISSE", "💰 PREVISIONI", "💳 TOTALE GIO"])

# ============================================
# TAB CARTE
# ============================================
with tab1:
    st.subheader("Gestione Carte")
    
    with st.expander("➕ Nuova Spesa", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            descrizione = st.selectbox("Carta", ['INTESA GIO', 'INTESA SEBA', 'UNICREDIT'], key="new_carta")
        with col2:
            importo = st.number_input("Importo €", min_value=0.0, step=0.01, key="new_importo")
        with col3:
            quota_seba = st.number_input("Quota Seba €", min_value=0.0, step=0.01, key="new_seba")
        
        if st.button("Aggiungi Spesa", type="primary"):
            if descrizione:
                add_carta(descrizione, importo, quota_seba)
                st.success("✅ Spesa aggiunta!")
                st.rerun()
    
    st.write("---")

    df_carte = load_carte()
    
    if not df_carte.empty:
        # Header colonne stile app
        st.markdown('''<div style="display:flex;padding:4px 6px;margin-bottom:2px;">
            <div style="flex:2;font-size:0.75rem;font-weight:700;color:#777;text-transform:uppercase;letter-spacing:.06em;">Carta</div>
            <div style="flex:1.2;font-size:0.75rem;font-weight:700;color:#777;text-transform:uppercase;letter-spacing:.06em;text-align:right;">Importo</div>
            <div style="flex:1.2;font-size:0.75rem;font-weight:700;color:#777;text-transform:uppercase;letter-spacing:.06em;text-align:right;">Seba</div>
            <div style="flex:1.2;font-size:0.75rem;font-weight:700;color:#4caf50;text-transform:uppercase;letter-spacing:.06em;text-align:right;">Gio</div>
            <div style="flex:.7;"></div>
        </div>''', unsafe_allow_html=True)

        for idx, row in df_carte.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 1.2, 1.2, 1.2, 0.4, 0.4])
            
            with col1:
                new_desc = st.selectbox(
                    "Carta",
                    ['INTESA GIO', 'INTESA SEBA', 'UNICREDIT'],
                    index=['INTESA GIO', 'INTESA SEBA', 'UNICREDIT'].index(row['descrizione']) if row['descrizione'] in ['INTESA GIO', 'INTESA SEBA', 'UNICREDIT'] else 0,
                    key=f"desc_{row['id']}",
                    label_visibility="collapsed"
                )
            with col2:
                new_imp = st.number_input("Importo", value=float(row['importo']), key=f"imp_{row['id']}", label_visibility="collapsed", format="%.2f")
            with col3:
                new_seba = st.number_input("Seba", value=float(row['quota_seba']), key=f"seba_{row['id']}", label_visibility="collapsed", format="%.2f")
            with col4:
                st.markdown(f'<div style="text-align:right;padding-top:8px;font-size:0.9rem;color:#4caf50;font-weight:600;">€ {row['quota_gio']:.2f}</div>', unsafe_allow_html=True)
            with col5:
                if st.button("💾", key=f"save_{row['id']}"):
                    if new_desc != row['descrizione']: update_carta(row['id'], 'descrizione', new_desc)
                    if new_imp != row['importo']: update_carta(row['id'], 'importo', new_imp)
                    if new_seba != row['quota_seba']: update_carta(row['id'], 'quota_seba', new_seba)
                    st.rerun()
            with col6:
                if st.button("🗑️", key=f"del_{row['id']}"):
                    delete_carta(row['id'])
                    st.rerun()

        # Totali in fondo stile footer-card
        st.markdown('''<div style="height:1px;background:rgba(255,255,255,0.12);margin:8px 0 6px;"></div>''', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Totale", f"€ {df_carte['importo'].sum():.2f}")
        with col2:
            st.metric("Seba", f"€ {df_carte['quota_seba'].sum():.2f}")
        with col3:
            st.metric("Gio", f"€ {df_carte['quota_gio'].sum():.2f}")
    
    else:
        st.info("📝 Nessuna spesa inserita. Usa il form qui sopra per aggiungere la prima spesa!")

# ============================================
# TAB SPESE FISSE
# ============================================
with tab2:
    st.subheader("Spese Fisse")
    
    with st.expander("➕ Nuova Spesa Fissa", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            desc_fissa = st.text_input("Descrizione", key="desc_fissa")
        with col2:
            importo_fissa = st.number_input("Importo €", min_value=0.0, step=0.01, key="importo_fissa")
        with col3:
            mesi_options = [(date.today().replace(day=1) + relativedelta(months=i)) for i in range(-3, 10)]
            mesi_labels  = [m.strftime("%B %Y") for m in mesi_options]
            default_idx  = next((i for i, m in enumerate(mesi_options) if m.month == date.today().month and m.year == date.today().year), 3)
            mese_sel     = st.selectbox("Mese di competenza", mesi_labels, index=default_idx, key="mese_fissa")
            mese_saldo   = mesi_options[mesi_labels.index(mese_sel)]
        
        if st.button("Aggiungi Spesa Fissa", type="primary"):
            if desc_fissa:
                add_fissa(desc_fissa, importo_fissa, mese_saldo)
                st.success("✅ Spesa fissa aggiunta!")
                st.rerun()
            else:
                st.error("Inserisci una descrizione!")
    
    st.write("---")
    
    # Import da Google Sheets
    with st.expander("📋 Importa da Google Sheets", expanded=False):
        st.write("1. Apri il foglio Google")
        st.write("2. Seleziona TUTTE le righe e colonne che vuoi importare")
        st.write("3. Copia (Ctrl+C)")
        st.write("4. Incolla qui sotto (Ctrl+V):")
        
        dati_importati = st.text_area(
            "Incolla qui i dati",
            placeholder="Descrizione\tImporto\tData\nAffitto\t500.00\t01/06/2024",
            height=200
        )
        
        if st.button("📥 Importa Dati", type="primary"):
            if dati_importati:
                righe = dati_importati.strip().split('\n')
                count = 0
                errori = 0
                inizio = 1 if st.checkbox("La prima riga contiene intestazioni", value=True) else 0
                
                for i, riga in enumerate(righe[inizio:], start=1):
                    try:
                        parti = riga.split('\t')
                        if len(parti) >= 2:
                            desc = parti[0].strip()
                            imp_str = parti[1].strip().replace('€', '').replace(' ', '').replace('.', '').replace(',', '.')
                            imp = float(imp_str)
                            if len(parti) >= 3 and parti[2].strip():
                                data_str = parti[2].strip()
                                data = None
                                for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y']:
                                    try:
                                        data = datetime.strptime(data_str, fmt).date()
                                        break
                                    except:
                                        pass
                                if not data:
                                    data = date.today().replace(day=1)
                            else:
                                data = date.today().replace(day=1)
                            add_fissa(desc, imp, data)
                            count += 1
                        else:
                            errori += 1
                    except Exception as e:
                        errori += 1
                        st.warning(f"❌ Riga {i}: {e}")
                
                if count > 0:
                    st.success(f"✅ Importate {count} spese fisse!")
                    if errori > 0:
                        st.warning(f"⚠️ {errori} righe non importate")
                    st.rerun()
                else:
                    st.error(f"❌ Nessuna spesa importata. {errori} errori.")
    
    st.write("---")
    
    df_fisse = load_fisse()
    
    if not df_fisse.empty:
        df_fisse['data_date'] = pd.to_datetime(df_fisse['data'])
        df_fisse['mese_key'] = df_fisse['data_date'].dt.strftime('%Y-%m')
        df_fisse['mese'] = df_fisse['data_date'].dt.strftime('%B %Y')
        df_fisse = df_fisse.sort_values(['data_date', 'descrizione'])
        
        oggi = date.today().replace(day=1)
        prossimo = oggi + relativedelta(months=1)
        mese_corrente_key = oggi.strftime('%Y-%m')
        mese_prossimo_key = prossimo.strftime('%Y-%m')
        
        def render_mese_fisse(df_mese):
            # Header colonne
            st.markdown('''<div style="display:flex;padding:2px 6px 4px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:2px;">
                <div style="flex:3;font-size:0.72rem;font-weight:700;color:#666;text-transform:uppercase;letter-spacing:.06em;">Descrizione</div>
                <div style="flex:1.5;font-size:0.72rem;font-weight:700;color:#666;text-transform:uppercase;letter-spacing:.06em;text-align:right;padding-right:8px;">Importo</div>
                <div style="flex:.6;"></div>
            </div>''', unsafe_allow_html=True)
            for idx, row in df_mese.iterrows():
                col1, col2, col3, col4 = st.columns([3, 1.5, 0.4, 0.4])
                with col1:
                    st.markdown(f'<div style="padding-top:8px;font-size:0.9rem;font-weight:500;">{row['descrizione']}</div>', unsafe_allow_html=True)
                with col2:
                    new_imp = st.number_input("€", value=float(row['importo']), key=f"fissa_imp_{row['id']}", label_visibility="collapsed", format="%.2f")
                with col3:
                    if st.button("💾", key=f"save_fissa_{row['id']}"):
                        if new_imp != row['importo']:
                            update_fissa(row['id'], new_imp)
                        st.rerun()
                with col4:
                    if st.button("🗑️", key=f"del_fissa_{row['id']}"):
                        delete_fissa(row['id'])
                        st.rerun()
        
        # Mesi passati (collassati)
        df_passati = df_fisse[df_fisse['mese_key'] < mese_corrente_key]
        if not df_passati.empty:
            with st.expander(f"📁 Mesi precedenti ({df_passati['mese_key'].nunique()})", expanded=False):
                for mk in df_passati['mese_key'].unique():
                    df_m = df_passati[df_passati['mese_key'] == mk]
                    st.write(f"##### 📅 {df_m.iloc[0]['mese']}")
                    render_mese_fisse(df_m)
        
        # Mese corrente (aperto)
        df_corrente = df_fisse[df_fisse['mese_key'] == mese_corrente_key]
        if not df_corrente.empty:
            st.write(f"### 📅 {oggi.strftime('%B %Y')} — *mese corrente*")
            render_mese_fisse(df_corrente)
            st.write("---")
        
        # Mese prossimo (aperto)
        df_prossimo = df_fisse[df_fisse['mese_key'] == mese_prossimo_key]
        if not df_prossimo.empty:
            st.write(f"### 📅 {prossimo.strftime('%B %Y')} — *mese prossimo*")
            render_mese_fisse(df_prossimo)
            st.write("---")
        
        # Mesi futuri oltre il prossimo (collassati)
        df_futuri = df_fisse[df_fisse['mese_key'] > mese_prossimo_key]
        if not df_futuri.empty:
            with st.expander(f"📁 Mesi futuri ({df_futuri['mese_key'].nunique()})", expanded=False):
                for mk in df_futuri['mese_key'].unique():
                    df_m = df_futuri[df_futuri['mese_key'] == mk]
                    st.write(f"##### 📅 {df_m.iloc[0]['mese']}")
                    render_mese_fisse(df_m)
    else:
        st.info("Nessuna spesa fissa inserita.")

# ============================================
# TAB PREVISIONI (CORRETTO: usa mese corrente, non mese_prec)
# ============================================
with tab3:
    st.subheader("Previsioni 12 Mesi")
    
    previsioni = []
    data_corrente = date.today().replace(day=1)
    
    for i in range(12):
        mese_key = data_corrente.strftime("%Y-%m")
        
        # Saldo iniziale
        if i == 0:
            saldo_iniziale = load_saldo_iniziale(mese_key)
        else:
            saldo_iniziale = previsioni[-1]['Saldo Finale']
        
        # Carica stipendio salvato
        stipendio_salvato = load_stipendio(mese_key)
        
        # Calcola somme - USA IL MESE CORRENTE (non mese_prec)
        df_carte_prev = load_carte()
        # Per le CARTE: spese del mese PRECEDENTE (logica carte: spesa maggio -> saldata giugno)
        mese_prec = data_corrente - relativedelta(months=1)
        carte_total = df_carte_prev[
            (pd.to_datetime(df_carte_prev['data']).dt.month == mese_prec.month) &
            (pd.to_datetime(df_carte_prev['data']).dt.year == mese_prec.year)
        ]['quota_seba'].sum() if not df_carte_prev.empty else 0
        
        # Per le FISSE: spese del MESE CORRENTE (logica fisse: spesa giugno -> scalata giugno)
        df_fisse_prev = load_fisse()
        fisse_total = df_fisse_prev[
            (pd.to_datetime(df_fisse_prev['data']).dt.month == data_corrente.month) &
            (pd.to_datetime(df_fisse_prev['data']).dt.year == data_corrente.year)
        ]['importo'].sum() / 2 if not df_fisse_prev.empty else 0
        
        uni_total = df_carte_prev[
            (df_carte_prev['descrizione'] == 'UNICREDIT') &
            (pd.to_datetime(df_carte_prev['data']).dt.month == mese_prec.month) &
            (pd.to_datetime(df_carte_prev['data']).dt.year == mese_prec.year)
        ]['quota_gio'].sum() if not df_carte_prev.empty else 0
        
        # Mostra mese
        st.write(f"### 📅 {data_corrente.strftime('%B %Y')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if i == 0:
                nuovo_saldo = st.number_input("Saldo Iniziale €", value=float(saldo_iniziale), key=f"saldo_{i}", format="%.2f")
                if nuovo_saldo != saldo_iniziale:
                    save_saldo_iniziale(mese_key, nuovo_saldo)
                    saldo_iniziale = nuovo_saldo
                    st.rerun()
            else:
                st.metric("Saldo Iniziale", f"€ {saldo_iniziale:.2f}")
        
        with col2:
            nuovo_stipendio = st.number_input("Stipendio €", value=float(stipendio_salvato), key=f"stip_{i}", format="%.2f")
            if nuovo_stipendio != stipendio_salvato:
                save_stipendio(mese_key, nuovo_stipendio)
                stipendio_salvato = nuovo_stipendio
                st.rerun()
        
        # Calcola saldo finale
        saldo_finale = saldo_iniziale + stipendio_salvato - carte_total - fisse_total + uni_total
        
        # Mostra dettagli
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Carte (Seba)", f"€ {carte_total:.2f}")
        with col2:
            st.metric("Fisse (Seba)", f"€ {fisse_total:.2f}")
        with col3:
            st.metric("UniGio", f"€ {uni_total:.2f}")
        with col4:
            delta = saldo_finale - saldo_iniziale
            st.metric("Saldo Finale", f"€ {saldo_finale:.2f}", delta=f"€ {delta:+.2f}")
        
        st.write("---")
        
        previsioni.append({'Saldo Finale': saldo_finale})
        data_corrente += relativedelta(months=1)

# ============================================
# TAB TOTALE GIO (CORRETTO: usa mese corrente per FISSE)
# ============================================
with tab4:
    st.subheader("Totale Spese Gio")
    
    totali = []
    data_corrente = date.today().replace(day=1)
    
    for i in range(12):
        mese_prec = data_corrente - relativedelta(months=1)
        
        df_carte_tot = load_carte()
        # CARTE: mese precedente
        carte_total = df_carte_tot[
            (pd.to_datetime(df_carte_tot['data']).dt.month == mese_prec.month) &
            (pd.to_datetime(df_carte_tot['data']).dt.year == mese_prec.year)
        ]['quota_gio'].sum() if not df_carte_tot.empty else 0
        
        df_fisse_tot = load_fisse()
        # FISSE: mese CORRENTE
        fisse_total = df_fisse_tot[
            (pd.to_datetime(df_fisse_tot['data']).dt.month == data_corrente.month) &
            (pd.to_datetime(df_fisse_tot['data']).dt.year == data_corrente.year)
        ]['importo'].sum() / 2 if not df_fisse_tot.empty else 0
        
        totali.append({
            'Mese': data_corrente.strftime("%B %Y"),
            'Carte (Gio)': f"€ {carte_total:.2f}",
            'Fisse (Gio)': f"€ {fisse_total:.2f}",
            'TOTALE': f"€ {carte_total + fisse_total:.2f}"
        })
        
        data_corrente += relativedelta(months=1)
    
    df_totali = pd.DataFrame(totali)
    
    # Evidenzia il mese prossimo (quello che più interessa)
    mese_evidenziato = (date.today().replace(day=1) + relativedelta(months=1)).strftime("%B %Y")
    
    def highlight_next_month(row):
        if row["Mese"] == mese_evidenziato:
            return ["background-color: #1a3a1a; color: #00ff88; font-weight: bold"] * len(row)
        return [""] * len(row)
    
    st.dataframe(
        df_totali.style.apply(highlight_next_month, axis=1),
        use_container_width=True,
        hide_index=True
    )
