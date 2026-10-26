# GreenCheck

GreenCheck aide à savoir si une plante est malade. On envoie la photo d'une feuille,
et l'application indique si la plante semble saine ou malade, avec des conseils.

Le projet est testé sur Mac, avec Python 3.14.

## Comment ça marche ?

GreenCheck utilise trois programmes qui travaillent ensemble :

1. **La base de données (MySQL)** garde les comptes, les plantes et les diagnostics.
2. **Le site (Django)** est ce que l'utilisateur voit dans son navigateur.
3. **Le service d'analyse (IA)** regarde la photo et dit si la feuille est malade.

Il faut donc lancer ces trois programmes pour que tout fonctionne.

## Ce qu'il faut installer avant

- **Python 3.14** : https://www.python.org
- **Docker Desktop** : https://www.docker.com (il faut l'ouvrir et attendre qu'il démarre)

Les commandes ci-dessous se tapent dans le **Terminal** (sur Mac : touches Cmd + Espace,
puis écrire "Terminal"). Il faut d'abord aller dans le dossier du projet :

```bash
cd chemin/vers/Application_GreenCheck2
```

## Étape 1 : le fichier de configuration

Ce fichier contient les informations secrètes du projet : le mot de passe de la base
de données et la clé de sécurité du site.

```bash
cp .env.example .env
```

Ouvrir le fichier `.env` et remplacer les deux valeurs `change_me` :

- `MYSQL_PASSWORD` : un mot de passe de ton choix pour la base de données.
- `SECRET_KEY` : une longue clé aléatoire. Pour en générer une, taper :
```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```
  puis copier le résultat dans `.env`.

Il n'y a rien d'autre à modifier : la base de données et le site lisent tous les deux
ce fichier. Il ne faut jamais l'envoyer sur GitHub (le projet l'ignore déjà).

## Étape 2 : lancer la base de données

Docker Desktop doit être ouvert. Puis :

```bash
docker-compose up -d
```

Attendre environ 20 secondes. La base est prête quand cette commande affiche
`greencheck_mysql` :

```bash
docker ps
```

## Étape 3 : installer et préparer le site

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py createsuperuser
```

Explications :
- Les deux premières lignes créent un espace de travail propre pour le projet.
  Quand il est actif, le terminal affiche `(.venv)` au début de la ligne.
- `pip install` installe les outils dont le site a besoin.
- `migrate` crée les tables dans la base de données.
- `createsuperuser` crée un compte administrateur. Il demande un nom, un email et un
  mot de passe : choisis ce que tu veux et note-le.

## Étape 4 : installer le service d'analyse

Ce programme a son **propre** espace de travail, séparé du site.

```bash
cd ai_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

L'installation est longue (plusieurs minutes), c'est normal.

Vérifier que ces deux fichiers sont bien dans le dossier `ai_service` :
`plant_model.keras` et `class_names.json`. Sans eux, l'analyse ne marche pas.

## Étape 5 : lancer le projet

Il faut **deux terminaux ouverts en même temps** (menu Terminal, puis Nouvelle fenêtre).
La base de données tourne déjà depuis l'étape 2.

**Terminal 1 : le service d'analyse**

```bash
cd ai_service
source .venv/bin/activate
uvicorn main:app --port 8001
```

Quand `Uvicorn running on http://127.0.0.1:8001` s'affiche, laisser cette fenêtre ouverte.

**Terminal 2 : le site**

```bash
source .venv/bin/activate
python3 manage.py runserver
```

Quand `Starting development server at http://127.0.0.1:8000/` s'affiche,
laisser cette fenêtre ouverte aussi.

## Étape 6 : première utilisation

1. Ouvrir http://127.0.0.1:8000/admin/ et se connecter avec le compte créé à l'étape 3.
2. Ajouter quelques **Exposures** (par exemple : Plein soleil, Mi-ombre, Ombre)
   et quelques **Locations** (par exemple : Salon, Balcon, Jardin).
   Ce sont les choix proposés quand on ajoute une plante.
3. Aller sur http://127.0.0.1:8000/register/ et créer un compte utilisateur.
4. Se connecter, cliquer sur **+ Ajouter une plante**, puis sur **Diagnostiquer**
   et envoyer une photo de feuille.

Conseil pour la photo : une feuille seule, sur un fond clair et uni, en lumière naturelle.

## Lancer les tests

```bash
python3 manage.py test
```

Résultat attendu : `Ran 20 tests` puis `OK`. Le service d'analyse n'a pas besoin
de tourner pour les tests.

## Pour arrêter le projet

- Dans chaque terminal ouvert : touches **Ctrl + C**.
- La base de données : `docker-compose down`

## Si ça ne marche pas

| Problème | Solution |
|---|---|
| `Can't connect to MySQL server` | Docker Desktop n'est pas ouvert, ou la base est encore en train de démarrer. Attendre 20 secondes. |
| `No module named ...` | L'espace de travail n'est pas actif. Relancer `source .venv/bin/activate`. |
| `address already in use` | Le programme tourne déjà dans un autre terminal. Le fermer avec Ctrl + C. |
| Le message "service d'analyse indisponible" | Le terminal 1 (analyse) n'est pas lancé. |
| La liste Exposition ou Localisation est vide | Elles n'ont pas été créées dans l'administration (étape 6). |

## À savoir sur l'analyse

Le modèle a été entraîné sur des photos de feuilles prises en laboratoire, sur fond uni.
Il connaît 14 cultures (tomate, pomme de terre, pomme, vigne, maïs...) et peut se tromper
sur une autre plante ou sur une photo avec un fond chargé. Le pourcentage affiché est
un indicateur, pas une certitude.