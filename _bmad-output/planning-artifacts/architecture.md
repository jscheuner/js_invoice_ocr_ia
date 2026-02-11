---
stepsCompleted: ['step-01-init', 'step-02-context', 'step-03-starter', 'step-04-decisions', 'step-05-patterns', 'step-06-structure', 'step-07-validation', 'step-08-complete']
status: 'updated'
completedAt: '2026-01-29'
updatedAt: '2026-02-11'
inputDocuments:
  - prd.md
  - product-brief-js_invoice_ocr_ia-2026-01-28.md
  - brainstorming-session-2026-01-28.md
  - reflexion-factures.md
  - research/technical-integration-ia-cloud-research-2026-02-06.md
workflowType: 'architecture'
project_name: 'js_invoice_ocr_ia'
user_name: 'J.scheuner'
date: '2026-02-11'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

_Updated 2026-02-11: Integration multi-provider IA (Claude AI, OpenAI) basee sur la recherche technique du 2026-02-06._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (46 FRs):**
L'addon couvre 10 domaines fonctionnels : ingestion fichiers (5), extraction OCR (4), analyse IA (8), gestion factures Odoo (7), apprentissage/corrections (4), masques fournisseurs (3), jobs asynchrones (4), configuration (5), securite (4), et alertes (2).

Les FR critiques pour l'architecture :
- FR1-5 : File watcher avec gestion d'etat des fichiers
- FR10-17 : Pipeline IA avec indices de confiance
- FR25-27 : Systeme d'apprentissage par corrections
- FR32-35 : Traitement asynchrone via queue_job

**Non-Functional Requirements (20 NFRs):**
- Performance : < 2 min traitement, < 1s UI
- Securite : ACL Odoo, cles API admin-only, HTTPS pour cloud
- Fiabilite : 99% dispo, isolation erreurs, fichiers jamais perdus, fallback IA
- Integration : Odoo 18 Community, queue_job OCA
- Maintenabilite : PEP8, OCA guidelines, README

**Scale & Complexity:**

- Primary domain: ERP Addon (Backend Python + Frontend OWL)
- Complexity level: Medium-High (multi-provider IA)
- Estimated architectural components: 12 (config, mask, job, correction, OCR service, AI base, AI ollama, AI claude, AI openai, AI factory, file watcher, notification)

### Technical Constraints & Dependencies

**Hard Constraints:**
- Odoo 18 Community uniquement (pas Enterprise)
- Au moins un provider IA doit etre configure (Ollama, Claude ou OpenAI)
- Ollama reste le fallback par defaut (zero cout, zero dependance reseau)
- OCA queue_job pour l'asynchrone
- Tesseract installe sur le serveur

**Python Dependencies:**
- pymupdf (extraction PDF)
- pytesseract (OCR)
- requests (API Ollama)
- Pillow (images)
- anthropic>=0.40.0 (SDK Anthropic Claude — optionnel)
- openai>=1.50.0 (SDK OpenAI GPT — optionnel)

### Cross-Cutting Concerns Identified

1. **Error Handling** — Chaque etape du pipeline peut echouer (fichier corrompu, OCR illisible, API timeout, donnees invalides)
2. **Async Processing** — queue_job pour decoupler ingestion et traitement
3. **Data Privacy** — Logs sans donnees sensibles, option Ollama local pour clients sensibles
4. **Learning Loop** — Corrections utilisateur → enrichissement alias/masques
5. **Observability** — Statuts jobs visibles, indices confiance par champ
6. **Cost Tracking** — Suivi tokens/cout par requete dans _metadata, plafond par lot configurable
7. **Rate Limiting** — Retry avec backoff + fallback en cascade si rate limit atteint
8. **Provider Resilience** — Fallback automatique si provider principal indisponible

## Starter Template Evaluation

### Primary Technology Domain

**Odoo 18 Community Addon** — Framework ERP Python avec ORM proprietaire et frontend OWL.

### Starter Options Considered

| Option | Avantages | Inconvenients |
|--------|-----------|---------------|
| `odoo scaffold` | Officiel, rapide | Trop basique, pas OCA |
| Template OCA custom | Complet, maintenable | Creation manuelle |

### Selected Starter: Template OCA Personnalise

**Rationale:**
- Aligne avec les guidelines OCA (Odoo Community Association)
- Structure services separee pour logique metier (OCR, IA)
- Tests configures des le depart
- Pret pour publication open source

**Project Structure:**

```
js_invoice_ocr_ia/
├── __manifest__.py          # Metadata addon
├── __init__.py
├── models/                   # Modeles Odoo ORM
│   ├── jsocr_config.py      # Configuration singleton
│   ├── jsocr_mask.py        # Masques fournisseurs
│   ├── jsocr_import_job.py  # Jobs d'import
│   ├── jsocr_correction.py  # Historique corrections
│   ├── res_partner.py       # Extension partner
│   └── account_move.py      # Extension facture
├── services/                 # Logique metier isolee
│   ├── ai_service_base.py   # Interface abstraite IA
│   ├── ai_service_ollama.py # Client Ollama
│   ├── ai_service_claude.py # Client Claude API
│   ├── ai_service_openai.py # Client OpenAI API
│   ├── ai_service_factory.py# Factory + fallback
│   ├── ocr_service.py       # PyMuPDF + Tesseract
│   └── file_watcher.py      # Surveillance dossier
├── views/                    # Vues XML Odoo
├── security/                 # ACL et groupes
├── data/                     # Cron jobs
├── tests/                    # Tests unitaires
└── static/                   # Assets
```

**Architectural Decisions Provided:**

| Aspect | Decision |
|--------|----------|
| **Language** | Python 3.10+ |
| **Framework** | Odoo 18 ORM |
| **Frontend** | OWL components |
| **Testing** | Odoo TransactionCase |
| **Linting** | PEP8 + OCA pre-commit |
| **Structure** | Models/Services/Views separes |
| **AI Pattern** | Strategy + Factory + Fallback |

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Architecture multi-provider : Strategy Pattern + Factory
- Client IA abstrait : AIServiceBase avec implementations par provider
- Fallback en cascade : Provider principal → secondaire → Ollama local
- Format prompt IA : JSON schema strict (partage entre providers)
- Gestion erreurs : Hybride avec retry + fallback

**Important Decisions (Shape Architecture):**
- Stockage masques/confiance : JSON flexible avec _metadata provider
- Indicateurs UI : Badges colores
- Logging : Standard + Debug activable
- Securite cles API : Admin-only avec rotation
- Suivi des couts : Tracking tokens/cout par requete

**Deferred Decisions (Post-MVP):**
- Batch API pour volumes importants (Phase 4)
- Prompt caching Claude (Phase 4)
- Dashboard couts/statistiques (Phase 4)
- Ingestion email (V2)

### Data Architecture

| Decision | Choix | Rationale |
|----------|-------|-----------|
| Stockage masques | JSON dans champ Text | Flexible, evolutif, pas de migration |
| Indices de confiance | JSON global sur `account.move` | Extensible si nouveaux champs |
| Historique corrections | Table `jsocr.correction` | Tracabilite, apprentissage |
| Metadata provider | Champ `_metadata` dans JSON confiance | Tracabilite couts/provider sans migration |

**Format JSON Confiance (v2 — multi-provider) :**
```json
{
  "supplier": {"value": "Muller SA", "confidence": 95},
  "date": {"value": "2026-01-15", "confidence": 88},
  "total": {"value": 1250.00, "confidence": 92},
  "lines": [
    {"description": "Service X", "confidence": 85}
  ],
  "_metadata": {
    "provider": "claude",
    "model": "claude-sonnet-4-5",
    "processing_time_ms": 2340,
    "input_tokens": 1500,
    "output_tokens": 800,
    "cost_estimate": 0.0165
  }
}
```

**Champs supplementaires pour `jsocr.config` :**

| Champ | Type | Description |
|-------|------|-------------|
| `ai_provider` | Selection | `ollama`, `claude`, `openai` |
| `ai_api_key` | Char | Cle API (groups=base.group_system) |
| `ai_model_name` | Char | Nom du modele |
| `ai_fallback_provider` | Selection | Provider de fallback |
| `ai_max_cost_per_batch` | Float | Cout max par lot ($) |
| `ai_base_url` | Char | URL de base (pour Ollama custom) |

### Authentication & Security

| Decision | Choix | Rationale |
|----------|-------|-----------|
| Authentification | Odoo native | Framework standard |
| Autorisation | ACL 3 groupes | user/manager/admin |
| Donnees sensibles | Logs sans montants/fournisseurs | NFR8 compliance |
| Cles API cloud | `jsocr.config` avec groups admin | Acces restreint, rotation |
| Transport cloud | HTTPS/TLS 1.2+ obligatoire | Securite en transit |

**Gestion des cles API :**
- Stockage : Champ `Char` avec `groups="base.group_system"` (admin uniquement)
- Jamais en clair dans les logs ou le code source
- Rotation : Champ date derniere rotation + alerte automatique
- Fallback : Si cle invalide/expiree → fallback vers Ollama local
- Transport : HTTPS obligatoire pour Claude et OpenAI

### API & Communication Patterns

| Decision | Choix | Rationale |
|----------|-------|-----------|
| Architecture IA | Strategy Pattern + Factory | Multi-provider, extensible |
| Interface abstraite | `AIServiceBase` (ABC) | Logique metier partagee |
| Selection provider | `AIServiceFactory` | Base sur `jsocr.config` |
| Format prompt | Prompt + JSON schema (partage) | Parsing fiable, coherent |
| Gestion erreurs | Retry + Fallback en cascade | Resilience maximale |
| Timeout | 120 sec (cloud et Ollama) | NFR1 < 2 min |

**Pattern Strategy Multi-Provider :**

```python
from abc import ABC, abstractmethod

class AIServiceBase(ABC):
    """Logique metier partagee : prompts, parsing, confiance."""

    def extract_invoice_data(self, text: str, images: list = None) -> dict:
        """Point d'entree commun — orchestre l'extraction."""
        raw = self._call_api(text, images)
        return self._parse_response(raw)

    @abstractmethod
    def _call_api(self, text: str, images: list = None) -> str:
        """Appel API specifique au provider. Seule methode a implementer."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connexion pour UI config."""

    def _parse_response(self, raw: str) -> dict:
        """Parsing JSON + calcul confiance (partage)."""

    def _build_prompt(self, text: str) -> str:
        """Construction du prompt (partage)."""
```

```python
class AIServiceFactory:
    """Instancie le bon service selon jsocr.config."""

    @staticmethod
    def create(config) -> AIServiceBase:
        providers = {
            'ollama': OllamaService,
            'claude': ClaudeService,
            'openai': OpenAIService,
        }
        provider_cls = providers.get(config.ai_provider, OllamaService)
        return provider_cls(config)

    @staticmethod
    def create_with_fallback(config) -> AIServiceBase:
        """Cree le service avec fallback en cascade."""
        primary = AIServiceFactory.create(config)
        fallback = config.ai_fallback_provider
        if fallback:
            primary.set_fallback(AIServiceFactory._create_for(fallback, config))
        return primary
```

**Strategie Fallback en Cascade :**

```
1. Provider principal (config.ai_provider, ex: Claude)
   ├── Succes → retourner les donnees
   └── Echec (rate limit, timeout, erreur API)
       ├── 2. Provider secondaire (config.ai_fallback_provider, ex: OpenAI)
       │   ├── Succes → retourner les donnees
       │   └── Echec
       │       └── 3. Ollama local (toujours disponible)
       │           ├── Succes → retourner les donnees (qualite reduite)
       │           └── Echec → erreur finale, job en statut "error"
       └── Ou directement Ollama si pas de secondaire configure
```

**Strategie Retry (par provider) :**
- Timeout reseau → Retry 3x avec backoff (1s, 2s, 4s)
- Rate limit (429) → Retry avec `retry_after` header
- Serveur surcharge (503) → Retry 3x
- JSON invalide → Echec immediat → **fallback vers provider suivant**
- Cle API invalide (401/403) → Echec immediat → **fallback vers provider suivant**

### Frontend Architecture

| Decision | Choix | Rationale |
|----------|-------|-----------|
| Indicateurs confiance | Badges colores | Simple, visible, UX Odoo |
| Affichage PDF | Chatter natif | MVP rapide, comportement standard |
| Composants OWL | Widget confiance custom | Reutilisable |

**Seuils Couleurs Confiance :**
- Vert (>= 90%) : Haute confiance
- Orange (70-89%) : Verification suggeree
- Rouge (< 70%) : Correction probable

### Infrastructure & Deployment

| Decision | Choix | Rationale |
|----------|-------|-----------|
| Hebergement | On-premise | Politique donnees locales |
| Frequence cron | 5 minutes | Equilibre reactivite/charge |
| Logging | Standard + Debug activable | Troubleshooting flexible |
| File watcher | Cron Odoo | Integration native |
| Fallback IA | Cascade configurable | Resilience, disponibilite |
| Suivi couts | _metadata dans JSON confiance | Monitoring integre |

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

**Estimation couts par volume :**

| Volume | Provider recommande | Cout estime |
|--------|-------------------|-------------|
| 1-10 factures/jour | Claude Sonnet 4.5 | ~$0.10/jour |
| 10-50 factures/jour | Claude Sonnet 4.5 | ~$0.50/jour |
| 50-200 factures/jour | Claude Haiku 4.5 (batch) | ~$0.50/jour |
| 200+ factures/jour | Batch API + queue | Selon volume |

### Decision Impact Analysis

**Implementation Sequence (Multi-Provider) :**
1. Phase 1 — Abstraction : Extraire AIServiceBase + refactorer OllamaService + Factory
2. Phase 2 — Claude : Implementer ClaudeService + champs config + tests
3. Phase 3 — OpenAI + Fallback : Implementer OpenAIService + cascade fallback
4. Phase 4 — Optimisation : Batch API, cost tracking, prompt caching

**Cross-Component Dependencies:**
- `AIServiceFactory` → utilise par `jsocr.import.job`
- `AIServiceBase` → heritee par OllamaService, ClaudeService, OpenAIService
- `OCRService` → appele avant le service IA
- `jsocr.config` → determine le provider via `ai_provider`
- `jsocr.correction` → enrichit `res.partner.jsocr_aliases`
- Badges confiance → lisent JSON + _metadata sur `account.move`

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 7 zones ou les agents IA pourraient diverger
- Nommage XML IDs
- Nommage methodes
- Format logs
- Structure JSON
- Gestion etats
- Instanciation provider IA (Factory obligatoire)
- Separation logique metier / appel API

### Naming Patterns

**Modeles Odoo:**

| Element | Convention | Exemple |
|---------|------------|---------|
| Modele | `jsocr.nom` (prefixe jsocr) | `jsocr.import.job` |
| Champ | `snake_case` | `pdf_path`, `error_msg` |
| Champ Many2one | `{model}_id` | `partner_id`, `invoice_id` |
| Champ One2many | `{model}_ids` | `correction_ids` |
| Champ computed | `_compute_{field}` | `_compute_confidence` |
| Methode action | `action_{verb}` | `action_process`, `action_retry` |
| Methode privee | `_{verb}_{noun}` | `_extract_text`, `_parse_response` |

**XML IDs:**

| Element | Convention | Exemple |
|---------|------------|---------|
| Vue form | `{model}_view_form` | `jsocr_import_job_view_form` |
| Vue tree | `{model}_view_tree` | `jsocr_import_job_view_tree` |
| Vue kanban | `{model}_view_kanban` | `jsocr_import_job_view_kanban` |
| Action | `{model}_action` | `jsocr_import_job_action` |
| Menu | `menu_{model}` | `menu_jsocr_import_job` |
| Cron | `ir_cron_{fonction}` | `ir_cron_jsocr_scan_folder` |
| Groupe | `group_{role}` | `group_jsocr_user` |

**Fichiers Python:**

| Element | Convention | Exemple |
|---------|------------|---------|
| Modele | `{model_name}.py` | `jsocr_import_job.py` |
| Service | `{service}_service.py` | `ocr_service.py` |
| Service IA | `ai_service_{provider}.py` | `ai_service_claude.py` |
| Extension | `{model_extended}.py` | `res_partner.py` |

### Structure Patterns

**Organisation des Fichiers:**

```
js_invoice_ocr_ia/
├── models/
│   ├── __init__.py           # Import tous les modeles
│   ├── jsocr_config.py       # UN fichier = UN modele
│   └── ...
├── services/
│   ├── __init__.py
│   ├── ai_service_base.py    # Classe abstraite AIServiceBase
│   ├── ai_service_ollama.py  # OllamaService (refactore)
│   ├── ai_service_claude.py  # ClaudeService (nouveau)
│   ├── ai_service_openai.py  # OpenAIService (nouveau)
│   ├── ai_service_factory.py # Factory + fallback
│   └── ocr_service.py        # Classe OCRService
├── views/
│   ├── jsocr_config_views.xml    # UN fichier = vues d'UN modele
│   ├── menu.xml                  # Menus separes
│   └── ...
├── security/
│   ├── jsocr_security.xml        # Groupes
│   └── ir.model.access.csv       # ACL
├── data/
│   └── jsocr_cron.xml            # Crons
└── tests/
    ├── __init__.py
    ├── test_ai_service_base.py   # Tests logique partagee
    ├── test_ai_service_ollama.py # Tests OllamaService
    ├── test_ai_service_claude.py # Tests ClaudeService (mocks)
    ├── test_ai_service_openai.py # Tests OpenAIService (mocks)
    ├── test_ai_service_factory.py# Tests Factory + fallback
    ├── test_ocr_service.py       # Tests par composant
    └── test_import_job.py
```

**Regle:** Un Fichier = Une Responsabilite
**Regle:** Un Provider = Un Fichier Service

### Format Patterns

**Format JSON (Masques & Confiance):**

```json
{
  "version": "1.0",
  "fields": {
    "supplier": {
      "value": "Muller SA",
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

**Regles JSON:**
- Cles en `snake_case`
- Toujours inclure `version` pour evolutions futures
- Confiance = entier 0-100
- Dates en ISO 8601 (`YYYY-MM-DD`)
- Prefixe `_` pour les champs metadata (`_metadata`)

**Format Logs:**

```python
# BON - Sans donnees sensibles
_logger.info("JSOCR: Job %s started for file %s", job.id, job.filename)
_logger.error("JSOCR: Job %s failed: %s", job.id, error_type)
_logger.info("JSOCR: Job %s processed with provider %s", job.id, provider)

# MAUVAIS - Avec donnees sensibles
_logger.info("Processing invoice from %s for %s CHF", supplier_name, amount)
_logger.info("Using API key %s", api_key)
```

**Regles Logs:**
- Prefixe `JSOCR:` pour tous les logs
- ID job toujours inclus
- Jamais de montants, noms fournisseurs, numeros de facture
- Jamais de cles API ou tokens d'authentification
- Provider utilise peut etre logue (pas sensible)

### Process Patterns

**Machine a Etats (Job):**

```
draft → pending → processing → done
                           ↘ error → pending (retry)
                                   → failed (abandon)
```

| Etat | Description | Transitions |
|------|-------------|-------------|
| `draft` | Cree, pas encore soumis | → `pending` |
| `pending` | En queue | → `processing` |
| `processing` | En cours | → `done`, `error` |
| `done` | Succes | (final) |
| `error` | Echec, retry possible | → `pending`, `failed` |
| `failed` | Echec definitif | (final) |

**Pattern Retry:**

```python
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # secondes (backoff exponentiel)

def _should_retry(self, error_type):
    retryable = ['timeout', 'connection_error', 'service_unavailable', 'rate_limit']
    return error_type in retryable and self.retry_count < MAX_RETRIES
```

### Enforcement Guidelines

**Tous les Agents IA DOIVENT:**

1. Utiliser le prefixe `jsocr` pour modeles, XML IDs, logs
2. Respecter snake_case pour champs, methodes, cles JSON
3. Ne jamais logger de donnees sensibles ni de cles API
4. Implementer la machine a etats pour les jobs
5. Utiliser `AIServiceFactory` pour obtenir le service IA (jamais instancier directement)
6. Heriter de `AIServiceBase` pour tout nouveau provider
7. Un fichier = une responsabilite, Un provider = un fichier service
8. Inclure `_metadata` dans toutes les reponses IA

**Anti-Patterns a Eviter:**

```python
# MAUVAIS: Instanciation directe d'un provider
class JsocrImportJob(models.Model):
    def process(self):
        ai = OllamaService(config)  # Couplage fort !

# BON: Utilisation de la Factory
class JsocrImportJob(models.Model):
    def process(self):
        config = self.env['jsocr.config'].get_config()
        ai = AIServiceFactory.create_with_fallback(config)
        data = ai.extract_invoice_data(text)
        self._create_invoice(data)

# MAUVAIS: Logique metier dans une implementation provider
class ClaudeService(AIServiceBase):
    def extract_invoice_data(self, text):
        # Prompts, parsing, confiance ici... DUPLIQUE !

# BON: Logique metier dans AIServiceBase, provider = juste _call_api()
class ClaudeService(AIServiceBase):
    def _call_api(self, text, images=None):
        # Seulement l'appel API Anthropic
```

## Project Structure & Boundaries

### Complete Project Directory Structure

```
js_invoice_ocr_ia/
│
├── __manifest__.py                 # Metadata addon Odoo
├── __init__.py                     # Import racine
├── README.md                       # Documentation installation/usage
├── requirements.txt                # Dependances Python (+ anthropic, openai)
│
├── models/
│   ├── __init__.py
│   ├── jsocr_config.py             # Configuration singleton (+ ai_provider, ai_api_key...)
│   ├── jsocr_mask.py               # Masques extraction par fournisseur
│   ├── jsocr_import_job.py         # Jobs d'import (machine a etats)
│   ├── jsocr_correction.py         # Historique corrections
│   ├── res_partner.py              # Extension partner (aliases)
│   └── account_move.py             # Extension facture (confiance)
│
├── services/
│   ├── __init__.py
│   ├── ai_service_base.py          # AIServiceBase (ABC) — logique metier partagee
│   ├── ai_service_ollama.py        # OllamaService (refactore depuis ai_service.py)
│   ├── ai_service_claude.py        # ClaudeService (SDK Anthropic)
│   ├── ai_service_openai.py        # OpenAIService (SDK OpenAI)
│   ├── ai_service_factory.py       # AIServiceFactory + fallback cascade
│   ├── ocr_service.py              # OCRService (PyMuPDF + Tesseract)
│   └── file_watcher.py             # FileWatcher (scan dossier)
│
├── views/
│   ├── jsocr_config_views.xml      # Config: form (+ section provider IA)
│   ├── jsocr_mask_views.xml        # Masques: tree, form
│   ├── jsocr_import_job_views.xml  # Jobs: kanban, tree, form
│   ├── jsocr_correction_views.xml  # Corrections: tree
│   ├── account_move_views.xml      # Extension vues facture
│   └── menu.xml                    # Structure menus
│
├── security/
│   ├── jsocr_security.xml          # Groupes et categorie
│   └── ir.model.access.csv         # ACL par modele/groupe
│
├── data/
│   ├── jsocr_cron.xml              # Cron scan dossier (5 min)
│   └── jsocr_data.xml              # Donnees initiales (si besoin)
│
├── wizards/
│   ├── __init__.py
│   └── jsocr_test_connection.py    # Wizard test connexion IA (multi-provider)
│
├── static/
│   ├── description/
│   │   ├── icon.png                # Icone addon (128x128)
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
│   ├── test_ai_service_base.py     # Tests logique partagee (prompts, parsing)
│   ├── test_ai_service_ollama.py   # Tests OllamaService
│   ├── test_ai_service_claude.py   # Tests ClaudeService (mocks API)
│   ├── test_ai_service_openai.py   # Tests OpenAIService (mocks API)
│   ├── test_ai_service_factory.py  # Tests Factory + fallback cascade
│   ├── test_file_watcher.py        # Tests FileWatcher
│   ├── test_import_job.py          # Tests workflow complet
│   └── test_correction.py          # Tests apprentissage
│
├── demo/
│   └── jsocr_demo.xml              # Donnees demo (optionnel)
│
└── i18n/
    ├── fr.po                       # Traduction francais
    └── de.po                       # Traduction allemand
```

### Architectural Boundaries

**Service Layer Boundaries (Multi-Provider) :**

```
┌──────────────────────────────────────────────────────────────┐
│                    ODOO FRAMEWORK                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Models     │  │    Views     │  │   Security   │       │
│  │  (ORM)       │  │   (XML)      │  │   (ACL)      │       │
│  └──────┬───────┘  └──────────────┘  └──────────────┘       │
│         │                                                     │
│         ▼                                                     │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              SERVICES LAYER                             │  │
│  │  ┌────────────┐ ┌──────────────────────┐ ┌──────────┐ │  │
│  │  │ OCRService │ │  AIServiceFactory    │ │FileWatch.│ │  │
│  │  └─────┬──────┘ │  ┌───────────────┐  │ └────┬─────┘ │  │
│  │        │        │  │ AIServiceBase │  │      │       │  │
│  │        │        │  └───────┬───────┘  │      │       │  │
│  │        │        │    ┌─────┼─────┐    │      │       │  │
│  │        │        │    ▼     ▼     ▼    │      │       │  │
│  │        │        │  Ollama Claude OpenAI│      │       │  │
│  │        │        └──────────────────────┘      │       │  │
│  └────────┼──────────────┼─────┼─────┼──────────┼───────┘  │
└───────────┼──────────────┼─────┼─────┼──────────┼───────────┘
            ▼              ▼     ▼     ▼          ▼
     ┌──────────┐   ┌────────┐ ┌────┐ ┌────┐  ┌──────────┐
     │Tesseract │   │Ollama  │ │API │ │API │  │Filesystem│
     │ PyMuPDF  │   │(local) │ │Ant.│ │OAI │  │  (I/O)   │
     └──────────┘   └────────┘ └────┘ └────┘  └──────────┘
```

**Data Boundaries:**

| Frontiere | Entree | Sortie |
|-----------|--------|--------|
| FileWatcher | Dossier filesystem | `jsocr.import.job` (draft) |
| OCRService | Chemin PDF | Texte extrait (string) |
| AIServiceFactory | Config provider | Instance AIServiceBase |
| AIServiceBase | Texte + prompt | JSON structure + confiance + _metadata |
| ImportJob | JSON structure | `account.move` (draft) |
| Correction | Modification user | `res.partner.jsocr_aliases` |

**API Boundaries (Methodes Publiques):**

| Modele | Methodes Publiques |
|--------|-------------------|
| `jsocr.config` | `get_config()`, `test_ai_connection()`, `scan_input_folder()` |
| `jsocr.import.job` | `action_process()`, `action_retry()`, `action_cancel()` |
| `jsocr.mask` | `get_mask_for_partner()`, `create_from_correction()` |
| `jsocr.correction` | `apply_correction()` |
| `AIServiceFactory` | `create(config)`, `create_with_fallback(config)` |
| `AIServiceBase` | `extract_invoice_data(text, images)`, `test_connection()` |

### Requirements to Structure Mapping

**FR Categories → Files:**

| Categorie FR | Fichiers Principaux |
|--------------|---------------------|
| Ingestion (FR1-5) | `services/file_watcher.py`, `data/jsocr_cron.xml` |
| OCR (FR6-9) | `services/ocr_service.py` |
| IA (FR10-17) | `services/ai_service_base.py`, `services/ai_service_factory.py`, `services/ai_service_*.py` |
| Factures (FR18-24) | `models/jsocr_import_job.py`, `models/account_move.py` |
| Apprentissage (FR25-28) | `models/jsocr_correction.py`, `models/res_partner.py` |
| Masques (FR29-31) | `models/jsocr_mask.py` |
| Jobs (FR32-35) | `models/jsocr_import_job.py` |
| Config (FR36-40) | `models/jsocr_config.py`, `views/jsocr_config_views.xml` |
| Securite (FR41-44) | `security/jsocr_security.xml`, `security/ir.model.access.csv` |
| Alertes (FR45-46) | `static/src/components/confidence_badge/` |

### Cross-Cutting Concerns Mapping

| Preoccupation | Fichiers Impliques |
|---------------|-------------------|
| Error Handling | Tous les services, `jsocr_import_job.py` |
| Logging | `services/*.py` (prefixe JSOCR:) |
| Async Processing | `jsocr_import_job.py`, `data/jsocr_cron.xml` |
| Confidentialite | `services/*.py` (pas de donnees sensibles, pas de cles API) |
| Apprentissage | `jsocr_correction.py`, `res_partner.py` |
| Cost Tracking | `ai_service_base.py` (_metadata), `jsocr_config.py` (plafond) |
| Rate Limiting | `ai_service_base.py` (retry), `ai_service_factory.py` (fallback) |
| Provider Resilience | `ai_service_factory.py` (cascade fallback) |

### Test Organization

| Fichier Test | Couverture |
|--------------|------------|
| `test_ai_service_base.py` | Logique partagee : prompts, parsing JSON, calcul confiance |
| `test_ai_service_ollama.py` | Connexion Ollama, appel API locale |
| `test_ai_service_claude.py` | Appel API Anthropic (mocks), gestion erreurs |
| `test_ai_service_openai.py` | Appel API OpenAI (mocks), structured outputs |
| `test_ai_service_factory.py` | Factory, selection provider, fallback cascade |
| `test_ocr_service.py` | Extraction PDF, OCR, multi-pages |
| `test_file_watcher.py` | Scan dossier, deplacement fichiers |
| `test_import_job.py` | Workflow complet, machine a etats |
| `test_correction.py` | Apprentissage alias, enrichissement |

## Architecture Validation Results

### Coherence Validation

**Decision Compatibility:** Toutes les technologies sont compatibles (Odoo 18 + Python 3.10+ + queue_job OCA + Ollama + Anthropic SDK + OpenAI SDK).

**Pattern Consistency:** Nommage jsocr.* coherent, snake_case uniforme, logs avec prefixe JSOCR:, fichiers ai_service_{provider}.py coherents.

**Structure Alignment:** Structure OCA alignee avec les patterns et decisions. Strategy Pattern coherent avec la separation services/modeles.

### Requirements Coverage

**Functional Requirements:** 46/46 FRs couverts (100%)

**Non-Functional Requirements:** 20/20 NFRs adresses (100%) — resilience amelioree par fallback multi-provider

### Implementation Readiness

**Decision Completeness:** Stack complet, versions specifiees, patterns documentes, multi-provider architecture.

**Structure Completeness:** Arborescence complete, frontieres definies, mapping FR→fichiers.

**Pattern Completeness:** Nommage, structure, process, exemples fournis, anti-patterns documentes.

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Contexte projet analyse (46 FRs, 20 NFRs)
- [x] Complexite evaluee (Medium-High)
- [x] Contraintes identifiees (Odoo 18 Community, multi-provider IA)
- [x] Preoccupations transversales mappees (+ cost tracking, rate limiting, resilience)

**Architectural Decisions**
- [x] Stack technologique complet (+ Anthropic SDK, OpenAI SDK)
- [x] Patterns d'integration definis (Strategy + Factory + Fallback)
- [x] Performance adressee (timeout, retry, fallback)
- [x] Securite couverte (ACL, logs, cles API admin-only, HTTPS)

**Implementation Patterns**
- [x] Conventions de nommage etablies (+ ai_service_{provider}.py)
- [x] Patterns de structure definis (+ un provider = un fichier)
- [x] Patterns de communication specifies (+ fallback cascade)
- [x] Patterns de process documentes
- [x] Anti-patterns documentes (instanciation directe, logique dupliquee)

**Project Structure**
- [x] Structure complete definie (12 composants architecturaux)
- [x] Frontieres etablies (+ AIServiceFactory, AIServiceBase)
- [x] Points d'integration mappes
- [x] Mapping exigences → structure complet

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** HIGH

**Key Strengths:**
- Architecture simple et pragmatique avec extensibilite multi-provider
- Separation claire services/modeles avec Strategy Pattern
- Patterns Odoo/OCA standards
- Couverture 100% des exigences
- Resilience par fallback en cascade (cloud → cloud → local)
- Zero regression : refactoring incremental en 4 phases

**Provider Recommendation:**
- Provider principal : Claude Sonnet 4.5 (JSON valide 100%, excellent sur documents complexes)
- Provider secondaire : GPT-4o (structured outputs natifs, alternative fiable)
- Fallback : Ollama local (zero cout, zero latence reseau, confidentialite totale)

### Implementation Handoff

**AI Agent Guidelines:**
1. Suivre les decisions architecturales exactement
2. Utiliser les patterns de nommage jsocr.*
3. Respecter la structure services/models/views
4. Utiliser AIServiceFactory, jamais instancier un provider directement
5. Consulter ce document pour toute question

**Implementation Sequence (Multi-Provider) :**

Phase 1 — Abstraction (zero regression) :
1. Extraire `AIServiceBase` depuis `OllamaService` actuel
2. Refactorer `OllamaService` → `ai_service_ollama.py` implementant `AIServiceBase`
3. Creer `AIServiceFactory` avec selection par config
4. Ajouter champs provider dans `jsocr.config`
5. Tests de non-regression (tous les tests existants passent)

Phase 2 — Claude Service :
1. Implementer `ClaudeService` dans `ai_service_claude.py`
2. Ajouter `anthropic` dans `requirements.txt`
3. Tests unitaires avec mocks API
4. UI config : champ cle API + test connexion

Phase 3 — OpenAI + Fallback :
1. Implementer `OpenAIService` dans `ai_service_openai.py`
2. Ajouter `openai` dans `requirements.txt`
3. Implementer la logique fallback en cascade dans `AIServiceFactory`
4. Tests d'integration multi-provider

Phase 4 — Optimisation :
1. Tracking des couts et usage (_metadata)
2. Batch API pour gros volumes
3. Prompt caching (Claude)
4. Dashboard de monitoring (optionnel)
