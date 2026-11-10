# Dockerfile

## Rafraîchissement de `actions-runner-pw`

Le workflow [Refresh actions-runner-pw](.github/workflows/refresh-runner.yml)
s’exécute chaque lundi à **05:17 UTC** et peut être lancé manuellement sur `main` :

```sh
gh workflow run refresh-runner.yml --ref main
```

Il effectue les opérations suivantes, sur des runners GitHub hébergés indépendants d’ARC :

1. Incrémenter uniquement la révision de `actions-runner-pw` dans `ci/matrix.json`
   (`26-1.65.0-1` → `26-1.65.0-2`), sans modifier Node ou Playwright.
2. Pousser directement ce changement sur `main`, sans PR.
3. Construire le SHA exact de ce commit en amd64 et arm64, avec `pull: true`
   pour récupérer la base `ghcr.io/actions/actions-runner:latest` récente.
4. Vérifier, sous l’utilisateur par défaut de l’image, l’exécution de
   `Runner.Listener`, Node, pnpm et des navigateurs Chromium/Firefox (`--version`).
   Ce contrôle des binaires n’est pas un test E2E ni un enregistrement auprès de GitHub.
5. Publier le nouveau tag multiarchitecture et les alias habituels, dont `latest`.
   Les images par digest sont téléversées avant les vérifications ; les tags ne
   sont publiés qu’après la réussite des vérifications sur les deux architectures.

Les exécutions de ce workflow sont sérialisées. Une nouvelle révision complète
est créée à chaque rafraîchissement ; les anciens tags complets ne sont pas
réutilisés par les rafraîchissements suivants. Les alias restent mobiles.
Le workflow CI manuel existant reste disponible.

### Permissions et échecs

Le workflow utilise `GITHUB_TOKEN` avec `contents: write` pour le commit et
`packages: write` pour GHCR. Les politiques du dépôt/de l’organisation doivent
permettre ces opérations, notamment le push sur `main`. Le workflow ne contourne
aucune protection : si le push est refusé, il échoue avant de construire.
Le build est appelé explicitement, car un push avec `GITHUB_TOKEN` ne déclenche
pas un autre workflow `push`.

Le commit précède la construction : **une révision enregistrée ne garantit pas
que l’image a été publiée**. En cas d’échec, consulter les logs et le résumé du
workflow, corriger le problème, puis relancer les jobs en échec. Un nouveau
rafraîchissement incrémente à nouveau la révision ; les trous dans la séquence
sont acceptables. Les notifications d’échec dépendent des abonnements GitHub
Actions : veiller à ce qu’un mainteneur les reçoive.

### Adoption dans ARC — manuelle

Après une publication réussie, un développeur doit mettre à jour le tag de
l’image dans les valeurs du chart `gha-runner-scale-set`, par commit/PR dans le
dépôt de configuration. Le résumé du workflow indique la référence publiée.
`imagePullPolicy: IfNotPresent` convient à ces nouveaux tags.

**Publier une nouvelle image ne met pas à jour ARC** : tant que le chart pointe
sur l’ancien tag, ses runners restent exposés au blocage pour version obsolète.
Cette étape manuelle est un risque résiduel accepté. Le chemin de validation de
la mise à jour du chart doit rester utilisable lorsque les runners ARC sont bloqués.

### Vérifications locales

Les tests nécessitent Python 3, PyYAML, Git, Bash et jq :

```sh
python3 -m pip install PyYAML
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s ci/tests -v
shellcheck ci/check-actions-runner-pw.sh
actionlint
```

Pour vérifier les binaires d’une image locale sans l’enregistrer comme runner :

```sh
docker run --rm -i --entrypoint bash actions-runner-pw:latest -s \
  < ci/check-actions-runner-pw.sh
```
