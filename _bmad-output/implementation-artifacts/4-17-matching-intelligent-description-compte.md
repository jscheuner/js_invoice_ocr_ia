# Story 4.17: Matching Intelligent Description -> Compte

Status: done

## Story

As a **systeme**,
I want **predire le compte de charge le plus probable pour chaque ligne de facture base sur la similarite des descriptions**,
So that **les lignes soient pre-remplies avec le bon compte**.

## Acceptance Criteria

1. **AC1: Comparaison descriptions**
   - **Given** une ligne de facture a creer avec une description
   - **And** l'historique des lignes du fournisseur
   - **When** le systeme calcule le compte a utiliser
   - **Then** la description de la ligne actuelle est comparee aux descriptions historiques

2. **AC2: Algorithme de matching**
   - **Given** les descriptions a comparer
   - **When** l'algorithme s'execute
   - **Then** il utilise correspondance exacte (priorite max), mots-cles communs normalises, score de similarite

3. **AC3: Calcul confiance**
   - **Given** des matches trouves
   - **When** le compte est determine
   - **Then** un score de confiance (0-100%) est calcule base sur nombre de matches et frequence du compte

4. **AC4: Fallback**
   - **Given** aucun match trouve (confiance < 30%)
   - **When** le systeme determine le compte
   - **Then** le fallback _get_expense_account() est utilise

## Tasks / Subtasks

- [x] **Task 1: Normalisation descriptions** (AC: #1)
  - [x] `_normalize_description(text)`
  - [x] Lowercase, suppression accents, mots vides

- [x] **Task 2: Algorithme de matching** (AC: #2)
  - [x] `_calculate_similarity(desc1, desc2)`
  - [x] Score base sur mots communs / total mots

- [x] **Task 3: Prediction compte** (AC: #3, #4)
  - [x] `_predict_account_from_history(partner_id, line_description)`
  - [x] Retourne (account_id, confidence)
  - [x] Fallback si confiance < 30%

## Dev Notes

### Similarity Algorithm
1. Normaliser les deux descriptions
2. Tokeniser en mots
3. Calculer intersection / union (Jaccard)
4. Score = ratio * 100

### Confidence Calculation
- Nombre de matches avec similarite > 50%
- Frequence du compte dominant parmi les matches
- confidence = min(matches * 20, 100) * frequence_ratio

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- _normalize_description removes accents and stopwords
- _calculate_similarity uses Jaccard index
- _predict_account_from_history returns account_id and confidence
- Falls back to generic expense account when confidence < 30%

### File List

**Files modified:**
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - Added matching methods

## Change Log
- **2026-02-03**: Story implemented
