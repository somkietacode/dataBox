from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_from_directory, send_file, abort, session
from campagne.gestion import CampagneManager
import os
import json
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import shutil

app = Flask(__name__)
app.secret_key = 'votre_clé_secrète'
campagne_manager = CampagneManager()

CONFIG_PATH = 'config.json'

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return None

def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f)

@app.before_request
def before_request():
    # Vérifie si le fichier config.json existe, sinon redirige vers la page de configuration
    config = load_config()
    if not config and request.endpoint != 'configure' and request.endpoint != 'login':
        return redirect(url_for('configure'))
    
    if config and request.endpoint == 'configure' and 'user' not in session :
        return redirect(url_for('login'))
    if config and request.endpoint == 'configure' and 'user' in session :
        return render_template('configure.html')
    # Redirige vers la page de login si l'utilisateur n'est pas authentifié
    if 'user' not in session and request.endpoint not in ['login', 'configure', 'collect_data']:
        return redirect(url_for('login'))

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    if os.path.exists(CONFIG_PATH):
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form['password']
        if password:
            hashed_password = generate_password_hash(password)
            save_config({'password': hashed_password})
            return redirect(url_for('login'))
    
    return render_template('configure.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    config = load_config()
    
    if not config:
        return redirect(url_for('configure'))
    
    if request.method == 'POST':
        password = request.form['password']
        if check_password_hash(config['password'], password):
            session['user'] = True
            return redirect(url_for('index'))
        else:
            flash('Mot de passe incorrect.')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/')
def index():
    campagnes = os.listdir(campagne_manager.base_dir)
    return render_template('index.html', campagnes=campagnes)

@app.route('/load_home')
def load_home():
    campagnes = os.listdir(campagne_manager.base_dir)
    return render_template('home_content.html', campagnes=campagnes)

@app.route('/create_campaign', methods=['POST'])
def create_campaign():
    nom_campagne = request.form['nom_campagne']
    nom_campagne = nom_campagne.replace(' ','_')
    success, message = campagne_manager.creer_campagne(nom_campagne)
    
    if success:
        return redirect(url_for('add_campaign_field', nom_campagne=nom_campagne))
    else:
        flash(message)
        return redirect(url_for('create_campaign_form'))

@app.route('/create_campaign_form')
def create_campaign_form():
    return render_template('create_campaign.html')

@app.route('/add_campaign_field', methods=['GET','POST'])
def add_campaign_field():
    if request.method == 'POST':
        nom_campagne = request.form.get('nom_campagne')
        nom_champ = request.form.get('nom_champ')
        type_champ = request.form.get('type_champ')
        if type_champ == "choix_multiple" :
            options = request.form.get('options')
            resultat = campagne_manager.ajouter_champ(nom_campagne, nom_champ, type_champ, choicesValues = options)
        else :
            resultat = campagne_manager.ajouter_champ(nom_campagne, nom_champ, type_champ)
            
        if not nom_campagne or not nom_champ or not type_champ:
            return jsonify({"error": "Les paramètres nom_campagne, nom_champ et type_champ sont requis."}), 400
    else:
        nom_campagne = request.args.get('nom_campagne')
        print(nom_campagne)
    
    return render_template('add_campaign_field.html', nom_campagne=nom_campagne)

@app.route('/load_create_campaign')
def load_create_campaign():
    return render_template('create_campaign.html')



@app.route('/collect_data/<nom_campagne>', methods=['GET', 'POST'])
def collect_data(nom_campagne):
    # Récupérer la campagne
    campagne = campagne_manager.get_campaign(nom_campagne)
    
    if not campagne:
        return f"Campagne {nom_campagne} non trouvée."

    # Chemin vers le fichier access_policy.json
    access_policy_path = os.path.join('data', nom_campagne, 'access_policy.json')

    # Vérifier si un mot de passe est requis
    if os.path.exists(access_policy_path):
        with open(access_policy_path, 'r') as f:
            access_policy = json.load(f)
        mot_de_passe_requis = access_policy.get('password')

        # Initialiser le dictionnaire de session pour les campagnes si non défini
        if 'access_granted' not in session:
            session['access_granted'] = {}

        # Vérification du mot de passe pour cette campagne spécifique
        if session['access_granted'].get(nom_campagne) != True:
            if request.method == 'POST':
                input_password = request.form.get('password')
                if input_password == mot_de_passe_requis:
                    session['access_granted'][nom_campagne] = True
                else:
                    flash('Mot de passe incorrect.')
                    return redirect(url_for('collect_data', nom_campagne=nom_campagne))
            else:
                return render_template('password_prompt.html', nom_campagne=nom_campagne)
    
    # Si l'accès est accordé ou non protégé
    if request.method == 'POST':
        data = {}
        fichiers = {}
        for champ, type_champ in campagne['champs']['Field'].items():
            if type_champ in ['audio', 'image', 'video', 'fichier']:
                fichiers[champ] = request.files.get(champ)
            else:
                data[champ] = request.form.get(champ)
        
        campagne_manager.sauvegarder_donnees(nom_campagne, data, fichiers)
        
        flash("Données collectées avec succès.")
        return redirect(url_for('collect_data', nom_campagne=nom_campagne))

    return render_template('collect_data.html', campagne=campagne, nom_campagne=nom_campagne)


@app.route('/view_campaign/<nom_campagne>')
def view_campaign(nom_campagne):
    campagne = campagne_manager.get_campaign(nom_campagne)
    if campagne:
        return render_template('view_campaign.html', campagne=campagne)
    else:
        flash("La campagne n'existe pas.")
        return redirect(url_for('index'))



@app.route('/delete_campaign', methods=['POST'])
def delete_campaign():
    data = request.get_json()
    nom_campagne = data.get('campagne')

    if not nom_campagne:
        return jsonify({'error': 'Nom de la campagne manquant'}), 400

    chemin_campagne = campagne_manager.obtenir_chemin_campagne(nom_campagne)

    if os.path.exists(chemin_campagne):
        shutil.rmtree(chemin_campagne)
        return jsonify({'message': 'Campagne supprimée avec succès'}), 200
    else:
        return jsonify({'error': 'Campagne non trouvée'}), 404


@app.route('/download_file/<campagneName>/<key>/<id>', methods=['GET'])
def download_file(campagneName,key, id):
    # Dossier où les fichiers sont stockés
    download_folder = os.path.join('data', campagneName, key)

    # Rechercher tous les fichiers dans le dossier avec le nom correspondant à l'ID
    for filename in os.listdir(download_folder):
        if filename.split(".")[0] == id :  # Vérifie si le fichier commence par l'ID
            file_path = os.path.join(download_folder, filename)
            print(file_path)
            if os.path.isfile(file_path):
                return send_from_directory(download_folder, filename, as_attachment=True)

    # Si aucun fichier correspondant n'est trouvé, retourne une erreur 404
    abort(404)

@app.route('/clean_data/<campagne_name>', methods=['POST'])
def clean_data(campagne_name):
    file_path = f"data/{campagne_name}/data.xlsx"
    
    if os.path.exists(file_path):
        # Charger le fichier Excel
        df = pd.read_excel(file_path,index_col='ID')
        
        # Appliquer les opérations de nettoyage de base
        df_cleaned = df.dropna(how='all')  # Supprimer les lignes complètement vides
        
        # Sauvegarder les données nettoyées
        df_cleaned.to_excel(file_path, index=True)
    
    # Rediriger vers la vue mise à jour
    return redirect(url_for('view_campaign', nom_campagne=campagne_name))

@app.route('/deduplicate_data/<campagne_name>', methods=['POST'])
def deduplicate_data(campagne_name):
    file_path = f"data/{campagne_name}/data.xlsx"
    print(file_path)
    
    if os.path.exists(file_path):
        # Charger le fichier Excel
        df = pd.read_excel(file_path, index_col='ID')
        print(df)
        # Appliquer la déduplication en conservant les premières occurrences
        df_deduplicated = df.drop_duplicates()
        
        # Sauvegarder les données dédupliquées
        df_deduplicated.to_excel(file_path, index=True)
    
    # Rediriger vers la vue mise à jour
    return redirect(url_for('view_campaign', nom_campagne=campagne_name))


@app.route('/analyze_data/<campagne>', methods=['POST'])
def analyze_data(campagne):
    analyse_resultats = campagne_manager.analyser_donnees(campagne)

    if isinstance(analyse_resultats, str):  # En cas d'erreur (ex. fichier non trouvé)
        return jsonify({
            'status': 'error',
            'message': analyse_resultats
        })

    # Génération du template HTML pour afficher les résultats
    return render_template(
        'analyse_campagne.html',
        nom_campagne=campagne,
        resume_statistique=analyse_resultats["resume_statistique"],
        visualisations=analyse_resultats["visualisations"]
    )




@app.route('/load_import_campaign', methods=['GET'])
def load_import_campaign():
    
    return render_template('import_campaign.html')

@app.route('/manage_form_access', methods=['POST','GET'])
def manage_form_access():
    campagnes = os.listdir(campagne_manager.base_dir)
    if request.method == 'GET':
        campagnes_password = {}
        for c in campagnes :
            campagne_dir = os.path.join('data', c)
            access_policy_path = os.path.join(campagne_dir, 'access_policy.json')
            try :
                f = open(access_policy_path)
                data = json.load(f)
                password = data['password']
                campagnes_password[c] = password
            except :
                campagnes_password[c] = ""
                pass
        return render_template('manage_campagne_access.html', campagnes= campagnes, campagnes_password = campagnes_password)
    
    if request.method == 'POST' :
        data = request.json
        campagne = data.get('campagne')
        password = data.get('password')

        if campagne and password:
            # Path du fichier access_policy.json
            campagne_dir = os.path.join('data', campagne)
            access_policy_path = os.path.join(campagne_dir, 'access_policy.json')
            


            # Création du dossier si nécessaire
            os.makedirs(campagne_dir, exist_ok=True)

            # Sauvegarde du mot de passe dans le fichier JSON
            access_policy = {'password': password}
            with open(access_policy_path, 'w') as f:
                json.dump(access_policy, f)

            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Données manquantes'})

@app.route('/import_campaign', methods=['POST'])
def import_campaign():
    nom_campagne = request.form.get('nom_campagne')
    nom_campagne = nom_campagne.replace(" ","_")
    file = request.files['file']

    if file and (file.filename.endswith('.xls') or file.filename.endswith('.xlsx') or file.filename.endswith('.csv')):
        # Lire le fichier dans un DataFrame pandas
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # Ajouter l'index comme colonne ID
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'ID'}, inplace=True)

        # Créer une nouvelle campagne
        campagne_manager = CampagneManager()
        campagne_manager.creer_campagne(nom_campagne)

        # Détection automatique des types de champs et ajout à la campagne
        for colonne in df.columns:
            if pd.api.types.is_numeric_dtype(df[colonne]):
                type_champ = 'nombre'
            elif pd.api.types.is_datetime64_any_dtype(df[colonne]):
                type_champ = 'date'
            elif pd.api.types.is_bool_dtype(df[colonne]):
                type_champ = 'boolean'
            else:
                type_champ = 'texte'
            if colonne != "ID" :
                campagne_manager.ajouter_champ(nom_campagne, colonne, type_champ)

        # Sauvegarder le DataFrame dans un fichier Excel
        chemin_fichier =  f"data/{nom_campagne}/data.xlsx"
        df.to_excel(chemin_fichier, index=False)

        # Rediriger vers la vue principale après l'importation
        return redirect(url_for('index'))
    else:
        return "Format de fichier non supporté", 400



if __name__ == '__main__':
    app.run(debug=True)
