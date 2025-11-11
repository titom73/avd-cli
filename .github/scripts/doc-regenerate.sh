#!/bin/bash
# Désactiver exit on error pour gérer les erreurs proprement
set +e

# Se déplacer à la racine du repository
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "📂 Working directory: $REPO_ROOT"

# Sauvegarder la branche actuelle
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "� Current branch/ref: $CURRENT_BRANCH"

# Vérifier les changements non commités
if ! git diff --quiet || ! git diff --staged --quiet; then
  echo "❌ Error: You have uncommitted changes. Please commit or stash them first."
  git status --short
  exit 1
fi

# Récupérer tous les tags semver
TAGS=$(git tag -l 'v*.*.*' | sort -V)

echo "📚 Regenerating documentation for all tags..."
echo "Tags found: $(echo $TAGS | wc -w)"

for tag in $TAGS; do
  echo ""
  echo "🏷️  Processing $tag..."

  # Checkout du tag
  if ! git checkout $tag 2>&1 | grep -v "HEAD is now at"; then
    echo "❌ Failed to checkout $tag"
    continue
  fi

  # Vérifier que mkdocs.yml existe
  if [ ! -f "mkdocs.yml" ]; then
    echo "⚠️  No mkdocs.yml found for $tag, skipping..."
    continue
  fi

  # Nettoyer uv.lock pour éviter les conflits
  git checkout HEAD -- uv.lock 2>/dev/null || true

  # Installer les dépendances pour ce tag
  echo "📦 Installing dependencies for $tag..."
  if ! uv sync --group docs 2>&1 | grep -v "Resolved\|Installed\|Uninstalled\|Audited"; then
    echo "⚠️  Failed to install dependencies for $tag, trying without docs group..."
    if ! uv sync 2>&1 | grep -v "Resolved\|Installed\|Uninstalled\|Audited"; then
      echo "❌ Failed to install dependencies for $tag, skipping..."
      continue
    fi
  fi

  # Déployer avec mike (sans push pour l'instant)
  echo "🔨 Building and deploying docs..."
  if uv run mike deploy --update-aliases $tag 2>&1 | grep -E "INFO|error|Error" | grep -v "FutureWarning\|warning:"; then
    echo "✅ $tag deployed"
  else
    echo "⚠️  Deployment completed with warnings for $tag"
  fi

  # Nettoyer les changements dans uv.lock après le build
  git checkout HEAD -- uv.lock 2>/dev/null || true
done

# Retourner à la branche d'origine
echo ""
echo "🔄 Returning to $CURRENT_BRANCH..."
git checkout $CURRENT_BRANCH 2>&1 | grep -v "HEAD is now at"

# Nettoyer uv.lock une dernière fois
git checkout HEAD -- uv.lock 2>/dev/null || true

# Définir le dernier tag comme stable
LATEST_TAG=$(git tag -l 'v*.*.*' | sort -V | tail -n 1)
echo ""
echo "🎯 Setting $LATEST_TAG as stable..."
uv run mike alias $LATEST_TAG stable

# Pousser toutes les versions
echo ""
echo "📤 Pushing to gh-pages..."
git push origin gh-pages --force

echo ""
echo "✅ Documentation regenerated for all versions!"
echo "🌐 View at: https://titom73.github.io/avd-cli/"