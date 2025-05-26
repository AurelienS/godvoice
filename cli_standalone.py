#!/usr/bin/env python3
"""
GodVoice CLI - Analyseur de conversations WhatsApp (Version autonome)
Usage: godvoice --chat-file chat.txt --anthropic-key sk-ant-...
"""

import click
import os
import sys
import re
from collections import defaultdict
from pathlib import Path
import pandas as pd

# Configuration matplotlib pour l'exécutable
import matplotlib
matplotlib.use('Agg')  # Backend non-interactif pour l'exécutable
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import tiktoken
import seaborn as sns

# === Utilitaires ===
def count_tokens(text):
    """Compte les tokens dans un texte"""
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception as e:
        # Fallback: estimation approximative basée sur les mots
        # Approximation: 1 token ≈ 0.75 mots en français/anglais
        word_count = len(text.split())
        estimated_tokens = int(word_count / 0.75)
        if hasattr(click, 'echo'):
            click.echo(f"⚠️  Tiktoken non disponible, estimation approximative: {estimated_tokens} tokens")
        return estimated_tokens

def extract_hour(t):
    """Extrait l'heure d'un timestamp"""
    try:
        return int(str(t).split(':')[0])
    except Exception:
        return None

def parse_whatsapp_chat(chat_file):
    """Parse le fichier de chat WhatsApp"""
    click.echo(f"📱 Parsing du fichier: {chat_file}")

    # Regex pour détecter début de message WhatsApp
    pattern = re.compile(r'^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2}) - ([^:]+): (.+)')

    # Stockage des messages par auteur
    user_messages = defaultdict(list)
    # Stockage sous forme de liste pour pandas
    all_messages = []

    with open(chat_file, "r", encoding="utf-8") as f:
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

    click.echo(f"✅ {len(all_messages)} messages parsés de {len(user_messages)} auteurs")
    return user_messages, all_messages

def create_chunks(user_messages, output_dir="by_authors", chunk_token_limit=750):
    """Crée les chunks par auteur"""
    click.echo(f"📁 Création des chunks dans {output_dir}/")

    Path(output_dir).mkdir(exist_ok=True)

    for author, messages in user_messages.items():
        author_dir = Path(output_dir) / author.replace(" ", "_")
        author_dir.mkdir(parents=True, exist_ok=True)

        # Découpage intelligent par tokens
        chunks = []
        current_chunk = []
        current_tokens = 0
        for msg in messages:
            msg_tokens = count_tokens(msg)
            if current_tokens + msg_tokens > chunk_token_limit and current_chunk:
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

    click.echo("✅ Chunks générés")

def generate_statistics(all_messages, figures_dir="figures", top_n=10):
    """Génère les statistiques et graphiques"""
    click.echo(f"📊 Génération des statistiques (top {top_n})")

    # Création du DataFrame
    df = pd.DataFrame(all_messages)
    df['nb_mots'] = df['message'].apply(lambda x: len(x.split()))
    df['hour'] = df['time'].apply(extract_hour)

    # Statistiques par auteur
    stats = df.groupby('author').agg(
        nb_messages=('message', 'count'),
        nb_mots=('nb_mots', 'sum'),
        moyenne_mots=('nb_mots', 'mean')
    )

    click.echo("\n=== Statistiques par auteur ===")
    click.echo(stats.sort_values('nb_messages', ascending=False).head(top_n).to_string())

    # Création du dossier figures
    os.makedirs(figures_dir, exist_ok=True)

    # Top auteurs
    top_authors = stats['nb_messages'].sort_values(ascending=False).head(top_n)

    try:
        # Graphique du nombre de messages par auteur
        plt.figure(figsize=(10, 6))
        top_authors.plot(kind='bar')
        plt.title(f'Top {top_n} - Nombre de messages par auteur')
        plt.xlabel('Auteur')
        plt.ylabel('Nombre de messages')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, 'messages_par_auteur_top.png'))
        plt.close()

        # Participation dans le temps
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%y', errors='coerce')
        daily_counts = df.groupby(['date', 'author']).size().unstack(fill_value=0)
        top_authors_list = top_authors.index.tolist()
        daily_counts_top = daily_counts[top_authors_list]
        plt.figure(figsize=(14, 6))
        daily_counts_top.plot(ax=plt.gca())
        plt.title(f'Top {top_n} - Participation quotidienne par auteur')
        plt.xlabel('Date')
        plt.ylabel('Nombre de messages')
        plt.legend(title='Auteur', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, 'participation_quotidienne_top.png'))
        plt.close()

        # Répartition horaire
        hourly_df = df.dropna(subset=['hour'])
        hourly_counts = hourly_df.groupby(['hour', 'author']).size().unstack(fill_value=0)
        hourly_counts_top = hourly_counts[top_authors_list]
        plt.figure(figsize=(14, 6))
        hourly_counts_top.plot(ax=plt.gca())
        plt.title(f'Top {top_n} - Répartition horaire des messages par auteur')
        plt.xlabel('Heure de la journée')
        plt.ylabel('Nombre de messages')
        plt.legend(title='Auteur', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, 'repartition_horaire_top.png'))
        plt.close()

        # Pourcentage de participation (camembert)
        plt.figure(figsize=(8, 8))
        top_authors.plot(kind='pie', autopct='%1.1f%%', startangle=90, colormap='tab20')
        plt.title(f'Top {top_n} - Pourcentage de participation par auteur')
        plt.ylabel('')
        plt.tight_layout()
        plt.savefig(os.path.join(figures_dir, 'pourcentage_participation_top.png'))
        plt.close()

        click.echo("✅ Graphiques générés")
    except Exception as e:
        click.echo(f"⚠️  Erreur lors de la génération des graphiques: {e}")
        click.echo("📊 Statistiques générées sans graphiques")

    return df, stats, top_authors

def run_ai_analysis(user_messages, top_authors, anthropic_key, figures_dir="figures", output_dir="by_authors"):
    """Lance l'analyse IA avec Anthropic"""
    click.echo("🤖 Démarrage de l'analyse IA...")

    try:
        from anthropic import Anthropic
    except ImportError:
        click.echo("❌ Librairie Anthropic non disponible")
        return

    if not anthropic_key:
        click.echo("❌ Clé Anthropic manquante")
        return

    anthropic_client = Anthropic(api_key=anthropic_key)
    click.echo("✅ Anthropic configuré (Claude Sonnet 3.5)")

    # Créer le dossier de résultats IA
    ai_results_dir = os.path.join(figures_dir, 'analyses_ia')
    os.makedirs(ai_results_dir, exist_ok=True)

    def analyze_with_anthropic(text, author, analysis_type="general"):
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

        try:
            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[
                    {"role": "user", "content": f"{prompts.get(analysis_type, prompts['summary'])}\n\nMessages de {author}:\n{text[:15000]}"}
                ]
            )
            return response.content[0].text
        except Exception as e:
            click.echo(f"Erreur Anthropic pour {author}: {e}")
            return None

    # Analyser le TOP des auteurs
    for author in top_authors.head(10).index:
        click.echo(f"🔍 Analyse de {author}...")

        # Lire les chunks de cet auteur
        author_dir = Path(output_dir) / author.replace(" ", "_")
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

        click.echo(f"  📝 {len(author_text)} caractères analysés pour {author}")

        # Analyses COMPLÈTES
        analyses = {}
        analysis_types = ["sentiment", "topics", "style", "summary", "political", "controversial", "humor", "secrets"]

        for analysis_type in analysis_types:
            click.echo(f"  🔍 {analysis_type}...")
            result = analyze_with_anthropic(author_text, author, analysis_type)
            if result:
                analyses[analysis_type] = result

        # Sauvegarder les résultats
        if analyses:
            safe_author = author.replace(' ', '_').replace('.', '_')
            filename = f"{safe_author}_PREMIUM_analysis.txt"

            with open(os.path.join(ai_results_dir, filename), 'w', encoding='utf-8') as f:
                f.write(f"🏆 === ANALYSE PREMIUM de {author} ===\n\n")
                f.write(f"📊 Données analysées: {len(author_text):,} caractères\n")
                f.write(f"📁 Chunks traités: {len(chunk_files)}\n")
                f.write(f"🤖 Modèle utilisé: Claude Sonnet 3.5\n\n")

                for analysis_type, result in analyses.items():
                    emoji_map = {
                        "sentiment": "😊", "topics": "📋", "style": "✍️", "summary": "📝",
                        "political": "🏛️", "controversial": "🔥", "humor": "😂", "secrets": "🕵️"
                    }
                    emoji = emoji_map.get(analysis_type, "📌")
                    f.write(f"{emoji} ## {analysis_type.upper()}\n{result}\n\n")

    click.echo("✅ Analyse IA terminée ! Résultats dans figures/analyses_ia/")

@click.command()
@click.option('--chat-file', '-c',
              required=True,
              type=click.Path(exists=True, readable=True),
              help='Chemin vers le fichier chat.txt à analyser')
@click.option('--anthropic-key', '-k',
              help='Clé API Anthropic (sk-ant-...)')
@click.option('--output-dir', '-o',
              default='by_authors',
              help='Dossier de sortie pour les chunks (défaut: by_authors)')
@click.option('--figures-dir', '-f',
              default='figures',
              help='Dossier de sortie pour les graphiques (défaut: figures)')
@click.option('--chunk-tokens',
              default=750,
              type=int,
              help='Limite de tokens par chunk (défaut: 750)')
@click.option('--top', '-t',
              default=10,
              type=int,
              help='Nombre d\'auteurs à afficher dans les graphiques (défaut: 10)')
@click.option('--no-ai',
              is_flag=True,
              help='Désactiver l\'analyse IA (seulement statistiques)')
@click.option('--verbose', '-v',
              is_flag=True,
              help='Mode verbeux')
def main(chat_file, anthropic_key, output_dir, figures_dir, chunk_tokens, top, no_ai, verbose):
    """
    🎤 GodVoice - Analyseur de conversations WhatsApp avec IA

    Analyse les conversations WhatsApp, génère des statistiques et des analyses IA.
    """

    if verbose:
        click.echo("🎤 GodVoice CLI - Démarrage de l'analyse...")
        click.echo(f"📁 Fichier chat: {chat_file}")
        click.echo(f"🤖 API Anthropic: {'✅ Configurée' if anthropic_key else '❌ Manquante'}")

    # Vérifications
    if not no_ai and not anthropic_key:
        click.echo("⚠️  Clé Anthropic non fournie. Analyse IA désactivée.")
        click.echo("   Utilisez --anthropic-key ou --no-ai pour supprimer cet avertissement.")
        no_ai = True

    click.echo("🚀 GodVoice CLI - Analyseur de conversations WhatsApp")
    click.echo(f"📱 Fichier de chat: {chat_file}")
    click.echo(f"📁 Dossier de sortie: {output_dir}")
    click.echo(f"📊 Top auteurs: {top}")
    click.echo(f"🤖 Analyse IA: {'Activée' if not no_ai else 'Désactivée'}")
    click.echo()

    try:
        # Étape 1: Parse le chat
        user_messages, all_messages = parse_whatsapp_chat(chat_file)

        # Étape 2: Crée les chunks
        create_chunks(user_messages, output_dir, chunk_tokens)

        # Étape 3: Génère les statistiques
        df, stats, top_authors = generate_statistics(all_messages, figures_dir, top)

        # Étape 4: Analyse IA (si activée)
        if not no_ai and anthropic_key:
            run_ai_analysis(user_messages, top_authors, anthropic_key, figures_dir, output_dir)

        click.echo("\n🎉 Analyse terminée avec succès !")
        click.echo(f"📁 Chunks: {output_dir}/")
        click.echo(f"📊 Graphiques: {figures_dir}/")
        if not no_ai and anthropic_key:
            click.echo(f"🤖 Analyses IA: {figures_dir}/analyses_ia/")

    except KeyboardInterrupt:
        click.echo("\n⚠️  Analyse interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Erreur: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()