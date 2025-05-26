# Makefile pour GodVoice CLI
# Usage: make build, make clean, make install, make test

PYTHON := python3
PIP := pip3

# Détection automatique de la plateforme
UNAME_S := $(shell uname -s)
UNAME_M := $(shell uname -m)

ifeq ($(UNAME_S),Linux)
    PLATFORM := linux
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM := darwin
endif
ifeq ($(OS),Windows_NT)
    PLATFORM := windows
    PYTHON := python
    PIP := pip
endif

ifeq ($(UNAME_M),x86_64)
    ARCH := x64
endif
ifeq ($(UNAME_M),amd64)
    ARCH := x64
endif
ifeq ($(UNAME_M),arm64)
    ARCH := arm64
endif
ifeq ($(UNAME_M),aarch64)
    ARCH := arm64
endif

# Nom de l'exécutable
EXE_NAME := godvoice-$(PLATFORM)-$(ARCH)
ifeq ($(PLATFORM),windows)
    EXE_NAME := $(EXE_NAME).exe
endif

.PHONY: help install build build-all clean test run-example all

help:
	@echo "🎤 GodVoice CLI - Makefile"
	@echo ""
	@echo "Commandes disponibles:"
	@echo "  make install     - Installer les dépendances"
	@echo "  make build       - Créer l'exécutable pour la plateforme actuelle"
	@echo "  make build-all   - Créer les exécutables pour toutes les plateformes"
	@echo "  make test        - Tester l'exécutable"
	@echo "  make clean       - Nettoyer les fichiers temporaires"
	@echo "  make all         - install + build + test"
	@echo "  make run-example - Exemple d'utilisation"
	@echo ""
	@echo "Plateforme détectée: $(PLATFORM)-$(ARCH)"
	@echo "Exécutable cible: $(EXE_NAME)"

install:
	@echo "📦 Installation des dépendances..."
	$(PIP) install -r requirements_cli.txt

build:
	@echo "🔨 Build de l'exécutable $(EXE_NAME)..."
	$(PYTHON) build.py

build-all:
	@echo "🌍 Build pour toutes les plateformes..."
	$(PYTHON) build.py --all

test:
	@echo "🧪 Test de l'exécutable..."
	@if [ -f "dist/$(EXE_NAME)" ]; then \
		echo "✅ Exécutable trouvé: dist/$(EXE_NAME)"; \
		./dist/$(EXE_NAME) --help; \
	else \
		echo "❌ Exécutable non trouvé. Lancez 'make build' d'abord."; \
		exit 1; \
	fi

clean:
	@echo "🧹 Nettoyage..."
	rm -rf build/
	rm -rf dist/
	rm -rf __pycache__/
	rm -f *.spec
	@echo "✅ Nettoyage terminé"

run-example:
	@echo "📋 Exemple d'utilisation:"
	@echo ""
	@echo "# Avec analyse IA complète:"
	@echo "./dist/$(EXE_NAME) --chat-file chat.txt --anthropic-key sk-ant-your-key-here"
	@echo ""
	@echo "# Seulement statistiques (sans IA):"
	@echo "./dist/$(EXE_NAME) --chat-file chat.txt --no-ai"
	@echo ""
	@echo "# Avec options personnalisées:"
	@echo "./dist/$(EXE_NAME) --chat-file chat.txt --anthropic-key sk-ant-... --top 15 --output-dir results"

all: install build test
	@echo "🎉 Build complet terminé!"
	@echo "📦 Exécutable prêt: dist/$(EXE_NAME)"

# Commandes pour différentes plateformes
build-linux:
	@echo "🐧 Build pour Linux..."
	$(PYTHON) build.py

build-windows:
	@echo "🪟 Build pour Windows..."
	$(PYTHON) build.py

build-macos:
	@echo "🍎 Build pour macOS..."
	$(PYTHON) build.py

# Release multi-plateforme
release: build-all
	@echo "🚀 Création des releases multi-plateformes..."
	@echo "📦 Exécutables créés:"
	@ls -la dist/godvoice-* 2>/dev/null || echo "❌ Aucun exécutable trouvé"
	@echo ""
	@echo "📋 Plateformes supportées:"
	@echo "  - Linux x64"
	@echo "  - Windows x64"
	@echo "  - macOS x64"
	@echo "  - macOS arm64 (Apple Silicon)"
	@echo ""
	@echo "💡 Pour distribuer:"
	@echo "  - Copiez les fichiers dist/godvoice-* vers les machines cibles"
	@echo "  - Aucune installation Python requise sur les machines cibles"

# Test avec le fichier de test
test-full:
	@echo "🧪 Test complet avec le fichier de test..."
	@if [ -f "dist/$(EXE_NAME)" ] && [ -f "test_chat.txt" ]; then \
		echo "✅ Test sans IA..."; \
		./dist/$(EXE_NAME) --chat-file test_chat.txt --no-ai --verbose; \
		echo ""; \
		echo "✅ Test terminé avec succès!"; \
	else \
		echo "❌ Fichiers manquants. Vérifiez que l'exécutable et test_chat.txt existent."; \
		exit 1; \
	fi