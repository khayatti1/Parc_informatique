# Parc informatique

##  Description
**Parc_informatique** est une application web développée avec **Python** (probablement Flask) et **HTML**, destinée à la gestion complète d’un parc informatique. Elle permet d’administrer des données essentielles telles que les équipements, les utilisateurs et les interventions via une interface structurée.

## Fonctionnalités principales
- **Gestion des équipements** : ajouter, modifier, supprimer et consulter les informations des matériels informatiques (PC, imprimantes, etc.).
- **Gestion des utilisateurs** : suivre les utilisateurs ou services responsables des équipements.
- **Gestion des interventions** : planifier et suivre les réparations ou maintenances.
- **Interface web interactive** : navigation fluide via pages HTML.
- **Opérations CRUD** (Créer, Lire, Mettre à jour, Supprimer) pour toutes les entités.
- **Organisation des templates** pour présenter les informations dans le navigateur.

## Architecture & Technologies
- **Langage** : Python  
- **Framework web** : possiblement **Flask** (fichier `app.py`)  
- **Templates** : dossier `templates/` (HTML)  
- **Ressources statiques** : dossier `static/images/`  
- **Structure** :
  - `app.py` → logique principale de l’application  
  - `templates/` → pages HTML  
  - `static/images/` → ressources graphiques (images…)  

## Installation
1. Clonez ou téléchargez le projet :
    ```bash
    git clone https://github.com/khayatti1/Parc_informatique.git
    ```
2. Placez-vous dans le répertoire du projet :
    ```bash
    cd Parc_informatique
    ```
3. (Optionnel) Créez un environnement virtuel Python et activez-le :
    ```bash
    python -m venv venv
    source venv/bin/activate  # sur macOS/Linux
    venv\Scripts\activate     # sur Windows
    ```
4. Installez les dépendances (Flask, etc.) si un fichier `requirements.txt` est disponible :
    ```bash
    pip install -r requirements.txt
    ```
5. Lancez l’application :
    ```bash
    python app.py
    ```
6. Accédez à l’application via votre navigateur à l’adresse :
    ```
    http://localhost:5000
    ```

## Utilisation
- Ouvrez l’application depuis votre navigateur.
- Naviguez entre les sections équipements, utilisateurs, interventions.
- Réalisez des opérations CRUD selon vos besoins.
- Consultez ou modifiez les informations selon votre rôle (administrateur, technicien, etc.).


