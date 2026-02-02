---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
inputDocuments:
  - product-brief-js_invoice_ocr_ia-2026-01-28.md
  - brainstorming-session-2026-01-28.md
workflowType: 'prd'
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 1
  projectDocs: 0
classification:
  projectType: erp_addon
  domain: accounting_finance
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - js_invoice_ocr_ia

**Author:** J.scheuner
**Date:** 2026-01-28

## Introduction

Ce PRD définit les exigences pour **js_invoice_ocr_ia**, un addon Odoo 18 Community qui automatise la saisie des factures fournisseurs via OCR et intelligence artificielle. L'addon cible les PME suisses (50-200 factures/mois) et utilise Ollama en local pour garantir la confidentialité des données. Le document couvre les critères de succès, les parcours utilisateurs, les exigences fonctionnelles et non-fonctionnelles nécessaires au développement.

## Success Criteria

### User Success

- **Moment "Aha!"** : 10 factures traitées consécutivement sans erreur
- **Validation rapide** : < 1 minute par facture (vs 2-4 min en manuel)
- **Confiance** : L'utilisateur fait confiance aux suggestions de l'IA
- **Adoption naturelle** : Devient le workflow par défaut en < 2 semaines

### Business Success

| Métrique | Cible | Échéance |
|----------|-------|----------|
| Gain de temps | 75% réduction | Dès le 1er mois |
| Adoption interne | 3 sociétés | 3 mois |
| ROI | Positif | 1er mois |

### Technical Success

| Métrique | Cible |
|----------|-------|
| Précision globale | 95-98% |
| Détection fournisseur | 99%+ |
| Lignes de facture | 95%+ |
| Temps traitement | < 2 min/PDF |
| Disponibilité | 99% |
| Installation | < 30 min |

### Measurable Outcomes

**Seuil de Succès :**
- Précision ≥ 90% = projet viable
- Précision ≥ 95% = objectif atteint
- Précision ≥ 98% = excellence

**Seuil d'Échec :**
- Précision < 90% = échec, revoir l'approche

**Validation MVP :**
- 10 factures consécutives sans erreur
- 1 mois d'utilisation stable
- 50+ factures traitées au total

## Product Scope & Phased Development

### MVP Strategy

**Approche :** Problem-Solving MVP
- Résoudre le problème principal : saisie manuelle chronophage
- Livrer une solution fonctionnelle rapidement
- Valider avec de vraies factures en conditions réelles

**Ressources requises :**
- 1 développeur Odoo/Python
- Accès serveur Odoo 18 test
- Ollama installé localement
- ~50 factures réelles pour tests

### MVP Feature Set (Phase 1)

**Parcours utilisateurs supportés :**
- Gérant pressé (happy path)
- Correction fournisseur (edge case)
- Comptable validateur
- Installation admin

**Capacités Must-Have :**

| Domaine | Capacités |
|---------|-----------|
| **Extraction OCR** | PyMuPDF (PDF texte) + Tesseract (scans), multi-pages, multilingue (FR/DE/EN) |
| **Analyse IA** | Connexion Ollama local, extraction structurée, indices de confiance par champ |
| **Intégration Odoo** | Dossier surveillé, queue asynchrone, création facture brouillon, masques en base |
| **Validation** | Interface native Odoo, mémoire des corrections |
| **Gestion fichiers** | Arborescence OK/erreur/non-PDF |
| **Configuration** | URL Ollama + dossiers, test connexion |
| **Sécurité** | Droits d'accès Odoo natifs (user/manager/admin) |

### Post-MVP Features

**Phase 2 (V1.1 - Growth) :**
- Dashboard statistiques pour DAF
- Mode debug avec logs détaillés
- Planification heures creuses
- Profil fournisseur enrichi auto-apprenant

**Phase 3 (V2+ - Expansion) :**
- Ingestion email automatique
- Matching avec bons de commande
- Alertes écarts facturation
- Publication marketplace Odoo

### Risk Mitigation

| Type | Risque | Mitigation |
|------|--------|------------|
| Technique | Précision IA insuffisante | Tests précoces avec vraies factures |
| Technique | Qualité OCR variable | Documenter prérequis scan |
| Marché | Faible adoption | Projet interne d'abord, puis GitHub |
| Ressources | Dépassement temps | MVP strict, pas de scope creep |

## User Journeys

### Parcours 1 : Le Gérant Pressé (Happy Path)

**Protagoniste :** Jean-Marc, gérant d'une PME de négoce, 52 ans

**Scène d'ouverture :**
Vendredi 16h30. Jean-Marc a une pile de 15 factures sur son bureau. Le comptable externe passe lundi. Il doit tout saisir avant de partir.

**Action montante :**
Jean-Marc scanne les 15 factures et les dépose dans le dossier `factures_a_traiter/`. Il va se servir un café. Quand il revient, Odoo affiche "12 factures prêtes à valider".

**Climax :**
Il ouvre la première facture. Le fournisseur est bon (vert). Le total est bon (vert). Les lignes sont correctes (vert). Il clique "Valider". 10 secondes. Il enchaîne les 12 factures en 5 minutes.

**Résolution :**
Jean-Marc part à 17h avec un sourire. Lundi, le comptable trouve tout prêt dans Odoo.

---

### Parcours 2 : La Correction (Edge Case)

**Protagoniste :** Jean-Marc, même personne

**Scène d'ouverture :**
Une facture d'un nouveau fournisseur arrive. L'addon ne le reconnaît pas.

**Action montante :**
L'IA a extrait le texte mais le fournisseur est en orange (confiance 60%). Jean-Marc voit "MUELLER AG" suggéré, mais c'est "Müller SA" dans Odoo.

**Climax :**
Jean-Marc corrige le fournisseur dans le dropdown Odoo. Le système mémorise : "MUELLER AG" → "Müller SA".

**Résolution :**
La prochaine facture de Mueller arrive. Cette fois, confiance 99%. Le système a appris.

---

### Parcours 3 : Le Comptable Validateur

**Protagoniste :** Sophie, comptable externe, 38 ans

**Scène d'ouverture :**
Lundi matin, Sophie se connecte à Odoo depuis son bureau. Elle voit "23 factures en attente de validation".

**Action montante :**
Elle ouvre chaque facture, vérifie le PDF à droite, contrôle fournisseur + total + compte de charge. Elle note le numéro Odoo sur la facture papier que Jean-Marc lui a envoyée.

**Climax :**
Sur 23 factures, 21 sont parfaites. 2 nécessitent une correction de compte de charge (607 au lieu de 606). Elle corrige et valide.

**Résolution :**
En 30 minutes, Sophie a validé ce qui lui prenait 2 heures avant. Elle peut se concentrer sur l'analyse des comptes.

---

### Parcours 4 : L'Installation (Admin)

**Protagoniste :** Jean-Marc (qui est aussi l'admin)

**Scène d'ouverture :**
Jean-Marc a téléchargé l'addon sur GitHub. Il se demande si ça va être compliqué.

**Action montante :**
Il copie le module dans le dossier addons. Met à jour la liste des modules. Installe. Configure l'URL Ollama. Clique "Tester connexion" → "OK".

**Climax :**
Il crée le dossier surveillé et dépose une facture test. 30 secondes plus tard, une facture brouillon apparaît. Les données sont bonnes.

**Résolution :**
Installation en 25 minutes. Jean-Marc n'a pas eu besoin d'appeler un informaticien.

---

### Journey Requirements Summary

| Parcours | Capacités Requises |
|----------|-------------------|
| Happy Path | Dossier surveillé, OCR, IA, création facture, validation rapide |
| Correction | Dropdown fournisseur, mémoire corrections, indices confiance |
| Comptable | Multi-utilisateur, droits accès, audit trail |
| Installation | Config simple, test connexion, documentation |

## Domain-Specific Requirements

### Confidentialité & Hébergement

- **Hébergement** : Serveur Odoo on-premise (local)
- **Politique données** : Aucune donnée ne quitte le réseau interne
- **IA locale** : Ollama obligatoire en production
- **Cloud dev uniquement** : API cloud (OpenAI/Claude) acceptable en développement

### Comptabilité Suisse

- **Plan comptable** : Utiliser le plan comptable suisse existant dans Odoo
- **TVA** : Mapper les taux suisses existants (7.7%, 2.5%, 0%)
- **Pas de recréation** : L'addon utilise les données Odoo, il ne les recrée pas
- **Multidevise** : CHF principalement, EUR occasionnel

### Intégrations

- **Odoo standalone** : Pas de connexion à d'autres systèmes externes
- **Seule dépendance externe** : Ollama (réseau local)
- **Modules OCA** : `queue_job` pour le traitement asynchrone

## ERP Addon Technical Specifications

### Data Models

#### New Models

| Model | Description | Key Fields |
|-------|-------------|------------|
| `jsocr.mask` | Masques extraction fournisseur | partner_id, zones_json, confidence |
| `jsocr.import.job` | Jobs d'import OCR | pdf_path, state, invoice_id, error_msg |
| `jsocr.correction` | Historique corrections | original_value, corrected_value, field_name |
| `jsocr.config` | Configuration globale | ollama_url, model_name, folders |

#### Extended Models

| Model | Extension |
|-------|-----------|
| `res.partner` | `jsocr_mask_id`, `jsocr_aliases` (noms reconnus) |
| `account.move` | `jsocr_confidence`, `jsocr_job_id` |

### Views & Menu Structure

```
Comptabilité
└── OCR Factures
    ├── Jobs en cours (Kanban)
    ├── Historique imports (Liste)
    ├── Masques fournisseurs (Liste)
    └── Configuration (Formulaire)
```

### Dependencies

**Odoo Modules:**
- `account` (core)
- `base` (core)
- `queue_job` (OCA)

**Python Packages:**
- `pymupdf` - Extraction PDF
- `pytesseract` - OCR images
- `requests` - API Ollama
- `Pillow` - Traitement images

**External Services:**
- Tesseract OCR (installé sur serveur)
- Ollama (réseau local)

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ollama_url` | Char | `http://localhost:11434` | URL serveur Ollama |
| `ollama_model` | Char | `llama3` | Modèle IA à utiliser |
| `folder_input` | Char | `/odoo/ocr/a_traiter` | Dossier surveillé |
| `folder_success` | Char | `/odoo/ocr/traite_ok` | Dossier traités OK |
| `folder_error` | Char | `/odoo/ocr/erreur` | Dossier erreurs |
| `folder_invalid` | Char | `/odoo/ocr/non_pdf` | Dossier fichiers invalides |
| `alert_amount` | Float | `5000.00` | Seuil alerte montant (CHF) |
| `admin_email` | Char | — | Email alertes admin |

### Security & Access Rights

| Group | Permissions |
|-------|-------------|
| `jsocr.group_user` | Voir/valider ses factures OCR |
| `jsocr.group_manager` | Tout voir + gérer masques |
| `jsocr.group_admin` | Configuration technique |

### Implementation Notes

- Utiliser `queue_job` pour traitement asynchrone
- Cron job pour scanner le dossier surveillé (toutes les 5 min)
- Stockage masques en JSON dans champ Text (flexible)
- Indices de confiance stockés par champ (JSON)

## Functional Requirements

### Ingestion de Fichiers

- FR1: Le système peut surveiller un dossier pour détecter de nouveaux fichiers PDF
- FR2: Le système peut déplacer les fichiers traités vers un dossier de succès
- FR3: Le système peut déplacer les fichiers en erreur vers un dossier dédié
- FR4: Le système peut rejeter les fichiers non-PDF vers un dossier spécifique
- FR5: L'administrateur peut configurer les chemins des dossiers surveillés

### Extraction OCR

- FR6: Le système peut extraire le texte des PDF natifs (texte sélectionnable)
- FR7: Le système peut extraire le texte des PDF scannés via OCR
- FR8: Le système peut traiter des factures multi-pages
- FR9: Le système peut détecter automatiquement la langue (FR/DE/EN)

### Analyse IA

- FR10: Le système peut se connecter à un serveur Ollama local
- FR11: L'administrateur peut tester la connexion Ollama depuis l'interface
- FR12: Le système peut extraire le nom/identifiant du fournisseur
- FR13: Le système peut extraire la date de facture
- FR14: Le système peut extraire le numéro de facture
- FR15: Le système peut extraire les lignes de produits/services
- FR16: Le système peut extraire les montants (HT, TVA, TTC)
- FR17: Le système peut calculer un indice de confiance par champ extrait

### Gestion des Factures Odoo

- FR18: Le système peut créer une facture fournisseur brouillon dans Odoo
- FR19: Le système peut associer le fournisseur Odoo détecté à la facture
- FR20: Le système peut pré-remplir les lignes de facture
- FR21: Le système peut attacher le PDF source à la facture créée
- FR22: L'utilisateur peut voir l'indice de confiance de chaque champ
- FR23: L'utilisateur peut corriger les champs pré-remplis avant validation
- FR24: L'utilisateur peut valider une facture brouillon

### Apprentissage & Corrections

- FR25: Le système peut mémoriser les corrections de fournisseur (alias)
- FR26: Le système peut mémoriser les corrections de compte de charge par fournisseur
- FR27: Le système peut améliorer sa précision basée sur les corrections passées
- FR28: L'administrateur peut voir l'historique des corrections

### Masques & Fournisseurs

- FR29: Le système peut stocker des masques d'extraction par fournisseur
- FR30: L'administrateur peut voir et gérer les masques existants
- FR31: Le système peut associer des alias de noms à un fournisseur Odoo

### Jobs & Traitement Asynchrone

- FR32: Le système peut traiter les factures en arrière-plan (asynchrone)
- FR33: L'utilisateur peut voir la liste des jobs en cours
- FR34: L'utilisateur peut voir le statut de chaque job (en attente, en cours, traité, erreur)
- FR35: Le système peut notifier l'utilisateur quand des factures sont prêtes

### Configuration & Administration

- FR36: L'administrateur peut configurer l'URL du serveur Ollama
- FR37: L'administrateur peut sélectionner le modèle IA à utiliser
- FR38: L'administrateur peut définir un seuil d'alerte montant
- FR39: L'administrateur peut configurer l'email pour les alertes d'erreur
- FR40: Le système peut envoyer un email en cas de fichier corrompu ou non-PDF

### Sécurité & Droits d'Accès

- FR41: L'administrateur peut attribuer des rôles utilisateur OCR
- FR42: Un utilisateur standard peut voir et valider ses propres factures OCR
- FR43: Un manager peut voir et valider toutes les factures OCR
- FR44: Seul un administrateur peut modifier la configuration technique

### Alertes & Indicateurs

- FR45: Le système peut afficher un indicateur visuel (couleur) selon la confiance
- FR46: Le système peut mettre en évidence les montants supérieurs au seuil d'alerte

## Non-Functional Requirements

### Performance

- NFR1: Le traitement OCR+IA d'un PDF doit se terminer en < 2 minutes
- NFR2: L'interface de validation doit répondre en < 1 seconde
- NFR3: Le scan du dossier surveillé doit s'exécuter en < 10 secondes
- NFR4: La création de facture Odoo doit se terminer en < 5 secondes

### Sécurité

- NFR5: Aucune donnée de facture ne doit transiter vers des serveurs externes en production
- NFR6: L'accès aux factures doit respecter les droits Odoo natifs
- NFR7: Les corrections et masques doivent être protégés par les ACL Odoo
- NFR8: Les logs ne doivent pas contenir de données sensibles (montants, fournisseurs)

### Fiabilité

- NFR9: L'addon doit avoir une disponibilité de 99% (hors maintenance Odoo/Ollama)
- NFR10: Un échec de traitement ne doit pas bloquer les autres factures en queue
- NFR11: Le système doit reprendre automatiquement après un redémarrage Odoo
- NFR12: Les fichiers ne doivent jamais être perdus (déplacés, jamais supprimés)

### Intégration

- NFR13: L'addon doit être compatible Odoo 18 Community
- NFR14: L'addon doit fonctionner avec queue_job OCA standard
- NFR15: L'API Ollama doit supporter les modèles Llama 3 et Mistral
- NFR16: L'installation ne doit pas nécessiter de modification du core Odoo

### Maintenabilité

- NFR17: L'installation complète doit être réalisable en < 30 minutes
- NFR18: La mise à jour de l'addon ne doit pas perdre les masques existants
- NFR19: Le code doit suivre les conventions Odoo (PEP8, guidelines OCA)
- NFR20: Une documentation README claire doit accompagner l'addon
