# app.py

# ==============================================================================
# 1. importazione fondamentali 
# ==============================================================================
import re                                                                                   
from flask import (Flask, render_template, request, redirect, url_for, session, flash)                                                                                               
from pymongo import MongoClient, DESCENDING                                                     
from pymongo.errors import ConnectionFailure                                                    
from werkzeug.security import generate_password_hash, check_password_hash                                       
from functools import wraps                                                                                         
from datetime import datetime                                                               
from bson import ObjectId                                                                       


# ==============================================================================
# config dell'applicazione 
# ==============================================================================
app = Flask(__name__)
app.secret_key = 'test'

# Definiamo i ruoli
RUOLO_CLIENTE = 0
RUOLO_STAFF = 1
RUOLO_PROPRIETARIO = 2

# ==============================================================================
#  lista esercizi e funzioni per il calcolo 
# ==============================================================================

def get_elenco_esercizi():
    """
    Restituisce un elenco completo di esercizi da palestra con valori MET approssimativi.
    MET (Metabolic Equivalent of Task) è un'unità che stima il dispendio energetico.
    Valori di riferimento: 1 MET = riposo, 3-6 MET = moderato, >6 MET = intenso.
    """
    esercizi = {
        "Cardio": [
            {"nome": "Corsa (Tapis Roulant)", "met": 9.8},
            {"nome": "Ciclismo (Cyclette)", "met": 7.0},
            {"nome": "Ellittica", "met": 5.0},
            {"nome": "Vogatore", "met": 7.0},
            {"nome": "Stair Climber / Stepper", "met": 9.0},
            {"nome": "Salto con la corda", "met": 11.0},
            {"nome": "Camminata Veloce (Tapis Roulant)", "met": 4.3},
            {"nome": "Spinning (classe)", "met": 8.5},
            {"nome": "Rowing Machine", "met": 7.0},
            {"nome": "Assault Bike", "met": 12.0},
            {"nome": "Burpees", "met": 8.0},
            {"nome": "Jumping Jacks", "met": 7.0}
        ],
        "Petto": [
            {"nome": "Panca Piana (Bilanciere)", "met": 5.0},
            {"nome": "Panca Piana (Manubri)", "met": 5.0},
            {"nome": "Panca Inclinata (Bilanciere)", "met": 5.0},
            {"nome": "Panca Inclinata (Manubri)", "met": 5.0},
            {"nome": "Panca Declinata (Bilanciere)", "met": 5.0},
            {"nome": "Croci su Panca (Manubri)", "met": 4.0},
            {"nome": "Croci ai Cavi", "met": 4.0},
            {"nome": "Piegamenti sulle braccia (Push-up)", "met": 8.0},
            {"nome": "Dips alle parallele (focus petto)", "met": 8.0},
            {"nome": "Chest Press (Macchina)", "met": 4.0},
            {"nome": "Pec Deck / Butterfly Machine", "met": 3.0},
            {"nome": "Svend Press", "met": 3.0}
        ],
        "Dorso": [
            {"nome": "Trazioni alla sbarra (Pull-up/Chin-up)", "met": 8.0},
            {"nome": "Rematore con Bilanciere", "met": 6.0},
            {"nome": "Rematore con Manubrio", "met": 6.0},
            {"nome": "Lat Machine", "met": 4.0},
            {"nome": "Pulley Basso", "met": 4.0},
            {"nome": "Stacchi da terra (Deadlift)", "met": 8.0},
            {"nome": "Hyperextension", "met": 4.0},
            {"nome": "T-Bar Row", "met": 6.0},
            {"nome": "Face Pull", "met": 3.0},
            {"nome": "Good Morning", "met": 5.0},
            {"nome": "Kettlebell Swing", "met": 9.5}
        ],
        "Gambe e Glutei": [
            {"nome": "Squat con Bilanciere", "met": 7.0},
            {"nome": "Affondi (Lunges)", "met": 5.0},
            {"nome": "Leg Press", "met": 5.0},
            {"nome": "Leg Extension", "met": 3.0},
            {"nome": "Leg Curl", "met": 3.0},
            {"nome": "Stacchi Rumeni", "met": 6.0},
            {"nome": "Hip Thrust", "met": 5.0},
            {"nome": "Calf Raise", "met": 3.0},
            {"nome": "Goblet Squat", "met": 6.0},
            {"nome": "Box Jump", "met": 8.0},
            {"nome": "Ponte Glutei", "met": 4.0},
            {"nome": "Step-up", "met": 7.0}
        ],
        "Spalle": [
            {"nome": "Military Press (in piedi)", "met": 6.0},
            {"nome": "Shoulder Press (Manubri)", "met": 5.0},
            {"nome": "Alzate Laterali (Manubri)", "met": 4.0},
            {"nome": "Alzate Frontali", "met": 4.0},
            {"nome": "Tirate al mento (Upright Row)", "met": 5.0},
            {"nome": "Arnold Press", "met": 5.0},
            {"nome": "Alzate a 90° (Bent-over raise)", "met": 4.0},
            {"nome": "Shoulder Press (Macchina)", "met": 4.0}
        ],
        "Braccia (Bicipiti e Tricipiti)": [
            {"nome": "Curl con Bilanciere", "met": 4.0},
            {"nome": "Curl con Manubri", "met": 4.0},
            {"nome": "Hammer Curl", "met": 4.0},
            {"nome": "Panca Scott (Preacher Curl)", "met": 3.0},
            {"nome": "French Press / Skull Crusher", "met": 4.0},
            {"nome": "Spinte in basso ai cavi (Push-down)", "met": 3.0},
            {"nome": "Dips su panca", "met": 7.0},
            {"nome": "Curl di concentrazione", "met": 3.0}
        ],
        "Addominali e Core": [
            {"nome": "Crunch", "met": 3.0},
            {"nome": "Plank", "met": 3.0},
            {"nome": "Leg Raise (sollevamento gambe)", "met": 4.0},
            {"nome": "Russian Twist", "met": 4.0},
            {"nome": "Ab Roller", "met": 5.0},
            {"nome": "Sit-up", "met": 4.0},
            {"nome": "Hanging Leg Raise", "met": 6.0},
            {"nome": "Side Plank", "met": 3.0}
        ]
    }
    
    flat_list = []
    for category in esercizi.values():
        flat_list.extend(category)
    return esercizi, flat_list

ESERCIZI_CATEGORIZZATI, ESERCIZI_FLAT_LIST = get_elenco_esercizi()

def get_met_by_name(nome_esercizio):
    """Cerca il valore MET di un esercizio dal suo nome."""
    for ex in ESERCIZI_FLAT_LIST:
        if ex['nome'] == nome_esercizio:
            return ex['met']
    return 3.0  # Valore di default 

def stima_calorie(nome_esercizio, peso_kg, serie_target_str=None, tempo_min=None):
    try:
        peso_kg = float(peso_kg)
    except (ValueError, TypeError):
        peso_kg = 75.0

    """
    Stima le calorie bruciate per un esercizio.
    Formula: (MET * peso_corporeo_kg * 3.5) / 200 * minuti
    """
    met = get_met_by_name(nome_esercizio)
    durata_min_stimata = 0

    if tempo_min and tempo_min > 0:
        # Se è un esercizio cardio con durata specificata
        durata_min_stimata = tempo_min
    elif serie_target_str:
        # Altrimenti, per esercizi di forza, stimiamo la durata dalle serie
        # Es: "3x10", "4x8-12", "5x5". Estraiamo il primo numero.
        match = re.match(r'(\d+)', serie_target_str)  #pattern :'(\d+)' per cercare uno o piu cifre da 0 a 9 
        if match:
            num_serie = int(match.group(1))
            # Assumiamo circa 1.5 minuti per serie (inclusa pausa)
            durata_min_stimata = num_serie * 1.5

    if durata_min_stimata > 0:
        calorie = (met * peso_kg * 3.5) / 200 * durata_min_stimata
        return round(calorie), round(durata_min_stimata)
    
    return 0, 0


# ==============================================================================
# 3. decorators
# ==============================================================================
def staff_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('ruolo') != RUOLO_STAFF and session.get('ruolo') != RUOLO_PROPRIETARIO:
            flash('Accesso negato. Funzione riservata allo staff.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def proprietario_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('ruolo') != RUOLO_PROPRIETARIO:
            flash('Accesso negato. Funzione riservata al proprietario.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash('Per accedere a questa pagina devi prima effettuare il login.', 'warning')
            return redirect(url_for('login', next=request.url))
        if not is_db_connected():
            flash('Errore del server: il database non è attualmente disponibile. Riprova più tardi.', 'danger')
            return redirect(url_for('index_page'))
        return f(*args, **kwargs)
    return decorated_function


# ==============================================================================
# connessione al mongdb 
# ==============================================================================
MONGODB_URI = "mongodb+srv://TechGym:aNv8T4qf3zSdTkBr@gym.06rhp1p.mongodb.net/?retryWrites=true&w=majority&appName=Gym"
try:
    client = MongoClient(MONGODB_URI)
    client.admin.command('ping')
    print("MongoDB Atlas connesso con successo!")
    db = client['gym']
    utenti_collection = db['utenti_collection']
    dati_profile_collection = db['dati_profile_collection']
    schede_collection = db['schede_utente']
    turni_collection = db['turni_staff']
    risultati_allenamenti_collection = db['risultati_allenamenti']
except ConnectionFailure as e:
    print(f"Errore di connessione a MongoDB Atlas (ConnectionFailure): {e}")
    client = db = utenti_collection = dati_profile_collection = schede_collection = turni_collection = risultati_allenamenti_collection = None
except Exception as e:
    print(f"Errore generico durante la connessione o inizializzazione di MongoDB Atlas: {e}")
    client = db = utenti_collection = dati_profile_collection = schede_collection = turni_collection = risultati_allenamenti_collection = None


# ==============================================================================
# 5. funzioni utili
# ==============================================================================
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.context_processor
def inject_css_path():
    return dict(css_file=url_for('static', filename='css/styles.css'))

def is_db_connected():
    return all(coll is not None for coll in [utenti_collection, dati_profile_collection, schede_collection, turni_collection, risultati_allenamenti_collection])

@app.template_filter('month_name')
def month_name(month_num):
    months = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    return months[month_num - 1]


# ==============================================================================
# routes
# ==============================================================================

# --- Route Principali e Autenticazione 
@app.route('/')
@app.route('/index')
def index_page():
    if 'email' in session:
        return redirect(url_for('home'))
    return render_template('index.html', db_connected=is_db_connected())

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not is_db_connected():
        flash('Servizio momentaneamente non disponibile, riprova più tardi.', 'danger')
        return redirect(url_for('index_page'))
    
    if 'email' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        nome = request.form.get('nome', '').strip()
        cognome = request.form.get('cognome', '').strip()

        if not email or not password:
            flash('Email e password sono obbligatori.', 'warning')
            return render_template('signup.html', email=email, nome=nome, cognome=cognome)
        if len(password) < 8:
            flash('La password deve contenere almeno 8 caratteri.', 'warning')
            return render_template('signup.html', email=email, nome=nome, cognome=cognome)
        if utenti_collection.find_one({'email': email}):
            flash('Utente già registrato con questa email!', 'warning')
            return render_template('signup.html', email=email, nome=nome, cognome=cognome)

        hashed_password = generate_password_hash(password)
        nuovo_utente = {
            'email': email, 'password': hashed_password, 'nome': nome, 'cognome': cognome,
            'data_registrazione': datetime.utcnow(), 'ruolo': RUOLO_CLIENTE
        }
        try:
            utenti_collection.insert_one(nuovo_utente)
            flash('Registrazione avvenuta con successo! Ora effettua il login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f"Errore durante l'inserimento dell'utente: {e}")
            flash('Errore durante la registrazione. Riprova.', 'danger')
            return render_template('signup.html', email=email, nome=nome, cognome=cognome)

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if not is_db_connected():
        flash('Servizio momentaneamente non disponibile, riprova più tardi.', 'danger')
        return redirect(url_for('index_page'))
    
    if 'email' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Inserisci email e password.', 'warning')
            return render_template('login.html', email=email)

        user = utenti_collection.find_one({'email': email})

        if user and check_password_hash(user.get('password', ''), password):
            session['email'] = user['email']
            session['user_id'] = str(user['_id'])
            session['nome'] = user.get('nome', user['email'].split('@')[0])
            session['ruolo'] = user.get('ruolo')
            flash('Login effettuato con successo!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('home'))
        else:
            flash('Email o password errati. Riprova.', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('Logout effettuato con successo!', 'info')
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    utente_ruolo = session.get('ruolo')
    nome_utente = session.get('nome', 'Utente')
    if utente_ruolo == RUOLO_STAFF:
        return render_template('home_staff.html', nome_utente=nome_utente)
    return render_template('home.html', nome_utente=nome_utente)

@app.route('/profilo', methods=['GET', 'POST'])
@login_required
def profilo():
    user_id_str = session.get('user_id')
    email = session.get('email')
    try:
        user_obj_id = ObjectId(user_id_str)
    except Exception:
        flash('ID utente non valido in sessione.', 'danger')
        session.clear()
        return redirect(url_for('login'))

    utente_db = utenti_collection.find_one({'_id': user_obj_id})
    if not utente_db:
        flash('Utente non trovato.', 'danger')
        session.clear()
        return redirect(url_for('login'))

    if request.method == 'POST':
        
        nome = request.form.get('nome')
        cognome = request.form.get('cognome')
        peso = request.form.get('peso')
        altezza = request.form.get('altezza')
        obiettivo = request.form.get('obiettivo')

        update_fields_utente = {}
        if nome is not None: update_fields_utente['nome'] = nome.strip()
        if cognome is not None: update_fields_utente['cognome'] = cognome.strip()
        if update_fields_utente:
            utenti_collection.update_one({'_id': utente_db['_id']}, {'$set': update_fields_utente})
            if 'nome' in update_fields_utente:
                session['nome'] = update_fields_utente['nome']

        update_fields_profilo = {'email': email, 'ultima_modifica': datetime.utcnow()}
        if peso: update_fields_profilo['peso'] = float(peso.replace(',', '.'))
        if altezza: update_fields_profilo['altezza'] = altezza
        if obiettivo: update_fields_profilo['obiettivo'] = obiettivo
        
        dati_profile_collection.update_one(
            {'user_id': user_id_str},
            {'$set': update_fields_profilo, '$setOnInsert': {'user_id': user_id_str}},
            upsert=True
        )
        flash('Profilo aggiornato con successo!', 'success')
        return redirect(url_for('profilo'))

    dati_profilo_db = dati_profile_collection.find_one({'user_id': user_id_str}) or {}
    utente_per_template = {**dati_profilo_db, **utente_db}
    # Formattazione per visualizzazione
    utente_per_template['peso'] = str(dati_profilo_db.get('peso', '')).replace('.', ',')
    utente_per_template['altezza'] = dati_profilo_db.get('altezza', '')
    utente_per_template['obiettivo'] = dati_profilo_db.get('obiettivo', '')
    utente_per_template['nome'] = utente_db.get('nome', '')
    utente_per_template['cognome'] = utente_db.get('cognome', '')

    return render_template('profilo.html', utente=utente_per_template)


# --- Route per visualizzare le schede di allenamento dell'utente ---
@app.route('/schede')
@login_required
def schede():
    email = session.get('email')
    user_schede = list(schede_collection.find({'email': email}).sort('data_creazione', DESCENDING))
    return render_template('schede.html', title="Le Tue Schede", schede=user_schede)


# --- Route per creare una scheda di allenamento per un cliente (SOLO STAFF) ---
@app.route('/staff/crea_scheda', methods=['GET', 'POST'])
@staff_required
def crea_scheda():
    clienti_list = list(utenti_collection.find().sort('cognome', 1))

    if request.method == 'POST':
        try:
            #  Recupera dati generali scheda
            email_cliente = request.form.get('email_cliente')
            titolo_scheda = request.form.get('titolo_scheda')
            note_generali = request.form.get('note_generali')

            if not email_cliente or not titolo_scheda:
                flash('Email cliente e titolo scheda sono obbligatori.', 'warning')
                return redirect(url_for('crea_scheda'))

            #  Recupera il peso del cliente per il calcolo calorie
            dati_cliente = dati_profile_collection.find_one({'email': email_cliente})
            peso_cliente = dati_cliente.get('peso', 75.0) # Default a 75kg se non specificato

            esercizi_scheda = []
            calorie_totali_stimate = 0
            durata_totale_stimata = 0
            
            #  Cicla attraverso gli esercizi inviati dal form
            i = 0
            while f'esercizi[{i}][nome]' in request.form:
                nome_ex = request.form.get(f'esercizi[{i}][nome]')
                dettagli_ex = request.form.get(f'esercizi[{i}][dettagli]')
                tempo_cardio_min = request.form.get(f'esercizi[{i}][tempo]', type=int)
                note_ex = request.form.get(f'esercizi[{i}][note]')

                if not nome_ex:
                    i += 1
                    continue
                
                #  Calcola calorie e durata stimate per l'esercizio
                calorie_stimate, durata_stimata = stima_calorie(
                    nome_ex, peso_cliente, dettagli_ex, tempo_cardio_min
                )
                
                calorie_totali_stimate += calorie_stimate
                durata_totale_stimata += durata_stimata

                esercizio_obj = {
                    "nome_esercizio": nome_ex,
                    "descrizione_serie_target": dettagli_ex,
                    "tempo_min_cardio_target": tempo_cardio_min,
                    "note_esercizio": note_ex,
                    "calorie_stimate_esercizio": calorie_stimate,
                    "tempo_stimato_esercizio_min": durata_stimata
                }
                esercizi_scheda.append(esercizio_obj)
                i += 1

            if not esercizi_scheda:
                flash("Aggiungi almeno un esercizio alla scheda.", "warning")
                return redirect(url_for('crea_scheda'))

            #  Costruisce e salva l'oggetto scheda nel DB
            nuova_scheda = {
                'email': email_cliente,
                'titolo': titolo_scheda,
                'tipo_scheda': 'dettagliata',
                'esercizi': esercizi_scheda,
                'note_generali_scheda': note_generali,
                'calorie_totali_stimate_scheda': round(calorie_totali_stimate),
                'durata_totale_stimata_min': round(durata_totale_stimata),
                'data_creazione': datetime.utcnow(),
                'creata_da_staff_email': session['email']
            }
            schede_collection.insert_one(nuova_scheda)
            flash('Scheda creata con successo!', 'success')
            return redirect(url_for('crea_scheda'))

        except Exception as e:
            app.logger.error(f"Errore durante la creazione della scheda: {e}", exc_info=True)
            flash(f"Si è verificato un errore: {e}", "danger")

    return render_template('crea_scheda.html', 
                           clienti=clienti_list, 
                           esercizi_gym=ESERCIZI_CATEGORIZZATI,
                           form_data={})


# --- Route per l'inserimento di un allenamento  ---

@app.route('/inserisci_allenamento', methods=['GET', 'POST'])
@login_required
def inserisci_allenamento():
    data_allenamento_default_str = datetime.now().strftime("%Y-%m-%dT%H:%M")

    if request.method == 'POST':
        try:
            user_id_str = session.get('user_id')
            user_email = session.get('email')

            try:
                user_obj_id = ObjectId(user_id_str)
            except Exception:
                flash('ID utente non valido in sessione. Effettua di nuovo il login.', 'danger')
                session.clear()
                return redirect(url_for('login'))

            dati_utente = dati_profile_collection.find_one({'user_id': user_id_str}) or {}
            try:
                peso_utente = float(dati_utente.get('peso', 75.0))
            except (ValueError, TypeError):
                peso_utente = 75.0

            data_allenamento_str = request.form.get('data_allenamento')
            nome_allenamento = request.form.get('nome_allenamento')
            note_generali = request.form.get('note_generali_sessione')

            try:
                data_allenamento_dt = datetime.strptime(data_allenamento_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash('Formato data non valido.', 'danger')
                return render_template('inserisci_allenamento.html',
                                       form_data=request.form,
                                       data_allenamento_default=data_allenamento_default_str,
                                       esercizi_gym=ESERCIZI_CATEGORIZZATI)

            esercizi_completati = []
            calorie_totali_stimate = 0
            durata_totale_minuti = 0
            i = 0

            while f'esercizi[{i}][nome_esercizio]' in request.form:
                nome_ex = request.form.get(f'esercizi[{i}][nome_esercizio]')
                if not nome_ex:
                    i += 1
                    continue

                serie_rip = request.form.getlist(f'esercizi[{i}][serie_ripetizioni][]')
                serie_peso = request.form.getlist(f'esercizi[{i}][serie_peso_kg][]')
                serie_note = request.form.getlist(f'esercizi[{i}][serie_note][]')
                tempo_cardio = request.form.get(f'esercizi[{i}][tempo_min_cardio]', type=float)
                distanza_cardio = request.form.get(f'esercizi[{i}][distanza_km]', type=float)

                esercizio_obj = {"nome_esercizio": nome_ex}
                durata_esercizio_min = 0
                calorie_stimate_ex = 0

                is_strength_exercise = any(rip.strip() for rip in serie_rip)
                is_cardio_exercise = tempo_cardio is not None and tempo_cardio > 0

                if is_strength_exercise:
                    esercizio_obj['serie'] = []
                    num_serie_valide = 0
                    for k, rip in enumerate(serie_rip):
                        if rip:
                            num_serie_valide += 1
                            try:
                                peso = float(serie_peso[k]) if serie_peso[k] else 0
                            except ValueError:
                                peso = 0
                            esercizio_obj['serie'].append({
                                'n_serie': k + 1,
                                'ripetizioni': rip,
                                'peso_kg': peso,
                                'note': serie_note[k].strip() if serie_note[k] else ''
                            })
                    if num_serie_valide > 0:
                        durata_esercizio_min = num_serie_valide * 1.5
                        calorie_stimate_ex, _ = stima_calorie(nome_ex, peso_utente, serie_target_str=f"{num_serie_valide}x")
                    else:
                        is_strength_exercise = False

                if is_cardio_exercise:
                    durata_esercizio_min = tempo_cardio
                    esercizio_obj['tempo_min'] = tempo_cardio
                    if distanza_cardio is not None:
                        esercizio_obj['distanza_km'] = distanza_cardio
                    calorie_stimate_ex, _ = stima_calorie(nome_ex, peso_utente, tempo_min=tempo_cardio)

                if not is_strength_exercise and not is_cardio_exercise:
                    i += 1
                    continue

                esercizio_obj['calorie_stimate_esercizio'] = calorie_stimate_ex
                esercizio_obj['tempo_dedicato_esercizio_min'] = durata_esercizio_min
                calorie_totali_stimate += calorie_stimate_ex
                durata_totale_minuti += durata_esercizio_min

                esercizi_completati.append(esercizio_obj)
                i += 1

            if not esercizi_completati:
                flash("Nessun esercizio valido inserito.", "warning")
                return render_template('inserisci_allenamento.html',
                                       form_data=request.form,
                                       data_allenamento_default=data_allenamento_default_str,
                                       esercizi_gym=ESERCIZI_CATEGORIZZATI)

            nuovo_allenamento = {
                'user_id': user_obj_id,
                'email': user_email,
                'data_allenamento': data_allenamento_dt,
                'nome_allenamento': nome_allenamento.strip() if nome_allenamento else None,
                'esercizi_completati': esercizi_completati,
                'note_generali_sessione': note_generali.strip() if note_generali else None,
                'calorie_totali_stimate_sessione': round(calorie_totali_stimate),
                'durata_totale_allenamento_min': round(durata_totale_minuti),
                'data_inserimento': datetime.utcnow()
            }

            risultati_allenamenti_collection.insert_one(nuovo_allenamento)
            flash('Allenamento registrato con successo!', 'success')
            return redirect(url_for('visualizza_risultati'))

        except Exception as e:
            app.logger.error(f"Errore durante l'inserimento dell'allenamento: {e}", exc_info=True)
            flash(f'Si è verificato un errore imprevisto durante il salvataggio: {str(e)}. Controlla i dati inseriti.', 'danger')
            return render_template('inserisci_allenamento.html',
                                   form_data=request.form,
                                   data_allenamento_default=data_allenamento_default_str,
                                   esercizi_gym=ESERCIZI_CATEGORIZZATI)

    return render_template('inserisci_allenamento.html',
                           data_allenamento_default=data_allenamento_default_str,
                           esercizi_gym=ESERCIZI_CATEGORIZZATI,
                           form_data={})


@app.route('/risultati')
@login_required
def visualizza_risultati():
    user_id_str = session.get('user_id')
    if not user_id_str:
        flash('ID utente non disponibile. Si prega di effettuare nuovamente il login.', 'danger')
        session.clear()
        return redirect(url_for('login'))
    
    try:
        user_obj_id = ObjectId(user_id_str)
    except Exception:
        flash('ID utente non valido. Si prega di effettuare nuovamente il login.', 'danger')
        session.clear()
        return redirect(url_for('login'))

    
    allenamenti_utente = list(risultati_allenamenti_collection.find(
        {"user_id": user_obj_id} 
    ).sort("data_allenamento", DESCENDING))
    
    return render_template('risultati.html',
                           allenamenti_utente=allenamenti_utente,
                           title="I Tuoi Risultati")

@app.route('/staff/clienti')
@staff_required
def staff_clienti():
    clienti = list(utenti_collection.find({'ruolo': RUOLO_CLIENTE}).sort('cognome', 1))
    return render_template('staff_clienti.html', clienti=clienti)

@app.route('/staff/schede')
@staff_required
def staff_schede():
    schede_tutte = list(schede_collection.find().sort('data_creazione', DESCENDING))
    return render_template('crea_schede.html', schede=schede_tutte)



@app.route('/promuovi_a_staff', methods=['GET', 'POST'])
@proprietario_required
def promuovi_a_staff():
    if request.method == 'GET':
        clienti = list(utenti_collection.find({'ruolo': RUOLO_CLIENTE}).sort('cognome', 1))
        staff_members = list(utenti_collection.find({'ruolo': RUOLO_STAFF}).sort('cognome', 1))
        return render_template('promuovi_a_staff.html', title='Gestione Ruoli', clienti=clienti, staff_members=staff_members)
    
    if request.method == 'POST':
        email = request.form.get('email')
        action = request.form.get('action')
        
        if not email or action not in ['promote', 'demote']:
            flash('Selezione non valida.', 'warning')
            return redirect(url_for('promuovi_a_staff'))
        
        utente = utenti_collection.find_one({'email': email})
        if not utente:
            flash('Utente non trovato.', 'danger')
            return redirect(url_for('promuovi_a_staff'))
        
        try:
            if action == 'promote':
                if utente['ruolo'] != RUOLO_CLIENTE:
                    flash('Solo i clienti possono essere promossi a Staff.', 'warning')
                else:
                    utenti_collection.update_one({'email': email}, {'$set': {'ruolo': RUOLO_STAFF}})
                    flash(f'{utente.get("cognome", "")} {utente.get("nome", "")} promosso a Staff!', 'success')
            
            elif action == 'demote':
                if utente['ruolo'] != RUOLO_STAFF:
                    flash('Solo i membri Staff possono essere retrocessi a Clienti.', 'warning')
                else:
                    utenti_collection.update_one({'email': email}, {'$set': {'ruolo': RUOLO_CLIENTE}})
                    flash(f'{utente.get("cognome", "")} {utente.get("nome", "")} retrocesso a Cliente.', 'success')
        except Exception as e:
            app.logger.error(f"Errore aggiornamento ruolo: {e}")
            flash('Errore durante l\'operazione.', 'danger')
        
        return redirect(url_for('promuovi_a_staff'))


@app.route('/gestione_turni_staff', methods=['GET', 'POST'])
@proprietario_required # Solo il proprietario può creare turni.
def gestione_turni_staff():
    # Se il proprietario crea un nuovo turno
    if request.method == 'POST':
        try:
            # Raccogliamo i dati dal form.
            email_staff = request.form.get('email_staff')
            data_turno = request.form.get('data_turno')
            ora_inizio = request.form.get('ora_inizio')
            ora_fine = request.form.get('ora_fine')

            # Controlliamo che tutti i campi siano stati compilati.
            if not all([email_staff, data_turno, ora_inizio, ora_fine]):
                flash('Compila tutti i campi obbligatori.', 'warning')
                return redirect(url_for('gestione_turni_staff'))

            # Verifichiamo che l'utente selezionato esista e sia davvero dello staff.
            staff = utenti_collection.find_one({'email': email_staff, 'ruolo': RUOLO_STAFF})
            if not staff:
                flash('Membro staff non trovato.', 'danger')
                return redirect(url_for('gestione_turni_staff'))

            # Creiamo il documento per il nuovo turno.
            nuovo_turno = {
                'email_staff': email_staff,
                'nome_staff': staff['nome'],
                'cognome_staff': staff['cognome'],
                'data': datetime.strptime(data_turno, '%Y-%m-%d'), # Convertiamo la stringa in un oggetto data.
                'ora_inizio': ora_inizio,
                'ora_fine': ora_fine,
                'creato_da': session['email'], # Tracciamo chi ha creato il turno.
                'data_creazione': datetime.utcnow()
            }

            # Inseriamo il turno nel database.
            turni_collection.insert_one(nuovo_turno)
            flash('Turno creato con successo!', 'success')
            return redirect(url_for('gestione_turni_staff'))

        except Exception as e:
            app.logger.error(f"Errore creazione turno: {e}")
            flash('Errore durante la creazione del turno.', 'danger')

    # Se la richiesta è GET (o dopo un POST andato a buon fine):
    # 1. Carichiamo la lista dei membri dello staff da mostrare nel menu a tendina.
    staff_list = list(utenti_collection.find({'ruolo': RUOLO_STAFF}).sort('cognome', 1))
    # 2. Carichiamo la lista di tutti i turni già creati per visualizzarli.
    turni = list(turni_collection.find().sort('data', 1))
    # 3. Mostriamo la pagina.
    return render_template('gestione_turni_staff.html', 
                         title='Gestione Turni Staff',
                         staff_list=staff_list,
                         turni=turni)

# --- Route per una pagina statica di contatti ---
@app.route('/contatti')
def contatti():
    return render_template('contatti.html')

# --- Route per visualizzare i turni (vista dallo staff)---
@app.route('/staff/turni')
@staff_required # Solo lo staff.
def staff_turni():
    # Trova tutti i turni nel database e li ordina per data.
    turni = list(turni_collection.find().sort('data', 1))
    # Mostra la pagina con la lista dei turni.
    return render_template('staff_turni.html', turni=turni)

# ==============================================================================
#   gestione errori http
# ==============================================================================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errore_db.html', error=e), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Internal server error: {e}", exc_info=True)
    return render_template('500.html', error="Si è verificato un errore interno al server."), 500

@app.errorhandler(ConnectionFailure)
def handle_db_connection_error(e):
    app.logger.error(f"Errore di connessione al Database: {e}", exc_info=True)
    flash("Impossibile connettersi al database. Riprova più tardi.", "critical")
    return render_template('errore_db.html', error_message=str(e)), 503


# ==============================================================================
#  esecuzione dell'app
# ==============================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
