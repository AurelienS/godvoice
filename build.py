#!/usr/bin/env python3
"""
Script de build pour créer l'exécutable GodVoice CLI cross-platform
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description):
    """Exécute une commande et affiche le résultat"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erreur:")
        print(e.stderr)
        return False

def build_executable(target_platform=None):
    """Build l'exécutable pour une plateforme donnée"""

    # Déterminer le nom de l'exécutable selon la plateforme
    if target_platform:
        system, arch = target_platform.split('-')
    else:
        system = platform.system().lower()
        arch = platform.machine().lower()

        if 'arm' in arch or 'aarch64' in arch:
            arch = 'arm64'
        elif 'x86_64' in arch or 'amd64' in arch:
            arch = 'x64'
        else:
            arch = 'x86'

    exe_name = f"godvoice-{system}-{arch}"
    if system == "windows":
        exe_name += ".exe"

    print(f"🔨 Création de l'exécutable: {exe_name}")

    # Créer le dossier dist s'il n'existe pas
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)

    # Commande PyInstaller
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",  # Un seul fichier exécutable
        "--name", exe_name,
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        "--clean",  # Nettoyer avant le build
        "--noconfirm",  # Pas de confirmation
        # Inclure les modules nécessaires
        "--hidden-import", "pandas",
        "--hidden-import", "matplotlib",
        "--hidden-import", "matplotlib.backends.backend_agg",  # Backend pour matplotlib
        "--hidden-import", "seaborn",
        "--hidden-import", "tiktoken",
        "--hidden-import", "tiktoken.load",
        "--hidden-import", "tiktoken_ext",
        "--hidden-import", "tiktoken_ext.openai_public",
        "--hidden-import", "anthropic",
        "--hidden-import", "click",
        # Inclure les données tiktoken
        "--collect-data", "tiktoken_ext",
        "--collect-data", "tiktoken",
        # Exclure les modules inutiles pour réduire la taille
        "--exclude-module", "tkinter",
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2",
        "--exclude-module", "PySide6",
        "--exclude-module", "IPython",
        "--exclude-module", "jupyter",
        # Fichier principal (version autonome)
        "cli_standalone.py"
    ]

    if not run_command(" ".join(pyinstaller_cmd), f"Build PyInstaller pour {exe_name}"):
        return False

    # Vérifier que l'exécutable a été créé
    exe_path = dist_dir / exe_name
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"✅ Exécutable créé: {exe_path}")
        print(f"📏 Taille: {size_mb:.1f} MB")

        # Test rapide de l'exécutable (seulement pour la plateforme actuelle)
        if not target_platform or system == platform.system().lower():
            print("🧪 Test de l'exécutable...")
            test_cmd = f'"{exe_path}" --help'
            if run_command(test_cmd, "Test de l'exécutable"):
                print("✅ L'exécutable fonctionne correctement!")
            else:
                print("⚠️  L'exécutable a été créé mais le test a échoué")
        return True
    else:
        print(f"❌ Exécutable non trouvé: {exe_path}")
        return False

def main():
    print("🚀 Build GodVoice CLI - Exécutable cross-platform")
    print(f"🖥️  Plateforme: {platform.system()} {platform.machine()}")
    print()

    # Vérifier que les fichiers nécessaires existent
    required_files = ['cli_standalone.py', 'requirements_cli.txt']
    for file in required_files:
        if Path(file).exists():
            print(f"✅ Fichier trouvé: {file}")
        else:
            print(f"❌ Fichier manquant: {file}")
            sys.exit(1)

    # Installer les dépendances
    if not run_command(
        f"{sys.executable} -m pip install -r requirements_cli.txt",
        "Installation des dépendances"
    ):
        sys.exit(1)

    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Build pour toutes les plateformes supportées
        platforms = ["linux-x64", "windows-x64", "darwin-x64", "darwin-arm64"]
        print("🌍 Build pour toutes les plateformes...")

        success_count = 0
        for platform_target in platforms:
            print(f"\n{'='*50}")
            print(f"🔨 Build pour {platform_target}")
            print(f"{'='*50}")
            if build_executable(platform_target):
                success_count += 1
            else:
                print(f"❌ Échec du build pour {platform_target}")

        print(f"\n🎯 Résumé: {success_count}/{len(platforms)} builds réussis")

    else:
        # Build pour la plateforme actuelle uniquement
        if not build_executable():
            sys.exit(1)

    # Nettoyer les fichiers temporaires
    print("\n🧹 Nettoyage des fichiers temporaires...")
    try:
        import shutil
        if Path("build").exists():
            shutil.rmtree("build")
        # Supprimer les fichiers .spec générés
        spec_files = list(Path(".").glob("*.spec"))
        for spec_file in spec_files:
            spec_file.unlink()
        print("✅ Nettoyage terminé")
    except Exception as e:
        print(f"⚠️  Erreur lors du nettoyage: {e}")

    print()
    print("🎉 Build terminé avec succès!")

    # Lister les exécutables créés
    dist_dir = Path("dist")
    if dist_dir.exists():
        executables = list(dist_dir.glob("godvoice-*"))
        if executables:
            print("📦 Exécutables disponibles:")
            for exe in executables:
                size_mb = exe.stat().st_size / (1024 * 1024)
                print(f"   - {exe.name} ({size_mb:.1f} MB)")

    print()
    print("📋 Utilisation:")
    print("   ./dist/godvoice-<platform> --chat-file chat.txt --anthropic-key sk-ant-...")
    print("   ./dist/godvoice-<platform> --chat-file chat.txt --no-ai  # Sans IA")
    print()
    print("💡 Pour distribuer l'exécutable:")
    print("   - Copiez le fichier dist/godvoice-<platform> sur la machine cible")
    print("   - Aucune installation Python requise sur la machine cible")
    print("   - Compatible avec la même architecture/OS")
    print()
    print("🔧 Pour build toutes les plateformes: python build.py --all")

if __name__ == "__main__":
    main()