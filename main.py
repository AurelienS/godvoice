import os
import re
from collections import defaultdict
from pathlib import Path
import textwrap
import pandas as pd  # Ajout de pandas
import matplotlib.pyplot as plt  # Ajout de matplotlib
import matplotlib.colors as mcolors  # Pour la normalisation non-linéaire
import tiktoken
import seaborn as sns  # Pour la heatmap

# Chargement des variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Fichier .env chargé")
except ImportError:
    print("⚠️  python-dotenv non installé. Installez avec: pip install python-dotenv")
    print("📝 Ou créez manuellement les variables d'environnement")

# === Config ===
INPUT_FILE = "chat.txt"
OUTPUT_DIR = "by_authors"  # Correction : c'est un dossier
CHUNK_CHAR_LIMIT = 3000  # Ancienne limite en caractères
CHUNK_TOKEN_LIMIT = 750  # Limite en tokens (configurable)
TOP_N = 10  # Nombre d'auteurs à afficher dans les graphes globaux

# === Utilitaire pour compter les tokens ===
def count_tokens(text):
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

# chat.txt format


# Regex pour détecter début de message WhatsApp
pattern = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) - ([^:]+): (.+)')

# Stockage des messages par auteur
user_messages = defaultdict(list)
# Stockage sous forme de liste pour pandas
all_messages = []

# === Étape 1 : Parse le fichier ===
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    current_author = None
    current_date = None
    current_time = None
    for line in f:
        line = line.strip()
        if not line:
            continue

        match = pattern.match(line)
        if match:
            date, time, author, message = match.groups()
            current_author = author
            current_date = date
            current_time = time
            user_messages[author].append(message)
            all_messages.append({
                'date': date,
                'time': time,
                'author': author,
                'message': message
            })
        elif current_author:
            # Ajoute la ligne au dernier message
            user_messages[current_author][-1] += " " + line
            # Ajoute aussi à la liste pour pandas
            if all_messages:
                all_messages[-1]['message'] += " " + line

# === Étape 2 : Crée les chunks et les fichiers ===
Path(OUTPUT_DIR).mkdir(exist_ok=True)

for author, messages in user_messages.items():
    author_dir = Path(OUTPUT_DIR) / author.replace(" ", "_")
    author_dir.mkdir(parents=True, exist_ok=True)

    # Découpage intelligent par tokens
    chunks = []
    current_chunk = []
    current_tokens = 0
    for msg in messages:
        msg_tokens = count_tokens(msg)
        if current_tokens + msg_tokens > CHUNK_TOKEN_LIMIT and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_tokens = 0
        current_chunk.append(msg)
        current_tokens += msg_tokens
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    for idx, chunk in enumerate(chunks, 1):
        filename = author_dir / f"chunk_{idx:03}.txt"
        with open(filename, "w", encoding="utf-8") as out:
            out.write(chunk)

print("✅ Chunks générés dans le dossier 'chunks/' (par tokens)")

# === Étape 3 : Statistiques de base avec pandas ===
df = pd.DataFrame(all_messages)
df['nb_mots'] = df['message'].apply(lambda x: len(x.split()))

# === Étape 3b : Ajout de la colonne 'hour' (heure du message) ===
def extract_hour(t):
    try:
        return int(str(t).split(':')[0])
    except Exception:
        return None

df['hour'] = df['time'].apply(extract_hour)

print("\n=== Statistiques par auteur (pandas) ===")
stats = df.groupby('author').agg(
    nb_messages=('message', 'count'),
    nb_mots=('nb_mots', 'sum'),
    moyenne_mots=('nb_mots', 'mean')
)
print(stats)

# === Création du dossier figures ===
FIGURES_DIR = "figures"
os.makedirs(FIGURES_DIR, exist_ok=True)

# === Étape 4 : Graphique du nombre de messages par auteur (top N) ===
top_authors = stats['nb_messages'].sort_values(ascending=False).head(TOP_N)
plt.figure(figsize=(10, 6))
top_authors.plot(kind='bar')
plt.title(f'Top {TOP_N} - Nombre de messages par auteur')
plt.xlabel('Auteur')
plt.ylabel('Nombre de messages')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'messages_par_auteur_top.png'))
plt.close()

# === Participation dans le temps (par jour, top N auteurs) ===
df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y', errors='coerce')
daily_counts = df.groupby(['date', 'author']).size().unstack(fill_value=0)
top_authors_list = top_authors.index.tolist()
daily_counts_top = daily_counts[top_authors_list]
plt.figure(figsize=(14, 6))
daily_counts_top.plot(ax=plt.gca())
plt.title(f'Top {TOP_N} - Participation quotidienne par auteur')
plt.xlabel('Date')
plt.ylabel('Nombre de messages')
plt.legend(title='Auteur', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'participation_quotidienne_top.png'))
plt.close()

# === Répartition horaire (par heure, top N auteurs) ===
# On retire les messages sans heure valide
hourly_df = df.dropna(subset=['hour'])
hourly_counts = hourly_df.groupby(['hour', 'author']).size().unstack(fill_value=0)
hourly_counts_top = hourly_counts[top_authors_list]
plt.figure(figsize=(14, 6))
hourly_counts_top.plot(ax=plt.gca())
plt.title(f'Top {TOP_N} - Répartition horaire des messages par auteur')
plt.xlabel('Heure de la journée')
plt.ylabel('Nombre de messages')
plt.legend(title='Auteur', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'repartition_horaire_top.png'))
plt.close()

# === Pourcentage de participation (camembert, top N) ===
plt.figure(figsize=(8, 8))
top_authors.plot(kind='pie', autopct='%1.1f%%', startangle=90, colormap='tab20')
plt.title(f'Top {TOP_N} - Pourcentage de participation par auteur')
plt.ylabel('')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'pourcentage_participation_top.png'))
plt.close()

# === Heatmap de participation à l'année (type GitHub, globale, carrés) ===
# S'assurer que la colonne date est bien datetime
heatmap_dates = df['date']  # Déjà convertie plus haut
valid_heatmap_mask = ~heatmap_dates.isna()
heatmap_days = heatmap_dates[valid_heatmap_mask].dt.date
# Compter le nombre de messages par jour (pas juste 1)
heatmap_data = df[valid_heatmap_mask].groupby(heatmap_days).size()
heatmap_df = heatmap_data.reindex(pd.date_range(heatmap_days.min(), heatmap_days.max()), fill_value=0)
heatmap_df.index = pd.to_datetime(heatmap_df.index)
heatmap_matrix = heatmap_df.groupby([
    heatmap_df.index.year,
    heatmap_df.index.isocalendar().week,
    heatmap_df.index.weekday
]).sum().unstack(fill_value=0)
heatmap_matrix = heatmap_matrix.T
plt.figure(figsize=(20, 6))
# Calculer vmax basé sur les vraies données (95e percentile pour éviter les outliers)
global_values = heatmap_matrix.values.flatten()
global_values_nonzero = global_values[global_values > 0]
if len(global_values_nonzero) > 0:
    global_vmax = int(global_values_nonzero.quantile(0.95)) if hasattr(global_values_nonzero, 'quantile') else int(pd.Series(global_values_nonzero).quantile(0.95))
else:
    global_vmax = 10
# Normalisation non-linéaire pour étaler les petites valeurs (racine carrée)
norm = mcolors.PowerNorm(gamma=0.5, vmin=0, vmax=global_vmax)
sns.heatmap(heatmap_matrix, cmap='YlGn', cbar=True, linewidths=0.5, square=True, norm=norm)
plt.title(f'Heatmap de participation par jour (global, échelle non-linéaire: 0-{global_vmax})')
plt.xlabel('Semaine de l\'année')
plt.ylabel('Jour de la semaine (0=lundi)')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'heatmap_github_global.png'))
plt.close()

# === Heatmap par personne ===
HEATMAPS_DIR = os.path.join(FIGURES_DIR, 'heatmaps_par_auteur')
os.makedirs(HEATMAPS_DIR, exist_ok=True)
for author in stats.index:
    author_df = df[df['author'] == author]
    author_dates = author_df['date'].dropna()
    author_days = author_dates.dt.date
    # Compter le nombre de messages par jour pour cet auteur
    author_heatmap_data = author_df.dropna(subset=['date']).groupby(author_days).size()
    author_heatmap_df = author_heatmap_data.reindex(pd.date_range(heatmap_days.min(), heatmap_days.max()), fill_value=0)
    author_heatmap_df.index = pd.to_datetime(author_heatmap_df.index)
    author_heatmap_matrix = author_heatmap_df.groupby([
        author_heatmap_df.index.year,
        author_heatmap_df.index.isocalendar().week,
        author_heatmap_df.index.weekday
    ]).sum().unstack(fill_value=0)
    author_heatmap_matrix = author_heatmap_matrix.T
    plt.figure(figsize=(20, 6))
    # Calculer vmax basé sur les données de cet auteur (95e percentile)
    author_values = author_heatmap_matrix.values.flatten()
    author_values_nonzero = author_values[author_values > 0]
    if len(author_values_nonzero) > 0:
        author_vmax = int(pd.Series(author_values_nonzero).quantile(0.95))
        author_vmax = max(5, author_vmax)  # Minimum de 5 pour avoir un dégradé visible
    else:
        author_vmax = 5
    # Normalisation non-linéaire pour cet auteur aussi
    author_norm = mcolors.PowerNorm(gamma=0.5, vmin=0, vmax=author_vmax)
    sns.heatmap(author_heatmap_matrix, cmap='YlGn', cbar=True, linewidths=0.5, square=True, norm=author_norm)
    plt.title(f'Heatmap de participation pour {author} (échelle non-linéaire: 0-{author_vmax})')
    plt.xlabel('Semaine de l\'année')
    plt.ylabel('Jour de la semaine (0=lundi)')
    plt.tight_layout()
    safe_author = str(author).replace('/', '_').replace(' ', '_')
    plt.savefig(os.path.join(HEATMAPS_DIR, f'heatmap_{safe_author}.png'))
    plt.close()

# === Stats rigolos supplémentaires ===
print("\n=== Stats rigolos ===")

# 1. Distribution du nombre de mots par message (histogramme)
plt.figure(figsize=(12, 6))
df['nb_mots'].hist(bins=50, alpha=0.7, edgecolor='black')
plt.title('Distribution du nombre de mots par message')
plt.xlabel('Nombre de mots par message')
plt.ylabel('Fréquence')
plt.axvline(df['nb_mots'].mean(), color='red', linestyle='--', label=f'Moyenne: {df["nb_mots"].mean():.1f}')
plt.axvline(df['nb_mots'].median(), color='orange', linestyle='--', label=f'Médiane: {df["nb_mots"].median():.1f}')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'distribution_mots_par_message.png'))
plt.close()

# 2. Scatter plot : Mots/message vs Nombre de messages (style de communication)
plt.figure(figsize=(12, 8))
for author in top_authors_list:
    author_data = df[df['author'] == author]
    avg_words = author_data['nb_mots'].mean()
    msg_count = len(author_data)
    plt.scatter(msg_count, avg_words, s=100, alpha=0.7, label=author)
    plt.annotate(author, (msg_count, avg_words), xytext=(5, 5), textcoords='offset points', fontsize=8)

plt.xlabel('Nombre total de messages')
plt.ylabel('Moyenne de mots par message')
plt.title('Style de communication : Bavard vs Prolixe')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'style_communication.png'))
plt.close()

# 3. Analyse messages courts vs longs
df['type_message'] = df['nb_mots'].apply(lambda x: 'Court (1-3 mots)' if x <= 3
                                        else 'Moyen (4-10 mots)' if x <= 10
                                        else 'Long (11+ mots)')
message_types = df.groupby(['author', 'type_message']).size().unstack(fill_value=0)
message_types_top = message_types.loc[top_authors_list]

plt.figure(figsize=(14, 8))
message_types_top.plot(kind='bar', stacked=True, ax=plt.gca())
plt.title('Répartition des types de messages par auteur')
plt.xlabel('Auteur')
plt.ylabel('Nombre de messages')
plt.xticks(rotation=45, ha='right')
plt.legend(title='Type de message')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'types_messages.png'))
plt.close()

# 4. Analyse des heures de pointe par auteur (top 3)
top_3_authors = top_authors.head(3).index.tolist()
hourly_top3 = hourly_df[hourly_df['author'].isin(top_3_authors)]
hourly_activity = hourly_top3.groupby(['hour', 'author']).size().unstack(fill_value=0)

plt.figure(figsize=(14, 6))
hourly_activity.plot(kind='area', stacked=False, alpha=0.7, ax=plt.gca())
plt.title('Activité horaire des 3 auteurs les plus actifs')
plt.xlabel('Heure de la journée')
plt.ylabel('Nombre de messages')
plt.legend(title='Auteur')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'activite_horaire_top3.png'))
plt.close()

# 5. Analyse des médias et emojis
df['contient_media'] = df['message'].str.contains('<Media omitted>', na=False)
df['contient_emoji'] = df['message'].str.contains('😀|😁|😂|😃|😄|😅|😆|😇|😈|😉|😊|😋|😌|😍|😎|😏|😐|😑|😒|😓|😔|😕|😖|😗|😘|😙|😚|😛|😜|😝|😞|😟|😠|😡|😢|😣|😤|😥|😦|😧|😨|😩|😪|😫|😬|😭|😮|😯|😰|😱|😲|😳|😴|😵|😶|😷|😸|😹|😺|😻|😼|😽|😾|😿|🙀|🙁|🙂|🙃|🙄|🤐|🤑|🤒|🤓|🤔|🤕|🤖|🤗|🤘|🤙|🤚|🤛|🤜|🤝|🤞|🤟|🤠|🤡|🤢|🤣|🤤|🤥|🤦|🤧|🤨|🤩|🤪|🤫|🤬|🤭|🤮|🤯|🤰|🤱|🤲|🤳|🤴|🤵|🤶|🤷|🤸|🤹|🤺|🤻|🤼|🤽|🤾|🤿|🥀|🥁|🥂|🥃|🥄|🥅|🥆|🥇|🥈|🥉|🥊|🥋|🥌|🥍|🥎|🥏|🥐|🥑|🥒|🥓|🥔|🥕|🥖|🥗|🥘|🥙|🥚|🥛|🥜|🥝|🥞|🥟|🥠|🥡|🥢|🥣|🥤|🥥|🥦|🥧|🥨|🥩|🥪|🥫|🥬|🥭|🥮|🥯|🥰|🥱|🥲|🥳|🥴|🥵|🥶|🥷|🥸|🥹|🥺|🥻|🥼|🥽|🥾|🥿|🦀|🦁|🦂|🦃|🦄|🦅|🦆|🦇|🦈|🦉|🦊|🦋|🦌|🦍|🦎|🦏|🦐|🦑|🦒|🦓|🦔|🦕|🦖|🦗|🦘|🦙|🦚|🦛|🦜|🦝|🦞|🦟|🦠|🦡|🦢|🦣|🦤|🦥|🦦|🦧|🦨|🦩|🦪|🦫|🦬|🦭|🦮|🦯|🦰|🦱|🦲|🦳|🦴|🦵|🦶|🦷|🦸|🦹|🦺|🦻|🦼|🦽|🦾|🦿|🧀|🧁|🧂|🧃|🧄|🧅|🧆|🧇|🧈|🧉|🧊|🧋|🧌|🧍|🧎|🧏|🧐|🧑|🧒|🧓|🧔|🧕|🧖|🧗|🧘|🧙|🧚|🧛|🧜|🧝|🧞|🧟|🧠|🧡|🧢|🧣|🧤|🧥|🧦|🧧|🧨|🧩|🧪|🧫|🧬|🧭|🧮|🧯|🧰|🧱|🧲|🧳|🧴|🧵|🧶|🧷|🧸|🧹|🧺|🧻|🧼|🧽|🧾|🧿|🩀|🩁|🩂|🩃|🩄|🩅|🩆|🩇|🩈|🩉|🩊|🩋|🩌|🩍|🩎|🩏|🩐|🩑|🩒|🩓|🩔|🩕|🩖|🩗|🩘|🩙|🩚|🩛|🩜|🩝|🩞|🩟|🩠|🩡|🩢|🩣|🩤|🩥|🩦|🩧|🩨|🩩|🩪|🩫|🩬|🩭|🩮|🩯|🩰|🩱|🩲|🩳|🩴|🩵|🩶|🩷|🩸|🩹|🩺|🩻|🩼|🪀|🪁|🪂|🪃|🪄|🪅|🪆|🪇|🪈|🪉|🪊|🪋|🪌|🪍|🪎|🪏|🪐|🪑|🪒|🪓|🪔|🪕|🪖|🪗|🪘|🪙|🪚|🪛|🪜|🪝|🪞|🪟|🪠|🪡|🪢|🪣|🪤|🪥|🪦|🪧|🪨|🪩|🪪|🪫|🪬|🪭|🪮|🪯|🪰|🪱|🪲|🪳|🪴|🪵|🪶|🪷|🪸|🪹|🪺|🪻|🪼|🪽|🪾|🪿|🫀|🫁|🫂|🫃|🫄|🫅|🫆|🫇|🫈|🫉|🫊|🫋|🫌|🫍|🫎|🫏|🫐|🫑|🫒|🫓|🫔|🫕|🫖|🫗|🫘|🫙|🫚|🫛|🫜|🫝|🫞|🫟|🫠|🫡|🫢|🫣|🫤|🫥|🫦|🫧|🫨|🫩|🫪|🫫|🫬|🫭|🫮|🫯|🫰|🫱|🫲|🫳|🫴|🫵|🫶|🫷|🫸|🫹|🫺|🫻|🫼|🫽|🫾|🫿', na=False)

media_emoji_stats = df.groupby('author').agg(
    total_messages=('message', 'count'),
    messages_avec_media=('contient_media', 'sum'),
    messages_avec_emoji=('contient_emoji', 'sum')
).reset_index()
media_emoji_stats['pct_media'] = (media_emoji_stats['messages_avec_media'] / media_emoji_stats['total_messages'] * 100).round(1)
media_emoji_stats['pct_emoji'] = (media_emoji_stats['messages_avec_emoji'] / media_emoji_stats['total_messages'] * 100).round(1)

# Graphique des pourcentages médias/emojis pour le top 10
media_emoji_top = media_emoji_stats[media_emoji_stats['author'].isin(top_authors_list)]
plt.figure(figsize=(14, 6))
x = range(len(media_emoji_top))
width = 0.35
plt.bar([i - width/2 for i in x], media_emoji_top['pct_media'], width, label='% Messages avec média', alpha=0.8)
plt.bar([i + width/2 for i in x], media_emoji_top['pct_emoji'], width, label='% Messages avec emoji', alpha=0.8)
plt.xlabel('Auteur')
plt.ylabel('Pourcentage (%)')
plt.title('Usage des médias et emojis par auteur')
plt.xticks(x, media_emoji_top['author'], rotation=45, ha='right')
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, 'medias_emojis.png'))
plt.close()

print("✅ Graphiques rigolos générés !")

# === Analyse IA du contenu ===
print("\n=== Préparation de l'analyse IA ===")

try:
    from anthropic import Anthropic
    HAS_AI_LIBS = True
except ImportError:
    print("⚠️  Librairie Anthropic non installée. Installez avec: pip install anthropic")
    HAS_AI_LIBS = False

if HAS_AI_LIBS:
    # Configuration de l'API key Anthropic (depuis le fichier .env)
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

    if anthropic_api_key:
        anthropic_client = Anthropic(api_key=anthropic_api_key)
        print("✅ Anthropic configuré (Claude Sonnet 3.5)")
    else:
        print("⚠️  ANTHROPIC_API_KEY non trouvée dans le fichier .env")

    # Fonction d'analyse avec Anthropic (Claude Sonnet 3.5 - QUALITÉ PREMIUM 🏆)
    def analyze_with_anthropic(text, author, analysis_type="general", model_name="sonnet"):
        if not anthropic_api_key:
            return None

        prompts = {
            "sentiment": f"Analyse le sentiment de {author}. Score 1-10 (1=négatif, 10=positif) + analyse détaillée des émotions dominantes et nuances psychologiques.",
            "topics": f"Top 5 sujets principaux de {author}. Pour chaque sujet: titre, fréquence, contexte, et exemples de messages représentatifs.",
            "style": f"Style de communication de {author}: personnalité détaillée, registre de langue, tics linguistiques, expressions favorites, évolution dans le temps.",
            "summary": f"Portrait complet de {author}: personnalité, rôle dans le groupe, relations avec les autres, évolution, anecdotes marquantes.",
            "political": f"🌶️ ANALYSE POLITIQUE APPROFONDIE de {author}: Orientation politique (gauche/droite/centre), positions sur immigration, économie, écologie, société. Cite des messages précis révélateurs de ses convictions.",
            "controversial": f"🔥 CONTENU CLIVANT ET POLÉMIQUE de {author}: Débats houleux, prises de position controversées, conflits, sujets sensibles. Analyse le niveau de provocation et cite les messages les plus épicés.",
            "humor": f"😂 ANALYSE HUMOUR COMPLÈTE de {author}: Type d'humour (noir, absurde, sarcastique, potache), niveau de politiquement incorrect, meilleures vannes, réactions du groupe à ses blagues.",
            "secrets": f"🕵️ RÉVÉLATIONS ET RAGOTS de {author}: Confessions personnelles, secrets révélés, anecdotes croustillantes, indiscretions, vie privée dévoilée dans le groupe."
        }

        # Choix du modèle selon la qualité demandée
        model_configs = {
            "haiku": {"model": "claude-3-5-haiku-20241022", "max_tokens": 400, "max_chars": 8000},
            "sonnet": {"model": "claude-3-5-sonnet-20241022", "max_tokens": 800, "max_chars": 15000},  # QUALITÉ PREMIUM
            "opus": {"model": "claude-3-opus-20240229", "max_tokens": 1000, "max_chars": 20000}
        }

        config = model_configs.get(model_name, model_configs["sonnet"])

        try:
            response = anthropic_client.messages.create(
                model=config["model"],
                max_tokens=config["max_tokens"],
                messages=[
                    {"role": "user", "content": f"{prompts.get(analysis_type, prompts['summary'])}\n\nMessages de {author}:\n{text[:config['max_chars']]}"}
                ]
            )
            return response.content[0].text
        except Exception as e:
            print(f"Erreur Anthropic pour {author}: {e}")
            return None

    # Fonction principale d'analyse IA (QUALITÉ PREMIUM 🏆)
    def run_ai_analysis():
        if not anthropic_api_key:
            print("❌ ANTHROPIC_API_KEY non configurée. Analyse IA ignorée.")
            return

        print("🏆 QUALITÉ PREMIUM ACTIVÉE - Claude Sonnet 3.5")
        print("🔥 Analyse approfondie du contenu politique, clivant et croustillant")
        print("📊 Analyse du TOP 10 des participants avec TOUTE leur data")

        # Créer le dossier de résultats IA
        AI_RESULTS_DIR = os.path.join(FIGURES_DIR, 'analyses_ia')
        os.makedirs(AI_RESULTS_DIR, exist_ok=True)

        # Configuration des modèles disponibles
        models_to_test = [
            {"name": "sonnet", "display": "Claude Sonnet 3.5", "emoji": "🏆"},
            # {"name": "haiku", "display": "Claude Haiku 3.5", "emoji": "⚡"},  # Optionnel pour comparaison
        ]

        for model_config in models_to_test:
            model_name = model_config["name"]
            model_display = model_config["display"]
            model_emoji = model_config["emoji"]

            print(f"\n{model_emoji} === ANALYSE AVEC {model_display.upper()} ===")

            # Analyser le TOP 10 des auteurs
            for author in top_authors.head(10).index:
                print(f"🔍 Analyse COMPLÈTE de {author} avec {model_display}...")

                # Lire les chunks de cet auteur
                author_dir = Path(OUTPUT_DIR) / author.replace(" ", "_")
                if not author_dir.exists():
                    continue

                # Combiner TOUS les chunks de cet auteur
                author_text = ""
                chunk_files = sorted(author_dir.glob("chunk_*.txt"))
                for chunk_file in chunk_files:
                    with open(chunk_file, 'r', encoding='utf-8') as f:
                        chunk_content = f.read()
                        author_text += chunk_content + "\n"

                if len(author_text.strip()) == 0:
                    continue

                print(f"  📝 {len(author_text)} caractères analysés pour {author}")

                # Analyses COMPLÈTES avec tous les types
                analyses = {}
                analysis_types = ["sentiment", "topics", "style", "summary", "political", "controversial", "humor", "secrets"]

                for analysis_type in analysis_types:
                    print(f"  🔍 {analysis_type}...")
                    result = analyze_with_anthropic(author_text, author, analysis_type, model_name)
                    if result:
                        analyses[analysis_type] = result

                # Sauvegarder les résultats avec le nom du modèle
                if analyses:
                    safe_author = author.replace(' ', '_').replace('.', '_')
                    filename = f"{safe_author}_{model_name}_PREMIUM_analysis.txt"

                    with open(os.path.join(AI_RESULTS_DIR, filename), 'w', encoding='utf-8') as f:
                        f.write(f"{model_emoji} === ANALYSE PREMIUM de {author} ({model_display}) ===\n\n")
                        f.write(f"📊 Données analysées: {len(author_text):,} caractères\n")
                        f.write(f"📁 Chunks traités: {len(chunk_files)}\n")
                        f.write(f"🤖 Modèle utilisé: {model_display}\n\n")

                        for analysis_type, result in analyses.items():
                            emoji_map = {
                                "sentiment": "😊", "topics": "📋", "style": "✍️", "summary": "📝",
                                "political": "🏛️", "controversial": "🔥", "humor": "😂", "secrets": "🕵️"
                            }
                            emoji = emoji_map.get(analysis_type, "📌")
                            f.write(f"{emoji} ## {analysis_type.upper()}\n{result}\n\n")

        print("✅ Analyse PREMIUM terminée ! Résultats dans figures/analyses_ia/")
        print("🏆 Qualité supérieure avec Claude Sonnet 3.5")
        print("🌶️ Contenu politique, clivant et croustillant détecté en détail !")
        print("💰 Coût estimé: ~$1-2 (analyse premium TOP 10)")

    # Lancer l'analyse IA automatiquement si configurée
    if anthropic_api_key and len(anthropic_api_key) > 20:  # Clé API valide (plus de 20 caractères)
        run_ai_analysis()
    else:
        print("\n🤖 Pour lancer l'analyse IA, configurez votre API key dans le fichier .env")
        print("Éditez .env et remplacez:")
        print("ANTHROPIC_API_KEY=your-anthropic-api-key-here")
        print("par votre vraie clé API Anthropic")

else:
    print("📦 Installez la librairie IA avec: pip install anthropic python-dotenv")
