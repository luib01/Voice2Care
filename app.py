import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import pydeck as pdk
import altair as alt

# Titolo principale rosso con emoji ambulanza
st.markdown("<h1 style='color:#B22222;'>🚑 Ambulance System</h1>", unsafe_allow_html=True)

# Introduzione generale
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

# ----------------------------
# Sezione: Area Geografica
# ----------------------------

st.markdown("<h2 style='color:#B22222;'>Mappa delle Città</h2>", unsafe_allow_html=True)

# Descrizione mappa
st.markdown(
    """
    <p style="color:#555; font-size:14px; margin-bottom:20px;">
    La mappa evidenzia le città con il maggior numero di interventi di emergenza. Queste aree richiedono un'organizzazione efficiente delle risorse, 
    inclusi personale e ambulanze, per garantire tempi di risposta rapidi e adeguati.
    </p>
    """,
    unsafe_allow_html=True
)

# Carica CSV
df = pd.read_csv("output/top_citta_interventi.csv")

# Geocoder
geolocator = Nominatim(user_agent="my_geocoder")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

@st.cache_data(show_spinner=False)
def get_coordinates(city_name):
    location = geocode(city_name + ", Italy")
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

# Aggiungi colonne lat e lon
if 'lat' not in df.columns or 'lon' not in df.columns:
    df['lat'] = None
    df['lon'] = None
    for i, row in df.iterrows():
        lat, lon = get_coordinates(row['citta'])
        df.at[i, 'lat'] = lat
        df.at[i, 'lon'] = lon

# Filtra righe con coordinate valide
df_map = df.dropna(subset=['lat', 'lon'])

if not df_map.empty:
    max_count = df_map['count'].max()

    # Funzione per scalare il raggio in modo proporzionale a count
    def scale_radius(count):
        base = 3000  # raggio minimo
        scale = 15000  # incremento massimo
        return base + (count / max_count) * scale

    # Crea la colonna 'radius' scalata
    df_map['radius'] = df_map['count'].apply(scale_radius)

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=df_map,
        get_position='[lon, lat]',
        get_fill_color='[178, 34, 34, 140]',  # rosso scuro semi-trasparente
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

# ----------------------------
# Sezione: Tempo di occupazione ambulanze
# ----------------------------

st.markdown("<h2 style='color:#B22222;'>Quanto Tempo Richiedono gli Interventi?</h2>", unsafe_allow_html=True)

st.markdown("""
<p style='font-size:16px; color:#333; margin-bottom:20px;'>
Il tempo è un fattore critico nel soccorso sanitario: ogni minuto può fare la differenza tra la vita e la morte. 
Monitorare quanto a lungo un’ambulanza resta occupata durante un intervento, quanto rapidamente riesce a raggiungere un paziente 
e quali aree mostrano maggiori ritardi ci aiuta a comprendere l’efficienza del sistema e a individuare le città che necessitano 
di un potenziamento di risorse. Questa sezione esplora le dinamiche temporali del servizio di emergenza, per riflettere non solo 
sui numeri, ma anche sulle implicazioni concrete per la salute dei cittadini.
</p>
""", unsafe_allow_html=True)

st.markdown("<h3 style='color:#B22222; margin-bottom:10px;'>Analisi dei Tempi di Occupazione delle Ambulanze</h3>", unsafe_allow_html=True)

# Descrizione analisi tempi di occupazione
st.markdown(
    """
    <p style="color:#555; font-size:14px; margin-bottom:20px;">
    Questa analisi mostra la distribuzione dei tempi di occupazione delle ambulanze durante gli interventi, evidenziando quanto tempo mediamente 
    un'ambulanza rimane impegnata, per comprendere l'efficienza e identificare eventuali criticità.
    </p>
    """,
    unsafe_allow_html=True
)

# Carica CSV
df_tempo = pd.read_csv("output/tempi_occupazione_ambulanza.csv")

# Pulisce i dati
df_tempo['durata_minuti'] = pd.to_numeric(df_tempo['durata_minuti'], errors='coerce')
df_tempo = df_tempo[df_tempo['durata_minuti'] >= 0]

# Crea fasce
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

# Raggruppa
df_fasce = df_tempo['fascia'].value_counts().reset_index()
df_fasce.columns = ['fascia', 'conteggio']
ordine = ['≤10 min', '11–20 min', '21–30 min', '>30 min']
df_fasce['fascia'] = pd.Categorical(df_fasce['fascia'], categories=ordine, ordered=True)
df_fasce = df_fasce.sort_values('fascia')

# Grafico
chart = alt.Chart(df_fasce).mark_bar(color='#B22222').encode(
    x=alt.X('fascia:N', title='Tempo occupazione ambulanza'),
    y=alt.Y('conteggio:Q', title='Numero di Ambulanze'),
    tooltip=['fascia', 'conteggio']
).properties(
    width=600,
    height=400,
    title='Distribuzione dei Tempi di Occupazione delle Ambulanze'
)

st.altair_chart(chart, use_container_width=True)

# Calcolo della durata media di occupazione
media_durata = df_tempo['durata_minuti'].mean()

st.markdown("<h3 style='color:#B22222; margin-bottom:10px;'>Durata media di occupazione</h3>", unsafe_allow_html=True)

st.markdown("""
<p style='color:#333; font-size:15px; margin-bottom:15px;'>
Nel soccorso sanitario d’emergenza, il tempo di risposta è un indicatore critico. In Italia, la normativa prevede che
in caso di emergenze gravi si debba intervenire in <strong>≤ 8 minuti</strong> nelle aree urbane e in <strong>≤ 20 minuti</strong> nelle aree extraurbane. 
Se la durata media supera queste soglie, si manifesta una <strong>criticità operativa</strong>; se resta al di sotto, 
possiamo considerarla un’<strong>ottima performance</strong> del sistema di emergenza.  
</p>
""", unsafe_allow_html=True)

st.metric("Tempo medio", f"{media_durata:.1f} minuti")

# Commento interpretativo
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

# Descrizione distribuzione ambulanze veloci e lente
st.markdown(
    """
    <p style="color:#555; font-size:14px; margin-bottom:20px;">
    In questa sezione vengono mostrate le percentuali di ambulanze con tempi di intervento estremamente rapidi (veloci) e particolarmente lunghi (lente) per ciascuna città, per evidenziare differenze locali nelle prestazioni del servizio.
    </p>
    """,
    unsafe_allow_html=True
)

# Carica dati aggregati
df_dist = pd.read_csv("output/distribuzione_ambulanze_estreme.csv")

if not df_dist.empty:
    # Grafico percentuali affiancate per città
    df_melted = df_dist.melt(id_vars=['citta'], 
                             value_vars=['percentuale_rapidi', 'percentuale_lenti'],
                             var_name='Tipo', value_name='Percentuale')

    # Cambia nomi per leggibilità
    df_melted['Tipo'] = df_melted['Tipo'].map({
        'percentuale_rapidi': 'Ambulanze Veloci (≤10 min)',
        'percentuale_lenti': 'Ambulanze Lente (≥30 min)'
    })

    chart_dist = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X('citta:N', sort='-y', title='Città'),
        y=alt.Y('Percentuale:Q', title='Percentuale (%)'),
        color=alt.Color('Tipo:N', scale=alt.Scale(range=['#1f77b4', '#ff7f0e']), legend=alt.Legend(title="Tipo Ambulanze")),
        tooltip=['citta', 'Tipo', alt.Tooltip('Percentuale', format='.2f')]
    ).properties(
        width=700,
        height=400,
        title='Percentuale di Ambulanze Veloci e Lente per Città'
    )

    st.altair_chart(chart_dist, use_container_width=True)
else:
    st.info("Il file con la distribuzione delle ambulanze estreme non è disponibile.")
