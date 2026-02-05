# Sprint Change Proposal - 2026-02-05

## Section 1 : Resume du Probleme

### Declencheur
Amelioration UX identifiee apres la livraison de tous les epics (6/6 done).

### Description du probleme
Le champ `jsocr_global_confidence` (indice de confiance globale OCR, widget progressbar) est actuellement place dans l'onglet **"PDF Source OCR"** du formulaire facture (`account_move_views.xml:47-49`).

L'utilisateur doit cliquer sur cet onglet secondaire pour voir la confiance globale de l'extraction OCR, alors que cette information est **critique** pour evaluer rapidement la fiabilite d'une facture brouillon.

### Changement demande
Deplacer le champ `jsocr_global_confidence` depuis l'onglet "PDF Source OCR" vers la **barre superieure (header)** du formulaire, a cote du bouton "Confirmer" et du widget de statut (Brouillon / Comptabilise).

### Contexte
- Decouvert lors de l'utilisation post-implementation
- Type : Amelioration UX / Ergonomie
- Stories originales : 5.1 (Vue Formulaire Facture avec PDF), 5.2 (Badges de Confiance)

---

## Section 2 : Analyse d'Impact

### Impact Epic
| Epic | Impact | Detail |
|------|--------|--------|
| Epic 5 : Validation & Indicateurs | **Mineur** | Refinement post-livraison sur Stories 5.1/5.2, pas de remise en cause |
| Epics 1-4, 6 | **Aucun** | Non concernes |

### Impact Stories
| Story | Impact | Detail |
|-------|--------|--------|
| 5.1 : Vue Formulaire Facture avec PDF | **Modification UI** | Retrait du champ du tab PDF Source OCR |
| 5.2 : Badges de Confiance par Champ | **Modification UI** | Ajout du champ dans le header |
| Autres stories | **Aucun** | Non impactees |

### Conflits Artefacts
| Artefact | Conflit | Detail |
|----------|---------|--------|
| PRD | **Aucun** | FR22/FR45 exigent l'affichage des indicateurs de confiance - le deplacement ameliore la visibilite |
| Architecture | **Aucun** | Pas de changement de modele, API ou composant |
| UI/UX | **Mineur** | Layout formulaire modifie (champ deplace, pas ajoute/retire) |

### Impact Technique
- **Fichiers modifies** : 1 seul fichier XML (`js_invoice_ocr_ia/views/account_move_views.xml`)
- **Changements Python** : Aucun
- **Changements modele** : Aucun
- **Migration de donnees** : Aucune
- **Tests impactes** : Aucun (pas de tests UI existants pour ce placement specifique)

---

## Section 3 : Approche Recommandee

### Option selectionnee : Ajustement Direct

**Justification :**
- Effort : **Faible** (modification d'un seul fichier XML)
- Risque : **Faible** (deplacement d'un champ existant, pas de nouvelle logique)
- Timeline : **< 5 minutes** d'implementation
- Aucun impact sur le planning, le scope MVP, ou les autres artefacts

**Alternatives evaluees :**
| Option | Viabilite | Raison |
|--------|-----------|--------|
| Rollback | Non viable | Aucun rollback necessaire pour un deplacement UI |
| Revue MVP | Non viable | Le MVP n'est pas remis en cause |

---

## Section 4 : Propositions de Modification Detaillees

### Modification 1 : Retrait du tab "PDF Source OCR"

**Fichier :** `js_invoice_ocr_ia/views/account_move_views.xml`
**Story :** 5.1 - Vue Formulaire Facture avec PDF
**Section :** Onglet PDF Source OCR (xpath `//page[@id='other_tab']` position after)

**AVANT :**
```xml
<page string="PDF Source OCR" name="jsocr_pdf"
      invisible="not jsocr_import_job_id">
    <group>
        <group>
            <field name="jsocr_import_job_id" readonly="1"/>
            <field name="jsocr_source_pdf_filename" readonly="1"
                   invisible="not jsocr_source_pdf"/>
        </group>
        <group>
            <field name="jsocr_global_confidence" readonly="1"
                   widget="progressbar"
                   invisible="jsocr_global_confidence == 0"/>
        </group>
    </group>
    <field name="jsocr_source_pdf" widget="pdf_viewer"
           invisible="not jsocr_source_pdf"
           style="height: 800px;"/>
</page>
```

**APRES :**
```xml
<page string="PDF Source OCR" name="jsocr_pdf"
      invisible="not jsocr_import_job_id">
    <group>
        <group>
            <field name="jsocr_import_job_id" readonly="1"/>
            <field name="jsocr_source_pdf_filename" readonly="1"
                   invisible="not jsocr_source_pdf"/>
        </group>
    </group>
    <field name="jsocr_source_pdf" widget="pdf_viewer"
           invisible="not jsocr_source_pdf"
           style="height: 800px;"/>
</page>
```

**Rationale :** Le champ jsocr_global_confidence est deplace dans le header ; le groupe vide est retire pour garder le layout propre.

---

### Modification 2 : Ajout dans le header

**Fichier :** `js_invoice_ocr_ia/views/account_move_views.xml`
**Story :** 5.2 - Badges de Confiance par Champ
**Section :** Nouveau xpath ciblant le header du formulaire facture

**AVANT :**
```xml
(Aucun champ jsocr dans le header)
```

**APRES :**
```xml
<!-- Global OCR Confidence in header (Sprint Change 2026-02-05) -->
<xpath expr="//header//field[@name='state']" position="before">
    <field name="jsocr_global_confidence" readonly="1"
           widget="progressbar"
           invisible="not jsocr_import_job_id or jsocr_global_confidence == 0"
           class="w-auto"/>
</xpath>
```

**Rationale :** Placer la confiance globale OCR directement visible dans la barre superieure, a cote du statut Brouillon/Comptabilise. Le champ est invisible pour les factures non-OCR et quand la confiance est a 0. La classe `w-auto` evite que le progressbar prenne toute la largeur du header.

---

## Section 5 : Plan de Mise en Oeuvre

### Scope : Minor
Implementation directe par l'equipe de developpement.

### Actions requises
1. Modifier `js_invoice_ocr_ia/views/account_move_views.xml` selon les propositions ci-dessus
2. Mettre a jour le module dans Odoo (`-u js_invoice_ocr_ia`)
3. Verifier visuellement que le champ apparait dans le header des factures OCR
4. Verifier que le champ n'apparait PAS pour les factures non-OCR
5. Verifier que l'onglet PDF Source OCR fonctionne toujours sans le champ confiance

### Handoff
| Role | Responsabilite |
|------|----------------|
| Developpeur | Implementation des modifications XML |

### Criteres de succes
- [ ] Le champ jsocr_global_confidence est visible dans le header des factures OCR
- [ ] Le champ est invisible pour les factures non-OCR
- [ ] L'onglet PDF Source OCR affiche toujours le job et le PDF viewer
- [ ] Le widget progressbar fonctionne correctement dans le header
