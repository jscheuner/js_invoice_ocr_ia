---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'Integration APIs IA cloud (Claude AI, ChatGPT) dans module Odoo 18 OCR'
research_goals: 'Comparer les APIs Claude et ChatGPT pour remplacer/completer Ollama local, evaluer couts, limites, qualite extraction, architecture multi-provider'
user_name: 'J.scheuner'
date: '2026-02-06'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-02-06
**Author:** J.scheuner
**Research Type:** technical

---

## Research Overview

Cette recherche technique evalue l'integration d'APIs IA cloud (Anthropic Claude et OpenAI ChatGPT) dans le module Odoo 18 `js_invoice_ocr_ia`, qui utilise actuellement Ollama en local pour l'extraction de donnees de factures fournisseurs. L'objectif est de determiner la meilleure approche architecturale pour un systeme multi-provider avec fallback, en comparant les couts, la qualite d'extraction, les patterns d'integration et les strategies d'implementation.

**Methodologie** : Recherche web verifiee avec sources multiples, analyse comparative factuelle, et recommandations basees sur des donnees actuelles (fevrier 2026).

## Table des matieres

1. [Technical Research Scope Confirmation](#technical-research-scope-confirmation)
2. [Technology Stack Analysis](#technology-stack-analysis)
   - APIs IA disponibles et modeles
   - Comparaison directe pour l'extraction de factures
   - SDK Python et integration
3. [Integration Patterns Analysis](#integration-patterns-analysis)
   - Pattern d'abstraction multi-provider (Strategy Pattern)
   - Gestion des erreurs et rate limiting
   - Securite et gestion des cles API
   - Strategie de fallback et resilience
4. [Architectural Patterns and Design](#architectural-patterns-and-design)
   - Architecture systeme recommandee
   - Principes de design (SOLID)
   - Scalabilite et traitement en arriere-plan
   - Architecture de securite et de donnees
5. [Implementation Approaches](#implementation-approaches-and-technology-adoption)
   - Strategie d'adoption graduelle (4 phases)
   - Testing et qualite
   - Suivi des couts et monitoring
   - Evaluation des risques
6. [Recommandations techniques finales](#recommandations-techniques-finales)
   - Provider recommande, roadmap, metriques de succes

---

## Technical Research Scope Confirmation

**Research Topic:** Integration APIs IA cloud (Claude AI, ChatGPT) dans module Odoo 18 OCR
**Research Goals:** Comparer les APIs Claude et ChatGPT pour remplacer/completer Ollama local, evaluer couts, limites, qualite extraction, architecture multi-provider

**Technical Research Scope:**

- Architecture Analysis - patterns de design multi-provider, abstraction du service IA, strategie de fallback
- Implementation Approaches - SDK Python Anthropic et OpenAI, integration Odoo, gestion asynchrone
- Technology Stack - APIs disponibles, modeles recommandes pour extraction de factures, support vision/OCR
- Integration Patterns - gestion des cles API, configuration multi-tenant, rate limiting, retry strategies
- Performance Considerations - latence cloud vs local, couts par requete, scalabilite, limites de tokens

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-02-06

## Technology Stack Analysis

### APIs IA disponibles et modeles

#### Anthropic Claude API

Anthropic propose trois modeles principaux via son API (fevrier 2026) :

| Modele | Input (par 1M tokens) | Output (par 1M tokens) | Usage recommande |
|--------|----------------------|------------------------|------------------|
| Claude Haiku 4.5 | $1.00 | $5.00 | Rapide, taches simples |
| Claude Sonnet 4.5 | $3.00 | $15.00 | Equilibre qualite/cout |
| Claude Opus 4.5 | $5.00 | $25.00 | Taches complexes |

- **Vision** : Tous les modeles Claude supportent l'input d'images (base64 ou URL) [Confiance: Haute]
- **Batch API** : Reduction de 50% sur les couts avec traitement asynchrone sous 24h
- **Fenetre de contexte** : Jusqu'a 200 000 tokens, permettant le traitement de lots de factures entiers
- **JSON structure** : JSON valide dans 100% des cas de test, avec coherence de format superieure a 95%
- _Sources : [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Anthropic Review 2026](https://hackceleration.com/anthropic-review/), [Claude Vision Docs](https://platform.claude.com/docs/en/build-with-claude/vision)_

#### OpenAI GPT API

OpenAI propose plusieurs modeles via son API :

| Modele | Input (par 1M tokens) | Output (par 1M tokens) | Usage recommande |
|--------|----------------------|------------------------|------------------|
| GPT-4o | $2.50 | $10.00 | Multimodal, equilibre |
| GPT-4o mini | $0.15 | $0.60 | Economique, rapide |
| o1 (reasoning) | $15.00 | $60.00 | Raisonnement complexe |

- **Vision** : GPT-4o supporte l'input d'images (base64 ou URL) avec cout additionnel par image
- **Batch API** : Reduction de 50% avec traitement sous 24h
- **Structured Outputs** : `response_format` natif avec validation de schema JSON (Pydantic)
- **Precision extraction** : 92.8% de precision en extraction de champs sur factures (GPT-4o)
- _Sources : [OpenAI Pricing](https://platform.openai.com/docs/pricing), [GPT-4o Pricing 2026](https://pricepertoken.com/pricing-page/model/openai-gpt-4o), [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)_

### Comparaison directe pour l'extraction de factures

| Critere | Claude (Sonnet 4.5) | GPT-4o | Ollama (local) |
|---------|---------------------|--------|----------------|
| Precision extraction | 97% (champs) | 98% (texte PDF) | ~80-85% (variable) |
| JSON valide | 100% des cas | ~95% (avec response_format) | ~70-85% |
| Cout par facture (1-2 pages) | $0.005 - $0.018 | $0.005 - $0.018 | Gratuit (GPU local) |
| Latence | 1-5 sec | 1-5 sec | 5-30 sec (selon GPU) |
| Documents complexes | Excellent (multi-pages) | Bon | Limite |
| Donnees sensibles | Cloud (privacy policy) | Cloud (privacy policy) | 100% local |

[Confiance: Haute - Sources multiples concordantes]
_Sources : [Claude vs GPT vs Gemini - Koncile](https://www.koncile.ai/en/ressources/claude-gpt-or-gemini-which-is-the-best-llm-for-invoice-extraction), [Claude vs ChatGPT Invoice Processing - Gennai](https://www.gennai.io/blog/claude-vs-chatgpt-invoice-processing), [Document Parsing Comparison - Invofox](https://www.invofox.com/en/post/document-parsing-using-gpt-4o-api-vs-claude-sonnet-3-5-api-vs-invofox-api-with-code-samples)_

### SDK Python et integration

#### Anthropic Python SDK

```python
# Installation : pip install anthropic
import base64
from anthropic import Anthropic

client = Anthropic(api_key="sk-ant-...")
message = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=4096,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/jpeg",
                "data": base64_string
            }},
            {"type": "text", "text": "Extraire les donnees de cette facture en JSON..."}
        ]
    }]
)
```

- SDK officiel : [anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python)
- Gestion integree des rate limits et retries
- Support async natif (`AsyncAnthropic`)

#### OpenAI Python SDK

```python
# Installation : pip install openai
from openai import OpenAI

client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o",
    response_format={"type": "json_object"},
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{base64_string}"
            }},
            {"type": "text", "text": "Extraire les donnees de cette facture en JSON..."}
        ]
    }]
)
```

- SDK officiel : [openai-python](https://github.com/openai/openai-python)
- Structured Outputs natif avec `response_format` et validation Pydantic
- Support async natif (`AsyncOpenAI`)

_Sources : [Anthropic SDK GitHub](https://github.com/anthropics/anthropic-sdk-python), [OpenAI SDK GitHub](https://github.com/openai/openai-python), [OpenAI Vision Guide](https://platform.openai.com/docs/guides/images-vision)_

### Integration dans Odoo 18

- **Bonnes pratiques** : Utiliser HTTPS, ne jamais exposer les cles API dans le code, stocker dans `ir.config_parameter` ou `jsocr.config`
- **Authentification** : Cles API stockees comme parametres systeme Odoo (similaire aux API keys Odoo)
- **Gestion d'erreurs** : Logging, retry automatique, monitoring des performances
- **Securite** : Limiter l'acces aux modeles et champs necessaires, validation des entrees
- **Tests** : Toujours tester en sandbox avant production

[Confiance: Haute]
_Sources : [Odoo 18 External API Docs](https://www.odoo.com/documentation/18.0/developer/reference/external_api.html), [Odoo API Integration Guide](https://www.getknit.dev/blog/odoo-api-integration-guide-in-depth)_

### Tendances d'adoption technologique

- **Migration Cloud IA** : Tendance forte a combiner IA locale (confidentialite) et cloud (qualite) avec pattern de fallback
- **Multi-provider** : Pattern "Strategy" pour abstraire le fournisseur IA, permettant de basculer entre providers
- **Structured Outputs** : Les deux APIs convergent vers des sorties JSON structurees et validees
- **Batch Processing** : Les deux fournisseurs offrent des reductions de 50% pour le traitement asynchrone
- **Cout en baisse** : Les prix des APIs IA ont significativement baisse en 2025-2026, rendant le cloud accessible meme pour des volumes moderes

[Confiance: Haute]
_Sources : [OpenAI vs Claude for Production 2026](https://zenvanriel.nl/ai-engineer-blog/openai-vs-claude-for-production/), [Claude API vs OpenAI API Comparison](https://collabnix.com/claude-api-vs-openai-api-2025-complete-developer-comparison-with-benchmarks-code-examples/)_

## Integration Patterns Analysis

### Pattern d'abstraction multi-provider (Strategy Pattern)

Le pattern recommande pour integrer plusieurs fournisseurs IA est le **Strategy Pattern** avec une couche d'abstraction unifiee. Le principe : le code applicatif ne parle jamais directement a un fournisseur specifique, mais passe par une interface commune.

**Architecture recommandee en 3 couches :**

1. **Interface abstraite** (`AIServiceBase`) : Definit les methodes communes `extract_invoice_data()`, `analyze_image()`, `calculate_confidence()`
2. **Implementations concretes** : `OllamaService`, `ClaudeService`, `OpenAIService` - chacune implemente l'interface
3. **Factory/Router** : Selectionne le bon service selon la configuration Odoo (`jsocr.config`)

```python
# Pattern abstrait (pseudo-code)
class AIServiceBase(ABC):
    @abstractmethod
    def extract_invoice_data(self, image_base64, prompt):
        """Retourne dict avec donnees extraites + confidences"""
        pass

class ClaudeService(AIServiceBase):
    def extract_invoice_data(self, image_base64, prompt):
        # Appel API Anthropic avec vision
        ...

class OpenAIService(AIServiceBase):
    def extract_invoice_data(self, image_base64, prompt):
        # Appel API OpenAI GPT-4o avec vision
        ...

class OllamaService(AIServiceBase):
    def extract_invoice_data(self, image_base64, prompt):
        # Appel API locale Ollama (existant)
        ...
```

**Reference** : Le projet [odoo-llm (Apexive)](https://github.com/apexive/odoo-llm) implemente exactement ce pattern avec un Provider Pattern unifie et une methode `generate()` commune a tous les providers (OpenAI, Anthropic, Ollama, Mistral).

[Confiance: Haute]
_Sources : [LiteLLM Docs](https://docs.litellm.ai/), [Model Agnostic Pattern - Towards AI](https://towardsai.net/p/machine-learning/llm-ai-agent-applications-with-langchain-and-langgraph-part-29-model-agnostic-pattern-and-llm-api-gateway), [Odoo LLM GitHub](https://github.com/apexive/odoo-llm)_

### Gestion des erreurs et rate limiting

#### Anthropic Claude API

- **Rate limits** : Mesures en RPM (requetes/min), ITPM (tokens input/min), OTPM (tokens output/min)
- **Tiers** : De 50 RPM (Tier 1) a 4 000 RPM (Tier 4) pour Claude Sonnet
- **Algorithme** : Token bucket (remplissage continu, pas de reset fixe)
- **SDK Python** : Retry automatique integre (2 tentatives par defaut) avec backoff exponentiel pour erreurs 429, 409, 500+
- **Optimisation** : Le prompt caching peut augmenter le debit effectif de 5x (les tokens caches ne comptent pas dans les limites ITPM)

_Sources : [Claude Rate Limits Docs](https://platform.claude.com/docs/en/api/rate-limits), [Fix Claude 429 Error Guide](https://www.aifreeapi.com/en/posts/fix-claude-api-429-rate-limit-error)_

#### OpenAI GPT API

- **Rate limits** : RPM et TPM par tier d'utilisation
- **Headers de monitoring** : `x-ratelimit-limit-requests`, `x-ratelimit-remaining-requests`, `x-ratelimit-reset-requests`
- **Retry recommande** : Backoff exponentiel avec jitter aleatoire (librairies `tenacity` ou `backoff`)
- **Bonne pratique** : Reduire `max_completion_tokens` au minimum necessaire pour eviter les erreurs de rate limit

_Sources : [OpenAI Rate Limits Guide](https://platform.openai.com/docs/guides/rate-limits), [OpenAI Cookbook - Rate Limits](https://cookbook.openai.com/examples/how_to_handle_rate_limits)_

#### Implementation unifiee pour Odoo

```python
# Pattern de retry unifie
import time
import logging

def call_with_retry(api_call, max_retries=3, base_delay=1.0):
    for attempt in range(max_retries):
        try:
            return api_call()
        except RateLimitError as e:
            retry_after = getattr(e, 'retry_after', base_delay * (2 ** attempt))
            time.sleep(retry_after)
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
    raise MaxRetriesExceeded()
```

[Confiance: Haute]

### Securite et gestion des cles API

#### Stockage dans Odoo

Les cles API doivent etre stockees dans le modele `jsocr.config` existant (ou `ir.config_parameter`) avec les precautions suivantes :

- **Champs chiffres** : Utiliser `fields.Char` avec `groups="base.group_system"` pour limiter l'acces aux administrateurs
- **Jamais en clair dans le code** : Les cles ne doivent jamais etre committees dans le repository git
- **Rotation reguliere** : Rotation mensuelle pour les cles a faible privilege, hebdomadaire pour les cles a haut privilege
- **Permissions granulaires** : Si le fournisseur le permet, creer des cles avec acces restreint (modeles specifiques uniquement)

#### Bonnes pratiques de securite

| Pratique | Implementation |
|----------|---------------|
| Stockage | `jsocr.config` avec `groups="base.group_system"` |
| Transport | HTTPS obligatoire (TLS 1.2+) |
| Logging | Ne jamais loguer les cles API ou les donnees sensibles de factures |
| Acces | Role-based : seuls les admins voient/modifient les cles |
| Rotation | Champ "date derniere rotation" + alerte automatique |
| Fallback | Si cle invalide/expiree, fallback vers Ollama local |

[Confiance: Haute]
_Sources : [OpenAI API Key Best Practices](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety), [API Key Management Best Practices](https://blog.gitguardian.com/secrets-api-management/), [Odoo LLM Security](https://github.com/apexive/odoo-llm)_

### Formats de donnees et communication

#### Format d'echange standard

Les deux APIs utilisent **JSON sur HTTPS** (REST) :

- **Anthropic** : `POST https://api.anthropic.com/v1/messages` avec header `x-api-key`
- **OpenAI** : `POST https://api.openai.com/v1/chat/completions` avec header `Authorization: Bearer`
- **Ollama** : `POST http://localhost:11434/api/generate` (local, pas d'auth)

#### Schema de reponse unifie (pour notre module)

```json
{
  "provider": "claude|openai|ollama",
  "model": "claude-sonnet-4-5|gpt-4o|llama3.2-vision",
  "extracted_data": {
    "supplier": {"value": "ACME Corp", "confidence": 97},
    "date": {"value": "2026-01-15", "confidence": 95},
    "invoice_number": {"value": "INV-2026-001", "confidence": 92},
    "total": {"value": 1250.00, "confidence": 98},
    "lines": [...]
  },
  "usage": {"input_tokens": 1500, "output_tokens": 800, "cost_estimate": 0.012}
}
```

[Confiance: Haute]

### Strategie de fallback et resilience

Le pattern recommande pour notre module Odoo :

```
1. Tentative avec le provider configure (ex: Claude)
   ├── Succes → retourner les donnees
   └── Echec (rate limit, timeout, erreur API)
       ├── 2. Tentative avec provider secondaire (ex: OpenAI)
       │   ├── Succes → retourner les donnees
       │   └── Echec
       │       └── 3. Fallback vers Ollama local
       │           ├── Succes → retourner les donnees (qualite reduite)
       │           └── Echec → erreur finale, job en statut "error"
       └── Ou directement Ollama si pas de secondaire configure
```

Ce pattern garantit la resilience : meme si les services cloud sont indisponibles, le traitement continue en local via Ollama.

[Confiance: Haute]
_Sources : [LiteLLM Fallback/Retry](https://docs.litellm.ai/), [Top LLM Gateways 2025](https://agenta.ai/blog/top-llm-gateways)_

## Architectural Patterns and Design

### Architecture systeme recommandee pour le module

L'architecture actuelle du module `js_invoice_ocr_ia` utilise une classe `OllamaService` monolithique dans `services/ai_service.py`. Pour supporter multi-provider, l'architecture recommandee est un **refactoring vers le pattern Factory + Strategy** :

```
js_invoice_ocr_ia/
├── services/
│   ├── ai_service_base.py      # Classe abstraite AIServiceBase
│   ├── ai_service_ollama.py    # OllamaService (existant, refactored)
│   ├── ai_service_claude.py    # ClaudeService (nouveau)
│   ├── ai_service_openai.py    # OpenAIService (nouveau)
│   └── ai_service_factory.py   # Factory pour instancier le bon service
├── models/
│   ├── jsocr_config.py         # + champs provider, api_key, model_name
│   └── ...
```

**Decision architecturale cle :** Le `OllamaService` actuel (450+ lignes) contient a la fois :
1. La logique de communication API (specifique au provider)
2. La logique metier d'extraction (prompts, parsing, confidence) - **partagee entre tous les providers**

Le refactoring doit separer ces deux aspects :
- **`AIServiceBase`** : Contient la logique metier partagee (prompts, calcul de confiance, parsing JSON, `find_supplier()`)
- **Implementations concretes** : Contiennent uniquement l'appel API specifique au provider

[Confiance: Haute]
_Sources : [Design Patterns for AI Engineers](https://www.unite.ai/design-patterns-in-python-for-ai-and-llm-engineers-a-practical-guide/), [Multi-LLM Abstract Classes](https://medium.com/algomart/multi-llm-systems-with-abstract-classes-in-python-038cd6ce78d5), [Dynamic Factory Pattern](https://blacksuan19.dev/blog/llm-dynamic-factory-design-pattern/)_

### Principes de design

| Principe | Application |
|----------|------------|
| **Open/Closed** | Ajouter un nouveau provider sans modifier le code existant |
| **Single Responsibility** | Chaque service ne gere qu'un seul provider |
| **Dependency Inversion** | `jsocr_import_job.py` depend de l'interface abstraite, pas d'une implementation |
| **Factory Method** | `jsocr.config` determine quel service instancier |
| **Strategy** | Le service IA est interchangeable a runtime via la configuration |

**Reference existante dans Odoo :** Odoo utilise deja ce pattern pour ses propres integrations IA. La fonction `request_llm` du module AI natif orchestre les appels vers differents providers (GPT, Gemini) avec un schema de retour unifie.

[Confiance: Haute]
_Sources : [Odoo AI Module Guide](https://oduist.com/blog/odoo-experience-2025-ai-summaries-2/357-developing-odoo-modules-using-ai-a-practical-guide-358), [Odoo Modular Architecture](https://rootstack.com/en/blog/modular-architecture-odoo-how-it-works-and-why-its-key-successful-implementation)_

### Scalabilite et traitement en arriere-plan

Le module actuel traite les factures via des **cron jobs Odoo** (`ir.cron`). Pour l'integration cloud, des considerations supplementaires s'imposent :

**Traitement synchrone (actuel) :**
- Un import job traite une facture a la fois
- Adapte pour Ollama local (pas de rate limiting)
- Latence acceptable (5-30 sec par facture)

**Traitement avec APIs cloud (recommande) :**
- **Rate limiting** : Les APIs cloud ont des limites RPM/TPM. Pour des lots importants, utiliser le Batch API (50% de reduction, traitement sous 24h)
- **Queue OCA** : Le module [OCA/queue](https://github.com/OCA/queue) offre un framework de jobs asynchrones mature pour Odoo
- **Cron workers** : Possibilite de paralleliser via plusieurs `ir.cron` records
- **Estimation de cout** : Calculer le cout avant le traitement d'un lot et alerter l'utilisateur

| Volume | Approche recommandee | Cout estime (Claude Sonnet) |
|--------|---------------------|----------------------------|
| 1-10 factures/jour | Synchrone, API standard | ~$0.10/jour |
| 10-50 factures/jour | Synchrone avec retry | ~$0.50/jour |
| 50-200 factures/jour | Batch API (async 24h) | ~$1.00/jour (50% reduc) |
| 200+ factures/jour | Queue OCA + Batch API | Selon volume |

[Confiance: Haute]
_Sources : [OCA Queue GitHub](https://github.com/OCA/queue), [Odoo AI Jobs Module](https://apps.odoo.com/apps/modules/16.0/evh_ai_jobs), [Odoo Scalability Trends](https://medium.com/@jacobweber005/odoo-app-development-trends-to-watch-in-2025-ce35a8503ca9)_

### Architecture de securite

```
┌─────────────────────────────────────────────┐
│ Odoo 18 (js_invoice_ocr_ia)                 │
│                                             │
│  jsocr.config                               │
│  ┌─────────────────────────────────────┐    │
│  │ provider: claude|openai|ollama      │    │
│  │ api_key: ******* (groups=admin)     │    │
│  │ model_name: claude-sonnet-4-5       │    │
│  │ fallback_provider: ollama           │    │
│  │ max_cost_per_batch: 5.00            │    │
│  └─────────────────────────────────────┘    │
│                                             │
│  AIServiceFactory                           │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ │
│  │ Claude    │ │ OpenAI    │ │ Ollama    │ │
│  │ Service   │ │ Service   │ │ Service   │ │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ │
│        │              │              │       │
└────────┼──────────────┼──────────────┼───────┘
         │ HTTPS/TLS    │ HTTPS/TLS    │ HTTP local
         ▼              ▼              ▼
   api.anthropic.com  api.openai.com  localhost:11434
```

**Mesures de securite :**
- Cles API stockees avec `groups="base.group_system"` (admin uniquement)
- Communications cloud en HTTPS/TLS 1.2+ obligatoire
- Pas de donnees de facture dans les logs (NFR8 du module existant)
- Estimation de cout avant traitement de lots
- Alerte si le cout depasse un seuil configure

[Confiance: Haute]
_Sources : [OpenAI API Key Best Practices](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety), [Security for LLM APIs](https://www.rohan-paul.com/p/security-and-privacy-considerations)_

### Architecture de donnees

Le schema `jsocr_confidence_data` existant est **deja compatible** avec le multi-provider. Ajout recommande :

```json
{
  "supplier": {"value": "ACME Corp", "confidence": 97},
  "date": {"value": "2026-01-15", "confidence": 95},
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

Le champ `_metadata` est prefixe par `_` pour ne pas interferer avec les champs de confiance existants. Il permet le suivi des couts et performances par provider.

**Champs supplementaires pour `jsocr.config` :**

| Champ | Type | Description |
|-------|------|-------------|
| `ai_provider` | Selection | `ollama`, `claude`, `openai` |
| `ai_api_key` | Char | Cle API (admin only) |
| `ai_model_name` | Char | Nom du modele |
| `ai_fallback_provider` | Selection | Provider de fallback |
| `ai_max_cost_per_batch` | Float | Cout max par lot ($) |
| `ai_base_url` | Char | URL de base (pour Ollama custom) |

[Confiance: Haute]

## Implementation Approaches and Technology Adoption

### Strategie d'adoption graduelle

La migration vers le multi-provider doit suivre une approche **incrementale en 4 phases** pour minimiser les risques :

**Phase 1 - Abstraction (sans changement fonctionnel)**
- Extraire l'interface abstraite `AIServiceBase` depuis le `OllamaService` existant
- Refactorer `OllamaService` pour implementer cette interface
- Tous les tests existants doivent continuer a passer
- **Zero regression** : Le module fonctionne exactement comme avant

**Phase 2 - Premier provider cloud (Claude)**
- Implementer `ClaudeService` avec le SDK Anthropic
- Ajouter les champs de configuration dans `jsocr.config`
- Implementer le `AIServiceFactory`
- Tests unitaires avec mock des appels API
- Deploiement : l'administrateur peut basculer entre Ollama et Claude

**Phase 3 - Second provider + fallback**
- Implementer `OpenAIService` avec le SDK OpenAI
- Implementer la logique de fallback en cascade
- Ajouter le tracking des couts (_metadata)
- Tests d'integration avec les deux providers

**Phase 4 - Optimisation**
- Batch API pour les traitements de volume
- Dashboard de suivi des couts
- Alertes de depassement de budget
- Prompt caching (Anthropic) pour reduire les couts

[Confiance: Haute]
_Sources : [Gradual Migration Strategy](https://closeloop.com/blog/llms-in-legacy-system-migration/), [Google Code Migration Case Study](https://arxiv.org/pdf/2504.09691)_

### Testing et qualite

#### Strategie de test pour le multi-provider

| Type de test | Outil | Objectif |
|-------------|-------|----------|
| Unitaire | `unittest.mock.patch()` | Mocker les appels API externes |
| Integration | `TransactionCase` Odoo | Tester le flux complet avec mocks |
| Contrat | JSON Schema validation | Verifier le format de reponse de chaque provider |
| Regression | Tests existants | S'assurer que le refactoring ne casse rien |

```python
# Exemple de test avec mock pour ClaudeService
from unittest.mock import patch, MagicMock

class TestClaudeService(TransactionCase):
    @patch('anthropic.Anthropic')
    def test_extract_invoice_data(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text='{"supplier": "ACME", ...}')]
        )
        service = ClaudeService(api_key='test-key', model='claude-sonnet-4-5')
        result = service.extract_invoice_data(image_b64, prompt)
        self.assertIn('supplier', result)
```

**Bonne pratique Odoo** : Les tests doivent etre dans `tests/` avec des noms commencant par `test_` et importes depuis `tests/__init__.py`. Utiliser `@tagged('post_install', '-at_install', 'jsocr')`.

[Confiance: Haute]
_Sources : [Odoo 18 Testing Docs](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html), [Python Mock Library - Real Python](https://realpython.com/testing-third-party-apis-with-mocks/)_

### Suivi des couts et monitoring

Pour un module Odoo, le suivi des couts peut etre integre directement sans outil externe :

| Fonctionnalite | Implementation |
|---------------|----------------|
| Tracking par requete | Champ `_metadata` dans `jsocr_confidence_data` (cout, tokens) |
| Tracking par job | Champs `ai_cost`, `ai_tokens_used` sur `jsocr.import.job` |
| Dashboard | Vue liste groupee par mois/provider avec sommes |
| Alerte budget | Verification avant chaque lot dans `jsocr.config.ai_max_cost_per_batch` |
| Historique | Table `jsocr.ai.usage` (optionnel) pour reporting detaille |

**Outils externes (optionnels, pour usage avance) :**
- [Langfuse](https://langfuse.com/docs/observability/features/token-and-cost-tracking) : Suivi open-source avec API de metriques quotidiennes
- [LiteLLM](https://docs.litellm.ai/docs/proxy/cost_tracking) : Tracking automatique par cle/utilisateur/equipe

[Confiance: Haute]
_Sources : [Langfuse Cost Tracking](https://langfuse.com/docs/observability/features/token-and-cost-tracking), [LiteLLM Spend Tracking](https://docs.litellm.ai/docs/proxy/cost_tracking), [Traceloop Token Usage](https://www.traceloop.com/blog/from-bills-to-budgets-how-to-track-llm-token-usage-and-cost-per-user)_

### Evaluation des risques et mitigation

| Risque | Impact | Probabilite | Mitigation |
|--------|--------|-------------|------------|
| Indisponibilite API cloud | Haut | Moyen | Fallback automatique vers Ollama |
| Depassement de cout | Moyen | Moyen | Plafond par lot + alerte |
| Fuite de cle API | Haut | Faible | Admin-only + rotation reguliere |
| Changement de pricing API | Moyen | Moyen | Abstraction multi-provider, facilite le switch |
| Qualite extraction variable | Moyen | Faible | Tests de regression + metriques de confiance |
| Donnees sensibles dans le cloud | Haut | Selon reglementation | Option Ollama local pour clients sensibles |
| Rate limiting en pic | Moyen | Moyen | Retry avec backoff + queue pour gros volumes |

## Recommandations techniques finales

### Recommandation de provider

| Critere | Recommandation | Justification |
|---------|---------------|---------------|
| **Provider principal** | **Claude Sonnet 4.5** | JSON valide 100%, excellent sur documents complexes, cout competitif |
| **Provider secondaire** | **GPT-4o** | Structured outputs natifs, bonne precision, alternative fiable |
| **Fallback** | **Ollama (local)** | Zero cout, zero latence reseau, confidentialite totale |
| **Modele economique** | Claude Haiku 4.5 | Pour les factures simples/recurrentes (5x moins cher) |

### Roadmap d'implementation

```
Phase 1 : Abstraction (1 sprint)
├── Extraire AIServiceBase depuis OllamaService
├── Refactorer OllamaService -> implemente AIServiceBase
├── Factory + configuration dans jsocr.config
└── Tests de non-regression

Phase 2 : Claude Service (1 sprint)
├── Implementer ClaudeService
├── pip install anthropic dans requirements.txt
├── Tests unitaires avec mocks
└── Documentation configuration

Phase 3 : OpenAI Service + Fallback (1 sprint)
├── Implementer OpenAIService
├── pip install openai dans requirements.txt
├── Logique de fallback en cascade
└── Tests d'integration

Phase 4 : Optimisation (1 sprint)
├── Tracking des couts et usage
├── Dashboard de monitoring
├── Batch API pour gros volumes
└── Prompt caching (Claude)
```

### Dependances Python a ajouter

```
# requirements.txt
anthropic>=0.40.0    # SDK Anthropic Claude
openai>=1.50.0       # SDK OpenAI GPT
```

### Metriques de succes

| KPI | Objectif | Mesure |
|-----|----------|--------|
| Precision extraction | > 95% | Taux de corrections utilisateur |
| Cout par facture | < $0.02 | Tracking dans _metadata |
| Disponibilite | > 99.5% | Taux d'echec des jobs (avec fallback) |
| Temps de traitement | < 10 sec | Champ processing_time_ms |
| Satisfaction utilisateur | Reduction des corrections | Comparaison avant/apres |
