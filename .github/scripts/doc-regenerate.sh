#!/bin/bash
set -e

# Sauvegarder la branche actuelle
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Récupérer tous les tags semver
TAGS=$(git tag -l 'v*.*.*' | sort -V)

echo "📚 Regenerating documentation for all tags..."
echo "Tags found: $(echo $TAGS | wc -w)"

for tag in $TAGS; do
  echo ""
  echo "🏷️  Processing $tag..."
  git checkout $tag 2>/dev/null || { echo "Failed to checkout $tag"; continue; }

  # Déployer avec mike (sans push pour l'instant)
  uv run mike deploy --update-aliases $tag || { echo "Failed to deploy $tag"; continue; }

  echo "✅ $tag deployed"
done

# Retourner à la branche d'origine
echo ""
echo "🔄 Returning to $CURRENT_BRANCH..."
git checkout $CURRENT_BRANCH

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