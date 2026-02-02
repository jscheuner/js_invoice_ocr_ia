# Invoice OCR IA (js_invoice_ocr_ia)

Addon Odoo 18 Community pour automatiser la saisie des factures fournisseurs via OCR et Intelligence Artificielle.

## Fonctionnalités

- **Surveillance automatique** : Détection des nouveaux PDFs dans un dossier configuré
- **Extraction OCR** : Support PDF natifs (texte sélectionnable) et scannés (Tesseract)
- **Analyse IA** : Extraction structurée via Ollama local (Llama3, Mistral)
- **Création automatique** : Factures fournisseur brouillon pré-remplies
- **Indices de confiance** : Indicateurs visuels par champ (vert/orange/rouge)
- **Apprentissage** : Mémorisation des corrections pour amélioration continue
- **Multilingue** : Support natif FR/DE/EN (contexte suisse)

## Prérequis

### Système

| Composant | Version | Notes |
|-----------|---------|-------|
| Odoo | 18.0 Community | Enterprise non supporté |
| Python | 3.10+ | Requis par Odoo 18 |
| Tesseract OCR | 4.0+ | Avec packs de langue |
| Ollama | Latest | Serveur local |

### Installation Tesseract (Linux/Debian)

```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-fra tesseract-ocr-deu tesseract-ocr-eng
```

### Installation Tesseract (Windows)

Télécharger depuis : https://github.com/UB-Mannheim/tesseract/wiki

### Installation Ollama

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger un modèle
ollama pull llama3
# ou
ollama pull mistral
```

### Module OCA Requis

- **queue_job** : https://github.com/OCA/queue

```bash
# Cloner le repo OCA queue dans un dossier séparé
cd /path/to/odoo-addons
git clone https://github.com/OCA/queue.git --branch 18.0
```

**Configuration addons-path:** Ajouter le dossier queue_job au démarrage d'Odoo:

```bash
# Exemple de démarrage Odoo avec addons-path incluant queue_job
./odoo-bin -c odoo.conf --addons-path=/path/to/odoo/addons,/path/to/odoo-addons/queue
```

Ou dans `odoo.conf`:
```ini
[options]
addons_path = /path/to/odoo/addons,/path/to/odoo-addons/queue
```

## Installation

1. **Cloner ce dépôt** dans le dossier addons d'Odoo :
   ```bash
   cd /path/to/odoo/addons
   git clone <repo_url> js_invoice_ocr_ia
   ```

2. **Installer les dépendances Python** :
   ```bash
   pip install -r js_invoice_ocr_ia/requirements.txt
   ```

3. **Mettre à jour la liste des modules** :
   - Aller dans Apps
   - Cliquer sur "Mettre à jour la liste des applications"

4. **Installer le module** :
   - Rechercher "Invoice OCR IA"
   - Cliquer sur Installer

## Configuration

### 1. Ollama

1. Aller dans **Configuration > OCR IA**
2. Configurer l'URL Ollama : `http://localhost:11434`
3. Cliquer sur **Tester la connexion**
4. Sélectionner le modèle IA (llama3 recommandé)

### 2. Dossiers de surveillance

Configurer les chemins :
- **Dossier à surveiller** : `/path/to/factures/a_traiter/`
- **Dossier succès** : `/path/to/factures/traite_ok/`
- **Dossier erreur** : `/path/to/factures/erreur/`
- **Dossier rejeté** : `/path/to/factures/non_pdf/`

### 3. Alertes (optionnel)

- **Seuil montant** : Alerte si facture > X CHF
- **Email alerte** : Notification en cas d'erreur

### 4. Droits utilisateurs

Assigner les groupes aux utilisateurs :
- **Utilisateur OCR** : Voir et valider ses factures
- **Manager OCR** : Voir toutes les factures
- **Admin OCR** : Configuration complète

## Utilisation

1. **Déposer** les PDFs de factures dans le dossier surveillé
2. **Attendre** le traitement automatique (cron toutes les 5 minutes)
3. **Recevoir** la notification "X factures prêtes à valider"
4. **Valider** les factures brouillon dans Odoo
5. **Corriger** si nécessaire (le système apprend)

## Structure technique

```
js_invoice_ocr_ia/
├── models/          # Modèles Odoo (config, jobs, masques, corrections)
├── services/        # Services métier (OCR, IA, file watcher)
├── views/           # Vues XML Odoo
├── security/        # Groupes et ACL
├── data/            # Cron jobs
├── wizards/         # Assistants (test connexion)
├── tests/           # Tests unitaires
├── static/          # Assets frontend (OWL components)
├── i18n/            # Traductions
└── demo/            # Données de démonstration
```

## Support

- **Issues** : Créer une issue sur le dépôt GitHub
- **Documentation** : Voir le wiki du projet

## Licence

LGPL-3 - Voir le fichier LICENSE pour plus de détails.

## Auteur

J.scheuner - 2026
