import streamlit as st
import pandas as pd
import turni as t
import calendar
from datetime import datetime, timedelta
import locale

locale.setlocale(locale.LC_TIME, 'it_IT.utf8')

def color_vowel(value):
    return f"background-color: green;" if value in [*"R"] else None

def past_days(value):
    return f"background-color: grey;"

def main():
    st.set_page_config(layout="wide")
    
    # Greet the user by their name.
    #st.write('Ciao, %s !' % st.experimental_user.email)

    st.title("Pianificatore di turni")

    anno = None
    mese = None
    ultimi_5_gg             = pd.read_csv('ultimi_5_gg.csv', sep=";").set_index("Infermiere")
    esigenze                = pd.read_csv('esigenze.csv', sep=";")
    vincoli_infermiere      = pd.read_csv('vincoli_infermiere.csv', sep=";").set_index("Infermiere")

    with st.expander("Visualizza ultima pianificazione salvata"):
        try:
            turni_old             = pd.read_csv('turni.csv', sep=";").set_index("Infermiere")
            df_tu_old = st.dataframe(turni_old.style.map(past_days, subset=turni_old.columns[:5]).map(color_vowel))
        except:
            st.text("Non ci sono pianificazioni di turni salvate.")

    with st.expander("Configura la pianificazione (esigenze, vincoli e turni del mese precedente)"):    
        col_anno, col_mese = st.columns(2)
        with col_anno:
            anno = st.number_input("Seleziona l'anno:", min_value=2023, max_value=2100, value=datetime.now().year)
        with col_mese:
            mese = st.selectbox("Seleziona il mese:", list(calendar.month_name)[1:], index=(datetime.now().month % 12) + 1)

        tab_esigenze, tab_vincoli, tab_ultimi_5 = st.tabs(["Esigenze", "Vincoli per infermiere", "Ultimi 5 giorni del mese precedente"])

        with tab_esigenze:
            st.header("Esigenze")
            st.text("Inserisci qui sotto le esigenze dei tuoi infermieri. Puoi mettere le lettere P,M,R,F,G,N e concatenazioni di queste (P|N -> può fare sia pomeriggio che notte)")
            st.text("Esempi: P se vuoi che l'infermiere faccia pomeriggio, P|N se vuoi che l'infermiere faccia o pomeriggio o notte, R|P|M se vuoi che l'infermiere faccia o riposo, o pomeriggio o notte.")

            esigenze['Infermiere'] = esigenze['Infermiere'].astype(pd.CategoricalDtype(t.NurseShiftScheduler.infermieri))
            esigenze['Giorno'] = esigenze['Giorno'].astype(pd.CategoricalDtype([numero for numero in range(1, calendar.monthrange(anno, list(calendar.month_name).index(mese))[1]+1)]))
            df_es = st.data_editor(esigenze, num_rows="dynamic")

        with tab_vincoli:
            st.header("Vincoli per infermiere")
            st.text("Inserisci qui sotto i vincoli da rispettare per ciascun infermiere. Se il generatore non dovesse trovare soluzioni, prova a togliere qualche vincolo, a partire da quelli più soft.")
            
            vincoli_infermiere["no_6_turni_consecutivi"]=vincoli_infermiere["no_6_turni_consecutivi"].astype(pd.BooleanDtype())
            vincoli_infermiere["no_mattino_dopo_pomeriggio"]=vincoli_infermiere["no_mattino_dopo_pomeriggio"].astype(pd.BooleanDtype())
            vincoli_infermiere["no_mattino_dopo_giornata"]=vincoli_infermiere["no_mattino_dopo_giornata"].astype(pd.BooleanDtype())
            vincoli_infermiere["no_giornata_dopo_pomeriggio"]=vincoli_infermiere["no_giornata_dopo_pomeriggio"].astype(pd.BooleanDtype())
            vincoli_infermiere["due_riposi_dopo_notti"]=vincoli_infermiere["due_riposi_dopo_notti"].astype(pd.BooleanDtype())
            vincoli_infermiere["piu_turni_tra_riposi"]=vincoli_infermiere["piu_turni_tra_riposi"].astype(pd.BooleanDtype())
            vincoli_infermiere["no_5_notti_consecutive"]=vincoli_infermiere["no_5_notti_consecutive"].astype(pd.BooleanDtype())
            vincoli_infermiere["no_3_riposi_consecutivi"]=vincoli_infermiere["no_3_riposi_consecutivi"].astype(pd.BooleanDtype())
            vincoli_infermiere["riposi"]=vincoli_infermiere["riposi"].astype(pd.Int64Dtype())
            vincoli_infermiere["notti_max"]=vincoli_infermiere["notti_max"].astype(pd.Int64Dtype())
            vincoli_infermiere["mattini_max"]=vincoli_infermiere["mattini_max"].astype(pd.Int64Dtype())
            vincoli_infermiere["pomeriggi_max"]=vincoli_infermiere["pomeriggi_max"].astype(pd.Int64Dtype())
            vincoli_infermiere["giornate_max"]=vincoli_infermiere["giornate_max"].astype(pd.Int64Dtype())
            vincoli_infermiere["notti_min"]=vincoli_infermiere["notti_min"].astype(pd.Int64Dtype())
            vincoli_infermiere["mattini_min"]=vincoli_infermiere["mattini_min"].astype(pd.Int64Dtype())
            vincoli_infermiere["pomeriggi_min"]=vincoli_infermiere["pomeriggi_min"].astype(pd.Int64Dtype())
            vincoli_infermiere["giornate_min"]=vincoli_infermiere["giornate_min"].astype(pd.Int64Dtype())

            df_vi = st.data_editor(vincoli_infermiere)

        with tab_ultimi_5:
            st.header("Ultimi 5 giorni del mese precedente")
            st.text("Inserisci qui sotto i turni degli ultimi cinque giorni del mese precedente. Consentiranno il corretto calcolo dei turni dei primi giorni del mese attuale.")

            for g in ['-5','-4','-3','-2','-1']:
                ultimi_5_gg[g] = ultimi_5_gg[g].astype(pd.CategoricalDtype(t.NurseShiftScheduler.tipo_turno))
            df_u5 = st.data_editor(ultimi_5_gg)

    
    if st.button("Salva configurazione"):
        df_es.to_csv('esigenze.csv', index=False, sep=";")
        df_u5.reset_index().to_csv('ultimi_5_gg.csv', index=False, sep=";")
        df_vi.reset_index().to_csv('vincoli_infermiere.csv', index=False, sep=";")
        st.success("Configurazione salvata con successo. ")

    if st.button("Genera turni"):
        if df_u5.isnull().sum().sum() + df_u5.eq('').sum().sum() == 0 and df_es.isnull().sum().sum() + df_es.eq('').sum().sum() == 0 and df_vi.isnull().sum().sum() + df_vi.eq('').sum().sum() == 0:
 
            with st.spinner("Attendi, sto ragionando molto intensamente, l'è nen 'na roba facile..."):
                data_selezionata = datetime(anno, list(calendar.month_name).index(mese), 1)
                
                nurse_scheduler = t.NurseShiftScheduler(df_es, df_u5, df_vi, data_selezionata)
                if nurse_scheduler.pianifica_turni() == 1:
                    turni = nurse_scheduler.generate_output()
                    st.text(f"Turni del mese di {mese} {anno}")
                    df_tu = st.dataframe(turni.style.map(past_days, subset=nurse_scheduler.intestazione_output[:5]).map(color_vowel))

                    df_statistiche = turni[nurse_scheduler.intestazione_output[5:]].apply(pd.Series.value_counts, axis=1).fillna(0).astype(int)

                    for tt in nurse_scheduler.tipo_turno:
                        if tt not in df_statistiche.columns:
                            df_statistiche[tt] = 0

                    df_statistiche['Totale ore'] = df_statistiche.apply(lambda row: row['M'] * 8 + row['P'] * 8 + row['F'] * 8 + row['A'] * 8 + row['N'] * 8 + row['G'] * 9, axis=1)

                    st.text("Statistiche riepilogative")
                    st.dataframe(df_statistiche)

                    nurse_scheduler.write_output_to_csv()
                    
                else:
                    st.text("Il problema non è risolvibile. Iiiiiimpossibile. Rilassa qualche vincolo.")
        else:
            st.text("Ci sono caselle vuote nelle configurazioni. Riempile.")






    footer="""
    <div style='position: fixed;left: 0;bottom: 0;width: 100%; text-align: center;'>
        <p>
            Developed with ❤ by 
                    <a href="https://www.instagram.com/riccardoperotti_/" target="_blank">
                        Riccardo Perotti
                    </a>
                    &nbsp;- Copyright © 2024 
        </p>
    </div>
    """
    st.markdown(footer,unsafe_allow_html=True)








if __name__ == "__main__":
    main()