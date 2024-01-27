from itertools import combinations

def tutte_combinazioni(lista):
    risultati = []
    for lunghezza in range(1, len(lista) + 1):
        risultati.extend(combinations(lista, lunghezza))
    return risultati

# Esempio con una lista di 5 lettere
lista_di_lettere = ['A', 'B', 'C', 'D', 'E']

combinazioni = tutte_combinazioni(lista_di_lettere)

# Stampare le combinazioni
for combo in combinazioni:
    print(''.join(combo))