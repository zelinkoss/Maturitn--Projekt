import os
import sqlite3
from datetime import timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- KONFIGURACE ---
app.secret_key = 'tajne-heslo-maturita'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30) # Trvalé přihlášení

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
DB_PATH = os.path.join(basedir, 'database.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- POMOCNÉ FUNKCE ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # 1. Uživatelé
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            email TEXT
        );
    ''')

    # 2. Auta (včetně kontaktů)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS auta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            znacka TEXT NOT NULL,
            model TEXT NOT NULL,
            kategorie TEXT NOT NULL, 
            cena INTEGER NOT NULL,
            rok INTEGER NOT NULL,
            palivo TEXT NOT NULL,
            prevodovka TEXT NOT NULL,
            km INTEGER NOT NULL,
            vykon INTEGER,
            spotreba TEXT,
            objem TEXT,
            barva TEXT,
            stk TEXT,
            vin TEXT,
            zeme TEXT,
            majitel TEXT,
            serviska TEXT,
            airbagy INTEGER,
            dvere INTEGER,
            mista INTEGER,
            emise TEXT,
            vybava_text TEXT,
            popis TEXT,
            prodejce_jmeno TEXT,
            prodejce_tel TEXT,
            prodejce_email TEXT,
            obrazek TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    ''')
    
    # 3. Fotky (Galerie)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS fotky (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auto_id INTEGER NOT NULL,
            soubor TEXT NOT NULL,
            FOREIGN KEY (auto_id) REFERENCES auta (id)
        );
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Databáze připravena (Full verze).")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- AUTH TRASY ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', 
                         (username, hashed_pw, email))
            conn.commit()
            flash('Registrace úspěšná! Nyní se přihlaste.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Uživatelské jméno již existuje.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session.permanent = True  # Zapamatovat přihlášení
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('inzeraty')) # Jít na výpis aut
        else:
            flash('Špatné jméno nebo heslo.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- APLIKAČNÍ TRASY ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inzeraty')
def inzeraty():
    # Načítání filtrů
    kategorie = request.args.get('kategorie')
    q = request.args.get('q')
    cena_od = request.args.get('cena_od')
    cena_do = request.args.get('cena_do')
    rok_od = request.args.get('rok_od')
    rok_do = request.args.get('rok_do')
    km_od = request.args.get('km_od')
    km_do = request.args.get('km_do')
    vykon_od = request.args.get('vykon_od')
    vykon_do = request.args.get('vykon_do')
    palivo = request.args.get('palivo')
    prevodovka = request.args.get('prevodovka')

    conn = get_db_connection()
    query = "SELECT * FROM auta WHERE 1=1"
    params = []

    if kategorie:
        query += " AND kategorie = ?"
        params.append(kategorie)
    if q:
        query += " AND (znacka LIKE ? OR model LIKE ?)"
        params.append(f'%{q}%'); params.append(f'%{q}%')
    if cena_od and cena_od.isdigit():
        query += " AND cena >= ?"; params.append(cena_od)
    if cena_do and cena_do.isdigit():
        query += " AND cena <= ?"; params.append(cena_do)
    if rok_od and rok_od.isdigit():
        query += " AND rok >= ?"; params.append(rok_od)
    if rok_do and rok_do.isdigit():
        query += " AND rok <= ?"; params.append(rok_do)
    if km_od and km_od.isdigit():
        query += " AND km >= ?"; params.append(km_od)
    if km_do and km_do.isdigit():
        query += " AND km <= ?"; params.append(km_do)
    if vykon_od and vykon_od.isdigit():
        query += " AND vykon >= ?"; params.append(vykon_od)
    if vykon_do and vykon_do.isdigit():
        query += " AND vykon <= ?"; params.append(vykon_do)
    if palivo and palivo != "":
        query += " AND palivo = ?"; params.append(palivo)
    if prevodovka and prevodovka != "":
        query += " AND prevodovka = ?"; params.append(prevodovka)

    try:
        auta = conn.execute(query, params).fetchall()
    except sqlite3.OperationalError:
        init_db(); auta = []
    
    conn.close()
    return render_template('inzeraty.html', auta=auta)

@app.route('/moje-inzeraty')
def moje_inzeraty():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    auta = conn.execute('SELECT * FROM auta WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('moje_inzeraty.html', auta=auta)

@app.route('/detail/<int:id>')
def detail(id):
    conn = get_db_connection()
    auto = conn.execute('SELECT * FROM auta WHERE id = ?', (id,)).fetchone()
    fotky = conn.execute('SELECT * FROM fotky WHERE auto_id = ?', (id,)).fetchall()
    conn.close()
    if auto is None: return "Auto nenalezeno", 404
    return render_template('detail.html', auto=auto, fotky=fotky)

@app.route('/pridat', methods=('GET', 'POST'))
def pridat():
    if 'user_id' not in session: return redirect(url_for('login'))

    if request.method == 'POST':
        f = request.form
        files = request.files.getlist('obrazky')
        hlavni = "placeholder.jpg"
        ulozene = []

        for i, file in enumerate(files):
            if file and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
                ulozene.append(fname)
                if i == 0: hlavni = fname

        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO auta (
            user_id, znacka, model, kategorie, cena, rok, palivo, prevodovka, km, vykon, spotreba, 
            objem, barva, stk, vin, zeme, majitel, serviska, airbagy, dvere, mista, emise, vybava_text,
            popis, prodejce_jmeno, prodejce_tel, prodejce_email, obrazek
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (
            session['user_id'], f['znacka'], f['model'], f['kategorie'], f['cena'], f['rok'], 
            f.get('palivo'), f['prevodovka'], f['km'], f['vykon'], f['spotreba'],
            f['objem'], f['barva'], f['stk'], f['vin'], f['zeme'], f['majitel'], f['serviska'], 
            f['airbagy'], f['dvere'], f['mista'], f['emise'], f['vybava_text'],
            f['popis'], f['prodejce_jmeno'], f['prodejce_tel'], f['prodejce_email'], hlavni
        ))
        
        nid = c.lastrowid
        for foto in ulozene:
            c.execute('INSERT INTO fotky (auto_id, soubor) VALUES (?, ?)', (nid, foto))

        conn.commit()
        conn.close()
        return redirect(url_for('moje_inzeraty'))

    return render_template('pridat.html')

@app.route('/upravit/<int:id>', methods=('GET', 'POST'))
def upravit(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    auto = conn.execute('SELECT * FROM auta WHERE id = ?', (id,)).fetchone()
    
    if auto['user_id'] != session['user_id']:
        conn.close()
        return "Nemáte oprávnění!", 403

    if request.method == 'POST':
        f = request.form
        conn.execute('''UPDATE auta SET 
            znacka=?, model=?, kategorie=?, cena=?, rok=?, palivo=?, prevodovka=?, km=?, 
            vykon=?, spotreba=?, objem=?, barva=?, stk=?, vin=?, zeme=?, majitel=?, 
            serviska=?, airbagy=?, dvere=?, mista=?, emise=?, vybava_text=?, popis=?, 
            prodejce_jmeno=?, prodejce_tel=?, prodejce_email=?
            WHERE id = ?''',
            (
             f['znacka'], f['model'], f['kategorie'], f['cena'], f['rok'], f.get('palivo'), 
             f['prevodovka'], f['km'], f['vykon'], f['spotreba'], f['objem'], f['barva'], 
             f['stk'], f['vin'], f['zeme'], f['majitel'], f['serviska'], f['airbagy'], 
             f['dvere'], f['mista'], f['emise'], f['vybava_text'], f['popis'], 
             f['prodejce_jmeno'], f['prodejce_tel'], f['prodejce_email'], id
            ))
        conn.commit()
        conn.close()
        return redirect(url_for('detail', id=id))

    conn.close()
    return render_template('upravit.html', auto=auto)

@app.route('/smazat/<int:id>')
def smazat(id):
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    auto = conn.execute('SELECT * FROM auta WHERE id = ?', (id,)).fetchone()
    
    if auto['user_id'] != session['user_id']:
        conn.close()
        return "Nemáte oprávnění!", 403

    conn.execute('DELETE FROM auta WHERE id = ?', (id,))
    conn.execute('DELETE FROM fotky WHERE auto_id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('moje_inzeraty'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)