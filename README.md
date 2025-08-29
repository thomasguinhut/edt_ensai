# Synchronisation automatique d'un EDT au format ICS avec Google Calendar

Ce projet de synchroniser automatiquement un emploi du temps au format ICS (récupérable à partir d'une URL) vers un agenda déjà créé sur son compte Google Calendar. Il est notamment utilisable pour son EDT personnel à l'Ensai, disponible depuis Pamplemousse.

Une notification du bon déroulement de la mise à jour quotidienne est éventuellement possible par mail. Si elle n'est pas souhaitée, le paramètre dans la fonction main doit être mis en FALSE.

## Structure du projet

```
edt_ensai/
├── main.py                    
├── requirements.txt          
├── README.md                 
└── .github/
    └── workflows/
        └── daily-sync.yml    
```

## Prérequis généraux

### Configuration Google Calendar API

1. Créez un projet sur [Google Cloud Console](https://console.cloud.google.com/)
2. Activez l'API Google Calendar
3. Créez un compte de service et téléchargez le fichier JSON des clés
4. Partagez votre agenda Google avec l'adresse email du compte de service (avec permission d'écriture)
5. Récupérez l'ID de votre agenda Google (disponible dans les paramètres de l'agenda)

### Variables d'environnement

Le script nécessite les variables d'environnement suivantes :

#### Variables obligatoires

- `ICS_URL` : URL du fichier ICS à télécharger
- `CALENDAR_ID` : ID de l'agenda Google Calendar à mettre à jour
- `GOOGLE_CREDENTIALS` : Contenu JSON du fichier de clés du compte de service Google (format string)

#### Variables éventuellement pour l'envoi de la notification par mail

- `NOTIFY_EMAIL` : Adresse email pour recevoir les notifications
- `SMTP_SERVER` : Serveur SMTP (par défaut : `smtp.gmail.com`)
- `SMTP_PORT` : Port SMTP (par défaut : `587`)
- `SMTP_USER` : Nom d'utilisateur SMTP
- `SMTP_PASSWORD` : Mot de passe SMTP

## Prérequis pour une configuration manuelle

### Importation du projet en local depuis le terminal de VS Code
```bash
git clone https://github.com/thomasguinhut/edt_ensai
cd edt_ensai
```

### Dépendances Python

Installez les dépendances :
```bash
pip install -r requirements.txt
```

### Variables d'environnement

Les variables sont à définir dans un token edt-ensai sur la plateforme Onyxia utilisée pour lancer le script.

### Éxéxution du script
```bash
python main.py
```

## Prérequis pour une automatisation avec GitHub Actions

Le script peut être automatisé avec GitHub Actions grâce au fichier `daily-sync.yml` présent dans `.github/workflows/`. Ce fichier fixe la mise à jour quotidienne à 02h UTC (03h en heure française en hiver, 04h en été).

### Forker le projet

1. Allez sur la page GitHub du projet : https://github.com/thomasguinhut/edt_ensai
2. Cliquez en haut à droite sur Fork
3. Sélectionnez votre compte GitHub
4. GitHub crée une copie complète du projet sur votre compte

Puis dans les paramètre du service créé sur Onyxia, mettre https://github.com/<votre-utilisateur>/<nom-du-fork>.git.

### Configuration des secrets GitHub

Dans les paramètres de votre dépôt GitHub (Settings, Secrets and variables, Actions, New repository secret), ajoutez les variables suivants :

- `ICS_URL`
- `CALENDAR_ID` 
- `GOOGLE_CREDENTIALS`
- `NOTIFY_EMAIL` (optionnel)
- `SMTP_USER` (optionnel)
- `SMTP_PASSWORD` (optionnel)