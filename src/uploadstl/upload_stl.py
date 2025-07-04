import os
import uuid
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()
# === URL ET CLÉ DE SUPABASE ===
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
# === IDENTIFIANTS D'AUTHENTIFICATION ===
AUTH_EMAIL = os.getenv('AUTH_EMAIL')
AUTH_PASSWORD = os.getenv('AUTH_PASSWORD')



# === NOM DU BUCKET STORAGE ===
BUCKET_NAME = 'scans'

# === INITIALISATION DU CLIENT SUPABASE ===
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === CHEMIN VERS TON FICHIER STL LOCAL ===
LOCAL_FILE_PATH = "fichier_a_envoyer.stl"

def authenticate_user():
    """Authentifie l'utilisateur avec Supabase Auth"""
    try:
        print("🔐 Authentification en cours...")
        
        # Connexion avec email et mot de passe
        response = supabase.auth.sign_in_with_password({
            "email": AUTH_EMAIL,
            "password": AUTH_PASSWORD
        })
        
        if response.user:
            print(f"✅ Authentification réussie pour {AUTH_EMAIL}")
            print(f"👤 Utilisateur ID: {response.user.id}")
            return True
        else:
            print("❌ Échec de l'authentification")
            return False
            
    except Exception as e:
        print(f"❌ Erreur d'authentification : {str(e)}")
        return False

def save_file_metadata(user_folder_path, original_filename, public_url):
    """Sauvegarde les métadonnées du fichier dans votre table files existante"""
    try:
        # Récupérer l'utilisateur connecté
        user = supabase.auth.get_user()
        
        if user.user:
            # Adapter aux colonnes de votre table : id, user_id, filename, path, created_at
            metadata = {
                "user_id": user.user.id,
                "filename": original_filename,  # Nom original du fichier
                "path": user_folder_path       # Chemin avec dossier utilisateur
                # id et created_at sont gérés automatiquement par Supabase
            }
            
            # Insérer dans votre table 'files' existante
            result = supabase.table('files').insert(metadata).execute()
            print(f"📝 Métadonnées sauvegardées dans la base de données")
            print(f"📋 Nom du fichier : {original_filename}")
            print(f"🔗 Chemin sauvegardé : {user_folder_path}")
            print(f"🌐 URL publique : {public_url}")
            
    except Exception as e:
        print(f"⚠️  Erreur lors de la sauvegarde des métadonnées : {str(e)}")

def upload_stl_to_supabase(filepath):
    """Upload un fichier STL vers Supabase Storage dans le dossier de l'utilisateur"""
    try:
        # Vérifier l'authentification avant l'upload
        if not authenticate_user():
            print("❌ Impossible de continuer sans authentification")
            return
        
        if not os.path.exists(filepath):
            print(f"❌ Le fichier '{filepath}' n'existe pas.")
            return
            
        # Récupérer l'utilisateur connecté pour créer son dossier
        user = supabase.auth.get_user()
        if not user.user:
            print("❌ Impossible de récupérer les informations utilisateur")
            return
            
        user_id = user.user.id
        filename = os.path.basename(filepath)
        filename = secure_filename(filename)
        
        # Générer un nom de fichier unique pour éviter les conflits
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Créer le chemin avec le dossier utilisateur : user_id/nom_fichier
        user_folder_path = f"{user_id}/{unique_filename}"
        
        print(f"📤 Upload du fichier '{filename}' en cours...")
        print(f"📁 Dossier utilisateur : {user_id}")
        
        # Lecture du fichier binaire
        with open(filepath, "rb") as f:
            file_data = f.read()
        
        # Upload dans Supabase Storage avec le chemin utilisateur
        result = supabase.storage.from_(BUCKET_NAME).upload(user_folder_path, file_data, {
            "content-type": "model/stl"
        })
        
        if hasattr(result, 'error') and result.error:
            print(f"❌ Erreur lors de l'upload : {result.error}")
        else:
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{user_folder_path}"
            print(f"✅ Fichier '{filename}' uploadé avec succès !")
            print(f"🌐 URL publique : {public_url}")
            print(f"📋 Nom unique généré : {unique_filename}")
            print(f"📁 Chemin complet : {user_folder_path}")
            
            # Sauvegarder dans votre table files existante
            save_file_metadata(user_folder_path, filename, public_url)
            
    except Exception as e:
        print(f"❌ Exception : {str(e)}")

def logout_user():
    """Déconnecte l'utilisateur"""
    try:
        supabase.auth.sign_out()
        print("🔐 Déconnexion réussie")
    except Exception as e:
        print(f"❌ Erreur lors de la déconnexion : {str(e)}")

if __name__ == "__main__":
    print("=== UPLOAD STL AVEC AUTHENTIFICATION ===")
    upload_stl_to_supabase(LOCAL_FILE_PATH)
    
    # Optionnel : Se déconnecter après l'upload
    logout_user()