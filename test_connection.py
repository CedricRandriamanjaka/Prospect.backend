"""
Script de test de connexion à la base de données Neon.
Utilisez ce script pour vérifier que la connexion fonctionne.
"""
from src.db.database import test_connection, get_database_url

def main():
    print("🔍 Test de connexion à Neon...")
    print(f"📋 URL: {get_database_url()[:50]}...")  # Affiche seulement le début pour sécurité
    
    if test_connection():
        print("✅ Connexion réussie ! La base de données est accessible.")
        return 0
    else:
        print("❌ Échec de la connexion.")
        print("\n💡 Vérifiez :")
        print("  1. Que la base Neon n'est pas en pause (statut 'Idle')")
        print("  2. Que DATABASE_URL dans .env est correct")
        print("  3. Votre connexion internet")
        return 1

if __name__ == "__main__":
    exit(main())
