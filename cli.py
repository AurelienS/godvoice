#!/usr/bin/env python3
"""
GodVoice CLI - Analyseur de conversations WhatsApp
Usage: godvoice --chat-file chat.txt --anthropic-key sk-ant-...
"""

import click
import os
import sys
import subprocess
from pathlib import Path

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

    # Vérifier que le fichier main.py existe
    main_py_path = Path(__file__).parent / "main.py"
    if not main_py_path.exists():
        click.echo("❌ Erreur: main.py non trouvé dans le même dossier que le CLI", err=True)
        sys.exit(1)

    # Préparer les variables d'environnement
    env = os.environ.copy()
    if anthropic_key:
        env['ANTHROPIC_API_KEY'] = anthropic_key

    # Créer un fichier .env temporaire pour main.py
    env_content = f"ANTHROPIC_API_KEY={anthropic_key or ''}\n"
    with open('.env', 'w') as f:
        f.write(env_content)

    try:
        # Modifier temporairement main.py pour utiliser nos paramètres
        with open(main_py_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Remplacer les constantes dans main.py
        modified_content = original_content.replace(
            'INPUT_FILE = "chat.txt"',
            f'INPUT_FILE = "{chat_file}"'
        ).replace(
            'OUTPUT_DIR = "by_authors"',
            f'OUTPUT_DIR = "{output_dir}"'
        ).replace(
            'CHUNK_TOKEN_LIMIT = 750',
            f'CHUNK_TOKEN_LIMIT = {chunk_tokens}'
        ).replace(
            'TOP_N = 10',
            f'TOP_N = {top}'
        ).replace(
            'FIGURES_DIR = "figures"',
            f'FIGURES_DIR = "{figures_dir}"'
        )

        # Si --no-ai, désactiver l'analyse IA dans main.py
        if no_ai:
            modified_content = modified_content.replace(
                'if anthropic_api_key and len(anthropic_api_key) > 20:',
                'if False:  # Analyse IA désactivée par --no-ai'
            )

        # Écrire le fichier modifié temporairement
        temp_main_path = Path(__file__).parent / "main_temp.py"
        with open(temp_main_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        if verbose:
            click.echo("🚀 Lancement de l'analyse...")

        # Exécuter main.py modifié
        result = subprocess.run([
            sys.executable, str(temp_main_path)
        ], env=env, capture_output=not verbose, text=True)

        if result.returncode == 0:
            click.echo("✅ Analyse terminée avec succès!")
            click.echo(f"📊 Résultats dans: {output_dir}/")
            click.echo(f"📈 Graphiques dans: {figures_dir}/")
            if not no_ai and anthropic_key:
                click.echo(f"🤖 Analyses IA dans: {figures_dir}/analyses_ia/")
        else:
            click.echo("❌ Erreur lors de l'analyse:", err=True)
            if result.stderr:
                click.echo(result.stderr, err=True)
            if result.stdout:
                click.echo(result.stdout, err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Erreur inattendue: {e}", err=True)
        sys.exit(1)

    finally:
        # Nettoyer les fichiers temporaires
        try:
            if Path('.env').exists():
                os.remove('.env')
            if Path('main_temp.py').exists():
                os.remove('main_temp.py')
        except:
            pass

@click.command()
def version():
    """Affiche la version de GodVoice CLI"""
    click.echo("GodVoice CLI v1.0.0")
    click.echo("Analyseur de conversations WhatsApp avec IA")

if __name__ == '__main__':
    main()
