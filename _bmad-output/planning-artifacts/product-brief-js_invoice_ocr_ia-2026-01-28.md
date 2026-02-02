---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - brainstorming-session-2026-01-28.md
  - reflexion-factures.md
date: 2026-01-28
author: J.scheuner
---

# Product Brief: js_invoice_ocr_ia

## Executive Summary

**js_invoice_ocr_ia** est un addon open source pour Odoo 18 Community qui automatise la saisie des factures fournisseurs grâce à l'OCR et l'intelligence artificielle. Il répond à un besoin non couvert : Odoo Enterprise dispose d'une solution intégrée, mais les utilisateurs Community n'ont aucune alternative viable, gratuite et fiable.

L'addon permet d'extraire automatiquement les données des factures PDF (fournisseur, montants, lignes), de les pré-remplir dans Odoo, et de laisser l'utilisateur valider rapidement. L'architecture flexible supporte une IA locale (Ollama) pour la confidentialité ou une API cloud pour la simplicité.

**Cible initiale :** PME suisses utilisant Odoo Community avec 50-200 factures/mois.

---

## Core Vision

### Problem Statement

Les utilisateurs d'Odoo 18 Community qui reçoivent des factures fournisseurs doivent les saisir manuellement : ouvrir le PDF, identifier le fournisseur, recopier le numéro de facture, la date, les lignes produits, les montants. Ce travail répétitif consomme du temps (2-4 minutes par facture) et génère des erreurs, surtout en fin de journée.

### Problem Impact

- **Temps perdu** : 2+ heures/mois pour 50 factures, non-scalable
- **Erreurs humaines** : fatigue = erreurs de saisie, doublons, mauvais comptes
- **Frustration** : tâche ingrate sans valeur ajoutée
- **Inégalité** : les utilisateurs Enterprise ont une solution, pas Community

### Why Existing Solutions Fall Short

| Solution | Problème |
|----------|----------|
| Saisie manuelle | Chronophage, erreurs |
| OCR commerciaux (Dext, Yooz...) | Chers (200€+/mois), données sur le cloud |
| Odoo Enterprise OCR | Réservé à Enterprise (licence coûteuse) |
| Scripts maison | Complexes, non maintenus, peu fiables |

**Aucune solution open source fiable n'existe pour Odoo Community.**

### Proposed Solution

Un addon Odoo 18 Community qui :

1. **Surveille un dossier** pour les nouveaux PDFs de factures
2. **Extrait le texte** (PyMuPDF pour PDF texte, Tesseract pour scans)
3. **Analyse via IA** (Ollama local ou API cloud) pour identifier les champs
4. **Crée une facture brouillon** dans Odoo avec les données pré-remplies
5. **Affiche des indices de confiance** pour guider la validation
6. **Apprend des corrections** pour s'améliorer avec le temps

### Key Differentiators

| Différenciateur | Valeur |
|-----------------|--------|
| **Open source** | Gratuit, modifiable, communautaire |
| **Odoo Community** | Comble un vide, pas de concurrent direct |
| **IA locale (Ollama)** | Données 100% internes, confidentialité |
| **Multilingue CH** | FR/DE/EN natif, contexte suisse |
| **Apprentissage** | S'améliore avec chaque correction |
| **Intégration native** | Pas de nouvelle UI, workflow Odoo standard |

---

## Target Users

### Primary User: Le Gérant de PME

- **Profil** : Gérant de PME qui gère lui-même une partie de la comptabilité fournisseurs
- **Rôle double** : Installe/configure l'addon ET l'utilise au quotidien
- **Contexte** : Multiples sociétés possibles, 50-200 factures/mois au total
- **Motivation** : Gagner du temps sur les tâches répétitives sans valeur ajoutée
- **Frustration** : Saisie manuelle chronophage, solutions OCR trop chères ou peu fiables
- **Contrainte technique** : Pas de département IT → installation doit prendre < 30 minutes
- **Succès** : "Je valide mes factures en 15 minutes au lieu de 2 heures"

### Secondary User: Le Comptable

- **Profil** : Comptable interne ou externe utilisant le même workflow de validation
- **Différence** : Ne configure pas, consomme le résultat
- **Motivation** : Données fiables et structurées, moins de corrections
- **Succès** : "Les factures sont pré-remplies correctement"

### User Journey (identique pour tous)

| Étape | Action | Durée |
|-------|--------|-------|
| Réception | PDF déposé dans dossier surveillé | Auto |
| Traitement | OCR + IA en arrière-plan | Auto |
| Notification | "X factures prêtes à valider" | Push Odoo |
| Validation | Vérifier fournisseur + total + compte | 30 sec/facture |
| Correction | Ajuster si erreur (système apprend) | Si besoin |

### Workflow de Validation (unique)

Un seul parcours pour tous les utilisateurs :
1. Ouvrir la facture brouillon
2. PDF visible à droite, formulaire à gauche
3. Vérifier les champs avec indices de confiance (vert/orange/rouge)
4. Corriger si nécessaire (le système mémorise)
5. Valider → Facture enregistrée

---

## Success Metrics

### Métriques Utilisateur

| Métrique | Cible | Critique |
|----------|-------|----------|
| **Précision globale** | 95-98% des factures sans correction | Oui |
| **Détection fournisseur** | 99%+ (clé pour les masques) | Oui |
| **Lignes de facture** | 95%+ correctes | Oui |
| **Temps de validation** | < 1 min/facture | Non |

### Critères d'Échec

- Fournisseur mal détecté → mauvais masque → données incorrectes
- Lignes de facture manquantes ou incorrectes
- Montant TTC erroné de plus de 1%

### Métriques Techniques

| Métrique | Cible |
|----------|-------|
| **Temps de traitement** | < 2 min/PDF |
| **Disponibilité** | 99% (hors maintenance Ollama) |
| **Installation** | < 30 min pour un non-technicien |

### Business Objectives

| Objectif | Mesure |
|----------|--------|
| **Gain de temps** | Réduction de 75% du temps de saisie (2h → 30 min/mois) |
| **ROI** | Addon rentabilisé dès le 1er mois d'utilisation |
| **Adoption interne** | Utilisé sur les 3 sociétés dans les 3 mois |

### Key Performance Indicators (si partage GitHub)

| KPI | Cible 6 mois |
|-----|--------------|
| Stars GitHub | 50+ |
| Forks | 10+ |
| Issues résolues | > 80% |
| Contributeurs externes | 2+ |

---

## MVP Scope

### Core Features (Must Have V1)

#### 1. Extraction OCR
- Extraction texte PDF natifs (PyMuPDF)
- OCR pour PDF scannés (Tesseract)
- Support multi-pages
- Détection automatique langue (FR/DE/EN)

#### 2. Analyse IA
- Connexion Ollama local (config URL + test)
- Extraction structurée : fournisseur, date, numéro, lignes, totaux
- Indices de confiance par champ
- Architecture hybride (Cloud dev / Ollama prod)

#### 3. Intégration Odoo 18 Community
- Dossier surveillé avec traitement asynchrone
- Arborescence : `a_traiter/`, `traite_ok/`, `erreur/`, `non_pdf/`
- Création facture brouillon avec données pré-remplies
- Masques stockés en base Odoo (migration-proof)
- Droits d'accès Odoo natifs (Utilisateur/Manager/Admin)

#### 4. Validation Utilisateur
- Interface native Odoo (PDF à droite, formulaire à gauche)
- Indices de confiance visuels (vert/orange/rouge)
- Mémoire des corrections (apprentissage)

### Out of Scope for MVP

| Fonctionnalité | Raison | Version cible |
|----------------|--------|---------------|
| Ingestion email | Complexité ajoutée | V2 |
| Matching facture ↔ PO | Dépend de l'usage Purchase | V2 |
| Alerte écart PO/facture | Nécessite matching PO | V2 |
| Dashboard DAF | Nice to have | V1.1 |
| Mode debug avancé | Nice to have | V1.1 |
| Traitement heures creuses | Nice to have | V1.1 |

### MVP Success Criteria

| Critère | Validation |
|---------|------------|
| **Durée test** | 1 mois d'utilisation réelle |
| **Volume** | 50+ factures traitées |
| **Précision** | 95%+ sans correction |
| **Stabilité** | Aucun bug critique |
| **Adoption** | Utilisé quotidiennement |

**Le MVP est validé quand :** 1 mois d'utilisation avec succès sur une société réelle.

### Ordre de Développement

```
Phase 1: OCR
├── Extraction texte PyMuPDF
├── OCR Tesseract pour scans
├── Détection langue
└── Support multi-pages

Phase 2: IA
├── Connexion Ollama
├── Prompts extraction structurée
├── Parsing JSON réponse
└── Calcul indices confiance

Phase 3: Odoo
├── Modèles de données (masques, imports)
├── Dossier surveillé + queue jobs
├── Création facture brouillon
├── Interface validation
└── Droits d'accès
```

### Future Vision (V2+)

| Version | Fonctionnalités |
|---------|-----------------|
| **V1.1** | Dashboard DAF, mode debug, traitement heures creuses |
| **V2** | Ingestion email, matching PO, alertes écarts |
| **V3** | Multi-société centralisé, API externe, marketplace Odoo |
