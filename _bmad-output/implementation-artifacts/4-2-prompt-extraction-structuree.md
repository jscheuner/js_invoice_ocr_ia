# Story 4.2: Prompt d'Extraction Structuree

Status: done

## Story

As a **systeme**,
I want **un prompt optimise pour extraire les donnees de facture**,
So that **l'IA retourne des donnees structurees exploitables**.

## Acceptance Criteria

1. **AC1: Structure du prompt**
   - **Given** un texte de facture extrait
   - **When** le prompt est envoye a Ollama
   - **Then** le prompt demande: supplier_name, invoice_date, invoice_number, lines[], amount_untaxed, amount_tax, amount_total

2. **AC2: Format JSON**
   - **Given** le prompt envoye
   - **When** l'IA repond
   - **Then** le prompt specifie le format JSON attendu
   - **And** le prompt inclut un exemple de structure

3. **AC3: Contexte linguistique**
   - **Given** la langue detectee (FR/DE/EN)
   - **When** le prompt est construit
   - **Then** le prompt inclut la langue detectee pour guider l'IA
   - **And** le contexte suisse est mentionne (TVA 7.7%, 2.5%, 0%)

4. **AC4: Gestion formats date**
   - **Given** differents formats de date dans les factures
   - **When** le prompt demande la date
   - **Then** le prompt specifie le format ISO (YYYY-MM-DD)
   - **And** mentionne les formats sources possibles

## Tasks / Subtasks

- [x] **Task 1: Creer le prompt d'extraction** (AC: #1, #2)
  - [x] Methode `_build_extraction_prompt(text, language)`
  - [x] Structure JSON attendue documentee
  - [x] Instructions claires pour l'IA

- [x] **Task 2: Ajouter contexte suisse** (AC: #3)
  - [x] Mention des taux TVA suisses
  - [x] Support formats de montants avec apostrophe (1'234.56)
  - [x] Context linguistique selon la langue

- [x] **Task 3: Documenter les formats** (AC: #4)
  - [x] Format date ISO demande
  - [x] Format montants (float)
  - [x] Format lignes (array d'objets)

## Dev Notes

### Prompt Engineering
Le prompt est concu pour:
- Minimiser les hallucinations (instructions strictes)
- Garantir un format JSON parseable
- Gerer le multilinguisme suisse
- Extraire les donnees meme partielles

### Technical Requirements
- Temperature 0.1 pour consistance
- num_predict: 2000 tokens max
- Instructions de ne pas inventer les donnees manquantes

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- Prompt includes all required fields
- Swiss VAT context included (7.7%, 2.5%, 0%)
- Multi-language support (FR/DE/EN)
- JSON format clearly specified

### File List

**Files modified:**
- `js_invoice_ocr_ia/services/ai_service.py` - _build_extraction_prompt method

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
