import os
import json
import pandas as pd
import uuid
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

class CampagneManager:
    def __init__(self, base_dir='data'):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def obtenir_chemin_campagne(self, nom_campagne):
        return os.path.join(self.base_dir, nom_campagne)

    def creer_campagne(self, nom_campagne):
        chemin_campagne = self.obtenir_chemin_campagne(nom_campagne)
        if os.path.exists(chemin_campagne):
            return False, f"Une campagne avec le nom '{nom_campagne}' existe déjà. Veuillez choisir un autre nom."
        
        os.makedirs(chemin_campagne)
        chemin_data_structure = os.path.join(chemin_campagne, 'data_structure.json')
        
        # Créer un UID pour la campagne
        uid = str(uuid.uuid4())
        data_structure = {"UID": uid, "Field": {}, "MultipleChoices" : {}}
        
        with open(chemin_data_structure, 'w') as f:
            json.dump(data_structure, f)
        
        return True, f"Campagne '{nom_campagne}' créée avec succès. UID: {uid}"

    def ajouter_champ(self, nom_campagne, nom_champ, type_champ, choicesValues = ""):
        chemin_campagne = self.obtenir_chemin_campagne(nom_campagne)
        chemin_data_structure = os.path.join(chemin_campagne, 'data_structure.json')

        if not os.path.exists(chemin_data_structure):
            return "La campagne n'existe pas ou le fichier data_structure.json est manquant."

        # Charger la structure de données existante
        with open(chemin_data_structure, 'r') as f:
            data_structure = json.load(f)
        
        # Ajouter le nouveau champ sous la clé "Field"
        data_structure["Field"][nom_champ] = type_champ

        if type_champ == "choix_multiple" :
            data_structure["MultipleChoices"][nom_champ] = choicesValues
        
        # Sauvegarder la structure de données mise à jour
        with open(chemin_data_structure, 'w') as f:
            json.dump(data_structure, f)

        # Vérifier si le type de champ est un fichier
        types_fichier = ['audio', 'image', 'video', 'fichier']
        if type_champ in types_fichier:
            chemin_dossier_fichier = os.path.join(chemin_campagne, nom_champ)
            if not os.path.exists(chemin_dossier_fichier):
                os.makedirs(chemin_dossier_fichier)
        
        # Vérifier si le type de champ peut être stocké dans un fichier Excel
        types_excel = ['texte', 'nombre', 'date', 'boolean' , 'choix_multiple']
        if type_champ in types_excel:
            chemin_excel = os.path.join(chemin_campagne, 'data.xlsx')
            if os.path.exists(chemin_excel):
                # Charger le fichier Excel existant avec pandas
                df = pd.read_excel(chemin_excel)

                # Ajouter la colonne si elle n'existe pas
                if nom_champ not in df.columns:
                    df[nom_champ] = pd.NA  # Ajouter une colonne vide avec le nouveau champ
            else:
                # Créer un nouveau DataFrame avec la colonne du champ
                df = pd.DataFrame(columns=['ID', nom_champ])  # Inclure la colonne ID

            # Sauvegarder les modifications dans le fichier Excel
            df.to_excel(chemin_excel, index=False)

        return "Champ ajouté avec succès."

    def get_campaign(self, nom_campagne):
        campagne_path = os.path.join(self.base_dir, nom_campagne)
        data_structure_file = os.path.join(campagne_path, 'data_structure.json')
        data_file = os.path.join(campagne_path, 'data.xlsx')

        if os.path.exists(campagne_path) and os.path.exists(data_structure_file):
            # Charger la structure des champs
            with open(data_structure_file, 'r') as f:
                champs = json.load(f)

            # Charger les données, si disponibles
            if os.path.exists(data_file):
                df = pd.read_excel(data_file)
                data = df.to_dict(orient='records')
            else:
                data = []

            return {
                "nom_campagne": nom_campagne,
                "champs": champs,
                "data": data
            }
        return None
    


    def sauvegarder_donnees(self, nom_campagne, data, fichiers):
        chemin_campagne = self.obtenir_chemin_campagne(nom_campagne)
        chemin_excel = os.path.join(chemin_campagne, 'data.xlsx')
        
        if os.path.exists(chemin_excel):
            df = pd.read_excel(chemin_excel)
        else:
            df = pd.DataFrame(columns=['ID'] + list(data.keys()))
        
        new_id = len(df) + 1
        data['ID'] = new_id
        new_row = pd.DataFrame([data])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_excel(chemin_excel, index=False)
        
        for champ, fichier in fichiers.items():
            if fichier:
                chemin_dossier_fichier = os.path.join(chemin_campagne, champ)
                chemin_fichier = os.path.join(chemin_dossier_fichier, f"{new_id}{Path(fichier.filename).suffix}")
                fichier.save(chemin_fichier)

        return "Données sauvegardées avec succès."

    def analyser_donnees(self, nom_campagne):
        chemin_campagne = self.obtenir_chemin_campagne(nom_campagne)
        chemin_excel = os.path.join(chemin_campagne, 'data.xlsx')
        os.makedirs(f'static/{chemin_campagne}', exist_ok=True)
        chemin_campagne = f'static/{chemin_campagne}'

        if not os.path.exists(chemin_excel):
            return "Le fichier data.xlsx est introuvable."

        # Charger les données du fichier Excel
        df = pd.read_excel(chemin_excel, index_col='ID')

        # 1. Résumé statistique des données numériques
        resume_statistique = df.describe().to_dict()

        # 2. Identification des outliers avec Isolation Forest
        isolation_forest = IsolationForest(contamination=0.1)
        df['outlier'] = isolation_forest.fit_predict(df.select_dtypes(include=['number']))

        # Visualisation des outliers
        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=df.index, y=df.select_dtypes(include=['number']).iloc[:, 0], hue=df['outlier'], palette={1: 'blue', -1: 'red'})
        plt.title("Détection des outliers")
        plt.xlabel("Index")
        plt.ylabel(df.select_dtypes(include=['number']).columns[0])
        chemin_image_outliers = os.path.join(chemin_campagne, "outliers.png")
        plt.savefig(chemin_image_outliers)
        plt.close()

        # 3. Box plots pour visualiser la distribution des variables
        visualisations_boxplots = []
        for colonne in df.select_dtypes(include=['number']).columns:
            plt.figure(figsize=(10, 6))
            sns.boxplot(df[colonne])
            plt.title(f"Box plot de {colonne}")
            plt.xlabel(colonne)
            chemin_image_boxplot = os.path.join(chemin_campagne, f"boxplot_{colonne}.png")
            plt.savefig(chemin_image_boxplot)
            plt.close()
            visualisations_boxplots.append(chemin_image_boxplot)

        # 4. Nuages de points (scatter plots) pour visualiser les relations entre variables
        visualisations_scatter = []
        numeric_columns = df.select_dtypes(include=['number']).columns
        if len(numeric_columns) > 1:
            for i, col1 in enumerate(numeric_columns):
                for col2 in numeric_columns[i+1:]:
                    plt.figure(figsize=(10, 6))
                    sns.scatterplot(x=df[col1], y=df[col2])
                    plt.title(f"Nuage de points entre {col1} et {col2}")
                    plt.xlabel(col1)
                    plt.ylabel(col2)
                    chemin_image_scatter = os.path.join(chemin_campagne, f"scatter_{col1}_vs_{col2}.png")
                    plt.savefig(chemin_image_scatter)
                    plt.close()
                    visualisations_scatter.append(chemin_image_scatter)

        # 5. Matrice de corrélation
        numeric_cols = df.select_dtypes(include=[float, int]).columns
        corr_matrix = df[numeric_cols].corr()
        plt.figure(figsize=(12, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1)
        plt.title("Matrice de corrélation")
        chemin_image_corr = os.path.join(chemin_campagne, "correlation_matrix.png")
        plt.savefig(chemin_image_corr)
        plt.close()

        # 6. Analyse en Composantes Principales (ACP)
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(df.select_dtypes(include=['number']).drop(columns=['outlier']))
        df['PCA1'] = pca_result[:, 0]
        df['PCA2'] = pca_result[:, 1]

        plt.figure(figsize=(10, 6))
        sns.scatterplot(x=df['PCA1'], y=df['PCA2'], hue=df['outlier'], palette={1: 'blue', -1: 'red'})
        plt.title("Analyse en Composantes Principales (ACP)")
        plt.xlabel("PCA1")
        plt.ylabel("PCA2")
        chemin_image_pca = os.path.join(chemin_campagne, "pca.png")
        plt.savefig(chemin_image_pca)
        plt.close()

        # Enregistrement de la base de données mise à jour avec les résultats PCA et outliers
        #df.drop(columns=['outlier']).to_excel(chemin_excel, index=True)

        return {
            "resume_statistique": resume_statistique,
            "visualisations": {
                "outliers": chemin_image_outliers,
                "boxplots": visualisations_boxplots,
                "scatter": visualisations_scatter,
                "correlation": chemin_image_corr,
                "pca": chemin_image_pca
            }
        }