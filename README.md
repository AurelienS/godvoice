# 🔍 GodVoice - WhatsApp Chat Analysis

Une application Python avancée pour analyser les conversations WhatsApp avec des statistiques détaillées, des visualisations interactives et une analyse IA approfondie.

## 🌟 Fonctionnalités

### 📊 **Analyses Statistiques**
- Nombre de messages et mots par participant
- Répartition temporelle (quotidienne et horaire)
- Styles de communication (prolixe vs bavard)
- Usage des médias et emojis

### 📈 **Visualisations**
- Graphiques de participation (top 10)
- Heatmaps GitHub-style par participant
- Distribution des types de messages
- Analyse des heures de pointe
- Camemberts de répartition

### 🤖 **Analyse IA (Claude Sonnet 3.5)**
- **Sentiment** : Analyse émotionnelle détaillée
- **Sujets** : Top 5 des thèmes principaux
- **Style** : Personnalité et tics linguistiques
- **Politique** : Orientation et positions clivantes 🌶️
- **Controversé** : Débats et contenus polémiques 🔥
- **Humour** : Type d'humour et niveau de provocation 😂
- **Secrets** : Révélations et anecdotes croustillantes 🕵️

## 🚀 Installation

### Prérequis
- Python 3.8+
- pip

### Dépendances
```bash
pip install pandas matplotlib seaborn tiktoken anthropic python-dotenv
```

## ⚙️ Configuration

### 1. Fichier `.env`
Créez un fichier `.env` à la racine du projet :
```env
ANTHROPIC_API_KEY=your-anthropic-api-key-here
```

**🔑 Obtenir une clé API Anthropic :**
1. Allez sur [console.anthropic.com](https://console.anthropic.com)
2. Créez un compte et ajoutez du crédit (5$ recommandés)
3. Générez une clé API
4. Remplacez `your-anthropic-api-key-here` par votre vraie clé

### 2. Fichier de chat WhatsApp
Exportez votre conversation WhatsApp :

**📱 Sur mobile :**
1. Ouvrez la conversation WhatsApp
2. Appuyez sur le nom du groupe/contact
3. Faites défiler vers le bas
4. **"Exporter la discussion"** > **"Sans fichiers multimédias"**
5. Sauvegardez le fichier comme `chat.txt` dans le dossier du projet

**💻 Sur WhatsApp Web :**
1. Ouvrez la conversation
2. Cliquez sur les 3 points (**⋮**) > **Plus** > **Exporter la discussion**
3. Choisissez **"Sans fichiers multimédias"**
4. Renommez le fichier en `chat.txt`

## 🎯 Utilisation

```bash
python main.py
```

### 📁 Structure des résultats

```
godvoice/
├── main.py                    # Script principal
├── chat.txt                   # Votre export WhatsApp
├── .env                       # Clés API (non versionnées)
├── by_authors/                # Chunks par participant (non versionnés)
│   ├── AurelienS/
│   ├── Gilles/
│   └── ...
└── figures/                   # Visualisations générées
    ├── messages_par_auteur_top.png
    ├── participation_quotidienne_top.png
    ├── heatmap_github_global.png
    ├── analyses_ia/           # Analyses IA (non versionnées)
    │   ├── AurelienS_sonnet_PREMIUM_analysis.txt
    │   └── ...
    └── heatmaps_par_auteur/    # Heatmaps individuelles
        ├── heatmap_AurelienS.png
        └── ...
```

## 🎨 Exemples de visualisations

- **📊 Top participants** : Graphiques en barres des plus actifs
- **📅 Participation quotidienne** : Évolution dans le temps
- **🕐 Répartition horaire** : Heures de pointe par participant
- **🔥 Heatmap GitHub** : Activité quotidienne sur l'année
- **💬 Types de messages** : Court/Moyen/Long par participant
- **😂 Médias & Emojis** : Usage par participant

## 🤖 Analyse IA - Exemples de résultats

### 🏛️ **Analyse Politique**
```
Orientation: Centre-gauche modéré
Positions détectées:
- Pro-européen avec nuances critiques
- Écologie: sensibilité environnementale marquée
- Économie: favorable aux régulations sociales
```

### 🔥 **Contenu Controversé**
```
Niveau de provocation: 7/10
Sujets clivants identifiés:
- Débats sur l'immigration (3 échanges houleux)
- Critiques du gouvernement (ton sarcastique)
- Positions sur le nucléaire (arguments techniques)
```

### 😂 **Analyse Humour**
```
Type: Humour noir et références pop culture
Niveau politiquement incorrect: 6/10
Réactions du groupe: Très positives (nombreux 😂)
```

## 💰 Coûts IA

**Claude Sonnet 3.5** (recommandé) :
- ~$0.10-0.20 par participant analysé
- Budget 5$ = analyse complète de ~25-50 participants
- Qualité premium avec détection fine du contenu épicé

## 🔒 Confidentialité

- ✅ Toutes les données sensibles sont dans `.gitignore`
- ✅ Analyses IA stockées localement uniquement
- ✅ Aucune donnée personnelle n'est versionnée
- ✅ Clés API protégées

## 🛠️ Personnalisation

### Modifier les paramètres d'analyse
```python
# Dans main.py
TOP_N = 10                    # Nombre d'auteurs dans les graphiques
CHUNK_TOKEN_LIMIT = 750       # Taille des chunks pour l'IA
```

### Ajouter de nouveaux types d'analyse IA
```python
# Ajouter dans la fonction analyze_with_anthropic()
"nouveau_type": f"Votre prompt personnalisé pour {author}..."
```

## 🐛 Dépannage

### Erreur "ANTHROPIC_API_KEY non trouvée"
- Vérifiez que le fichier `.env` existe
- Vérifiez que la clé API est correcte (commence par `sk-ant-`)

### Erreur de parsing WhatsApp
- Vérifiez le format du fichier `chat.txt`
- Assurez-vous d'avoir exporté "sans fichiers multimédias"
- Le format attendu : `8/23/23, 18:26 - Nom: Message`

### Problèmes de visualisation
- Installez les dépendances : `pip install matplotlib seaborn`
- Sur WSL/Linux : les images sont sauvegardées (pas d'affichage direct)

## 📄 Licence

MIT License - Utilisez librement pour vos analyses personnelles !

## 🤝 Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou proposez une pull request.

---

**⚠️ Important :** Ce projet est destiné à l'analyse de vos propres conversations. Respectez la vie privée et obtenez le consentement avant d'analyser les messages d'autres personnes.