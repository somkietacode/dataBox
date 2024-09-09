# DataBox

Ce projet est une application web construite avec Flask, permettant la création, la gestion et la collecte de données à travers des campagnes personnalisées. Il intègre des fonctionnalités d'authentification, de création dynamique de champs de données, et de gestion des fichiers associés à chaque campagne. L'objectif est de fournir une plateforme flexible pour collecter des informations structurées via un système de campagnes.

## Fonctionnalités

- **Gestion des campagnes** : Créer, modifier et supprimer des campagnes de collecte de données.
- **Création de champs personnalisés** : Ajoutez des champs de différents types (texte, nombre, fichiers, images, vidéos, etc.) pour chaque campagne.
- **Collecte de données** : Interface utilisateur permettant de saisir les informations des campagnes, avec des options pour télécharger des fichiers multimédias.
- **Protection par mot de passe** : Accès restreint aux campagnes protégées par un mot de passe.
- **Nettoyage et déduplication des données** : Nettoyage des fichiers de données et suppression des doublons via des outils intégrés.
- **Téléchargement de fichiers** : Téléchargez les fichiers liés à une campagne directement depuis l'application.
- **Gestion d'utilisateur** : Authentification utilisateur pour protéger les fonctionnalités sensibles du système.

## Prérequis

Avant d'exécuter le projet, assurez-vous d'avoir installé les prérequis suivants :

- Python 3.x
- Flask
- Pandas
- Werkzeug
- Une configuration pour `virtualenv` (optionnelle mais recommandée)

### Installation des dépendances

Pour installer les dépendances du projet, exécutez :

```bash
pip install -r requirements.txt
 ```
### Configuration
Avant de pouvoir utiliser l'application, une configuration initiale est requise. Le fichier config.json sera généré automatiquement après avoir défini un mot de passe pour protéger l'accès à l'interface.

Rendez-vous sur la route /configure pour configurer votre mot de passe administrateur.
Connectez-vous ensuite via la route /login.
Utilisation
Démarrer l'application
Pour lancer l'application localement, exécutez la commande suivante :

```bash
python app.py
```
Accédez à l'application via http://localhost:5000.

### Principales routes
- **/configure** : Configure l'application avec un mot de passe initial.
- **/login** : Page de connexion pour accéder aux fonctionnalités protégées.
- **/create_campaign** : Créez une nouvelle campagne.
- **/collect_data/<nom_campagne>** : Collectez les données pour une campagne spécifique.
- **/view_campaign/<nom_campagne>** : Visualisez les données collectées pour une campagne.
- **/delete_campaign** : Supprimez une campagne existante.

### Contribution
Les contributions à ce projet sont les bienvenues. Si vous avez des suggestions ou des améliorations, veuillez soumettre une pull request ou ouvrir une issue.


