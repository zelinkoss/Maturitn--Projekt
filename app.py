import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'super-tajny-klic-pro-session'

# Konfigurace nahrávání
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- POMOCNÉ FUNKCE ---

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    # Důležité: Zapnutí podpory mazání v cascade (když smažeš auto, smažou se fotky)
    conn.execute("PRAGMA foreign_keys = ON") 
    return conn

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = get_db_connection()
    
    # 1. Tabulka uživatelů
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    # 2. Tabulka aut
    conn.execute('''
        CREATE TABLE IF NOT EXISTS auta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            znacka TEXT NOT NULL,
            model TEXT NOT NULL,
            kategorie TEXT NOT NULL,
            cena INTEGER NOT NULL,
            rok INTEGER,
            km INTEGER,
            vykon INTEGER,
            palivo TEXT,
            objem TEXT,
            spotreba TEXT,
            emise TEXT,
            prevodovka TEXT,
            barva TEXT,
            dvere INTEGER,
            mista INTEGER,
            airbagy INTEGER,
            vin TEXT,
            stk TEXT,
            zeme TEXT,
            majitel TEXT,
            serviska TEXT,
            vybava_text TEXT,
            popis TEXT,
            prodejce_jmeno TEXT,
            prodejce_tel TEXT,
            prodejce_email TEXT,
            obrazek TEXT,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 3. TABULKA PRO GALERII (Více fotek k jednomu autu)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS fotky (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auto_id INTEGER NOT NULL,
            soubor TEXT NOT NULL,
            FOREIGN KEY (auto_id) REFERENCES auta (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# --- HLAVNÍ STRÁNKY ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inzeraty')
def inzeraty():
    conn = get_db_connection()
    query = "SELECT * FROM auta WHERE 1=1"
    params = []

    # --- FILTROVÁNÍ ---
    if request.args.get('q'):
        query += " AND (znacka LIKE ? OR model LIKE ?)"
        term = f"%{request.args.get('q')}%"
        params.extend([term, term])
    
    if request.args.get('kategorie'):
        query += " AND kategorie = ?"
        params.append(request.args.get('kategorie'))

    if request.args.get('cena_od'):
        query += " AND cena >= ?"
        params.append(request.args.get('cena_od'))
    if request.args.get('cena_do'):
        query += " AND cena <= ?"
        params.append(request.args.get('cena_do'))
        
    if request.args.get('rok_od'):
        query += " AND rok >= ?"
        params.append(request.args.get('rok_od'))
    if request.args.get('rok_do'):
        query += " AND rok <= ?"
        params.append(request.args.get('rok_do'))
        
    if request.args.get('km_od'):
        query += " AND km >= ?"
        params.append(request.args.get('km_od'))
    if request.args.get('km_do'):
        query += " AND km <= ?"
        params.append(request.args.get('km_do'))

    if request.args.get('vykon_od'):
        query += " AND vykon >= ?"
        params.append(request.args.get('vykon_od'))
    if request.args.get('vykon_do'):
        query += " AND vykon <= ?"
        params.append(request.args.get('vykon_do'))
        
    if request.args.get('palivo'):
        query += " AND palivo = ?"
        params.append(request.args.get('palivo'))
        
    if request.args.get('prevodovka'):
        query += " AND prevodovka = ?"
        params.append(request.args.get('prevodovka'))

    auta = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('inzeraty.html', auta=auta)

@app.route('/detail/<int:id>')
def detail(id):
    conn = get_db_connection()
    auto = conn.execute('SELECT * FROM auta WHERE id = ?', (id,)).fetchone()
    
    # NAČTENÍ FOTEK DO GALERIE
    fotky = conn.execute('SELECT * FROM fotky WHERE auto_id = ?', (id,)).fetchall()
    
    conn.close()
    if auto is None:
        return "Inzerát nenalezen", 404
        
    return render_template('detail.html', auto=auto, fotky=fotky)

# --- AUTH TRASY ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        hashed_pw = generate_password_hash(password)
        
        # Admin logika: Jmenuje se "Admin"? Bude to admin.
        is_admin = 1 if username == "Admin" else 0

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)', 
                         (username, hashed_pw, email, is_admin))
            conn.commit()
            flash('Registrace úspěšná!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Jméno již existuje.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/loginadmin', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = (user['is_admin'] == 1)
            return redirect(url_for('inzeraty'))
        else:
            flash('Chyba přihlášení.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- PŘIDÁVÁNÍ A UKLÁDÁNÍ FOTEK (S GALERIÍ) ---

@app.route('/pridat', methods=['GET', 'POST'])
def pridat():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Načtení dat z formuláře
        form_data = request.form
        
        # Zpracování obrázků - TADY JE KLÍČOVÁ ČÁST PRO GALERII
        hlavni_obrazek = ''
        dalsi_fotky = []

        if 'obrazky' in request.files:
            files = request.files.getlist('obrazky')
            
            # Projdeme všechny nahrané soubory
            for i, file in enumerate(files):
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Uložíme soubor na disk
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    
                    if i == 0:
                        # První soubor je hlavní fotka (do tabulky auta)
                        hlavni_obrazek = filename
                    else:
                        # Ostatní si zapamatujeme do seznamu pro galerii (do tabulky fotky)
                        dalsi_fotky.append(filename)

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Vložíme auto (s hlavní fotkou)
        cursor.execute('''
            INSERT INTO auta (znacka, model, kategorie, cena, rok, km, vykon, palivo, objem, spotreba, emise, 
                              prevodovka, barva, dvere, mista, airbagy, vin, stk, zeme, majitel, serviska, 
                              vybava_text, popis, prodejce_jmeno, prodejce_tel, prodejce_email, obrazek, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            form_data['znacka'], form_data['model'], form_data['kategorie'], form_data['cena'],
            form_data['rok'], form_data['km'], form_data['vykon'], form_data.get('palivo'),
            form_data['objem'], form_data['spotreba'], form_data['emise'], form_data['prevodovka'],
            form_data['barva'], form_data['dvere'], form_data['mista'], form_data['airbagy'],
            form_data['vin'], form_data['stk'], form_data['zeme'], form_data['majitel'],
            form_data['serviska'], form_data['vybava_text'], form_data['popis'],
            form_data['prodejce_jmeno'], form_data['prodejce_tel'], form_data['prodejce_email'],
            hlavni_obrazek, session['user_id']
        ))
        
        # Získáme ID nově vytvořeného auta
        nove_auto_id = cursor.lastrowid
        
        # 2. Vložíme zbylé fotky do tabulky 'fotky'
        for foto in dalsi_fotky:
            cursor.execute('INSERT INTO fotky (auto_id, soubor) VALUES (?, ?)', (nove_auto_id, foto))

        conn.commit()
        conn.close()

        return redirect(url_for('inzeraty'))

    return render_template('pridat.html')

@app.route('/moje-inzeraty')
def moje_inzeraty():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    auta = conn.execute('SELECT * FROM auta WHERE user_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('moje_inzeraty.html', auta=auta)

@app.route('/smazat/<int:id>')
def smazat(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    auto = conn.execute('SELECT * FROM auta WHERE id = ?', (id,)).fetchone()
    
    if auto:
        if session.get('user_id') == auto['user_id'] or session.get('is_admin'):
            # Díky ON DELETE CASCADE v databázi se smažou i fotky z galerie automaticky
            conn.execute('DELETE FROM auta WHERE id = ?', (id,))
            conn.commit()
            flash('Smazáno.', 'success')
        else:
            flash('Nemáte oprávnění.', 'error')
    
    conn.close()
    return redirect(url_for('inzeraty') if session.get('is_admin') else url_for('moje_inzeraty'))

@app.route('/upravit/<int:id>', methods=['GET', 'POST'])
def upravit(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    auto = conn.execute('SELECT * FROM auta WHERE id = ?', (id,)).fetchone()
    
    if not auto or (auto['user_id'] != session['user_id'] and not session.get('is_admin')):
        conn.close()
        return "Nemáte oprávnění", 403

    if request.method == 'POST':
        # Update pouze textových polí
        conn.execute('''
            UPDATE auta SET znacka=?, model=?, cena=?, rok=?, km=?, vykon=?, popis=?
            WHERE id=?
        ''', (request.form['znacka'], request.form['model'], request.form['cena'], 
              request.form['rok'], request.form['km'], request.form['vykon'], 
              request.form['popis'], id))
        conn.commit()
        conn.close()
        return redirect(url_for('detail', id=id))

    conn.close()
    return render_template('upravit.html', auto=auto)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)