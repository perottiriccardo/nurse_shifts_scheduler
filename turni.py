from pulp import LpVariable, lpSum, LpProblem, LpMinimize
import pandas as pd
import configparser
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class NurseShiftScheduler():
    config = configparser.ConfigParser()

    # Leggi il file di configurazione
    config.read('config.ini')

    n_giorni                = int(config['Vincoli']['Giorni_Mese'])
    infermieri              = [infermiere.strip() for infermiere in config['Anagrafica']['Infermieri'].split(',')]

    tipo_turno              = [tipo.strip() for tipo in config['Anagrafica']['Tipologie_Turno'].split(',')]
    tipo_turno_lavorativi   = list(set(tipo_turno) - set(["F"]))
    turni_no_riposo         = list(set(tipo_turno) - set(["R"]))
    turni_no_RGN            = list(set(tipo_turno) - set(["R", "G", "N"]))

    giorni_mese             = ['-5','-4','-3','-2','-1'] + [str(numero) for numero in range(1, n_giorni+1)]
    giorni_mese_true        = [str(numero) for numero in range(1, n_giorni+1)]
    

    
    def __init__(self):
        self.config = configparser.ConfigParser()

        # Leggi il file di configurazione
        self.config.read('config.ini')

        self.n_giorni                = int(self.config['Vincoli']['Giorni_Mese'])
        self.infermieri              = [infermiere.strip() for infermiere in self.config['Anagrafica']['Infermieri'].split(',')]

        self.tipo_turno              = [tipo.strip() for tipo in self.config['Anagrafica']['Tipologie_Turno'].split(',')]
        self.tipo_turno_lavorativi   = list(set(self.tipo_turno) - set(["F"]))
        self.turni_no_riposo         = list(set(self.tipo_turno) - set(["R"]))
        self.turni_no_RGN            = list(set(self.tipo_turno) - set(["R", "G", "N"]))

        self.giorni_mese             = ['-5','-4','-3','-2','-1'] + [str(numero) for numero in range(1, self.n_giorni+1)]
        self.giorni_mese_true        = [str(numero) for numero in range(1, self.n_giorni+1)]

        self.esigenze                = pd.read_excel('esigenze.xlsx', engine='openpyxl')
        self.ultimi_5_gg             = pd.read_csv('ultimi_5_gg.csv', sep=";")
        self.vincoli_infermiere      = pd.read_excel('vincoli_infermiere.xlsx', engine='openpyxl').set_index("Infermiere").to_dict()

        self.vincoli = {
            'turni_massimi': self.n_giorni + 5
        }


        self.problema = LpProblem("Pianificazione_turni", LpMinimize)
        self.turni = LpVariable.dicts("Turno", (self.giorni_mese, self.tipo_turno, self.infermieri), cat='Binary')

    def __init__(self, esigenze, ultimi_5_gg, vincoli_infermiere):
        self.config = configparser.ConfigParser()

        # Leggi il file di configurazione
        self.config.read('config.ini')

        self.n_giorni                = int(self.config['Vincoli']['Giorni_Mese'])
        self.infermieri              = [infermiere.strip() for infermiere in self.config['Anagrafica']['Infermieri'].split(',')]

        self.tipo_turno              = [tipo.strip() for tipo in self.config['Anagrafica']['Tipologie_Turno'].split(',')]
        self.tipo_turno_lavorativi   = list(set(self.tipo_turno) - set(["F"]))
        self.turni_no_riposo         = list(set(self.tipo_turno) - set(["R"]))
        self.turni_no_RGN            = list(set(self.tipo_turno) - set(["R", "G", "N"]))

        self.giorni_mese             = ['-5','-4','-3','-2','-1'] + [str(numero) for numero in range(1, self.n_giorni+1)]
        self.giorni_mese_true        = [str(numero) for numero in range(1, self.n_giorni+1)]

        self.esigenze                = esigenze
        self.ultimi_5_gg             = ultimi_5_gg
        self.vincoli_infermiere      = vincoli_infermiere.to_dict()

        self.vincoli = {
            'turni_massimi': self.n_giorni + 5
        }


        self.problema = LpProblem("Pianificazione_turni", LpMinimize)
        self.turni = LpVariable.dicts("Turno", (self.giorni_mese, self.tipo_turno, self.infermieri), cat='Binary')

    def pianifica_turni(self):

        # Giorni mese precedente
        for indice, riga in self.ultimi_5_gg.iterrows():
            for i in ['-5', '-4', '-3', '-2', '-1']:
                if i in self.giorni_mese and riga[i] in self.tipo_turno and riga['Infermiere'] in self.infermieri:
                    self.turni[i][riga[i]][riga['Infermiere']].setInitialValue(1)
                    self.turni[i][riga[i]][riga['Infermiere']].fixValue()

        # Aggiungi la funzione obiettivo (puoi personalizzarla in base alle tue esigenze)
        # Agire su questa
        self.problema += lpSum(self.turni[giorno][turno][persona] for giorno in self.giorni_mese for turno in self.tipo_turno for persona in self.infermieri), "Funzione_Obiettivo"

        # Vincoli esigenze (leggo dal file) - Calcolo anche numerosità ferie che non vanno aggiunte dal sistema 
        n_ferie = 0
        for giorno in self.giorni_mese:
            for persona in self.infermieri:
                lt = []
                for indice, riga in self.esigenze.iterrows():
                    if riga['Infermiere'] == persona and str(riga['Giorno']) == giorno:
                        lt = lt + riga['Esigenze'].split('|')
                
                if len(lt) != 0:
                    self.problema += lpSum(self.turni[giorno][t][persona] for t in lt) >= 1, f"Vincolo_esigenza{persona}_{giorno}"

                n_ferie += lt.count("F")

        # Non usare ferie oltre quelle fissate
        self.problema += lpSum(self.turni[giorno]["F"][persona] for persona in self.infermieri for giorno in self.giorni_mese_true ) == n_ferie, f"Vincolo_Ferie_Max_{persona}"

        # Ogni persona deve assegnare un turno al giorno, che sia riposo o lavoro
        for persona in self.infermieri:
            self.problema += lpSum(self.turni[giorno][turno][persona] for giorno in self.giorni_mese for turno in self.tipo_turno) == self.vincoli['turni_massimi'], f"Vincolo_Turni_Max_{persona}"

        # RIPOSI DA FARE IN UN UN MESE
        for persona in self.infermieri:
            self.problema += lpSum(
                self.turni[giorno]["R"][persona] for giorno in self.giorni_mese_true) == self.vincoli_infermiere['riposi'][persona] \
                , f"Vincolo_Riposi_Max_{persona}"

        # Vincoli numerosità turni
        for persona in self.infermieri:
            self.problema += lpSum(
                self.turni[giorno]["N"][persona] for giorno in self.giorni_mese_true) <= self.vincoli_infermiere['notti_max'][persona] \
                , f"Vincolo_Notti_Max_{persona}"

            self.problema += lpSum(
                self.turni[giorno]["M"][persona] for giorno in self.giorni_mese_true) <= self.vincoli_infermiere['mattini_max'][persona] \
                , f"Vincolo_Mat_Max_{persona}"
            
            self.problema += lpSum(
                self.turni[giorno]["P"][persona] for giorno in self.giorni_mese_true) <= self.vincoli_infermiere['pomeriggi_max'][persona] \
                , f"Vincolo_Pom_Max_{persona}"

            self.problema += lpSum(
                self.turni[giorno]["G"][persona] for giorno in self.giorni_mese_true) <= self.vincoli_infermiere['giornate_max'][persona] \
                , f"Vincolo_Gio_Max_{persona}"


            self.problema += lpSum(
                self.turni[giorno]["N"][persona] for giorno in self.giorni_mese_true) >= self.vincoli_infermiere['notti_min'][persona] \
                , f"Vincolo_Notti_Min_{persona}"

            self.problema += lpSum(
                self.turni[giorno]["M"][persona] for giorno in self.giorni_mese_true) >= self.vincoli_infermiere['mattini_min'][persona] \
                , f"Vincolo_Mat_Min_{persona}"
            
            self.problema += lpSum(
                self.turni[giorno]["P"][persona] for giorno in self.giorni_mese_true) >= self.vincoli_infermiere['pomeriggi_min'][persona] \
                , f"Vincolo_Pom_Min_{persona}"

            self.problema += lpSum(
                self.turni[giorno]["G"][persona] for giorno in self.giorni_mese_true) >= self.vincoli_infermiere['giornate_min'][persona] \
                , f"Vincolo_Gio_Min_{persona}"

        # Una persona fa un turno solo al giorno
        for giorno in self.giorni_mese_true:
            for persona in self.infermieri:
                self.problema += lpSum(
                    self.turni[giorno][turno][persona] for turno in self.tipo_turno) == 1 \
                    , f"Vincolo_Turni_Tipo_{persona}_{giorno}"

        # in un giorno un turno non può essere fatto da 2 infermieri (a parte i riposi) TODO: anche ferie
        for giorno in self.giorni_mese_true:
            for turno in self.turni_no_riposo:
                self.problema += lpSum(
                    self.turni[giorno][turno][persona] for persona in self.infermieri) <= 1 \
                    , f"Vincolo_Turni_Tipo_{giorno}_{turno}"

        # Per ogni giorno deve esserci almeno un turno di notte coperto
        for giorno in self.giorni_mese:
            self.problema += lpSum(
            self.turni[giorno]["N"][persona] for persona in self.infermieri) == 1 \
            , f"Vincolo_Notte_{giorno}"

        # Non ci possono essere Mattine seguite da Pomeriggi per una persona
        for j in range(5, len(self.giorni_mese)):
            for persona in self.infermieri:
                if self.vincoli_infermiere["no_mattino_dopo_pomeriggio"][persona]:
                    self.problema += self.turni[self.giorni_mese[j]]["M"][persona] + self.turni[self.giorni_mese[j- 1]]["P"][persona]  <= 1 \
                        , f"Vincolo_Dipendente_Turni_pommat_{persona}_{j}"

        # Non ci possono essere giornate che seguono pomeriggi
        for j in range(1, len(self.giorni_mese)):
            for persona in self.infermieri:
                if self.vincoli_infermiere["no_giornata_dopo_pomeriggio"][persona]:
                    self.problema += self.turni[self.giorni_mese[j]]["G"][persona] + self.turni[self.giorni_mese[j- 1]]["P"][persona]  <= 1 \
                        , f"Vincolo_Dipendente_Turni_pomgiorn_{persona}_{j}"

        # No mattino dopo giornata
        for j in range(1, len(self.giorni_mese)):
            for persona in self.infermieri:
                if self.vincoli_infermiere["no_mattino_dopo_giornata"][persona]:
                    self.problema += self.turni[self.giorni_mese[j]]["M"][persona] + self.turni[self.giorni_mese[j- 1]]["G"][persona]  <= 1 \
                        , f"Vincolo_Dipendente_Turni_giormat_{persona}_{j}"

        # Non ci possono essere pomeriggi che seguono notti
        for j in range(1, len(self.giorni_mese)):
            for persona in self.infermieri:
                self.problema += self.turni[self.giorni_mese[j]]["P"][persona] + self.turni[self.giorni_mese[j- 1]]["N"][persona]  <= 1 \
                    , f"Vincolo_Dipendente_Turni_notpom_{persona}_{j}"
        
        # Non ci possono essere mattine che seguono notti
        for j in range(1, len(self.giorni_mese)):
            for persona in self.infermieri:
                self.problema += self.turni[self.giorni_mese[j]]["M"][persona] + self.turni[self.giorni_mese[j- 1]]["N"][persona]  <= 1 \
                    , f"Vincolo_Dipendente_Turni_notmat_{persona}_{j}"
        
        # Non ci possono essere giornate che seguono da notti
        for j in range(1, len(self.giorni_mese)):
            for persona in self.infermieri:
                self.problema += self.turni[self.giorni_mese[j]]["G"][persona] + self.turni[self.giorni_mese[j- 1]]["N"][persona]  <= 1 \
                    , f"Vincolo_Dipendente_Turni_notgiorn_{persona}_{j}"
            
        # ALmeno 1 riposo in 6 turni di fila                                    
        for j in range(5, len(self.giorni_mese)):
            for persona in self.infermieri: 
                if self.vincoli_infermiere["no_6_turni_consecutivi"][persona]:
                    self.problema += self.turni[self.giorni_mese[j]]["R"][persona] + \
                                self.turni[self.giorni_mese[j- 1]]["R"][persona] + \
                                self.turni[self.giorni_mese[j- 2]]["R"][persona] + \
                                self.turni[self.giorni_mese[j- 3]]["R"][persona] + \
                                self.turni[self.giorni_mese[j- 5]]["R"][persona] + \
                                self.turni[self.giorni_mese[j- 4]]["R"][persona] >= 1 \
                        , f"Vincolo_Dipendente_Turni_atleast1R_{persona}_{j}"

        # No 5 notti di fila
        for j in range(4, len(self.giorni_mese)):
            for persona in self.infermieri:
                if self.vincoli_infermiere["no_5_notti_consecutive"][persona]:
                    self.problema += self.turni[self.giorni_mese[j]]["N"][persona] + self.turni[self.giorni_mese[j- 1]]["N"][persona] + self.turni[self.giorni_mese[j- 2]]["N"][persona] + self.turni[self.giorni_mese[j- 3]]["N"][persona] + self.turni[self.giorni_mese[j- 4]]["N"][persona] <= 4 \
                        , f"Vincolo_Dipendente_Turni_no5N_{persona}_{j}"

        # No 3 riposi di fila
        for j in range(2, len(self.giorni_mese)):
            for persona in self.infermieri:
                if self.vincoli_infermiere["no_3_riposi_consecutivi"][persona]:
                    self.problema += self.turni[self.giorni_mese[j]]["R"][persona] + self.turni[self.giorni_mese[j- 1]]["R"][persona] + self.turni[self.giorni_mese[j- 2]]["R"][persona] <= 2 \
                        , f"Vincolo_Dipendente_Turni_no3R_{persona}_{j}"

        # devono esserci almeno 2 riposi dopo la fine delle notti
        for j in range(5, len(self.giorni_mese)):
            for persona in self.infermieri:
                if self.vincoli_infermiere["due_riposi_dopo_notti"][persona]:
                    for turno in self.turni_no_riposo:
                        self.problema += self.turni[self.giorni_mese[j]][turno][persona] + self.turni[self.giorni_mese[j- 1]]["R"][persona] + self.turni[self.giorni_mese[j- 2]]["N"][persona]  <= 2 \
                            , f"Vincolo_Dipendente_Turni_2RN_{persona}_{turno}_{j}"

        # Non possono esserci R - turno - R (1 solo turno tra due riposi)
        for j in range(6, len(self.giorni_mese)):
            for persona in self.infermieri:
                if self.vincoli_infermiere["piu_turni_tra_riposi"][persona]:
                    for turno in self.turni_no_riposo:
                        self.problema += self.turni[self.giorni_mese[j]]["R"][persona] + self.turni[self.giorni_mese[j- 1]][turno][persona] + self.turni[self.giorni_mese[j- 2]]["R"][persona]  <= 2 \
                            , f"Vincolo_Dipendente_Turni_RTR_{persona}_{turno}_{j}"

        # Giornate e (mattine, pomeriggi) non possono stare insieme 
        for giorno in self.giorni_mese:
            self.problema += lpSum(
                self.turni[giorno]["G"][persona] + self.turni[giorno]["P"][persona] for persona in self.infermieri) == 1 \
                , f"Vincolo_Turni_TipoGP_{giorno}"
            self.problema += lpSum(
                self.turni[giorno]["G"][persona] + self.turni[giorno]["M"][persona] for persona in self.infermieri) == 1 \
                , f"Vincolo_Turni_TipoGM_{giorno}"   


        # Risolvi il problema
        return self.problema.solve()


    def generate_output(self):
        dic = {}
        for persona in self.infermieri:
            for giorno in self.giorni_mese:
                for turno in self.tipo_turno:
                    if self.turni[giorno][turno][persona].value() == 1:
                        if persona not in dic:
                            dic[persona] = [turno]
                        else:
                            dic[persona].append(turno)

        with open('turni.csv', 'w') as file:
            file.write("Infermiere;" + ';'.join(map(str, self.giorni_mese)) + "\n")
            for persona in dic:
                file.write(f"{persona};{';'.join(dic[persona])}\n")         

        # Stampa il valore della funzione obiettivo
        # print("Costo totale:", self.problema.objective.value())