# Story 4.1: Service Ollama - Connexion et Requete

Status: done

## Story

As a **systeme**,
I want **envoyer des requetes au serveur Ollama et recevoir les reponses**,
So that **l'IA puisse analyser le texte des factures** (FR10).

## Acceptance Criteria

1. **AC1: Connexion Ollama**
   - **Given** un serveur Ollama configure et accessible
   - **When** le service envoie une requete avec un prompt
   - **Then** la requete est envoyee a {ollama_url}/api/generate
   - **And** le timeout est de 120 secondes

2. **AC2: Parsing reponse**
   - **Given** une reponse du serveur Ollama
   - **When** le service recoit la reponse
   - **Then** la reponse JSON est parsee correctement
   - **And** les erreurs de connexion sont capturees et loguees

3. **AC3: Gestion timeout**
   - **Given** un serveur Ollama qui ne repond pas
   - **When** le timeout est atteint (120s)
   - **Then** une erreur de type 'timeout' est retournee
   - **And** le job peut etre reessaye

4. **AC4: Gestion erreur connexion**
   - **Given** un serveur Ollama inaccessible
   - **When** la connexion echoue
   - **Then** une erreur de type 'connection_error' est retournee
   - **And** le message d'erreur est explicite

## Tasks / Subtasks

- [x] **Task 1: Creer le service Ollama** (AC: #1, #2)
  - [x] Creer le fichier `services/ai_service.py`
  - [x] Implementer la classe `OllamaService`
  - [x] Methode `__init__` avec url, model, timeout
  - [x] Methode `test_connection()` pour verifier la connectivite

- [x] **Task 2: Implementer l'envoi de requetes** (AC: #1)
  - [x] Methode `_send_request(prompt)` pour envoyer au endpoint /api/generate
  - [x] Configuration timeout a 120 secondes
  - [x] Configuration temperature basse (0.1) pour extraction consistante

- [x] **Task 3: Gerer les erreurs** (AC: #3, #4)
  - [x] Capturer requests.Timeout
  - [x] Capturer requests.ConnectionError
  - [x] Retourner error_type pour logique retry

- [x] **Task 4: Ecrire les tests** (AC: #1-#4)
  - [x] Test connexion reussie
  - [x] Test timeout
  - [x] Test erreur connexion
  - [x] Tests avec mock requests

## Dev Notes

### Architecture Compliance
- Pattern OllamaService conforme a architecture.md
- Logs avec prefixe JSOCR: sans donnees sensibles
- Timeout 120s respecte NFR1 (< 2 minutes)

### Technical Requirements
- Utilise requests pour HTTP
- Endpoint: POST /api/generate
- Payload: model, prompt, stream=False, options

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Created OllamaService class in services/ai_service.py
- Implemented connection testing and request sending
- Added timeout and connection error handling
- Full test coverage with mocked requests

### File List

**Files created:**
- `js_invoice_ocr_ia/services/ai_service.py` - OllamaService class

**Files modified:**
- `js_invoice_ocr_ia/services/__init__.py` - Added ai_service import
- `js_invoice_ocr_ia/tests/__init__.py` - Added test_ai_service import
- `js_invoice_ocr_ia/tests/test_ai_service.py` - Unit tests

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
