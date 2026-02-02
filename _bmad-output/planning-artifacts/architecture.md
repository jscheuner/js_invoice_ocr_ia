---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure', 'step-07-validation', 'step-08-complete']
status: 'complete'
completedAt: '2026-01-29'
inputDocuments:
  - prd.md
  - product-brief-js_invoice_ocr_ia-2026-01-28.md
  - brainstorming-session-2026-01-28.md
  - reflexion-factures.md
workflowType: 'architecture'
project_name: 'js_invoice_ocr_ia'
user_name: 'J.scheuner'
date: '2026-01-29'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (46 FRs):**
L'addon couvre 10 domaines fonctionnels : ingestion fichiers (5), extraction OCR (4), analyse IA (8), gestion factures Odoo (7), apprentissage/corrections (4), masques fournisseurs (3), jobs asynchrones (4), configuration (5), sécurité (4), et alertes (2).

Les FR critiques pour l'architecture :
- FR1-5 : File watcher avec gestion d'état des fichiers
- FR10-17 : Pipeline IA avec indices de confiance
- FR25-27 : Système d'apprentissage par corrections
- FR32-35 : Traitement asynchrone via queue_job

**Non-Functional Requirements (20 NFRs):**
- Performance : < 2 min traitement, < 1s UI
- Sécurité : Zero données externes, ACL Odoo
- Fiabilité : 99% dispo, isolation erreurs, fichiers jamais perdus
- Intégration : Odoo 18 Community, queue_job OCA
- Maintenabilité : PEP8, OCA guidelines, README

**Scale & Complexity:**

- Primary domain: ERP Addon (Backend Python + Frontend OWL)
- Complexity level: Medium
- Estimated architectural components: 8 (config, mask, job, correction, OCR service, AI service, file watcher, notification)

### Technical Constraints & Dependencies

**Hard Constraints:**
- Odoo 18 Community uniquement (pas Enterprise)
- Ollama local obligatoire en production
- OCA queue_job pour l'asynchrone
- Tesseract installé sur le serveur

**Python Dependencies:**
- pymupdf (extraction PDF)
- pytesseract (OCR)
- requests (API Ollama)
- Pillow (images)

### Cross-Cutting Concerns Identified

1. **Error Handling** — Chaque étape du pipeline peut échouer (fichier corrompu, OCR illisible, Ollama timeout, données invalides)
2. **Async Processing** — queue_job pour découpler ingestion et traitement
3. **Data Privacy** — Logs sans données sensibles, aucun appel cloud en prod
4. **Learning Loop** — Corrections utilisateur → enrichissement alias/masques
5. **Observability** — Statuts jobs visibles, indices confiance par champ

## Starter Template Evaluation

### Primary Technology Domain

**Odoo 18 Community Addon** — Framework ERP Python avec ORM propriétaire et frontend OWL.

### Starter Options Considered

| Option | Avantages | Inconvénients |
|--------|-----------|---------------|
| `odoo scaffold` | Officiel, rapide | Trop basique, pas OCA |
| Template OCA custom | Complet, maintenable | Création manuelle |

### Selected Starter: Template OCA Personnalisé

**Rationale:**
- Aligné avec les guidelines OCA (Odoo Community Association)
- Structure services séparée pour logique métier (OCR, IA)
- Tests configurés dès le départ
- Prêt pour publication open source

**Project Structure:**

```
js_invoice_ocr_ia/
├── __manifest__.py          # Metadata addon
├── __init__.py
├── models/                   # Modèles Odoo ORM
│   ├── jsocr_config.py      # Configuration singleton
│   ├── jsocr_mask.py        # Masques fournisseurs
│   ├── jsocr_import_job.py  # Jobs d'import
│   ├── jsocr_correction.py  # Historique corrections
│   ├── res_partner.py       # Extension partner
│   └── account_move.py      # Extension facture
├── services/                 # Logique métier isolée
│   ├── ocr_service.py       # PyMuPDF + Tesseract
│   ├── ai_service.py        # Client Ollama
│   └── file_watcher.py      # Surveillance dossier
├── views/                    # Vues XML Odoo
├── security/                 # ACL et groupes
├── data/                     # Cron jobs
├── tests/                    # Tests unitaires
└── static/                   # Assets
```

**Architectural Decisions Provided:**

| Aspect | Décision |
|--------|----------|
| **Language** | Python 3.10+ |
| **Framework** | Odoo 18 ORM |
| **Frontend** | OWL components |
| **Testing** | Odoo TransactionCase |
| **Linting** | PEP8 + OCA pre-commit |
| **Structure** | Models/Services/Views séparés |

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Client Ollama : Service dédié isolé
- Format prompt IA : JSON schema strict
- Gestion erreurs : Hybride avec retry

**Important Decisions (Shape Architecture):**
- Stockage masques/confiance : JSON flexible
- Indicateurs UI : Badges colorés
- Logging : Standard + Debug activable

**Deferred Decisions (Post-MVP):**
- Split view PDF (V1.1)
- Dashboard statistiques (V1.1)
- Ingestion email (V2)

### Data Architecture

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Stockage masques | JSON dans champ Text | Flexible, évolutif, pas de migration |
| Indices de confiance | JSON global sur `account.move` | Extensible si nouveaux champs |
| Historique corrections | Table `jsocr.correction` | Traçabilité, apprentissage |

**Format JSON Confiance :**
```json
{
  "supplier": {"value": "Müller SA", "confidence": 95},
  "date": {"value": "2026-01-15", "confidence": 88},
  "total": {"value": 1250.00, "confidence": 92},
  "lines": [
    {"description": "Service X", "confidence": 85}
  ]
}
```

### Authentication & Security

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Authentification | Odoo native | Framework standard |
| Autorisation | ACL 3 groupes | user/manager/admin |
| Données sensibles | Logs sans montants/fournisseurs | NFR8 compliance |

### API & Communication Patterns

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Client Ollama | Service dédié `OllamaService` | Séparation, testabilité |
| Format prompt | Prompt + JSON schema | Parsing fiable |
| Gestion erreurs | Hybride | Retry transitoires, fail données |
| Timeout Ollama | 120 secondes | NFR1 < 2 min |

**Pattern Service Ollama :**
```python
class OllamaService:
    def __init__(self, config):
        self.url = config.ollama_url
        self.model = config.ollama_model

    def extract_invoice_data(self, text: str) -> dict:
        """Retourne données structurées + confiance"""

    def test_connection(self) -> bool:
        """Test connexion pour UI config"""
```

**Stratégie Retry :**
- Timeout réseau → Retry 3x avec backoff (5s, 15s, 30s)
- Ollama surchargé (503) → Retry 3x
- JSON invalide → Échec immédiat
- Données manquantes → Échec immédiat

### Frontend Architecture

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Indicateurs confiance | Badges colorés | Simple, visible, UX Odoo |
| Affichage PDF | Chatter natif | MVP rapide, comportement standard |
| Composants OWL | Widget confiance custom | Réutilisable |

**Seuils Couleurs Confiance :**
- Vert (≥ 90%) : Haute confiance
- Orange (70-89%) : Vérification suggérée
- Rouge (< 70%) : Correction probable

### Infrastructure & Deployment

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Hébergement | On-premise | Politique données locales |
| Fréquence cron | 5 minutes | Équilibre réactivité/charge |
| Logging | Standard + Debug activable | Troubleshooting flexible |
| File watcher | Cron Odoo | Intégration native |

**Configuration Cron :**
```xml
<record id="ir_cron_jsocr_scan_folder" model="ir.cron">
    <field name="name">JSOCR: Scan Input Folder</field>
    <field name="model_id" ref="model_jsocr_config"/>
    <field name="state">code</field>
    <field name="code">model.scan_input_folder()</field>
    <field name="interval_number">5</field>
    <field name="interval_type">minutes</field>
</record>
```

### Decision Impact Analysis

**Implementation Sequence:**
1. Structure addon + modèles de base
2. Service OCR (PyMuPDF + Tesseract)
3. Service Ollama + prompts
4. File watcher + queue jobs
5. Création facture brouillon
6. UI validation + badges confiance
7. Apprentissage corrections

**Cross-Component Dependencies:**
- `OllamaService` → utilisé par `jsocr.import.job`
- `OCRService` → appelé avant `OllamaService`
- `jsocr.correction` → enrichit `res.partner.jsocr_aliases`
- Badges confiance → lisent JSON sur `account.move`

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 5 zones où les agents IA pourraient diverger
- Nommage XML IDs
- Nommage méthodes
- Format logs
- Structure JSON
- Gestion états

### Naming Patterns

**Modèles Odoo:**

| Élément | Convention | Exemple |
|---------|------------|---------|
| Modèle | `jsocr.nom` (préfixe jsocr) | `jsocr.import.job` |
| Champ | `snake_case` | `pdf_path`, `error_msg` |
| Champ Many2one | `{model}_id` | `partner_id`, `invoice_id` |
| Champ One2many | `{model}_ids` | `correction_ids` |
| Champ computed | `_compute_{field}` | `_compute_confidence` |
| Méthode action | `action_{verb}` | `action_process`, `action_retry` |
| Méthode privée | `_{verb}_{noun}` | `_extract_text`, `_parse_response` |

**XML IDs:**

| Élément | Convention | Exemple |
|---------|------------|---------|
| Vue form | `{model}_view_form` | `jsocr_import_job_view_form` |
| Vue tree | `{model}_view_tree` | `jsocr_import_job_view_tree` |
| Vue kanban | `{model}_view_kanban` | `jsocr_import_job_view_kanban` |
| Action | `{model}_action` | `jsocr_import_job_action` |
| Menu | `menu_{model}` | `menu_jsocr_import_job` |
| Cron | `ir_cron_{fonction}` | `ir_cron_jsocr_scan_folder` |
| Groupe | `group_{role}` | `group_jsocr_user` |

**Fichiers Python:**

| Élément | Convention | Exemple |
|---------|------------|---------|
| Modèle | `{model_name}.py` | `jsocr_import_job.py` |
| Service | `{service}_service.py` | `ocr_service.py` |
| Extension | `{model_extended}.py` | `res_partner.py` |

### Structure Patterns

**Organisation des Fichiers:**

```
js_invoice_ocr_ia/
├── models/
│   ├── __init__.py           # Import tous les modèles
│   ├── jsocr_config.py       # UN fichier = UN modèle
│   └── ...
├── services/
│   ├── __init__.py
│   ├── ocr_service.py        # Classe OCRService
│   └── ai_service.py         # Classe OllamaService
├── views/
│   ├── jsocr_config_views.xml    # UN fichier = vues d'UN modèle
│   ├── menu.xml                  # Menus séparés
│   └── ...
├── security/
│   ├── jsocr_security.xml        # Groupes
│   └── ir.model.access.csv       # ACL
├── data/
│   └── jsocr_cron.xml            # Crons
└── tests/
    ├── __init__.py
    ├── test_ocr_service.py       # Tests par composant
    └── test_import_job.py
```

**Règle:** Un Fichier = Une Responsabilité

### Format Patterns

**Format JSON (Masques & Confiance):**

```json
{
  "version": "1.0",
  "fields": {
    "supplier": {
      "value": "Müller SA",
      "confidence": 95,
      "source": "ocr"
    }
  },
  "lines": [
    {
      "description": "Service consulting",
      "quantity": 1.0,
      "unit_price": 150.00,
      "confidence": 85
    }
  ]
}
```

**Règles JSON:**
- Clés en `snake_case`
- Toujours inclure `version` pour évolutions futures
- Confiance = entier 0-100
- Dates en ISO 8601 (`YYYY-MM-DD`)

**Format Logs:**

```python
# BON - Sans données sensibles
_logger.info("JSOCR: Job %s started for file %s", job.id, job.filename)
_logger.error("JSOCR: Job %s failed: %s", job.id, error_type)

# MAUVAIS - Avec données sensibles
_logger.info("Processing invoice from %s for %s CHF", supplier_name, amount)
```

**Règles Logs:**
- Préfixe `JSOCR:` pour tous les logs
- ID job toujours inclus
- Jamais de montants, noms fournisseurs, numéros de facture

### Process Patterns

**Machine à États (Job):**

```
draft → pending → processing → done
                           ↘ error → pending (retry)
                                   → failed (abandon)
```

| État | Description | Transitions |
|------|-------------|-------------|
| `draft` | Créé, pas encore soumis | → `pending` |
| `pending` | En queue | → `processing` |
| `processing` | En cours | → `done`, `error` |
| `done` | Succès | (final) |
| `error` | Échec, retry possible | → `pending`, `failed` |
| `failed` | Échec définitif | (final) |

**Pattern Retry:**

```python
MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]  # secondes

def _should_retry(self, error_type):
    retryable = ['timeout', 'connection_error', 'service_unavailable']
    return error_type in retryable and self.retry_count < MAX_RETRIES
```

### Enforcement Guidelines

**Tous les Agents IA DOIVENT:**

1. Utiliser le préfixe `jsocr` pour modèles, XML IDs, logs
2. Respecter snake_case pour champs, méthodes, clés JSON
3. Ne jamais logger de données sensibles
4. Implémenter la machine à états pour les jobs
5. Utiliser les services dédiés (OCRService, OllamaService)
6. Un fichier = une responsabilité

**Anti-Pattern à Éviter:**

```python
# MAUVAIS: Logique métier dans le modèle
class JsocrImportJob(models.Model):
    def process(self):
        # 100 lignes de code OCR + IA ici...

# BON: Délégation aux services
class JsocrImportJob(models.Model):
    def process(self):
        ocr = OCRService()
        text = ocr.extract_text(self.pdf_path)
        ai = OllamaService(self.env['jsocr.config'].get_config())
        data = ai.extract_invoice_data(text)
        self._create_invoice(data)
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
js_invoice_ocr_ia/
│
├── __manifest__.py                 # Metadata addon Odoo
├── __init__.py                     # Import racine
├── README.md                       # Documentation installation/usage
├── requirements.txt                # Dépendances Python externes
│
├── models/
│   ├── __init__.py                 # Import tous les modèles
│   ├── jsocr_config.py             # Configuration singleton
│   ├── jsocr_mask.py               # Masques extraction par fournisseur
│   ├── jsocr_import_job.py         # Jobs d'import (machine à états)
│   ├── jsocr_correction.py         # Historique corrections
│   ├── res_partner.py              # Extension partner (aliases)
│   └── account_move.py             # Extension facture (confiance)
│
├── services/
│   ├── __init__.py
│   ├── ocr_service.py              # OCRService (PyMuPDF + Tesseract)
│   ├── ai_service.py               # OllamaService (client API)
│   └── file_watcher.py             # FileWatcher (scan dossier)
│
├── views/
│   ├── jsocr_config_views.xml      # Config: form
│   ├── jsocr_mask_views.xml        # Masques: tree, form
│   ├── jsocr_import_job_views.xml  # Jobs: kanban, tree, form
│   ├── jsocr_correction_views.xml  # Corrections: tree
│   ├── account_move_views.xml      # Extension vues facture
│   └── menu.xml                    # Structure menus
│
├── security/
│   ├── jsocr_security.xml          # Groupes et catégorie
│   └── ir.model.access.csv         # ACL par modèle/groupe
│
├── data/
│   ├── jsocr_cron.xml              # Cron scan dossier (5 min)
│   └── jsocr_data.xml              # Données initiales (si besoin)
│
├── wizards/
│   ├── __init__.py
│   └── jsocr_test_connection.py    # Wizard test connexion Ollama
│
├── static/
│   ├── description/
│   │   ├── icon.png                # Icône addon (128x128)
│   │   └── index.html              # Description marketplace
│   └── src/
│       ├── components/
│       │   └── confidence_badge/   # Widget badge confiance OWL
│       │       ├── confidence_badge.js
│       │       └── confidence_badge.xml
│       └── scss/
│           └── jsocr.scss          # Styles custom
│
├── tests/
│   ├── __init__.py
│   ├── common.py                   # Fixtures et helpers
│   ├── test_ocr_service.py         # Tests OCRService
│   ├── test_ai_service.py          # Tests OllamaService
│   ├── test_file_watcher.py        # Tests FileWatcher
│   ├── test_import_job.py          # Tests workflow complet
│   └── test_correction.py          # Tests apprentissage
│
├── demo/
│   └── jsocr_demo.xml              # Données démo (optionnel)
│
└── i18n/
    ├── fr.po                       # Traduction français
    └── de.po                       # Traduction allemand
```

### Architectural Boundaries

**Service Layer Boundaries:**

```
┌─────────────────────────────────────────────────────────┐
│                    ODOO FRAMEWORK                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Models     │  │    Views     │  │   Security   │  │
│  │  (ORM)       │  │   (XML)      │  │   (ACL)      │  │
│  └──────┬───────┘  └──────────────┘  └──────────────┘  │
│         │                                               │
│         ▼                                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │              SERVICES LAYER                       │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐   │  │
│  │  │ OCRService │ │OllamaServ. │ │FileWatcher │   │  │
│  │  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘   │  │
│  └────────┼──────────────┼──────────────┼───────────┘  │
└───────────┼──────────────┼──────────────┼───────────────┘
            ▼              ▼              ▼
     ┌──────────┐   ┌──────────┐   ┌──────────┐
     │Tesseract │   │  Ollama  │   │Filesystem│
     │ PyMuPDF  │   │  (API)   │   │  (I/O)   │
     └──────────┘   └──────────┘   └──────────┘
```

**Data Boundaries:**

| Frontière | Entrée | Sortie |
|-----------|--------|--------|
| FileWatcher | Dossier filesystem | `jsocr.import.job` (draft) |
| OCRService | Chemin PDF | Texte extrait (string) |
| OllamaService | Texte + prompt | JSON structuré + confiance |
| ImportJob | JSON structuré | `account.move` (draft) |
| Correction | Modification user | `res.partner.jsocr_aliases` |

**API Boundaries (Méthodes Publiques):**

| Modèle | Méthodes Publiques |
|--------|-------------------|
| `jsocr.config` | `get_config()`, `test_ollama_connection()`, `scan_input_folder()` |
| `jsocr.import.job` | `action_process()`, `action_retry()`, `action_cancel()` |
| `jsocr.mask` | `get_mask_for_partner()`, `create_from_correction()` |
| `jsocr.correction` | `apply_correction()` |

### Requirements to Structure Mapping

**FR Categories → Files:**

| Catégorie FR | Fichiers Principaux |
|--------------|---------------------|
| Ingestion (FR1-5) | `services/file_watcher.py`, `data/jsocr_cron.xml` |
| OCR (FR6-9) | `services/ocr_service.py` |
| IA (FR10-17) | `services/ai_service.py` |
| Factures (FR18-24) | `models/jsocr_import_job.py`, `models/account_move.py` |
| Apprentissage (FR25-28) | `models/jsocr_correction.py`, `models/res_partner.py` |
| Masques (FR29-31) | `models/jsocr_mask.py` |
| Jobs (FR32-35) | `models/jsocr_import_job.py` |
| Config (FR36-40) | `models/jsocr_config.py`, `views/jsocr_config_views.xml` |
| Sécurité (FR41-44) | `security/jsocr_security.xml`, `security/ir.model.access.csv` |
| Alertes (FR45-46) | `static/src/components/confidence_badge/` |

### Cross-Cutting Concerns Mapping

| Préoccupation | Fichiers Impliqués |
|---------------|-------------------|
| Error Handling | Tous les services, `jsocr_import_job.py` |
| Logging | `services/*.py` (préfixe JSOCR:) |
| Async Processing | `jsocr_import_job.py`, `data/jsocr_cron.xml` |
| Confidentialité | `services/*.py` (pas de données sensibles) |
| Apprentissage | `jsocr_correction.py`, `res_partner.py` |

### Test Organization

| Fichier Test | Couverture |
|--------------|------------|
| `test_ocr_service.py` | Extraction PDF, OCR, multi-pages |
| `test_ai_service.py` | Connexion Ollama, parsing JSON, retry |
| `test_file_watcher.py` | Scan dossier, déplacement fichiers |
| `test_import_job.py` | Workflow complet, machine à états |
| `test_correction.py` | Apprentissage alias, enrichissement |

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** Toutes les technologies sont compatibles (Odoo 18 + Python 3.10+ + queue_job OCA + Ollama).

**Pattern Consistency:** Nommage jsocr.* cohérent, snake_case uniforme, logs avec préfixe JSOCR:.

**Structure Alignment:** Structure OCA alignée avec les patterns et décisions.

### Requirements Coverage ✅

**Functional Requirements:** 46/46 FRs couverts (100%)

**Non-Functional Requirements:** 20/20 NFRs adressés (100%)

### Implementation Readiness ✅

**Decision Completeness:** Stack complet, versions spécifiées, patterns documentés.

**Structure Completeness:** Arborescence complète, frontières définies, mapping FR→fichiers.

**Pattern Completeness:** Nommage, structure, process, exemples fournis.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Contexte projet analysé (46 FRs, 20 NFRs)
- [x] Complexité évaluée (Medium)
- [x] Contraintes identifiées (Odoo 18 Community, Ollama local)
- [x] Préoccupations transversales mappées

**✅ Architectural Decisions**
- [x] Stack technologique complet
- [x] Patterns d'intégration définis
- [x] Performance adressée (timeout, retry)
- [x] Sécurité couverte (ACL, logs)

**✅ Implementation Patterns**
- [x] Conventions de nommage établies
- [x] Patterns de structure définis
- [x] Patterns de communication spécifiés
- [x] Patterns de process documentés

**✅ Project Structure**
- [x] Structure complète définie
- [x] Frontières établies
- [x] Points d'intégration mappés
- [x] Mapping exigences → structure complet

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** HIGH

**Key Strengths:**
- Architecture simple et pragmatique
- Séparation claire services/modèles
- Patterns Odoo/OCA standards
- Couverture 100% des exigences

**Areas for Future Enhancement:**
- Prompt Ollama à affiner pendant dev
- Stratégie fuzzy matching fournisseurs
- Dashboard statistiques (V1.1)

### Implementation Handoff

**AI Agent Guidelines:**
1. Suivre les décisions architecturales exactement
2. Utiliser les patterns de nommage jsocr.*
3. Respecter la structure services/models/views
4. Consulter ce document pour toute question

**First Implementation Priority:**
1. Créer la structure addon avec __manifest__.py
2. Implémenter jsocr.config (singleton)
3. Développer OCRService
4. Développer OllamaService
5. Créer jsocr.import.job avec machine à états

