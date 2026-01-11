import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)

# --- KONFIGURACE ---
app.secret_key = 'tajne-heslo-maturita'
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
    
    # 1. Hlavní tabulka aut (VČETNĚ KONTAKTŮ NA PRODEJCE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS auta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            
            -- NOVÉ: Kontakt na prodejce
            prodejce_jmeno TEXT,
            prodejce_tel TEXT,
            prodejce_email TEXT,
            
            obrazek TEXT
        );
    ''')
    
    # 2. Tabulka pro galerii
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
    print("✅ Databáze připravena (Verze s kontakty).")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- TRASY ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == 'admin123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Špatné heslo!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/inzeraty')
def inzeraty():
    # Filtry (stejné jako minule)
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
        params.append(f'%{q}%')
        params.append(f'%{q}%')
    if cena_od and cena_od.isdigit():
        query += " AND cena >= ?"
        params.append(cena_od)
    if cena_do and cena_do.isdigit():
        query += " AND cena <= ?"
        params.append(cena_do)
    if rok_od and rok_od.isdigit():
        query += " AND rok >= ?"
        params.append(rok_od)
    if rok_do and rok_do.isdigit():
        query += " AND rok <= ?"
        params.append(rok_do)
    if km_od and km_od.isdigit():
        query += " AND km >= ?"
        params.append(km_od)
    if km_do and km_do.isdigit():
        query += " AND km <= ?"
        params.append(km_do)
    if vykon_od and vykon_od.isdigit():
        query += " AND vykon >= ?"
        params.append(vykon_od)
    if vykon_do and vykon_do.isdigit():
        query += " AND vykon <= ?"
        params.append(vykon_do)
    if palivo and palivo != "":
        query += " AND palivo = ?"
        params.append(palivo)
    if prevodovka and prevodovka != "":
        query += " AND prevodovka = ?"
        params.append(prevodovka)

    try:
        auta = conn.execute(query, params).fetchall()
    except sqlite3.OperationalError:
        init_db()
        auta = []
    
    conn.close()
    return render_template('inzeraty.html', auta=auta)

@app.route('/detail/<int:id>')
def detail(id):
    conn = get_db_connection()
    auto = conn.execute('SELECT * FROM auta WHERE id = ?', (id,)).fetchone()
    fotky = conn.execute('SELECT * FROM fotky WHERE auto_id = ?', (id,)).fetchall()
    conn.close()
    
    if auto is None:
        return "Auto nenalezeno", 404
    return render_template('detail.html', auto=auto, fotky=fotky)

@app.route('/pridat', methods=('GET', 'POST'))
def pridat():
    if request.method == 'POST':
        # Načtení polí
        znacka = request.form['znacka']
        model = request.form['model']
        kategorie = request.form['kategorie']
        cena = request.form['cena']
        rok = request.form['rok']
        palivo = request.form.get('palivo')
        prevodovka = request.form['prevodovka']
        km = request.form['km']
        vykon = request.form['vykon']
        spotreba = request.form['spotreba']
        objem = request.form['objem']
        barva = request.form['barva']
        stk = request.form['stk']
        vin = request.form['vin']
        zeme = request.form['zeme']
        majitel = request.form['majitel']
        serviska = request.form['serviska']
        airbagy = request.form['airbagy']
        dvere = request.form['dvere']
        mista = request.form['mista']
        emise = request.form['emise']
        vybava_text = request.form['vybava_text']
        popis = request.form['popis']
        
        # NOVÉ: Kontakty
        prodejce_jmeno = request.form['prodejce_jmeno']
        prodejce_tel = request.form['prodejce_tel']
        prodejce_email = request.form['prodejce_email']
        
        # Zpracování fotek
        files = request.files.getlist('obrazky')
        hlavni_obrazek = "placeholder.jpg"
        ulozene_fotky = []

        for i, file in enumerate(files):
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                ulozene_fotky.append(filename)
                if i == 0:
                    hlavni_obrazek = filename

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''INSERT INTO auta (
            znacka, model, kategorie, cena, rok, palivo, prevodovka, km, vykon, spotreba, 
            objem, barva, stk, vin, zeme, majitel, serviska, airbagy, dvere, mista, emise, vybava_text,
            popis, prodejce_jmeno, prodejce_tel, prodejce_email, obrazek
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (
            znacka, model, kategorie, cena, rok, palivo, prevodovka, km, vykon, spotreba,
            objem, barva, stk, vin, zeme, majitel, serviska, airbagy, dvere, mista, emise, vybava_text,
            popis, prodejce_jmeno, prodejce_tel, prodejce_email, hlavni_obrazek
        ))
        
        new_auto_id = cursor.lastrowid
        
        for foto in ulozene_fotky:
            cursor.execute('INSERT INTO fotky (auto_id, soubor) VALUES (?, ?)', (new_auto_id, foto))

        conn.commit()
        conn.close()
        return redirect(url_for('inzeraty'))

    return render_template('pridat.html')

@app.route('/smazat/<int:id>')
def smazat(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM auta WHERE id = ?', (id,))
    conn.execute('DELETE FROM fotky WHERE auto_id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('inzeraty'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)