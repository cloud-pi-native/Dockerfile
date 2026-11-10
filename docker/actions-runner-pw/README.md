# Runner GitHub Actions Playwright

Cette image installe Chromium et Firefox avec la version exacte définie par l’argument de construction `PW_VERSION`. Elle expose cette même valeur dans `RUNNER_PLAYWRIGHT_VERSION`, accessible aux étapes des jobs exécutés sur le runner.

Les workflows consommateurs doivent comparer leur version exacte de Playwright à cette variable et échouer si elle est absente, illisible ou différente. Ils ne doivent pas réinstaller les navigateurs pour corriger un décalage. La configuration du runner et les workflows ne doivent pas surcharger cette variable : elle décrit l’image réellement exécutée.

## Vérification locale

```bash
docker build -t actions-runner-pw:check docker/actions-runner-pw
docker run --rm --entrypoint /bin/bash actions-runner-pw:check \
  -c 'test "$RUNNER_PLAYWRIGHT_VERSION" = "1.65.0" && printf "%s\n" "$RUNNER_PLAYWRIGHT_VERSION"'
```

Pour choisir une autre version lors de la construction, utiliser `--build-arg PW_VERSION=<version-exacte>` : ce même argument pilote l’installation et la valeur exposée.

## Publication et adoption

Le tag publié dans `ci/matrix.json` suit le format `<Node>-<Playwright>-<révision>`. Incrémenter la révision lors d’une reconstruction sans changement des versions Node et Playwright : le workflow de publication ignore les tags déjà présents avec les architectures demandées.

1. Après fusion, déclencher le workflow `CI` avec `IMAGES=actions-runner-pw` et les architectures nécessaires.
2. Vérifier la publication du nouveau tag, puis mettre à jour manuellement l’image référencée dans la configuration Actions Runner Controller (ARC). Ce dépôt ne réalise pas ce déploiement.
3. Vérifier la valeur depuis une étape de job exécutée sur le nouveau runner :

   ```yaml
   - name: Verify runner Playwright version
     shell: bash
     run: |
       test "${RUNNER_PLAYWRIGHT_VERSION:-}" = '1.65.0'
       printf 'Runner Playwright: %s\n' "$RUNNER_PLAYWRIGHT_VERSION"
   ```

4. Activer le contrôle bloquant côté Console seulement après cette vérification.

Toute montée de version de Playwright doit être justifiée en revue et coordonnée avec les dépendances des consommateurs, y compris leurs branches de maintenance. Mettre à jour les versions attendues des exemples de vérification ci-dessus lors de cette montée de version.

## Suivi

- Contrat du runner : [Dockerfile #10](https://github.com/cloud-pi-native/Dockerfile/issues/10)
- Contrôle côté application : [Console #3000](https://github.com/cloud-pi-native/console/issues/3000)
