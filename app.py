def cerca_su_json_locale(simbolo_letto, localita, dati_json):
    """Cerca la corrispondenza del segnavia tenendo conto di sinonimi e codici."""
    if not dati_json or 'features' not in dati_json:
        return None

    simbolo_letto = simbolo_letto.lower().strip()
    
    # Dizionario dei sinonimi per mappare le forme in formato OSMC
    mappa_forme = {
        "triangolo": "triangle",
        "cerchio": "round",
        "rombo": "diamond",
        "quadrato": "square",
        "croce": "cross"
    }
    
    # 1. Cerca una corrispondenza diretta o parziale
    for feature in dati_json['features']:
        properties = feature.get('properties', {})
        osmc_symbol = str(properties.get('osmc:symbol', '')).lower()
        nome = str(properties.get('name', '')).lower()
        simbolo_it = str(properties.get('symbol:it', '')).lower()
        ref = str(properties.get('ref', '')).lower()
        
        # 2. Controllo flessibile: verifica se c'è una parola chiave simile all'interno della stringa
        match_trovato = False
        
        # Controllo con le parole chiave della forma
        for chiave, valore in mappa_forme.items():
            if chiave in simbolo_letto and (valore in osmc_symbol or valore in simbolo_it):
                match_trovato = True
                break
                
        # Controllo testuale di base (es. se l'utente scrive 'triangolo rosso')
        if (simbolo_letto in osmc_symbol or 
            simbolo_letto in nome or 
            simbolo_letto in ref or 
            simbolo_letto in simbolo_it or 
            match_trovato):
            
            return {
                "nome": properties.get('name', 'Sentiero senza nome'),
                "ref": properties.get('ref', 'N/D'),
                "simbolo": properties.get('osmc:symbol', 'N/D'),
                "simbolo_it": properties.get('symbol:it', 'N/D')
            }
            
    return None
