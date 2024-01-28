import streamlit as st
import pandas as pd
import turni as t
import calendar
from datetime import datetime, timedelta
import locale
from itertools import combinations

class NurseShiftSchedulerLauncher():
    locale.setlocale(locale.LC_TIME, 'it_IT.utf8')

    def __init__(self):
        self.anno = datetime.now().year
        self.mese = (datetime.now().month % 12) + 1
        self.data_selezionata = datetime(self.anno, self.mese, 1)
        
        self.ultimi_5_gg             = pd.read_csv('ultimi_5_gg.csv', sep=";").set_index("Infermiere")
        self.esigenze                = pd.read_csv('esigenze.csv', sep=";")
        self.vincoli_infermiere      = pd.read_csv('vincoli_infermiere.csv', sep=";").set_index("Infermiere")

        self.nurse_scheduler = t.NurseShiftScheduler(self.esigenze, self.ultimi_5_gg, self.vincoli_infermiere, self.data_selezionata)

        try:
            self.turni_old = pd.read_csv('turni.csv', sep=";").set_index("Infermiere")
        except:
            self.turni_old = None

    def color_vowel(self, value):
        return f"background-color: green;" if value in [*"R"] else None

    def past_days(self, value):
        return f"background-color: grey;"

    def launch(self):
        st.set_page_config(layout="wide")

        header="""
        <div >
            <span style="float: left;"><h1> 👩‍⚕️ Pianificatore di turni </h1></span> 
            <span style="float: right;"><h4> Versione 1.0 </h4></span>
        </div>
        """
        st.markdown(header,unsafe_allow_html=True)

        with st.expander("📖 Legenda e istruzioni"):
            # Includi Bootstrap CSS
            st.markdown("""
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
                """, unsafe_allow_html=True)
            # Layout con Bootstrap
            st.markdown("""
                <div class="container-fluid">
                <h4>Benvenuto!</h4> 
                <div>Questo applicativo permette di pianificare i turni del personale in ambito RSA. Una volta definite le regole e i vincoli che l'algoritmo pianificatore dovrà rispettare, è in grado di produrre una schedulazione di turni per un mese definito.
                Di seguito vengono elencate regole e istruzioni per l'utilizzo.</div>
                </div>
                <hr>
                <div class="container-fluid">
                <h5>Pannello 📆 Ultima pianificazione salvata</h5>
                <div>Il pannello mostra l'ultima pianificazione elaborata e salvata. <br>
                Una pianificazione viene elaborata premendo il tasto "🧮 Genera turni" e salvata premendo il tasto "💾 Salva pianificazione". 
                Utilizzo proposto: <br>
                <ol>
                <li> Genero una pianificazione con il tasto "🧮 Genera turni" </li>
                <li> Fino a quando la pianificazione non mi aggrada, ripeto il passo 1 modificando i esigenze/vincoli </li>
                <li> Quando la pianificazione mi convince la posso salvare con il tasto "💾 Salva pianificazione", così la prossima volta che entro nel sistema la vedo tramite il pannello in oggetto.</li>
                </ol></div>
                </div>

                Nel terzo pannello invece puoi configurare la pianificazione su tre ambiti: esigenze, vincoli e turni del mese precedente.

                Nella pagina delle esigenze potrai inserire i turni che i tuoi infermieri sono disponibili a fare nei giorni scelti. 
                L'algoritmo, per quei giorni e quegli infermieri, non utilizzerà altre tipologie di turno se non quelle scelte.

                Nella pagina dei vincoli potrai scegliere se far rispettare all'algoritmo i vincoli per ciascun infermiere.
                Ci sono molti vincoli da utilizzare. In fondo ci sono vincoli di minimo e massimo numero di tipologie di turno.

                Nella pagina dei turni del mese precedente puoi impostare i turni del mese precedente affinché siano rispettati i vincoli nel mese corrente.

                Il tasto "🖍️ Salva configurazione" permette di salvare la configurazione impostata per prossime elaborazioni.

                Il tasto "🧮 Genera turni" tenta di pianificare i turni con la configurazione impostata. Se ci sono troppi vincoli/esigenze è possibile che fallisca, in tal caso togliere vincoli.

                <table class="table table-striped">
                <thead>
                    <tr>
                    <th scope="col">Simbolo</th>
                    <th scope="col">Esteso</th>
                    <th scope="col">Descrizione</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                    <td>M</td>
                    <td>Mattino</td>
                    <td>Turno di mattina (8 ore)</td>
                    </tr>
                    <tr>
                    <td>P</td>
                    <td>Pomeriggio</td>
                    <td>Turno di pomeriggio (8 ore)</td>
                    </tr>
                    <tr>
                    <td>N</td>
                    <td>Notte</td>
                    <td>Turno di notte (8 ore)</td>
                    </tr>
                    <tr>
                    <td>G</td>
                    <td>Giornata</td>
                    <td>Turno di giorno (9 ore)</td>
                    </tr>
                    <tr>
                    <td>R</td>
                    <td>Riposo</td>
                    <td>Turno di riposo</td>
                    </tr>
                    <tr>
                    <td>F</td>
                    <td>Ferie</td>
                    <td>Ferie/Permesso</td>
                    </tr>
                    <tr>
                    <td>A</td>
                    <td>Assente</td>
                    <td>Assente (da utilizzare per malattia..)</td>
                    </tr>
                </tbody>
                </table>
                </div>""", unsafe_allow_html=True)

        with st.expander("📆 Ultima pianificazione salvata"):
            try:
                df_tu_old = st.dataframe(self.turni_old.style.map(self.past_days, subset=self.turni_old.columns[:5]).map(self.color_vowel))
            except:
                st.text("Non ci sono pianificazioni di turni salvate.")

        with st.expander("🛠️ Configura la pianificazione"):    
            col_anno, col_mese = st.columns(2)
            with col_anno:
                self.anno = st.number_input("Seleziona l'anno:", min_value=2023, max_value=2100, value=self.anno)
            with col_mese:
                self.mese = st.selectbox("Seleziona il mese:", list(calendar.month_name)[1:], index=self.mese)

            tab_esigenze, tab_vincoli, tab_ultimi_5 = st.tabs(["Esigenze", "Vincoli per infermiere", "Ultimi 5 giorni del mese precedente"])

            with tab_esigenze:
                st.header("Esigenze")
                st.text("Inserisci qui sotto le esigenze dei tuoi infermieri.")
                
                self.esigenze['Infermiere'] = self.esigenze['Infermiere'].astype(pd.CategoricalDtype(t.NurseShiftScheduler.infermieri))
                self.esigenze['Giorno'] = self.esigenze['Giorno'].astype(pd.CategoricalDtype([numero for numero in range(1, calendar.monthrange(self.anno, list(calendar.month_name).index(self.mese))[1]+1)]))

                risultati = []
                for lunghezza in range(1, len(t.NurseShiftScheduler.tipo_turno) + 1):
                    risultati.extend(combinations(t.NurseShiftScheduler.tipo_turno, lunghezza))
                tipi_esigenze = []
                for combo in risultati:
                    tipi_esigenze.append('|'.join(combo))
                self.esigenze['Esigenze'] = self.esigenze['Esigenze'].astype(pd.CategoricalDtype(tipi_esigenze))
                
                df_es = st.data_editor(self.esigenze, num_rows="dynamic")

            with tab_vincoli:
                st.header("Vincoli per infermiere")
                st.text("Inserisci qui sotto i vincoli da rispettare per ciascun infermiere.")
                
                self.vincoli_infermiere["no_6_turni_consecutivi"]=self.vincoli_infermiere["no_6_turni_consecutivi"].astype(pd.BooleanDtype())
                self.vincoli_infermiere["no_mattino_dopo_pomeriggio"]=self.vincoli_infermiere["no_mattino_dopo_pomeriggio"].astype(pd.BooleanDtype())
                self.vincoli_infermiere["no_mattino_dopo_giornata"]=self.vincoli_infermiere["no_mattino_dopo_giornata"].astype(pd.BooleanDtype())
                self.vincoli_infermiere["no_giornata_dopo_pomeriggio"]=self.vincoli_infermiere["no_giornata_dopo_pomeriggio"].astype(pd.BooleanDtype())
                self.vincoli_infermiere["due_riposi_dopo_notti"]=self.vincoli_infermiere["due_riposi_dopo_notti"].astype(pd.BooleanDtype())
                self.vincoli_infermiere["piu_turni_tra_riposi"]=self.vincoli_infermiere["piu_turni_tra_riposi"].astype(pd.BooleanDtype())
                self.vincoli_infermiere["no_5_notti_consecutive"]=self.vincoli_infermiere["no_5_notti_consecutive"].astype(pd.BooleanDtype())
                self.vincoli_infermiere["no_3_riposi_consecutivi"]=self.vincoli_infermiere["no_3_riposi_consecutivi"].astype(pd.BooleanDtype())
                self.vincoli_infermiere["riposi"]=self.vincoli_infermiere["riposi"].astype(pd.Int64Dtype())
                self.vincoli_infermiere["notti_max"]=self.vincoli_infermiere["notti_max"].astype(pd.Int64Dtype())
                self.vincoli_infermiere["mattini_max"]=self.vincoli_infermiere["mattini_max"].astype(pd.Int64Dtype())
                self.vincoli_infermiere["pomeriggi_max"]=self.vincoli_infermiere["pomeriggi_max"].astype(pd.Int64Dtype())
                self.vincoli_infermiere["giornate_max"]=self.vincoli_infermiere["giornate_max"].astype(pd.Int64Dtype())
                self.vincoli_infermiere["notti_min"]=self.vincoli_infermiere["notti_min"].astype(pd.Int64Dtype())
                self.vincoli_infermiere["mattini_min"]=self.vincoli_infermiere["mattini_min"].astype(pd.Int64Dtype())
                self.vincoli_infermiere["pomeriggi_min"]=self.vincoli_infermiere["pomeriggi_min"].astype(pd.Int64Dtype())
                self.vincoli_infermiere["giornate_min"]=self.vincoli_infermiere["giornate_min"].astype(pd.Int64Dtype())

                df_vi = st.data_editor(self.vincoli_infermiere)

            with tab_ultimi_5:
                st.header("Ultimi 5 giorni del mese precedente")
                st.text("Inserisci qui sotto i turni degli ultimi cinque giorni del mese precedente. Consentiranno il corretto calcolo dei turni dei primi giorni del mese attuale.")

                for g in ['-5','-4','-3','-2','-1']:
                    self.ultimi_5_gg[g] = self.ultimi_5_gg[g].astype(pd.CategoricalDtype(t.NurseShiftScheduler.tipo_turno))
                df_u5 = st.data_editor(self.ultimi_5_gg)

            if st.button("🖍️ Salva configurazione"):
                df_es.to_csv('esigenze.csv', index=False, sep=";")
                df_u5.reset_index().to_csv('ultimi_5_gg.csv', index=False, sep=";")
                df_vi.reset_index().to_csv('vincoli_infermiere.csv', index=False, sep=";")
                st.toast('Configurazione salvata con successo.', icon='🎉') 
    
        
        st.markdown(""" <style> button {height: auto; padding-top: 10px !important; padding-bottom: 10px !important;}</style>""",unsafe_allow_html=True,)
    
        if st.button("🧮 Genera turni"):
            if df_u5.isnull().sum().sum() + df_u5.eq('').sum().sum() == 0 and df_es.isnull().sum().sum() + df_es.eq('').sum().sum() == 0 and df_vi.isnull().sum().sum() + df_vi.eq('').sum().sum() == 0:

                with st.spinner("Attendi, sto ragionando molto intensamente, l'è nen 'na roba facile..."):
                    self.data_selezionata = datetime(self.anno, list(calendar.month_name).index(self.mese), 1)
                    self.nurse_scheduler = t.NurseShiftScheduler(df_es, df_u5, df_vi, self.data_selezionata)

                    if self.nurse_scheduler.pianifica_turni() == 1:
                        st.toast('Super, abbiamo una pianificazione!', icon='🎉')

                        turni = self.nurse_scheduler.generate_output()
                        self.nurse_scheduler.write_output_to_csv()

                        title_pianificazione=f"""<h3> Turni di {self.mese} {self.anno} </h3>"""
                        st.markdown(title_pianificazione,unsafe_allow_html=True)

                        df_tu = st.dataframe(turni.style.map(self.past_days, subset=self.nurse_scheduler.intestazione_output[:5]).map(self.color_vowel))

                        df_statistiche = turni[self.nurse_scheduler.intestazione_output[5:]].apply(pd.Series.value_counts, axis=1).fillna(0).astype(int)

                        for tt in self.nurse_scheduler.tipo_turno:
                            if tt not in df_statistiche.columns:
                                df_statistiche[tt] = 0

                        df_statistiche['Totale ore'] = df_statistiche.apply(lambda row: row['M'] * 8 + row['P'] * 8 + row['F'] * 8 + row['A'] * 8 + row['N'] * 8 + row['G'] * 9, axis=1)

                        title_statistiche=f"""<h4> Statistiche riepilogative </h4>"""
                        st.markdown(title_statistiche,unsafe_allow_html=True)

                        st.dataframe(df_statistiche)

                    else:
                        st.text("Il problema non è risolvibile. Iiiiiimpossibile. Rilassa qualche vincolo.")
            else:
                st.text("Ci sono caselle vuote nelle configurazioni. Riempile.")

        #if st.button("💾 Salva pianificazione"):
        #    st.text("OOOOOOOO")
        #    self.nurse_scheduler.write_output_to_csv()

        footer="""
        <div style='position: fixed;left: 0;bottom: 0;width: 100%; text-align: center;'>
            <p style='margin:10px; font-size:12px' >
                Developed with ❤ by 
                        <a href="https://www.instagram.com/riccardoperotti_/" target="_blank">
                            Riccardo Perotti
                        </a>
                        &nbsp;- Copyright © 2024 
            </p>
        </div>
        """
        st.markdown(footer,unsafe_allow_html=True)
