# 🛡️ CyberGuard - Assistant IA en Cybersécurité

Assistant conversationnel intelligent pour sensibiliser les utilisateurs à la cybersécurité et les guider face aux incidents.

## 📋 Description

CyberGuard est un agent IA conçu pour aider les employés à :
- Détecter et réagir aux emails de phishing
- Créer des mots de passe robustes
- Activer l'authentification multifacteur (MFA)
- Utiliser correctement le VPN
- Signaler des incidents de sécurité
- Partager des fichiers sensibles en toute sécurité

L'assistant détecte automatiquement l'intention de l'utilisateur et fournit des réponses personnalisées avec des étapes claires, des bonnes pratiques et des suggestions de questions connexes.

## ✨ Fonctionnalités

- **Détection d'intention automatique** : Identifie le sujet de la question (phishing, mots de passe, MFA, VPN, etc.)
- **Réponses structurées** : Étapes claires + bonnes pratiques + erreurs courantes
- **Base de connaissances FAQ** : Recherche sémantique avec TF-IDF pour trouver la meilleure réponse
- **Suggestions intelligentes** : Propose des questions connexes pertinentes
- **Astuces de sécurité** : Conseils aléatoires affichés avec chaque réponse
- **Historique des conversations** : Sauvegarde dans SQLite pour audit et suivi
- **Interface moderne** : Design responsive avec dark mode

## 🏗️ Architecture

```
Agent Ia/
├── backend/
│   └── main.py                 # API FastAPI
├── frontend/
│   └── index.html              # Interface utilisateur
├── app/
│   └── agent/
│       ├── orchestrator.py     # Orchestrateur principal
│       ├── faq_agent.py        # Agent FAQ avec TF-IDF
│       ├── database.py         # Gestion SQLite
│       └── knowledge_base.yaml # Base de connaissances
├── serve_frontend.py           # Serveur HTTP pour le frontend
├── conversations.db            # Base de données SQLite
└── requirements.txt            # Dépendances Python
```

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Étapes

1. **Cloner le dépôt**
```bash
git clone https://github.com/votre-username/agent-ia.git
cd agent-ia
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Lancer le backend (API)**
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

4. **Lancer le frontend (dans un autre terminal)**
```bash
python serve_frontend.py
```

5. **Ouvrir le navigateur**
```
http://localhost:3000
```

## 📖 Utilisation

### Interface utilisateur
- Cliquez sur les boutons de questions rapides
- Ou tapez votre question dans le champ de texte
- L'assistant détecte automatiquement le sujet et répond avec :
  - Une réponse détaillée
  - Des étapes à suivre
  - Des questions connexes
  - Une astuce de sécurité

### API Backend

**Endpoint principal :** `POST /chat`

```json
{
  "message": "Comment détecter un email suspect ?",
  "user_id": "user123",
  "session": {}
}
```

**Réponse :**
```json
{
  "id": "user123",
  "response": "Vérifiez l'expéditeur, méfiez-vous des urgences...",
  "steps": ["Étape 1", "Étape 2"],
  "suggestions": [["Question 1", 0.95], ["Question 2", 0.89]],
  "tip": "Astuce: Vérifiez toujours le domaine réel",
  "follow_up": ""
}
```

## 🔧 Technologies utilisées

### Backend
- **FastAPI** : Framework API moderne et rapide
- **Uvicorn** : Serveur ASGI
- **scikit-learn** : TF-IDF pour la recherche sémantique
- **PyYAML** : Gestion de la base de connaissances
- **SQLite** : Base de données pour l'historique

### Frontend
- **HTML5 / CSS3** : Interface responsive
- **JavaScript vanilla** : Interactions dynamiques
- **Fetch API** : Communication avec le backend

## 📊 Base de données

La base SQLite stocke :
- **Conversations** : Historique des échanges (user_id, message, réponse, intent, timestamp)
- **Incidents** : Signalements de sécurité (user_id, severity, details, status)
- **Métriques** : Statistiques d'utilisation (metric_name, value, intent)

## 🎯 Intentions détectées

- `greeting` : Salutation
- `phishing_incident` : Phishing / emails suspects
- `password_security` : Mots de passe
- `mfa` : Authentification multifacteur
- `vpn` : VPN et accès distant
- `updates` : Mises à jour de sécurité
- `data_sensitivity` : Gestion des données sensibles
- `incident_reporting` : Signalement d'incidents

## 📝 Personnalisation

### Modifier la base de connaissances
Éditez `app/agent/knowledge_base.yaml` pour ajouter/modifier :
- FAQ (questions/réponses)
- Astuces de sécurité
- Bonnes pratiques
- Contacts d'escalade

### Ajuster la détection d'intention
Modifiez `app/agent/orchestrator.py` → méthode `detect_intent()` pour ajouter des mots-clés.

## 🔒 Sécurité

- Les conversations sont enregistrées pour audit
- CORS configuré (à restreindre en production)
- Pas d'authentification (à ajouter pour la production)
- Variables d'environnement recommandées pour les configurations sensibles

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :
1. Fork le projet
2. Créez une branche (`git checkout -b feature/amelioration`)
3. Committez vos changements (`git commit -m 'Ajout fonctionnalité X'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
