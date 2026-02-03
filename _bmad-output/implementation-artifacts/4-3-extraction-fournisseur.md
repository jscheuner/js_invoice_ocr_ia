# Story 4.3: Extraction Fournisseur

Status: done

## Story

As a **systeme**,
I want **extraire le nom/identifiant du fournisseur depuis la reponse IA**,
So that **le fournisseur Odoo puisse etre associe** (FR12).

## Acceptance Criteria

1. **AC1: Extraction nom fournisseur**
   - **Given** une reponse JSON de l'IA
   - **When** le systeme parse la reponse
   - **Then** le champ supplier_name est extrait
   - **And** la valeur est stockee dans extracted_supplier_name

2. **AC2: Recherche partenaire par nom**
   - **Given** un nom de fournisseur extrait
   - **When** une recherche est effectuee dans res.partner
   - **Then** la recherche inclut le champ name (exact et partiel)
   - **And** la recherche est case-insensitive

3. **AC3: Recherche partenaire par alias**
   - **Given** un nom de fournisseur extrait
   - **When** la recherche par nom echoue
   - **Then** une recherche est effectuee dans jsocr_aliases
   - **And** le partner avec l'alias correspondant est trouve

4. **AC4: Fournisseur non trouve**
   - **Given** un nom de fournisseur sans correspondance
   - **When** aucun partenaire n'est trouve
   - **Then** le champ partner_id reste vide
   - **And** la correction manuelle sera possible

## Tasks / Subtasks

- [x] **Task 1: Parser le nom fournisseur** (AC: #1)
  - [x] Extraire supplier_name de la reponse JSON
  - [x] Stocker dans job.extracted_supplier_name
  - [x] Gerer les cas null/vide

- [x] **Task 2: Implementer la recherche** (AC: #2, #3)
  - [x] Methode `find_supplier(env, supplier_name)`
  - [x] Recherche par nom exact (ilike)
  - [x] Recherche par nom partiel
  - [x] Recherche par alias (Partner.find_by_alias)

- [x] **Task 3: Associer le partenaire** (AC: #2, #4)
  - [x] Stocker partner_id dans le job
  - [x] Logger le resultat de la recherche
  - [x] Gerer le cas "non trouve"

- [x] **Task 4: Tests** (AC: #1-#4)
  - [x] Test extraction nom valide
  - [x] Test recherche par nom exact
  - [x] Test recherche par alias
  - [x] Test fournisseur non trouve

## Dev Notes

### Search Strategy
1. Exact name match (ilike)
2. Partial name match (ilike)
3. Alias match (find_by_alias from res_partner.py)

### Technical Requirements
- Recherche uniquement les companies (is_company=True)
- Performance: doit rester < 1s meme avec beaucoup de partenaires
- Logs sans le nom du fournisseur (NFR8)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.5

### Completion Notes List
- find_supplier method searches by name and alias
- Partner ID stored in job when found
- Supplier name stored even if not matched
- Full test coverage for matching scenarios

### File List

**Files modified:**
- `js_invoice_ocr_ia/services/ai_service.py` - find_supplier method
- `js_invoice_ocr_ia/models/jsocr_import_job.py` - partner_id field, _store_extracted_data
- `js_invoice_ocr_ia/tests/test_ai_service.py` - TestSupplierMatching class

## Change Log
- **2026-02-02**: Story implemented as part of Epic 4 batch
