import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pydeck as pdk
import altair as alt
import pymongo

# ----------------------------
# Sidebar per selezione pagina
# ----------------------------
pagina = st.sidebar.selectbox(
    "Seleziona sezione",
    ["Ambulanze", "Pazienti"]
)

# ----------------------------
# Funzione: Pagina Ambulanze
# ----------------------------
def pagina_ambulanze():
    st.markdown("<h1 style='color:#B22222;'>🚑 Ambulance System</h1>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color:#333; font-size:16px; margin-bottom:20px;">
        Benvenuti nell'applicazione dedicata all'analisi del sistema di emergenza ambulanza in Italia. 
        Questo sistema offre una panoramica approfondita sull'efficienza e la gestione delle emergenze sanitarie in Italia. 
        Attraverso dati aggiornati e visualizzazioni intuitive, vogliamo supportare la comprensione e il miglioramento del servizio ambulanza, 
        mettendo in luce i trend principali e le dinamiche sul territorio nazionale.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<h2 style='color:#B22222;'>Mappa delle Città</h2>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color:#555; font-size:14px; margin-bottom:20px;">
        La mappa evidenzia le città con il maggior numero di interventi di emergenza. Queste aree richiedono un'organizzazione efficiente delle risorse, 
        inclusi personale e ambulanze, per garantire tempi di risposta rapidi e adeguati.
        </p>
        """,
        unsafe_allow_html=True
    )

    df = pd.read_csv("output/top_citta_interventi.csv")

    geolocator = Nominatim(user_agent="my_geocoder")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    @st.cache_data(show_spinner=False)
    def get_coordinates(city_name):
        location = geocode(city_name + ", Italy")
        if location:
            return location.latitude, location.longitude
        else:
            return None, None

    if 'lat' not in df.columns or 'lon' not in df.columns:
        df['lat'] = None
        df['lon'] = None
        for i, row in df.iterrows():
            lat, lon = get_coordinates(row['citta'])
            df.at[i, 'lat'] = lat
            df.at[i, 'lon'] = lon

    df_map = df.dropna(subset=['lat', 'lon'])

    if not df_map.empty:
        max_count = df_map['count'].max()
        def scale_radius(count):
            base = 3000
            scale = 15000
            return base + (count / max_count) * scale
        df_map['radius'] = df_map['count'].apply(scale_radius)

        layer = pdk.Layer(
            'ScatterplotLayer',
            data=df_map,
            get_position='[lon, lat]',
            get_fill_color='[178, 34, 34, 140]',
            get_radius='radius',
            pickable=True,
            auto_highlight=True,
        )

        view_state = pdk.ViewState(
            latitude=df_map['lat'].mean(),
            longitude=df_map['lon'].mean(),
            zoom=6,
            pitch=0
        )

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{citta}\nInterventi: {count}"}
        )

        st.pydeck_chart(r)
    else:
        st.warning("Non è stato possibile geocodificare le città per mostrarle sulla mappa.")

    st.markdown("<h2 style='color:#B22222;'>Quanto Tempo Richiedono gli Interventi?</h2>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style='font-size:16px; color:#333; margin-bottom:20px;'>
        Il tempo è un fattore critico nel soccorso sanitario: ogni minuto può fare la differenza tra la vita e la morte. 
        Monitorare quanto a lungo un’ambulanza resta occupata durante un intervento, quanto rapidamente riesce a raggiungere un paziente 
        e quali aree mostrano maggiori ritardi ci aiuta a comprendere l’efficienza del sistema e a individuare le città che necessitano 
        di un potenziamento di risorse. Questa sezione esplora le dinamiche temporali del servizio di emergenza, per riflettere non solo 
        sui numeri, ma anche sulle implicazioni concrete per la salute dei cittadini.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<h3 style='color:#B22222; margin-bottom:10px;'>Analisi dei Tempi di Occupazione delle Ambulanze</h3>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color:#555; font-size:14px; margin-bottom:20px;">
        Questa analisi mostra la distribuzione dei tempi di occupazione delle ambulanze durante gli interventi, evidenziando quanto tempo mediamente 
        un'ambulanza rimane impegnata, per comprendere l'efficienza e identificare eventuali criticità.
        </p>
        """,
        unsafe_allow_html=True
    )

    df_tempo = pd.read_csv("output/tempi_occupazione_ambulanza.csv")
    df_tempo['durata_minuti'] = pd.to_numeric(df_tempo['durata_minuti'], errors='coerce')
    df_tempo = df_tempo[df_tempo['durata_minuti'] >= 0]

    def fascia_temporale(d):
        if d <= 10:
            return '≤10 min'
        elif d <= 20:
            return '11–20 min'
        elif d <= 30:
            return '21–30 min'
        else:
            return '>30 min'

    df_tempo['fascia'] = df_tempo['durata_minuti'].apply(fascia_temporale)

    df_fasce = df_tempo['fascia'].value_counts().reset_index()
    df_fasce.columns = ['fascia', 'conteggio']
    ordine = ['≤10 min', '11–20 min', '21–30 min', '>30 min']
    df_fasce['fascia'] = pd.Categorical(df_fasce['fascia'], categories=ordine, ordered=True)
    df_fasce = df_fasce.sort_values('fascia')

    chart = alt.Chart(df_fasce).mark_bar(color='#B22222').encode(
        x=alt.X('fascia:N', title='Tempo occupazione ambulanza'),
        y=alt.Y('conteggio:Q', title='Numero di Ambulanze'),
        tooltip=['fascia', 'conteggio']
    ).properties(width=600, height=400)

    st.altair_chart(chart, use_container_width=True)

    media_durata = df_tempo['durata_minuti'].mean()

    st.markdown("<h3 style='color:#B22222; margin-bottom:10px;'>Durata media di occupazione</h3>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style='color:#333; font-size:15px; margin-bottom:15px;'>
        Nel soccorso sanitario d’emergenza, il tempo di risposta è un indicatore critico. In Italia, la normativa prevede che
        in caso di emergenze gravi si debba intervenire in <strong>≤ 8 minuti</strong> nelle aree urbane e in <strong>≤ 20 minuti</strong> nelle aree extraurbane. 
        Se la durata media supera queste soglie, si manifesta una <strong>criticità operativa</strong>; se resta al di sotto, 
        possiamo considerarla un’<strong>ottima performance</strong> del sistema di emergenza.  
        </p>
        """,
        unsafe_allow_html=True
    )

    st.metric("Tempo medio", f"{media_durata:.1f} minuti")

    if media_durata > 20:
        messaggio = (
            "⚠️ <b>Criticità elevata:</b> la durata media supera i 20 minuti, soglia critica per le aree extraurbane. "
            "Questo può indicare una forte congestione del servizio, ritardi nella disponibilità di ambulanze o problematiche nella logistica territoriale."
        )
    elif media_durata > 8:
        messaggio = (
            "🟡 <b>Attenzione:</b> la durata media è compresa tra 8 e 20 minuti. "
            "È accettabile in contesto extraurbano, ma oltre il limite raccomandato per le aree urbane: potrebbero esserci margini di miglioramento."
        )
    else:
        messaggio = (
            "✅ <b>Ottimo risultato:</b> la durata media è inferiore agli 8 minuti, perfettamente in linea con gli standard delle aree urbane. "
            "Il sistema mostra una notevole efficienza nei tempi di intervento."
        )
    
    st.markdown(f"<p style='color:#444; font-size:15px; margin-bottom:20px;'>{messaggio}</p>", unsafe_allow_html=True)

    st.markdown("<h3 style='color:#B22222; margin-bottom:10px;'>Distribuzione delle Ambulanze Veloci e Lente per Città</h3>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color:#555; font-size:14px; margin-bottom:20px;">
        In questa sezione vengono mostrate le percentuali di ambulanze con tempi di intervento estremamente rapidi (veloci) e particolarmente lunghi (lente) per ciascuna città, per evidenziare differenze locali nelle prestazioni del servizio.
        </p>
        """,
        unsafe_allow_html=True
    )

    df_dist = pd.read_csv("output/distribuzione_ambulanze_estreme.csv")

    if not df_dist.empty:
        df_melted = df_dist.melt(id_vars=['citta'], 
                                 value_vars=['percentuale_rapidi', 'percentuale_lenti'],
                                 var_name='Tipo', value_name='Percentuale')
        df_melted['Tipo'] = df_melted['Tipo'].map({
            'percentuale_rapidi': 'Ambulanze Veloci (≤10 min)',
            'percentuale_lenti': 'Ambulanze Lente (≥30 min)'
        })
        chart_dist = alt.Chart(df_melted).mark_bar().encode(
            x=alt.X('citta:N', sort='-y', title='Città'),
            y=alt.Y('Percentuale:Q', title='Percentuale (%)'),
            color=alt.Color('Tipo:N', scale=alt.Scale(range=['#1f77b4', '#ff7f0e']), legend=alt.Legend(title="Tipo Ambulanze")),
            tooltip=['citta', 'Tipo', alt.Tooltip('Percentuale', format='.2f')]
        ).properties(width=700, height=400)
        st.altair_chart(chart_dist, use_container_width=True)
    else:
        st.info("Il file con la distribuzione delle ambulanze estreme non è disponibile.")

    st.markdown("<h4 style='color:#B22222; margin-top:40px;'>Volume di Interventi per Fascia Oraria</h4>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style='font-size:15px; color:#333; margin-bottom:20px;'>
        Conoscere l’orario in cui si concentrano le chiamate per ambulanza permette una migliore pianificazione delle risorse.
        Il grafico seguente mostra la distribuzione <strong>del numero di interventi</strong> in base all’orario di partenza del mezzo.
        </p>
        """,
        unsafe_allow_html=True
    )

    # Converte le ore in formato datetime
    df_tempo['ora_partenza_ambulanza'] = pd.to_datetime(df_tempo['ora_partenza_ambulanza'], format="%H:%M", errors='coerce')

    # Filtra righe valide
    df_orari = df_tempo.dropna(subset=['ora_partenza_ambulanza']).copy()

    # Definizione fasce orarie
    def fascia_oraria(h):
        if 6 <= h < 10:
            return "06:00 - 09:59"
        elif 10 <= h < 14:
            return "10:00 - 13:59"
        elif 14 <= h < 18:
            return "14:00 - 17:59"
        elif 18 <= h < 22:
            return "18:00 - 21:59"
        elif 22 <= h or h < 2:
            return "22:00 - 01:59"
        else:
            return "02:00 - 05:59"

    # Applica la fascia oraria
    df_orari['fascia_oraria'] = df_orari['ora_partenza_ambulanza'].dt.hour.apply(fascia_oraria)

    # Conta gli interventi per fascia
    df_interventi = df_orari['fascia_oraria'].value_counts().reset_index()
    df_interventi.columns = ['Fascia Oraria', 'Numero Interventi']
    ordine_fasce = ["06:00 - 09:59", "10:00 - 13:59", "14:00 - 17:59", "18:00 - 21:59", "22:00 - 01:59", "02:00 - 05:59"]
    df_interventi['Fascia Oraria'] = pd.Categorical(df_interventi['Fascia Oraria'], categories=ordine_fasce, ordered=True)
    df_interventi = df_interventi.sort_values('Fascia Oraria')

    # Grafico Altair
    chart_volume = alt.Chart(df_interventi).mark_bar(color='#B22222').encode(
        x=alt.X("Fascia Oraria:N", title="Fascia Oraria"),
        y=alt.Y("Numero Interventi:Q", title="Numero di Interventi"),
        tooltip=["Fascia Oraria", "Numero Interventi"]
    ).properties(width=600, height=400)

    st.altair_chart(chart_volume, use_container_width=True)

    st.markdown(
        """
        <p style='color:#444; font-size:14px;'>
        Il picco di interventi può coincidere con momenti della giornata a maggiore mobilità o eventi critici ricorrenti. 
        Questo tipo di analisi è essenziale per definire le fasce orarie di <strong>massimo carico operativo</strong>.
        </p>
        """,
        unsafe_allow_html=True
    )


    st.markdown("<h2 style='color:#B22222;'>Eventi Critici: Decessi sul Posto</h2>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style='font-size:16px; color:#333; margin-bottom:20px;'>
        Alcuni interventi di emergenza purtroppo si concludono con esiti fatali. Analizzare la frequenza dei <strong>decessi sul posto</strong> 
        ci permette di valutare la gravità degli eventi affrontati e le criticità nella risposta sanitaria. Qui esploriamo sia il dato a livello nazionale, 
        sia la distribuzione dei decessi per città, per identificare eventuali concentrazioni anomale o contesti ad alto rischio.
        </p>
        """,
        unsafe_allow_html=True
    )

    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["cartella_clinica_db"]
        collection = db["interventi"]
        dati = list(collection.find({}, {"decesso_sul_posto": 1, "citta": 1}))

        if not dati:
            st.warning("Nessun dato disponibile sugli esiti degli interventi.")
        else:
            df = pd.DataFrame(dati)

            totale_interventi = len(df)
            decessi_sul_posto = df[df["decesso_sul_posto"] == True]
            numero_decessi = len(decessi_sul_posto)
            percentuale_nazionale = (numero_decessi / totale_interventi) * 100 if totale_interventi > 0 else 0

            st.markdown("<h3 style='color:#B22222; margin-bottom:10px;'>Percentuale Nazionale di Decessi sul Posto</h3>", unsafe_allow_html=True)
            st.metric("Decessi sul posto", f"{percentuale_nazionale:.2f}%")

            st.markdown(
                """
                <p style='color:#444; font-size:15px; margin-bottom:20px;'>
                Questa percentuale indica quanti interventi si sono conclusi con un decesso prima del trasporto ospedaliero. 
                Un valore elevato potrebbe indicare condizioni gravi alla chiamata, ritardi nei soccorsi o mancanza di risorse tempestive.
                </p>
                """,
                unsafe_allow_html=True
            )

            st.markdown("<h3 style='color:#B22222; margin-bottom:10px;'>Distribuzione per Città</h3>", unsafe_allow_html=True)

            df["citta"] = df["citta"].fillna("Non specificata")
            df_citta = df.groupby("citta").size().reset_index(name="interventi_totali")
            df_citta_decessi = decessi_sul_posto.groupby("citta").size().reset_index(name="decessi")
            df_merge = pd.merge(df_citta, df_citta_decessi, on="citta", how="left").fillna(0)
            df_merge["percentuale"] = (df_merge["decessi"] / df_merge["interventi_totali"]) * 100
            df_merge = df_merge[df_merge["interventi_totali"] >= 10]  # escludiamo città con pochi dati

            chart_decessi = alt.Chart(df_merge.sort_values("percentuale", ascending=False).head(15)).mark_bar(color="#B22222").encode(
                x=alt.X("percentuale:Q", title="Percentuale (%)"),
                y=alt.Y("citta:N", title="Città", sort="-x"),
                tooltip=["citta", "decessi", "interventi_totali", alt.Tooltip("percentuale", format=".2f")]
            ).properties(width=700, height=400)

            st.altair_chart(chart_decessi, use_container_width=True)

    except Exception as e:
        st.error(f"Errore durante il recupero dei dati dal database: {e}")

# ----------------------------
# Funzione: Pagina Pazienti
# ----------------------------
def pagina_pazienti():
    st.markdown("<h1 style='color:#228B22;'>🧑‍⚕️ Gestione Pazienti</h1>", unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color:#333; font-size:16px; margin-bottom:20px;">
        In questa sezione puoi esplorare i dati dei pazienti raccolti durante gli interventi, come sintomi, età, città di provenienza 
        e destinazioni ospedaliere. L'obiettivo è identificare pattern clinici, frequenze di patologie e criticità nei trasporti sanitari.
        </p>
        """,
        unsafe_allow_html=True
    )

    try:
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["cartella_clinica_db"]  
        collection = db["interventi"]  

        dati = list(collection.find())
        if not dati:
            st.warning("Nessun dato trovato nella collezione.")
            return

        df = pd.DataFrame(dati)

        st.subheader("Sintomi più frequenti")
        if "sintomi" in df.columns:
            sintomi_espansi = df.explode("sintomi")
            sintomi_freq = sintomi_espansi["sintomi"].value_counts().reset_index()
            sintomi_freq.columns = ["Sintomo", "Frequenza"]

            chart_sintomi = alt.Chart(sintomi_freq.head(15)).mark_bar(color="#6A5ACD").encode(
                x=alt.X("Frequenza:Q"),
                y=alt.Y("Sintomo:N", sort='-x'),
                tooltip=["Sintomo", "Frequenza"]
            ).properties(width=700, height=400)

            st.altair_chart(chart_sintomi, use_container_width=True)

        st.subheader("Sintomi più frequenti per fascia d'età")

        if "eta" in df.columns and "sintomi" in df.columns:
            df = df[df["eta"].notnull()]
            df["eta"] = pd.to_numeric(df["eta"], errors="coerce")
            
            def fascia_eta(e):
                if e <= 18:
                    return "0–18"
                elif e <= 35:
                    return "19–35"
                elif e <= 60:
                    return "36–60"
                else:
                    return "60+"
            
            df["fascia_eta"] = df["eta"].apply(fascia_eta)
            df_exploded = df.explode("sintomi")
            df_gruppo = df_exploded.groupby(["fascia_eta", "sintomi"]).size().reset_index(name="conteggio")
            
            top_sintomi = df_gruppo.groupby("sintomi")["conteggio"].sum().nlargest(10).index
            df_gruppo_top = df_gruppo[df_gruppo["sintomi"].isin(top_sintomi)]
            
            chart_fasce = alt.Chart(df_gruppo_top).mark_bar().encode(
                x=alt.X("conteggio:Q", title="Frequenza"),
                y=alt.Y("sintomi:N", title="Sintomo", sort="-x"),
                color=alt.Color("fascia_eta:N", title="Fascia d'età"),
                tooltip=["sintomi", "fascia_eta", "conteggio"]
            ).properties(width=700, height=400)
            
            st.altair_chart(chart_fasce, use_container_width=True)
        else:
            st.info("Dati insufficienti per analizzare sintomi per età.")

    except Exception as e:
        st.error(f"Errore nella connessione al database: {e}")



# ----------------------------
# Logica di navigazione
# ----------------------------
if pagina == "Ambulanze":
    pagina_ambulanze()
elif pagina == "Pazienti":
    pagina_pazienti()
