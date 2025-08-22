from flask import  Flask, render_template, request, jsonify, redirect, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy 
from werkzeug.utils import secure_filename
from sqlalchemy import desc, false, true, func
from datetime import datetime
from sqlalchemy.orm import Session
from flask import flash
import hashlib, os
import qrcode, traceback
import json
from flask import Flask, send_file, request
from io import BytesIO
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import UniqueConstraint


UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','pdf'}  

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]= "postgresql"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

app.secret_key = 'ZOLDYCK'

def md5_hash(data: str) -> str:
    md5_hash_object = hashlib.md5()
    md5_hash_object.update(data.encode())
    return md5_hash_object.hexdigest()
###############################################################---MODELS--#########################################################################

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    matricule = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    service = db.Column(db.String(200), nullable=False)
    bureau = db.Column(db.String(200), nullable=True)
    type = db.Column(db.String(200), nullable=False)

    __table_args__ = (
        UniqueConstraint('matricule', 'type', name='uix_matricule_type'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'matricule': self.matricule,
            'type': self.type,
            'service': self.service,
            'bureau': self.bureau
        }

class Fiche(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    responsable_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    materielType = db.Column(db.String(200), nullable=False)
    materielDetails = db.Column(db.String(200), nullable=False)

    datetime = db.Column(db.Date, nullable=False)
    nom_utilisateur = db.Column(db.String(200), nullable=False)
    interventions_demandees = db.Column(db.Text, nullable=False)
    service = db.Column(db.String(200), nullable=False)
    bureau = db.Column(db.String(200), nullable=True)

    duree_intervention = db.Column(db.Integer, nullable=True)
    description_interventions = db.Column(db.Text, nullable=True)
    materiel_objet = db.Column(db.String(200), nullable=True)
    sn = db.Column(db.String(200), nullable=True)
    materiel_repare = db.Column(db.String(50), nullable=True)
    pourquoi = db.Column(db.String(200), nullable=True)
    intervenant = db.Column(db.String(200), nullable=True)
    nom_resp = db.Column(db.String(200), nullable=True)

    etat = db.Column(db.Boolean, default=False)  

    employe = db.relationship('User', foreign_keys=[employe_id])
    responsable = db.relationship('User', foreign_keys=[responsable_id])


    def to_dict(self):
        return {
            'id': self.id,
            'employe_id': self.employe_id,
            'responsable_id': self.responsable_id,
            'materielType' : self.materielType,
            'materielDetails' : self.materielDetails,
            'date': self.date,
            'nom_utilisateur': self.nom_utilisateur,
            'service': self.service,
            'bureau': self.bureau,
            'interventions_demandees': self.interventions_demandees,
            'duree_intervention': self.duree_intervention,
            'description_interventions': self.description_interventions,
            'materiel_objet': self.materiel_objet,
            'sn': self.sn,
            'materiel_repare': self.materiel_repare,
            'pourquoi': self.pourquoi,
            'intervenant': self.intervenant,
            'nom_resp': self.nom_resp,
            'etat': self.etat 
        }

with app.app_context():
    db.create_all()

###############################################################---INSCRIPTION--####################################################################

@app.route('/user', methods=['POST'])
def create_user():
    if request.method == 'POST':
        name = request.form['name']
        matricule = request.form['matricule']
        password = md5_hash(request.form['password'])
        service = request.form['service']
        bureau = request.form['bureau'] if 'bureau' in request.form else None
        bureau_input = request.form['bureau_input'] if 'bureau_input' in request.form else None

        if bureau_input:
            bureau = bureau_input

        user_type = request.form['user_type']

        # Vérifiez si un utilisateur avec le même matricule et le même type existe déjà
        existing_user = User.query.filter_by(matricule=matricule, type=user_type).first()

        if existing_user:
            flash('Un utilisateur avec ce matricule et ce type existe déjà.', 'error')
            return redirect(url_for('admin'))

        try:
            user = User(
                name=name, 
                matricule=matricule, 
                password=password, 
                type=user_type,
                service=service,
                bureau=bureau
            )
            db.session.add(user)
            db.session.commit()

            flash('Utilisateur créé avec succès!', 'success')
        except IntegrityError:
            db.session.rollback()
            flash('Erreur : Un problème est survenu lors de l\'ajout de l\'utilisateur.', 'error')
        
        return redirect(url_for('admin'))

###############################################################---LOGIN--##########################################################################
@app.route('/auth-callback', methods=['POST'])
def loginCallback():
    if request.method == 'POST':
        # Déterminer le type de données entrantes
        if request.content_type == 'application/json':
            data = request.get_json()
        else:
            data = request.form

        # Validation des champs requis
        if 'type' not in data:
            return jsonify({'error': 'Missing type'}), 400

        if 'matricule' not in data:
            return jsonify({'error': 'Missing matricule'}), 400
        
        if 'password' not in data:
            return jsonify({'error': 'Missing password'}), 400

        # Récupération des valeurs
        user_type = data.get('type')  # 'employe' ou 'responsable'
        matricule = data.get('matricule')
        password = md5_hash(data.get('password'))

        # Recherche de l'utilisateur en fonction du type
        if user_type:
            user = User.query.filter_by(
                matricule=matricule,
                password=password,
                type=user_type
            ).first()
        else:
            return jsonify({'error': 'Invalid user type'}), 400

        # Vérification des informations de connexion
        if user:
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_matricule'] = user.matricule
            session['user_type'] = user_type
            return redirect(url_for('check'))

        else:
            return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/check')
def check():
    if 'user_id' in session:
        return redirect(url_for('main'))
    else:
        return redirect(url_for('login'))

@app.route('/main')
def main():
    if 'user_id' in session:
        user_type = session.get('user_type')
        if user_type == 'admin':
            return redirect(url_for('dashboard'))
        elif user_type == 'employe':
            return redirect(url_for('employe'))
        elif user_type == 'responsable':
            return redirect(url_for('dashboardd'))
    return redirect(url_for('login'))

##############################################################---FORM-INSCRIPTION--###############################################################

@app.route('/inscription')
def inscription():
    return render_template('admin/admin.html')

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login')
def login():
    return render_template('login.html')

#####################################################################---ADMIN--####################################################################

@app.route('/admin')
def admin():
    if 'user_id' in session and session.get('user_type') == 'admin':
        user_id = session['user_id']
        user = User.query.get(user_id)  
        return render_template('admin/admin.html')
    else:
        return redirect(url_for('home'))
@app.route('/liste_responsable')
def liste_responsable():
    if 'user_id' in session and session.get('user_type') == 'admin':
        user_id = session['user_id']
        user = User.query.get(user_id)  # Get the current admin user

        if user:
            # Retrieve all responsables
            responsables = User.query.filter_by(type='responsable').all()

            # Retrieve fiches with a specific state
            fiches = Fiche.query.filter_by(etat=True).all()
            fiche_responsable_ids = [fiche.responsable.id for fiche in fiches if fiche.responsable is not None]  # List of responsable IDs

            return render_template('admin/responsable.html', user=user, responsables=responsables, fiche_responsable_ids=fiche_responsable_ids)
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/admin/deletee', methods=['POST'])
def adminDeleteeUser():
    if 'user_id' in session and session.get('user_type') == 'admin':
        user_id = session['user_id']
        user = User.query.get(user_id)  # Get the current admin user
        data = request.form

        if 'id' not in data:
            return jsonify({'error': 'Missing parameters'}), 400
        
        user_id_to_delete = data.get('id')

        user_to_delete = User.query.filter_by(id=user_id_to_delete).first()

        if not user_to_delete:
            return jsonify({'error': 'User not found'}), 404
        
        try:
            db.session.delete(user_to_delete)
            db.session.commit()

            # Retrieve the updated list of responsables
            responsables = User.query.filter_by(type='responsable').all()
            # Retrieve fiches with a specific state
            fiches = Fiche.query.filter_by(etat=False).all()
            fiche_responsable_ids = [fiche.responsable.id for fiche in fiches if fiche.responsable is not None]  # List of responsable IDs

            return render_template('admin/responsable.html', user=user, responsables=responsables, fiche_responsable_ids=fiche_responsable_ids)
        except Exception as e:
            print(f"Error during deletion: {e}")
            return jsonify({'error': f'Something went wrong! {str(e)}'}), 500
    else:
        return jsonify({'error': 'You cannot access this endpoint'}), 401

@app.route('/liste_employe')
def liste_employe():
    if 'user_id' in session and session.get('user_type') == 'admin':
        user_id = session['user_id']
        user = User.query.get(user_id)  # Get the current admin user
        
        if user:
            # Retrieve all employees
            employees = User.query.filter_by(type='employe').all()
            
            # Adjust the query to match the actual foreign key attribute
            fiches = Fiche.query.filter(Fiche.employe_id.in_([e.id for e in employees])).all()  # Change `employe_id` if different
            fiche_ids = [fiche.employe_id for fiche in fiches]  # List of employee IDs that have fiches
            
            return render_template('admin/employe.html', user=user, employees=employees, fiche_ids=fiche_ids)
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/admin/delete', methods=['POST'])
def adminDeleteUser():
    if 'user_id' in session and session.get('user_type') == 'admin':
        user_id = session['user_id']
        user = User.query.get(user_id)  # Récupérez l'utilisateur actuel
        data = request.form

        if 'id' not in data:
            return jsonify({'error': 'Missing parameters'}), 400
        
        user_id_to_delete = data.get('id')

        user_to_delete = User.query.filter_by(id=user_id_to_delete).first()

        if not user_to_delete:
            return jsonify({'error': 'User not found'}), 404
        
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            employees = User.query.filter_by(type='employe').all()
            
            # Adjust the query to match the actual foreign key attribute
            fiches = Fiche.query.filter(Fiche.employe_id.in_([e.id for e in employees])).all()  # Change `employe_id` if different
            fiche_ids = [fiche.employe_id for fiche in fiches]  # List of employee IDs that have fiches
            
            return render_template('admin/employe.html', user=user, employees=employees, fiche_ids=fiche_ids)
        except Exception as e:
            print(f"Error during deletion: {e}")
            return jsonify({'error': f'Something went wrong! {str(e)}'}), 500
    else:
        return jsonify({'error': 'You cannot access this endpoint'}), 401

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session and session.get('user_type') == 'admin':
        total_users = User.query.filter(User.type.in_(['employe', 'responsable'])).count()
        total_employees = User.query.filter_by(type='employe').count()
        total_responsables = User.query.filter_by(type='responsable').count()
        total_admins= User.query.filter_by(type='admin').count()
        total_fiches = Fiche.query.count()
        fiches_true = Fiche.query.filter_by(etat=True).count()
        fiches_false = Fiche.query.filter_by(etat=False).count()
        total_materials = Fiche.query.count()
        material_counts = db.session.query(
            Fiche.materielType,
            func.count(Fiche.id).label('count')
        ).group_by(Fiche.materielType).all()
        
        # Check if material_counts is empty and handle it
        material_counts_dict = {material: count for material, count in material_counts} if material_counts else {}
        total_materials
        return render_template('admin/dashboard.html',
                               total_users=total_users,
                               total_employees=total_employees,
                               total_responsables=total_responsables,
                               total_admins=total_admins,
                               total_fiches=total_fiches,
                               fiches_true=fiches_true,
                               fiches_false=fiches_false,
                               total_materials=total_materials,
                               material_counts_dict=material_counts_dict)
    else:
        flash('Accès interdit. Vous devez être un administrateur pour voir ce contenu.', 'error')
        return redirect(url_for('index'))
        
#####################################################################---EMPLOYE--####################################################################

@app.route('/employe')
def employe():
    if 'user_id' in session and session.get('user_type') == 'employe':
        user_id = session['user_id']
        user = User.query.get(user_id)
          
        employees = User.query.filter_by(type='employe').first()
        return render_template('employe/employe.html' ,employees=employees ,user=user)
    else:
        return redirect(url_for('home'))
@app.route('/create_fiche', methods=['POST'])
def create_fiche():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        data = request.form

        try:
            new_fiche = Fiche(
                employe_id=user.id,
                responsable_id=data.get('responsable_id') or None, 
                materielType=data.get('materielType'), 
                materielDetails=data.get('materielDetails'), 
                datetime=data.get('datetime'),
                nom_utilisateur=data.get('nom_utilisateur'),
                service=data.get('service'),
                bureau=data.get('bureau'),
                interventions_demandees=data.get('interventions_demandees'),
            )
            db.session.add(new_fiche)
            db.session.commit()
            return redirect(url_for('all_fiches'))

        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"Error occurred while creating fiche: {traceback_str}")
            flash("An error occurred while creating the fiche. Please try again later.", 'error')
            return redirect(url_for('create_fiche'))
    else:
        return jsonify({"message": "User not logged in"}), 403

@app.route('/intervention')
def all_fiches():
    if 'user_id' in session and session.get('user_type') == 'employe':
        employe_id = session['user_id']
        user = User.query.get(employe_id)
        fiches = Fiche.query.filter_by(employe_id=employe_id).filter(Fiche.etat == False).order_by(Fiche.id.desc()).all()

        if fiches:
            return render_template('employe/intervention.html', fiches=fiches, user=user)
        else:
            return render_template('employe/intervention.html', fiches=fiches, user=user)

    else:
        flash("Unauthorized access. Please log in as an employee.", 'error')
        return redirect(url_for('home'))

@app.route('/traitée')
def traitée():
    if 'user_id' in session and session.get('user_type') == 'employe':
        employe_id = session['user_id']
        user = User.query.get(employe_id)
        fiches = Fiche.query.filter_by(employe_id=employe_id).filter(Fiche.etat == True).order_by(Fiche.id.desc()).all()

        if fiches:
            return render_template('employe/traitée.html', fiches=fiches, user=user)
        else:
            return render_template('employe/traitée.html', fiches=fiches, user=user)
    else:
        flash("Accès non autorisé. Veuillez vous connecter en tant qu'employé.", 'error')
        return redirect(url_for('home'))

@app.route('/generate_qr/<int:fiche_id>')
def generate_qr(fiche_id):
    # Obtenez les détails de la fiche depuis la base de données
    fiche = Fiche.query.get_or_404(fiche_id)
    
    # Formatez les données pour le code QR
    data = (f"Fiche ID: {fiche.id}\n"
            f"Type de matériel: {fiche.materielType}\n"
            f"Détails du matériel: {fiche.materielDetails}\n"
            f"Date: {fiche.datetime}\n"
            f"Nom de l'utilisateur: {fiche.nom_utilisateur}\n"
            f"Service: {fiche.service}\n"
            f"Bureau: {fiche.bureau}\n"
            f"Interventions demandées: {fiche.interventions_demandees}")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    buf = BytesIO()
    img.save(buf)
    buf.seek(0)
    
    return send_file(buf, mimetype='image/png', as_attachment=False, download_name='qr_code.png')

@app.route('/details/<int:fiche_id>')
def details(fiche_id):
    try:
        if 'user_id' not in session:
            return redirect(url_for('login'))

        fiche = Fiche.query.get_or_404(fiche_id)   

        user = User.query.get(session['user_id'])
        if session.get('user_type') == 'employe':
            if fiche.employe_id != user.id:
                flash("Vous n'avez pas accès à ces détails.", 'warning')
                return redirect(url_for('index')) 
        
        return render_template('employe/details.html', fiche=fiche, user=user)
    
    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"Error occurred while accessing fiche details: {traceback_str}")
        return jsonify({"message": "An error occurred while accessing the fiche details"}), 500

#################################################################---RESPONSABLE--##################################################################
@app.route('/responsable')
def responsable():
    if 'user_id' in session and session.get('user_type') == 'responsable':
        # Récupérer toutes les fiches avec état false, triées par id en ordre décroissant
        fiches = Fiche.query.filter_by(etat=False).order_by(Fiche.id).all()
        return render_template('responsable/responsable.html', fiches=fiches)
    else:
        return redirect(url_for('home'))

@app.route('/inttervention')
def inttervention():
    if 'user_id' in session and session.get('user_type') == 'responsable':
        responsable_id = session['user_id']
        user = User.query.get(responsable_id)
        fiches = Fiche.query.filter_by(responsable_id=responsable_id).order_by(Fiche.id.desc()).all()

        if fiches:
            return render_template('responsable/inttervention.html', fiches=fiches, user=user)
        else:
            flash('Aucune fiche trouvée pour cet employé', 'info')
            return render_template('responsable/inttervention.html', fiches=[], user=user)  # Render with empty list
    else:
        flash("Unauthorized access. Please log in as a responsable.", 'error')
        return redirect(url_for('home'))

@app.route('/dettails/<int:fiche_id>')
def dettails(fiche_id):
    try:
        # Vérification de la session utilisateur
        if 'user_id' not in session:
            return redirect(url_for('login'))

        # Récupération de la fiche par ID
        fiche = Fiche.query.get_or_404(fiche_id)
        print(f"Fiche: {fiche}")

        # Récupération de l'utilisateur actuellement connecté
        user = User.query.get(session['user_id'])
        print(f"User: {user}")

        # Vérification du type d'utilisateur
        if session.get('user_type') == 'responsable':
            # Récupération des détails de l'employé associé à la fiche
            employe = User.query.get(fiche.employe_id)
            print(f"Employe: {employe}")
            
            # Rendu de la page avec les détails de la fiche et de l'employé
            return render_template('responsable/dettails.html', fiche=fiche, employe=employe, user=user)

        flash("Vous n'avez pas accès à ces détails.", 'warning')
        return redirect(url_for('inttervention'))

    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"Error occurred while accessing fiche details: {traceback_str}")
        return jsonify({"message": f"An error occurred while accessing the fiche details: {str(e)}"}), 500


@app.route('/dettail/<int:fiche_id>')
def dettail(fiche_id):
    try:
        # Vérification de la session utilisateur
        if 'user_id' not in session:
            return redirect(url_for('login'))

        # Récupération de la fiche par ID
        fiche = Fiche.query.get_or_404(fiche_id)
        print(f"Fiche: {fiche}")

        # Récupération de l'utilisateur actuellement connecté
        user = User.query.get(session['user_id'])
        print(f"User: {user}")

        # Vérification du type d'utilisateur
        if session.get('user_type') == 'responsable':
            # Récupération des détails de l'employé associé à la fiche
            employe = User.query.get(fiche.employe_id)
            print(f"Employe: {employe}")
            
            # Rendu de la page avec les détails de la fiche et de l'employé
            return render_template('responsable/dettail.html', fiche=fiche, employe=employe, user=user)

        flash("Vous n'avez pas accès à ces détails.", 'warning')
        return redirect(url_for('inttervention'))

    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"Error occurred while accessing fiche details: {traceback_str}")
        return jsonify({"message": f"An error occurred while accessing the fiche details: {str(e)}"}), 500

@app.route('/traiter_fiche/<int:fiche_id>', methods=['POST'])
def traiter_fiche(fiche_id):
    fiche = Fiche.query.get_or_404(fiche_id)
    
    # Update fiche with form data
    fiche.responsable_id = request.form.get('responsable_id', '')
    duree_intervention_str = request.form.get('duree_intervention', '')
    fiche.duree_intervention = int(duree_intervention_str) if duree_intervention_str.isdigit() else None
    fiche.description_interventions = request.form.get('description_interventions', '')
    fiche.materiel_objet = request.form.get('materiel_objet', '')
    fiche.materiel_repare = request.form.get('materiel_repare', '')
    fiche.pourquoi = request.form.get('pourquoi', '')
    fiche.sn = request.form.get('numero_serie', '')
    fiche.nom_resp = request.form.get('nom_resp', '')
    fiche.intervenant =  request.form.get('intervenant', '')

    # Update fiche status to true
    fiche.etat = True
    
    # Commit changes to the database
    db.session.commit()
    
    return redirect(url_for('responsable'))
    
@app.route('/dashboardd')
def dashboardd():
    if 'user_id' in session and session.get('user_type') == 'responsable':
        responsable_id = session['user_id']
        
        # Compter les fiches spécifiques à ce responsable
        total_fiches = Fiche.query.filter_by(responsable_id=responsable_id).count()
        fiches_true = Fiche.query.filter_by(responsable_id=responsable_id, etat=True).count()
        fiches_false = Fiche.query.filter_by(etat=False).count()
        
        # Compter les types de matériel pour ce responsable
        material_counts = db.session.query(
            Fiche.materielType,
            func.count(Fiche.id).label('count')
        ).filter_by(responsable_id=responsable_id).group_by(Fiche.materielType).all()

        # Gestion du dictionnaire des types de matériel
        total_parc = {material: count for material, count in material_counts} if material_counts else {}

        return render_template('responsable/dashboard.html',
                               total_fiches=total_fiches,
                               fiches_true=fiches_true,
                               fiches_false=fiches_false,
                               total_parc=total_parc)
    else:
        flash('Accès interdit. Vous devez être un responsable pour voir ce contenu.', 'error')
        return redirect(url_for('main'))  # Remplacer 'index' par 'main'

@app.route('/logout')
def logout():
    #session.clear()
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run(debug=True)