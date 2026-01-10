# Guide des Migrations Alembic avec Neon

## Configuration Recommandée

### Variables d'Environnement

Pour les migrations, Neon recommande d'utiliser l'**endpoint direct** (sans `-pooler`) car plus stable pour les opérations DDL.

#### Option 1 : URL Dédiée (Recommandée)

Créez deux variables dans votre `.env` :

```env
# Pour l'application (avec pooler)
DATABASE_URL=postgresql://user:password@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require

# Pour les migrations (sans pooler - endpoint direct)
DATABASE_URL_MIGRATIONS=postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

**Note** : Remplacez `-pooler` par rien dans l'URL des migrations.

#### Option 2 : Conversion Automatique

Si vous ne définissez que `DATABASE_URL`, Alembic convertira automatiquement l'URL pour retirer `-pooler`.

## Commandes

### Générer une migration (avec connexion)

```bash
python -m alembic revision --autogenerate -m "description"
```

### Générer une migration manuelle (sans connexion)

Si le port 5432 est bloqué :

```bash
python -m alembic revision -m "description"
```

Puis éditez le fichier généré dans `src/db/alembic/versions/` pour ajouter les opérations SQL.

### Appliquer les migrations

```bash
python -m alembic upgrade head
```

### Voir l'historique

```bash
python -m alembic history
```

### Voir l'état actuel

```bash
python -m alembic current
```

## Résolution de Problèmes

### Timeout de Connexion

**Causes fréquentes :**
- Port 5432 bloqué par firewall/réseau
- Base Neon en pause (statut "Idle")
- VPN/Proxy qui bloque les connexions

**Solutions :**
1. Réveillez la base depuis le dashboard Neon
2. Testez depuis un autre réseau (4G/5G, autre Wi-Fi)
3. Vérifiez les règles firewall
4. Utilisez `DATABASE_URL_MIGRATIONS` avec l'endpoint direct

### Migration Manuelle

Si la connexion est impossible :

1. Générez une migration vide :
   ```bash
   python -m alembic revision -m "ma migration"
   ```

2. Éditez le fichier dans `src/db/alembic/versions/` :
   ```python
   def upgrade() -> None:
       op.create_table('ma_table', ...)
       op.add_column('autre_table', sa.Column('nouveau_champ', sa.String()))
   
   def downgrade() -> None:
       op.drop_column('autre_table', 'nouveau_champ')
       op.drop_table('ma_table')
   ```

3. Appliquez plus tard depuis un environnement avec accès réseau :
   ```bash
   python -m alembic upgrade head
   ```

## Sécurité

⚠️ **Important** : Ne commitez jamais le fichier `.env` avec les credentials en clair.

- Utilisez des variables d'environnement sécurisées
- Rotatez les mots de passe régulièrement
- Utilisez des secrets managers en production
