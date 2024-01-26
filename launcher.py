import streamlit as st
import pandas as pd
import turni as t

def color_vowel(value):
    return f"background-color: green;" if value in [*"R"] else None

def past_days(value):
    return f"background-color: grey;"

def main():
    st.set_page_config(layout="wide")
    st.title("Nurse shift scheduler")

    tab1, tab2, tab3 = st.tabs(["Esigenze", "Vincoli per infermiere", "Ultimi 5 giorni del mese precedente"])

    ultimi_5_gg             = pd.read_csv('ultimi_5_gg.csv', sep=";")
    esigenze                = pd.read_csv('esigenze.csv', sep=";")
    vincoli_infermiere      = pd.read_csv('vincoli_infermiere.csv', sep=";").set_index("Infermiere")

    with tab1:
        st.header("Esigenze")
        st.text("Inserisci qui sotto le esigenze dei tuoi infermieri. Puoi mettere le lettere P,M,R,F,G,N e concatenazioni di queste (P|N -> può fare sia pomeriggio che notte)")

        esigenze['Infermiere'] = esigenze['Infermiere'].astype(pd.CategoricalDtype(t.NurseShiftScheduler.infermieri))
        esigenze['Giorno'] = esigenze['Giorno'].astype(pd.CategoricalDtype([numero for numero in range(1, t.NurseShiftScheduler.n_giorni+1)]))
        esigenze['Esigenze'] = esigenze['Esigenze'].astype(pd.CategoricalDtype(t.NurseShiftScheduler.tipo_turno))
        df_es = st.data_editor(esigenze, num_rows="dynamic")

    with tab2:
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
        
        df_vi = st.data_editor(vincoli_infermiere)

    with tab3:
        st.header("Ultimi 5 giorni del mese precedente")
        st.text("Inserisci qui sotto i turni degli ultimi cinque giorni del mese precedente. Consentiranno il corretto calcolo dei turni dei primi giorni del mese attuale.")
        for g in ['-5','-4','-3','-2','-1']:
            ultimi_5_gg[g] = ultimi_5_gg[g].astype(pd.CategoricalDtype(t.NurseShiftScheduler.tipo_turno))
        df_u5 = st.data_editor(ultimi_5_gg)

    if st.button("Genera turni"):
        df_es.to_csv('esigenze.csv', index=False, sep=";")
        df_u5.to_csv('ultimi_5_gg.csv', index=False, sep=";")
        df_vi.reset_index().to_csv('vincoli_infermiere.csv', index=False, sep=";")

        nurse_scheduler = t.NurseShiftScheduler(df_es, df_u5, df_vi)
        if nurse_scheduler.pianifica_turni() == 1:
            nurse_scheduler.generate_output()
            turni = pd.read_csv('turni.csv', sep=";")
            df_tu = st.dataframe(turni.style.applymap(past_days, subset=[str(numero) for numero in range(-5, 0)]).applymap(color_vowel))
        else:
            st.text("Il problema non è risolvibile. Rilassa qualche vincolo.")

if __name__ == "__main__":
    main()