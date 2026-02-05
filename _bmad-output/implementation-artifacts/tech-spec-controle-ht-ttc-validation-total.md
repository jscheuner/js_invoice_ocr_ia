---
title: 'Controle intelligent HT/TTC et validation total facture'
slug: 'controle-ht-ttc-validation-total'
created: '2026-02-04'
status: 'completed'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Odoo 18', 'Python', 'account.tax', 'account.move', 'account.move.line']
files_to_modify: ['js_invoice_ocr_ia/models/jsocr_import_job.py', 'js_invoice_ocr_ia/models/account_move.py', 'js_invoice_ocr_ia/views/account_move_views.xml']
code_patterns: ['ORM command tuples (0,0,vals)', 'invoice.write for line creation', 'ensure_one pattern', 'json.loads/dumps for extracted data', '_logger for tracing']
test_patterns: ['TransactionCase base', '@tagged post_install -at_install jsocr', 'setUp with fixtures', '_create_* helper methods', 'mock requests.post']
---

# Tech-Spec: Controle intelligent HT/TTC et validation total facture

**Created:** 2026-02-04

## Overview

### Problem Statement

Le systeme met le `price_unit` tel quel depuis l'extraction IA sans savoir si c'est un montant HT ou TTC. Si la taxe du compte predit attend du TTC (price_include_override = 'tax_included') mais que l'IA a extrait un montant HT (ou l'inverse), le total de la facture sera faux. De plus, aucune validation du total extrait vs total calcule n'est effectuee.

### Solution (Approche Hybride - Tree of Thoughts)

**Etape 1 - Detection globale HT/TTC :**
Sommer tous les `price_unit * quantity` extraits par l'IA (en valeur absolue pour gerer les avoirs) et comparer :
- Si somme ≈ `extracted_amount_untaxed` → montants extraits = HT
- Si somme ≈ `extracted_amount_total` → montants extraits = TTC
- Sinon → indetermine

**Etape 2 - Adaptation par ligne au besoin d'Odoo :**
Pour chaque ligne, lire la taxe du compte predit via `price_include_override` :
- Si montants extraits HT mais taxe attend TTC → `price_unit = montant * (1 + taux_taxe)`
- Si montants extraits TTC mais taxe attend HT → `price_unit = montant / (1 + taux_taxe)`
- Si indetermine → garder tel quel + warning + confiance basse

**Etape 3 - Validation post-creation :**
Comparer `invoice.amount_total` vs `extracted_amount_total` (tolerance fixe 0.03).
Si ecart → warning + baisse de confiance + flag mismatch

### Scope

**In Scope:**
- Detection HT/TTC par ligne via comparaison montants extraits
- Lecture `price_include_override` sur `account.tax` lie au compte predit
- Ajustement `price_unit` dans `_create_invoice_lines`
- Validation total post-creation des lignes
- Warning/flag si ecart non resolu
- Ajustement indice de confiance du montant
- Gestion des avoirs (quantites negatives)
- Gestion multi-taxes (taux combine)

**Out of Scope:**
- Modification du prompt IA (on travaille avec ce que l'IA extrait deja)
- Gestion multi-devises
- Modification des taxes Odoo

## Context for Development

### Codebase Patterns

- **Creation lignes** : `invoice.write({'invoice_line_ids': [(0, 0, line_vals)]})` - ORM command tuples (Odoo 18)
- **Prediction compte** : Pipeline 3 tiers dans `_predict_line_account()` : patterns → historique → fallback
- **JSON extracted_lines** : `[{description, quantity, unit_price, amount}]` - le champ `amount` est aussi disponible (total ligne)
- **Montants extraits** : `extracted_amount_untaxed`, `extracted_amount_tax`, `extracted_amount_total` sur jsocr.import.job
- **Confiance** : JSON sur `account.move.jsocr_confidence_data` avec schema `{field: {value, confidence}}`
- **Logging** : `_logger.info/warning/debug` avec prefix "JSOCR:"
- **Taxes Odoo 18** : `account.tax.price_include_override` (selection: 'tax_included'/'tax_excluded'/False), `account.tax.amount` (taux en %), `account.account.tax_ids` (M2M vers taxes par defaut)
- **Auto-assignation taxes** : `_compute_tax_ids()` sur account.move.line appelle `_get_computed_taxes()` qui lit `account_id.tax_ids` pour les documents achat
- **Syntaxe Odoo 17+** : Utiliser `invisible="condition"` au lieu de `attrs="{'invisible': [...]}"` (deprecated)

### Files to Reference

| File | Purpose | Lignes cles |
| ---- | ------- | ----------- |
| `js_invoice_ocr_ia/models/jsocr_import_job.py` | Pipeline creation facture et lignes | `_create_invoice_lines` (907-983), `_create_draft_invoice` (854-905), `_predict_line_account` (1081-1121), `_get_expense_account` (985-1017), `_store_extracted_data` (778-813) |
| `js_invoice_ocr_ia/models/account_move.py` | Extension account.move avec champs JSOCR | `jsocr_amount_alert`, `jsocr_global_confidence`, `set_field_confidence` (190-249) |
| `js_invoice_ocr_ia/services/ai_service.py` | Service IA avec calcul confiance montants | `_calculate_amounts_confidence` (504-550), poids confiance: amounts=40/100 |

### Technical Decisions

- Tolerance validation total : **0.03 fixe** (pas de tolerance relative pour eviter les incoherences)
- Le controle HT/TTC se base sur `account.tax.price_include_override`
- Les montants extraits sont `extracted_amount_total`, `extracted_amount_untaxed`, `extracted_amount_tax`
- La detection se fait AVANT la creation des lignes (lire account.account.tax_ids manuellement)
- Utiliser **valeurs absolues** pour la somme des lignes (gestion avoirs)
- **Multi-taxes** : calculer le taux combine en sommant les taux des taxes
- **Guard clause** : verifier que le diviseur (1 + taux) n'est jamais 0

### First Principles (Analyse fondamentale)

1. **Le `price_unit` est interprete selon la taxe** : C'est la taxe (via `price_include_override` ou `price_include`) qui decide si Odoo lit le montant comme HT ou TTC, pas le `price_unit` lui-meme.

2. **La taxe vient du compte** : En settant `account_id`, Odoo herite automatiquement des taxes via `account.account.tax_ids` et `_compute_tax_ids`. Pas besoin de setter `tax_ids` manuellement.

3. **L'IA extrait un nombre brut sans semantique** : La detection HT/TTC se fait en comparant `sum(abs(price_unit * qty))` avec `extracted_amount_untaxed` (HT) et `extracted_amount_total` (TTC).

4. **La conversion utilise le taux de la taxe** : `account.tax.amount` contient le taux (ex: 8.1 pour TVA suisse). Conversion : `prix_ttc = prix_ht * (1 + taux/100)`.

5. **L'ordre est critique - lire la taxe AVANT de creer la ligne** :
   - Lire `account.account.tax_ids` du compte predit
   - Determiner `price_include_override` de la taxe
   - Ajuster `price_unit` si mismatch
   - Puis seulement creer la ligne via `invoice.write({'invoice_line_ids': [(0, 0, vals)]})`

6. **Determination TTC/HT de la taxe** :
   ```python
   tax_expects_ttc = (tax.price_include_override == 'tax_included'
                      or (not tax.price_include_override and tax.price_include))
   ```

## Implementation Plan

### Tasks

- [x] **Task 1 : Methode `_detect_amounts_type`** (Detection globale HT/TTC)
  - File : `js_invoice_ocr_ia/models/jsocr_import_job.py`
  - Action : Creer une nouvelle methode `_detect_amounts_type(self, lines)` qui :
    1. **Guard clause** : Si `lines` est vide, retourner `'unknown'`
    2. Calcule `sum_lines = sum(abs(line.get('unit_price', 0.0) * line.get('quantity', 1.0)) for line in lines)`
    3. **Guard clause null** : Si `self.extracted_amount_untaxed` est None ou 0 ET `self.extracted_amount_total` est None ou 0, retourner `'unknown'`
    4. **Tolerance fixe** : `tolerance = 0.03`
    5. **Ordre de comparaison explicite** : D'abord comparer avec `extracted_amount_untaxed` (si match → `'ht'`), puis avec `extracted_amount_total` (si match → `'ttc'`), sinon `'unknown'`
    6. Logger le resultat avec les valeurs comparees
  - Notes : La comparaison HT est faite en premier car si HT = TTC (pas de taxe), on veut retourner `'ht'` par defaut.

- [x] **Task 2 : Methode `_get_tax_for_account`** (Lecture taxe du compte)
  - File : `js_invoice_ocr_ia/models/jsocr_import_job.py`
  - Action : Creer une methode `_get_tax_for_account(self, account_id)` qui :
    1. **Guard clause** : Si `account_id` est None ou 0, retourner `None`
    2. Lit `account = self.env['account.account'].browse(account_id)`
    3. **Guard clause** : Si `not account.exists()`, retourner `None`
    4. Filtre `account.tax_ids` pour garder les taxes d'achat (`type_tax_use in ('purchase', 'none')`)
    5. **Multi-taxes (F3)** : Calculer le taux combine `total_rate = sum(tax.amount for tax in purchase_taxes)`
    6. **Determination TTC** : Une seule taxe TTC suffit pour considerer le tout comme TTC
       ```python
       any_tax_expects_ttc = any(
           tax.price_include_override == 'tax_included'
           or (not tax.price_include_override and tax.price_include)
           for tax in purchase_taxes
       )
       ```
    7. Retourne `{'tax_expects_ttc': bool, 'tax_rate': float}` ou `None` si pas de taxe
    8. Logger le taux et le type (HT/TTC) pour tracabilite
  - Notes : Gestion multi-taxes par sommation des taux (simplifie, couvre 95% des cas).

- [x] **Task 3 : Methode `_adjust_price_unit`** (Conversion prix)
  - File : `js_invoice_ocr_ia/models/jsocr_import_job.py`
  - Action : Creer une methode `_adjust_price_unit(self, price_unit, amounts_type, tax_info)` qui :
    1. Si `tax_info` est None → retourner `(price_unit, False)` (pas de taxe)
    2. Si `amounts_type == 'unknown'` → retourner `(price_unit, False)`
    3. **Guard clause division par zero (F1)** :
       ```python
       divisor = 1 + tax_info['tax_rate'] / 100
       if divisor <= 0:
           _logger.warning("JSOCR: Invalid tax rate %s, skipping conversion", tax_info['tax_rate'])
           return (price_unit, False)
       ```
    4. Si `amounts_type == 'ht'` et `tax_info['tax_expects_ttc']` → `price_unit = price_unit * divisor`
    5. Si `amounts_type == 'ttc'` et pas `tax_info['tax_expects_ttc']` → `price_unit = price_unit / divisor`
    6. Sinon → pas de conversion necessaire
    7. Arrondir a 2 decimales avec `round(price_unit, 2)`
    8. Logger : `"JSOCR: Adjusted price %.2f -> %.2f (type=%s, tax_rate=%.2f%%, expects_ttc=%s)"`
    9. Retourner `(adjusted_price_unit, was_adjusted: bool)`

- [x] **Task 4 : Integrer dans `_create_invoice_lines`** (Orchestration)
  - File : `js_invoice_ocr_ia/models/jsocr_import_job.py`
  - Action : Modifier `_create_invoice_lines(self, invoice)` pour :
    1. Apres le parsing des lignes JSON, appeler `amounts_type = self._detect_amounts_type(lines)`
    2. Si `amounts_type == 'unknown'` → logger un warning et mettre un flag pour reduire la confiance
    3. Dans la boucle `for line in lines`, apres la prediction du compte :
       - `original_price = line.get('unit_price', 0.0)`
       - Appeler `tax_info = self._get_tax_for_account(account_id)`
       - Appeler `adjusted_price, was_adjusted = self._adjust_price_unit(original_price, amounts_type, tax_info)`
       - Utiliser `adjusted_price` dans `line_vals['price_unit']`
    4. Apres la boucle, si `amounts_type == 'unknown'`, setter `invoice.jsocr_amount_mismatch = True`

- [x] **Task 5 : Methode `_validate_invoice_total`** (Validation post-creation)
  - File : `js_invoice_ocr_ia/models/jsocr_import_job.py`
  - Action : Creer une methode `_validate_invoice_total(self, invoice)` qui :
    1. **Guard clause (F6)** : Si `self.extracted_amount_total` est None ou 0, logger debug et retourner `True` (pas de validation possible)
    2. Calcule `ecart = abs(invoice.amount_total - self.extracted_amount_total)`
    3. **Tolerance fixe (F4)** : `tolerance = 0.03`
    4. Si `ecart <= tolerance` → logger debug, retourner `True`
    5. Si `ecart > tolerance` :
       - Logger warning avec les deux valeurs
       - `invoice.jsocr_amount_mismatch = True`
       - Calculer confidence : `50 if ecart < 1.0 else 30`
       - Appeler `invoice.set_field_confidence('total', self.extracted_amount_total, confidence)`
       - Retourner `False`

- [x] **Task 6 : Integrer validation dans `_create_draft_invoice`**
  - File : `js_invoice_ocr_ia/models/jsocr_import_job.py`
  - Action : Dans `_create_draft_invoice`, apres `self._create_invoice_lines(invoice)`, appeler `self._validate_invoice_total(invoice)`
  - Notes : Appeler apres la creation des lignes car `invoice.amount_total` n'est calcule qu'a ce moment

- [x] **Task 7 : Champ `jsocr_amount_mismatch` sur account.move**
  - File : `js_invoice_ocr_ia/models/account_move.py`
  - Action : Ajouter un champ Boolean `jsocr_amount_mismatch` pour signaler visuellement un ecart de montant :
    ```python
    jsocr_amount_mismatch = fields.Boolean(
        string='Amount Mismatch',
        default=False,
        help='True if extracted total differs from computed total by more than 0.03, '
             'or if HT/TTC detection was inconclusive',
    )
    ```
  - Notes : Mis a True par `_validate_invoice_total` ou `_create_invoice_lines` (si unknown). Initialise a False.

- [x] **Task 8 : Affichage warning dans la vue facture**
  - File : `js_invoice_ocr_ia/views/account_move_views.xml`
  - Action : Ajouter un bandeau d'alerte dans la vue formulaire heritee quand `jsocr_amount_mismatch` est True :
    ```xml
    <div class="alert alert-warning" role="alert"
         invisible="not jsocr_amount_mismatch">
        Ecart detecte entre le total extrait par l'IA et le total calcule de la facture.
        Verifiez les montants des lignes (HT/TTC).
    </div>
    ```
  - Notes : Utiliser la syntaxe Odoo 17+ `invisible="condition"` au lieu de `attrs` (F7). Positionner apres le bandeau `jsocr_amount_alert` existant.

### Acceptance Criteria

- [ ] **AC1** : Given une facture avec lignes HT et taxe `price_include_override='tax_excluded'`, when le systeme cree les lignes, then `price_unit` reste inchange (HT vers HT = pas de conversion)

- [ ] **AC2** : Given une facture avec lignes HT et taxe `price_include_override='tax_included'`, when le systeme cree les lignes, then `price_unit` est converti en TTC (`prix * (1 + taux/100)`)

- [ ] **AC3** : Given une facture avec lignes TTC et taxe `price_include_override='tax_excluded'`, when le systeme cree les lignes, then `price_unit` est converti en HT (`prix / (1 + taux/100)`)

- [ ] **AC4** : Given une facture avec lignes TTC et taxe `price_include_override='tax_included'`, when le systeme cree les lignes, then `price_unit` reste inchange (TTC vers TTC = pas de conversion)

- [ ] **AC5** : Given des montants extraits qui ne matchent ni le total HT ni le total TTC, when le systeme detecte les montants, then `amounts_type = 'unknown'`, les prix restent inchanges, un warning est logge, et `jsocr_amount_mismatch = True`

- [ ] **AC6** : Given une facture creee avec un total calcule egal au total extrait (ecart <= 0.03), when la validation post-creation s'execute, then `jsocr_amount_mismatch = False`

- [ ] **AC7** : Given une facture creee avec un total calcule different du total extrait (ecart > 0.03), when la validation post-creation s'execute, then `jsocr_amount_mismatch = True` et la confiance du champ 'total' est reduite

- [ ] **AC8** : Given un compte sans taxe liee (account.tax_ids vide), when le systeme cherche la taxe, then `_get_tax_for_account` retourne None et le prix reste inchange

- [ ] **AC9** : Given une facture sans taxe (montants HT = TTC), when la detection s'execute, then le systeme retourne `'ht'` par defaut (car HT est teste en premier)

- [ ] **AC10** : Given une facture OCR avec `jsocr_amount_mismatch = True`, when l'utilisateur ouvre la facture, then un bandeau d'alerte orange est affiche

- [ ] **AC11 (F1)** : Given une taxe avec `amount = -100` (invalide), when le systeme tente une conversion, then aucune division par zero ne se produit et le prix reste inchange avec un warning

- [ ] **AC12 (F3)** : Given un compte avec deux taxes (TVA 8.1% + eco-taxe 2%), when le systeme calcule le taux, then le taux combine est 10.1%

- [ ] **AC13 (F5)** : Given un avoir (credit note) avec quantites negatives, when le systeme detecte le type de montant, then la detection fonctionne correctement (valeurs absolues)

- [ ] **AC14 (F6)** : Given `extracted_amount_total = None` ou `0`, when la validation s'execute, then aucune erreur et validation skippee

- [ ] **AC15 (F8)** : Given une taxe avec `price_include_override = False` et `price_include = True`, when le systeme determine si TTC, then la taxe est consideree comme TTC (fallback sur `price_include`)

## Additional Context

### Dependencies

- Champ `account.tax.price_include_override` (natif Odoo 18)
- Champ `account.tax.amount` (taux en %, natif Odoo 18)
- Champ `account.tax.price_include` (boolean, natif Odoo 18)
- Champ `account.tax.type_tax_use` (selection, natif Odoo 18)
- Champ `account.account.tax_ids` (M2M vers taxes par defaut, natif Odoo 18)
- Champs existants : `extracted_amount_total`, `extracted_amount_untaxed`, `extracted_amount_tax` sur jsocr.import.job
- Methode existante : `set_field_confidence` sur account.move

### Testing Strategy

**Tests unitaires** (`js_invoice_ocr_ia/tests/test_jsocr_import_job.py` ou nouveau fichier `test_ht_ttc_detection.py`) :

1. `test_detect_amounts_type_ht` : Montants lignes = extracted_amount_untaxed → retourne 'ht'
2. `test_detect_amounts_type_ttc` : Montants lignes = extracted_amount_total → retourne 'ttc'
3. `test_detect_amounts_type_unknown` : Montants lignes ne matchent aucun total → retourne 'unknown'
4. `test_detect_amounts_type_no_tax` : HT = TTC (pas de taxe) → retourne 'ht' (ordre explicite)
5. `test_detect_amounts_type_empty_lines` : Lignes vides → retourne 'unknown'
6. `test_detect_amounts_type_null_totals` : extracted_amount_* = None → retourne 'unknown'
7. `test_detect_amounts_type_negative_quantities` : Avoir avec qty < 0 → detection correcte (abs)
8. `test_get_tax_for_account_with_purchase_tax` : Compte avec taxe achat → retourne info taxe
9. `test_get_tax_for_account_no_tax` : Compte sans taxe → retourne None
10. `test_get_tax_for_account_multi_taxes` : Compte avec 2 taxes → taux combine
11. `test_get_tax_for_account_invalid_account` : account_id = None → retourne None
12. `test_adjust_price_ht_to_ttc` : HT + taxe attend TTC → prix converti en TTC
13. `test_adjust_price_ttc_to_ht` : TTC + taxe attend HT → prix converti en HT
14. `test_adjust_price_no_conversion` : Meme type → prix inchange
15. `test_adjust_price_unknown` : Type inconnu → prix inchange
16. `test_adjust_price_division_by_zero` : tax_rate = -100 → pas de crash, prix inchange
17. `test_adjust_price_rounding` : Verifier arrondi a 2 decimales
18. `test_validate_total_ok` : Ecart <= 0.03 → mismatch = False
19. `test_validate_total_mismatch` : Ecart > 0.03 → mismatch = True + confiance reduite
20. `test_validate_total_null_extracted` : extracted_amount_total = None → validation skippee
21. `test_price_include_fallback` : price_include_override = False, price_include = True → TTC
22. `test_create_invoice_lines_with_adjustment` : Integration complete avec prediction + ajustement + validation

**Tests manuels** :
1. Importer une facture PDF avec montants HT et verifier que les prix sont corrects selon la taxe du compte
2. Importer une facture PDF avec montants TTC et verifier la conversion
3. Verifier que le bandeau d'alerte apparait quand il y a un ecart de total
4. Tester avec un avoir (quantites negatives)

### Notes

- Certaines factures ont le montant HT par ligne, d'autres TTC, d'autres les deux
- Il faut comparer les totaux pour detecter automatiquement quel type de montant l'IA a extrait
- Approche hybride choisie via Tree of Thoughts : detection globale + adaptation par ligne + validation post-creation
- Chemin C selectionne car c'est le seul qui repond aux deux questions : "qu'a extrait l'IA ?" ET "qu'attend Odoo ?"
- JSON extracted_lines contient aussi un champ `amount` par ligne (total ligne) utilisable pour verification future
- TVA suisse : 8.1%, 2.5%, 0.0% sont les taux courants
- Attention aux arrondis : toujours `round(price_unit, 2)` apres conversion
- La tolerance de 0.03 CHF est fixe pour eviter les incoherences (F4)

### Findings corrigees

| Finding | Correction |
|---------|------------|
| F1 - Division par zero | Guard clause `if divisor <= 0` dans Task 3 |
| F3 - Multi-taxes | Sommation des taux dans Task 2 + AC12 |
| F4 - Tolerance incoherente | Tolerance fixe 0.03 partout |
| F5 - Quantites negatives | `abs()` dans Task 1 + AC13 |
| F6 - Null check | Guard clauses dans Task 1 et 5 + AC14 |
| F7 - Syntaxe attrs | `invisible="condition"` dans Task 8 |
| F8 - Fallback price_include | AC15 ajoute |

## Review Notes

- **Adversarial review completed:** 2026-02-05
- **Findings:** 7 total, 4 fixed, 3 skipped
- **Resolution approach:** Walk-through

### Fixes appliques lors de la review:
- F2: Reset du flag `jsocr_amount_mismatch` quand validation passe
- F6: Pas de conversion marquee comme ajustee pour taux 0%
- F7: Warning logge si `set_field_confidence` echoue
- F10: Bouton "Revalider le total" ajoute dans la vue

### Future enhancement identifiee:
- **Extraction et matching des taux TVA par ligne:** Modifier le prompt IA pour extraire les taux TVA par ligne, permettant un matching precis avec les taxes Odoo et une meilleure gestion multi-taux.
