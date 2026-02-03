---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: complete
completedAt: 2026-01-29
inputDocuments:
  - prd.md
  - architecture.md
totalEpics: 6
totalStories: 54
frCoverage: 46/46
---

# js_invoice_ocr_ia - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for js_invoice_ocr_ia, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Ingestion de Fichiers (5)**
- FR1: Le système peut surveiller un dossier pour détecter de nouveaux fichiers PDF
- FR2: Le système peut déplacer les fichiers traités vers un dossier de succès
- FR3: Le système peut déplacer les fichiers en erreur vers un dossier dédié
- FR4: Le système peut rejeter les fichiers non-PDF vers un dossier spécifique
- FR5: L'administrateur peut configurer les chemins des dossiers surveillés

**Extraction OCR (4)**
- FR6: Le système peut extraire le texte des PDF natifs (texte sélectionnable)
- FR7: Le système peut extraire le texte des PDF scannés via OCR
- FR8: Le système peut traiter des factures multi-pages
- FR9: Le système peut détecter automatiquement la langue (FR/DE/EN)

**Analyse IA (8)**
- FR10: Le système peut se connecter à un serveur Ollama local
- FR11: L'administrateur peut tester la connexion Ollama depuis l'interface
- FR12: Le système peut extraire le nom/identifiant du fournisseur
- FR13: Le système peut extraire la date de facture
- FR14: Le système peut extraire le numéro de facture
- FR15: Le système peut extraire les lignes de produits/services
- FR16: Le système peut extraire les montants (HT, TVA, TTC)
- FR17: Le système peut calculer un indice de confiance par champ extrait

**Gestion des Factures Odoo (7)**
- FR18: Le système peut créer une facture fournisseur brouillon dans Odoo
- FR19: Le système peut associer le fournisseur Odoo détecté à la facture
- FR20: Le système peut pré-remplir les lignes de facture
- FR21: Le système peut attacher le PDF source à la facture créée
- FR22: L'utilisateur peut voir l'indice de confiance de chaque champ
- FR23: L'utilisateur peut corriger les champs pré-remplis avant validation
- FR24: L'utilisateur peut valider une facture brouillon

**Apprentissage & Corrections (4)**
- FR25: Le système peut mémoriser les corrections de fournisseur (alias)
- FR26: Le système peut mémoriser les corrections de compte de charge par fournisseur
- FR27: Le système peut améliorer sa précision basée sur les corrections passées
- FR28: L'administrateur peut voir l'historique des corrections

**Masques & Fournisseurs (3)**
- FR29: Le système peut stocker des masques d'extraction par fournisseur
- FR30: L'administrateur peut voir et gérer les masques existants
- FR31: Le système peut associer des alias de noms à un fournisseur Odoo

**Jobs & Traitement Asynchrone (4)**
- FR32: Le système peut traiter les factures en arrière-plan (asynchrone)
- FR33: L'utilisateur peut voir la liste des jobs en cours
- FR34: L'utilisateur peut voir le statut de chaque job (en attente, en cours, traité, erreur)
- FR35: Le système peut notifier l'utilisateur quand des factures sont prêtes

**Configuration & Administration (5)**
- FR36: L'administrateur peut configurer l'URL du serveur Ollama
- FR37: L'administrateur peut sélectionner le modèle IA à utiliser
- FR38: L'administrateur peut définir un seuil d'alerte montant
- FR39: L'administrateur peut configurer l'email pour les alertes d'erreur
- FR40: Le système peut envoyer un email en cas de fichier corrompu ou non-PDF

**Sécurité & Droits d'Accès (4)**
- FR41: L'administrateur peut attribuer des rôles utilisateur OCR
- FR42: Un utilisateur standard peut voir et valider ses propres factures OCR
- FR43: Un manager peut voir et valider toutes les factures OCR
- FR44: Seul un administrateur peut modifier la configuration technique

**Alertes & Indicateurs (2)**
- FR45: Le système peut afficher un indicateur visuel (couleur) selon la confiance
- FR46: Le système peut mettre en évidence les montants supérieurs au seuil d'alerte

### NonFunctional Requirements

**Performance (4)**
- NFR1: Le traitement OCR+IA d'un PDF doit se terminer en < 2 minutes
- NFR2: L'interface de validation doit répondre en < 1 seconde
- NFR3: Le scan du dossier surveillé doit s'exécuter en < 10 secondes
- NFR4: La création de facture Odoo doit se terminer en < 5 secondes

**Sécurité (4)**
- NFR5: Aucune donnée de facture ne doit transiter vers des serveurs externes en production
- NFR6: L'accès aux factures doit respecter les droits Odoo natifs
- NFR7: Les corrections et masques doivent être protégés par les ACL Odoo
- NFR8: Les logs ne doivent pas contenir de données sensibles (montants, fournisseurs)

**Fiabilité (4)**
- NFR9: L'addon doit avoir une disponibilité de 99% (hors maintenance Odoo/Ollama)
- NFR10: Un échec de traitement ne doit pas bloquer les autres factures en queue
- NFR11: Le système doit reprendre automatiquement après un redémarrage Odoo
- NFR12: Les fichiers ne doivent jamais être perdus (déplacés, jamais supprimés)

**Intégration (4)**
- NFR13: L'addon doit être compatible Odoo 18 Community
- NFR14: L'addon doit fonctionner avec queue_job OCA standard
- NFR15: L'API Ollama doit supporter les modèles Llama 3 et Mistral
- NFR16: L'installation ne doit pas nécessiter de modification du core Odoo

**Maintenabilité (4)**
- NFR17: L'installation complète doit être réalisable en < 30 minutes
- NFR18: La mise à jour de l'addon ne doit pas perdre les masques existants
- NFR19: Le code doit suivre les conventions Odoo (PEP8, guidelines OCA)
- NFR20: Une documentation README claire doit accompagner l'addon

### Additional Requirements

**From Architecture - Starter Template:**
- Template OCA Personnalisé requis pour Epic 1 Story 1
- Structure: models/, services/, views/, security/, data/, tests/, static/

**From Architecture - Technical Requirements:**
- Utiliser queue_job OCA pour traitement asynchrone
- Cron job pour scanner le dossier surveillé (toutes les 5 min)
- Stockage masques en JSON dans champ Text
- Indices de confiance stockés par champ (JSON)
- Services dédiés: OCRService, OllamaService, FileWatcher
- Machine à états pour jobs: draft → pending → processing → done/error/failed
- Pattern retry: 3x avec backoff (5s, 15s, 30s) pour erreurs transitoires
- Timeout Ollama: 120 secondes

**From Architecture - Implementation Sequence:**
1. Structure addon + modèles de base
2. Service OCR (PyMuPDF + Tesseract)
3. Service Ollama + prompts
4. File watcher + queue jobs
5. Création facture brouillon
6. UI validation + badges confiance
7. Apprentissage corrections

**From Architecture - Patterns:**
- Préfixe jsocr.* pour tous les modèles
- snake_case pour champs, méthodes, JSON
- Logs avec préfixe JSOCR: sans données sensibles
- Un fichier = une responsabilité

### FR Coverage Map

| Epic | Functional Requirements Covered |
|------|--------------------------------|
| Epic 1: Fondations & Installation | NFR13, NFR16, NFR19, NFR20 (infrastructure technique) |
| Epic 2: Configuration & Connectivité | FR5, FR10, FR11, FR36, FR37, FR38, FR39, FR40, FR41, FR44 |
| Epic 3: Ingestion PDF & OCR | FR1, FR2, FR3, FR4, FR6, FR7, FR8, FR9 |
| Epic 4: Analyse IA & Création Factures | FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR32, FR33, FR34, FR35 |
| Epic 5: Validation & Indicateurs | FR22, FR23, FR24, FR42, FR43, FR45, FR46 |
| Epic 6: Apprentissage & Corrections | FR25, FR26, FR27, FR28, FR29, FR30, FR31 |

**NFR Coverage (transversal):**
- Performance (NFR1-4): Intégré dans Epic 3, Epic 4
- Sécurité (NFR5-8): Intégré dans Epic 2, Epic 5
- Fiabilité (NFR9-12): Intégré dans Epic 3, Epic 4
- Intégration (NFR13-16): Epic 1, Epic 4
- Maintenabilité (NFR17-20): Epic 1

## Epic List

### Epic 1: Fondations & Installation
**Goal:** Établir la structure technique de l'addon Odoo 18 avec tous les fichiers de base, permettant l'installation et le développement des fonctionnalités suivantes.

**Delivers:**
- Structure addon OCA complète
- Modèles de base (jsocr.config, jsocr.mask, jsocr.import.job, jsocr.correction)
- Extensions res.partner et account.move
- Groupes de sécurité (user/manager/admin)
- Manifest et dépendances

**Enables:** Tous les autres epics

---

### Epic 2: Configuration & Connectivité
**Goal:** Permettre à l'administrateur de configurer l'addon (dossiers, Ollama, alertes) et de valider la connectivité avant utilisation.

**FRs:** FR5, FR10, FR11, FR36, FR37, FR38, FR39, FR40, FR41, FR44

**Delivers:**
- Interface de configuration système
- Test de connexion Ollama
- Configuration des chemins de dossiers
- Configuration des alertes email
- Gestion des rôles utilisateurs

**Depends on:** Epic 1

---

### Epic 3: Ingestion PDF & OCR
**Goal:** Permettre au système de surveiller un dossier, détecter les nouveaux PDFs, extraire leur texte (natif ou OCR) et les router vers le traitement IA.

**FRs:** FR1, FR2, FR3, FR4, FR6, FR7, FR8, FR9

**Delivers:**
- Cron job de surveillance dossier
- Service OCR (PyMuPDF + Tesseract)
- Détection langue automatique
- Gestion arborescence fichiers (a_traiter, traite_ok, erreur, non_pdf)
- Support multi-pages

**Depends on:** Epic 2

---

### Epic 4: Analyse IA & Création Factures
**Goal:** Permettre au système d'analyser le texte extrait via Ollama, extraire les données structurées et créer une facture brouillon dans Odoo avec prédiction intelligente des comptes de charge.

**FRs:** FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR32, FR33, FR34, FR35

**Delivers:**
- Service Ollama avec prompts d'extraction
- Parsing JSON des réponses IA
- Calcul indices de confiance
- Création facture fournisseur brouillon
- Association fournisseur Odoo
- Traitement asynchrone queue_job
- Vue liste des jobs avec statuts
- Prédiction intelligente du compte de charge par ligne (basée sur historique fournisseur)
- Apprentissage des corrections de compte

**Depends on:** Epic 3

---

### Epic 5: Validation & Indicateurs
**Goal:** Permettre à l'utilisateur de valider les factures brouillon avec des indicateurs visuels de confiance et des alertes sur les montants.

**FRs:** FR22, FR23, FR24, FR42, FR43, FR45, FR46

**Delivers:**
- Interface validation avec PDF à droite
- Badges de confiance colorés (vert/orange/rouge)
- Alerte montants > seuil
- Édition des champs pré-remplis
- Validation finale de la facture
- Respect des droits user/manager

**Depends on:** Epic 4

---

### Epic 6: Apprentissage & Corrections
**Goal:** Permettre au système d'apprendre des corrections utilisateur pour améliorer la précision future.

**FRs:** FR25, FR26, FR27, FR28, FR29, FR30, FR31

**Delivers:**
- Mémorisation corrections fournisseur (alias)
- Mémorisation comptes de charge par fournisseur
- Enrichissement masques depuis corrections
- Vue historique des corrections
- Gestion des masques existants

**Depends on:** Epic 5

---

## Epic 1: Fondations & Installation

**Goal:** Établir la structure technique de l'addon Odoo 18 avec tous les fichiers de base, permettant l'installation et le développement des fonctionnalités suivantes.

**NFRs:** NFR13, NFR16, NFR19, NFR20

### Story 1.1: Structure Addon et Manifest

As a **développeur**,
I want **une structure addon Odoo 18 conforme OCA avec manifest complet**,
So that **l'addon puisse être installé et serve de base au développement**.

**Acceptance Criteria:**

**Given** un environnement Odoo 18 Community
**When** j'installe l'addon js_invoice_ocr_ia
**Then** l'addon apparaît dans la liste des modules disponibles
**And** le manifest déclare les dépendances (account, queue_job)
**And** la structure contient: models/, services/, views/, security/, data/, tests/, static/
**And** un README.md documente l'installation

---

### Story 1.2: Modèle Configuration (jsocr.config)

As a **administrateur**,
I want **un modèle de configuration singleton pour stocker les paramètres système**,
So that **les autres fonctionnalités puissent accéder à la configuration centralisée**.

**Acceptance Criteria:**

**Given** l'addon est installé
**When** je crée un enregistrement jsocr.config
**Then** le modèle stocke: ollama_url, ollama_model, watch_folder_path, success_folder_path, error_folder_path, rejected_folder_path, alert_amount_threshold, alert_email
**And** les chemins de dossiers ont des valeurs par défaut sensées
**And** seul un admin peut modifier ces valeurs (ir.model.access)

---

### Story 1.3: Modèle Import Job (jsocr.import.job)

As a **système**,
I want **un modèle pour tracker les jobs d'importation avec leur état**,
So that **le traitement asynchrone des PDFs soit géré proprement**.

**Acceptance Criteria:**

**Given** l'addon est installé
**When** un job d'import est créé
**Then** le modèle stocke: name, pdf_file (Binary), pdf_filename, state (draft/pending/processing/done/error/failed), extracted_text, ai_response (JSON), confidence_data (JSON), error_message, invoice_id (Many2one account.move)
**And** l'état initial est 'draft'
**And** les transitions d'état respectent la machine à états définie

---

### Story 1.4: Modèle Masque (jsocr.mask)

As a **système**,
I want **un modèle pour stocker les masques d'extraction par fournisseur**,
So that **l'extraction puisse être personnalisée par fournisseur**.

**Acceptance Criteria:**

**Given** l'addon est installé
**When** un masque est créé
**Then** le modèle stocke: name, partner_id (Many2one res.partner), mask_data (Text JSON), active (Boolean), usage_count (Integer)
**And** un fournisseur peut avoir plusieurs masques
**And** le champ mask_data contient la structure JSON des zones d'extraction

---

### Story 1.5: Modèle Correction (jsocr.correction)

As a **système**,
I want **un modèle pour enregistrer les corrections utilisateur**,
So that **le système puisse apprendre des corrections passées**.

**Acceptance Criteria:**

**Given** l'addon est installé
**When** une correction est enregistrée
**Then** le modèle stocke: import_job_id, field_name, original_value, corrected_value, correction_type (supplier_alias/charge_account/field_value), create_date, user_id
**And** les corrections sont liées au job d'import d'origine

---

### Story 1.6: Extensions Modèles Existants

As a **système**,
I want **étendre res.partner et account.move avec des champs OCR**,
So that **les données OCR soient intégrées nativement dans Odoo**.

**Acceptance Criteria:**

**Given** l'addon est installé
**When** un res.partner est créé/modifié
**Then** il possède: jsocr_aliases (Text), jsocr_default_account_id (Many2one account.account), jsocr_mask_ids (One2many)

**Given** l'addon est installé
**When** une account.move est créée/modifiée
**Then** elle possède: jsocr_import_job_id (Many2one), jsocr_confidence_data (Text JSON), jsocr_source_pdf (Binary)

---

### Story 1.7: Groupes de Sécurité et ACL

As a **administrateur**,
I want **des groupes de sécurité OCR avec des droits différenciés**,
So that **l'accès soit contrôlé selon les rôles**.

**Acceptance Criteria:**

**Given** l'addon est installé
**When** je consulte les groupes
**Then** 3 groupes existent: jsocr.group_user, jsocr.group_manager, jsocr.group_admin
**And** group_manager hérite de group_user
**And** group_admin hérite de group_manager
**And** les ACL (ir.model.access.csv) définissent les droits par modèle et groupe

---

## Epic 2: Configuration & Connectivité

**Goal:** Permettre à l'administrateur de configurer l'addon (dossiers, Ollama, alertes) et de valider la connectivité avant utilisation.

**FRs:** FR5, FR10, FR11, FR36, FR37, FR38, FR39, FR40, FR41, FR44

### Story 2.1: Vue Configuration Système

As a **administrateur**,
I want **une interface pour configurer les paramètres OCR**,
So that **je puisse adapter l'addon à mon environnement**.

**Acceptance Criteria:**

**Given** je suis connecté en tant qu'admin OCR
**When** j'accède au menu Configuration > OCR IA
**Then** je vois un formulaire avec tous les paramètres: URL Ollama, modèle IA, chemins dossiers, seuil alerte, email alerte
**And** je peux modifier et sauvegarder les valeurs
**And** un utilisateur non-admin ne voit pas ce menu (FR44)

---

### Story 2.2: Configuration des Dossiers Surveillés

As a **administrateur**,
I want **configurer les chemins des dossiers de traitement**,
So that **le système sache où chercher et ranger les fichiers** (FR5).

**Acceptance Criteria:**

**Given** je suis sur la page de configuration
**When** je définis watch_folder_path, success_folder_path, error_folder_path, rejected_folder_path
**Then** les chemins sont validés (existence du dossier parent)
**And** un message d'erreur apparaît si le chemin est invalide
**And** les valeurs sont persistées en base

---

### Story 2.3: Test de Connexion Ollama

As a **administrateur**,
I want **tester la connexion au serveur Ollama depuis l'interface**,
So that **je sache si l'IA est accessible avant de traiter des factures** (FR10, FR11).

**Acceptance Criteria:**

**Given** je suis sur la page de configuration avec une URL Ollama définie
**When** je clique sur le bouton "Tester la connexion"
**Then** le système envoie une requête GET à {ollama_url}/api/tags
**And** si succès: message "Connexion OK - Modèles disponibles: X, Y, Z"
**And** si échec: message "Erreur de connexion: {détail}"
**And** le timeout est de 10 secondes

---

### Story 2.4: Sélection du Modèle IA

As a **administrateur**,
I want **sélectionner le modèle IA à utiliser parmi ceux disponibles**,
So that **je puisse choisir le modèle adapté à mes besoins** (FR37).

**Acceptance Criteria:**

**Given** la connexion Ollama est établie
**When** je clique sur le champ "Modèle IA"
**Then** je vois une liste déroulante des modèles disponibles sur Ollama
**And** je peux sélectionner un modèle (ex: llama3, mistral)
**And** le choix est sauvegardé dans jsocr.config

---

### Story 2.5: Configuration des Alertes

As a **administrateur**,
I want **configurer le seuil d'alerte montant et l'email de notification**,
So that **je sois averti des situations anormales** (FR38, FR39, FR40).

**Acceptance Criteria:**

**Given** je suis sur la page de configuration
**When** je définis alert_amount_threshold (ex: 5000 CHF) et alert_email
**Then** les valeurs sont validées (montant > 0, email format valide)
**And** les valeurs sont sauvegardées
**And** ces paramètres seront utilisés lors du traitement des factures

---

### Story 2.6: Gestion des Rôles Utilisateurs

As a **administrateur**,
I want **attribuer des rôles OCR aux utilisateurs**,
So that **chacun ait les droits appropriés** (FR41).

**Acceptance Criteria:**

**Given** je suis admin Odoo
**When** j'édite un utilisateur
**Then** je vois les groupes OCR disponibles: Utilisateur OCR, Manager OCR, Admin OCR
**And** je peux assigner un ou plusieurs groupes
**And** les droits sont appliqués immédiatement

---

## Epic 3: Ingestion PDF & OCR

**Goal:** Permettre au système de surveiller un dossier, détecter les nouveaux PDFs, extraire leur texte (natif ou OCR) et les router vers le traitement IA.

**FRs:** FR1, FR2, FR3, FR4, FR6, FR7, FR8, FR9

### Story 3.1: Service OCR - Extraction PDF Natif

As a **système**,
I want **extraire le texte des PDFs contenant du texte sélectionnable**,
So that **les factures natives soient traitées rapidement** (FR6).

**Acceptance Criteria:**

**Given** un fichier PDF avec texte sélectionnable
**When** le service OCR traite ce fichier
**Then** le texte est extrait via PyMuPDF
**And** le texte de toutes les pages est concaténé (FR8)
**And** le résultat est stocké dans jsocr.import.job.extracted_text
**And** le traitement prend < 5 secondes pour un PDF de 10 pages

---

### Story 3.2: Service OCR - Extraction PDF Scanné

As a **système**,
I want **extraire le texte des PDFs scannés (images) via OCR**,
So that **les factures papier numérisées soient aussi traitées** (FR7).

**Acceptance Criteria:**

**Given** un fichier PDF sans texte sélectionnable (images)
**When** le service OCR traite ce fichier
**Then** chaque page est convertie en image
**And** Tesseract extrait le texte de chaque image
**And** le texte de toutes les pages est concaténé (FR8)
**And** le résultat est stocké dans jsocr.import.job.extracted_text

---

### Story 3.3: Détection Automatique de Langue

As a **système**,
I want **détecter automatiquement la langue du document (FR/DE/EN)**,
So that **l'OCR et l'IA utilisent la bonne langue** (FR9).

**Acceptance Criteria:**

**Given** un texte extrait d'un PDF
**When** le système analyse le texte
**Then** la langue est détectée parmi FR, DE, EN
**And** la détection utilise des mots-clés indicateurs (Facture/Rechnung/Invoice, TVA/MwSt/VAT)
**And** la langue détectée est stockée dans le job
**And** Tesseract utilise le pack de langue approprié

---

### Story 3.4: Cron Job de Surveillance Dossier

As a **système**,
I want **scanner périodiquement le dossier surveillé pour détecter les nouveaux PDFs**,
So that **les factures déposées soient traitées automatiquement** (FR1).

**Acceptance Criteria:**

**Given** un dossier surveillé configuré (watch_folder_path)
**When** le cron s'exécute (toutes les 5 minutes)
**Then** tous les fichiers PDF du dossier sont détectés
**And** pour chaque PDF, un jsocr.import.job est créé en état 'pending'
**And** le fichier PDF est stocké dans le job (Binary)
**And** le scan prend < 10 secondes (NFR3)

---

### Story 3.5: Gestion des Fichiers Non-PDF

As a **système**,
I want **rejeter les fichiers non-PDF vers un dossier dédié**,
So that **seuls les PDFs valides soient traités** (FR4).

**Acceptance Criteria:**

**Given** un fichier non-PDF dans le dossier surveillé
**When** le cron scanne le dossier
**Then** le fichier est déplacé vers rejected_folder_path
**And** le nom du fichier est préservé avec horodatage si doublon
**And** un email d'alerte est envoyé à alert_email (FR40)
**And** un log est créé avec le préfixe JSOCR:

---

### Story 3.6: Déplacement Fichiers Traités avec Succès

As a **système**,
I want **déplacer les PDFs traités avec succès vers le dossier de succès**,
So that **le dossier surveillé reste propre** (FR2).

**Acceptance Criteria:**

**Given** un job en état 'done' (facture créée avec succès)
**When** le traitement est terminé
**Then** le PDF source est déplacé vers success_folder_path
**And** le fichier est renommé avec horodatage: YYYYMMDD_HHMMSS_original.pdf
**And** le fichier n'est jamais supprimé (NFR12)

---

### Story 3.7: Déplacement Fichiers en Erreur

As a **système**,
I want **déplacer les PDFs en erreur vers le dossier d'erreur**,
So that **les fichiers problématiques soient isolés pour analyse** (FR3).

**Acceptance Criteria:**

**Given** un job en état 'error' ou 'failed'
**When** le traitement échoue définitivement
**Then** le PDF source est déplacé vers error_folder_path
**And** le fichier est renommé avec horodatage
**And** le message d'erreur est stocké dans le job
**And** un email d'alerte est envoyé à alert_email

---

## Epic 4: Analyse IA & Création Factures

**Goal:** Permettre au système d'analyser le texte extrait via Ollama, extraire les données structurées et créer une facture brouillon dans Odoo.

**FRs:** FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21, FR32, FR33, FR34, FR35

### Story 4.1: Service Ollama - Connexion et Requête

As a **système**,
I want **envoyer des requêtes au serveur Ollama et recevoir les réponses**,
So that **l'IA puisse analyser le texte des factures** (FR10).

**Acceptance Criteria:**

**Given** un serveur Ollama configuré et accessible
**When** le service envoie une requête avec un prompt
**Then** la requête est envoyée à {ollama_url}/api/generate
**And** le timeout est de 120 secondes
**And** la réponse JSON est parsée correctement
**And** les erreurs de connexion sont capturées et loguées

---

### Story 4.2: Prompt d'Extraction Structurée

As a **système**,
I want **un prompt optimisé pour extraire les données de facture**,
So that **l'IA retourne des données structurées exploitables**.

**Acceptance Criteria:**

**Given** un texte de facture extrait
**When** le prompt est envoyé à Ollama
**Then** le prompt demande: supplier_name, invoice_date, invoice_number, lines[], amount_untaxed, amount_tax, amount_total
**And** le prompt spécifie le format JSON attendu
**And** le prompt inclut la langue détectée pour guider l'IA
**And** le prompt gère les contextes suisses (TVA 7.7%, 2.5%, 0%)

---

### Story 4.3: Extraction Fournisseur

As a **système**,
I want **extraire le nom/identifiant du fournisseur depuis la réponse IA**,
So that **le fournisseur Odoo puisse être associé** (FR12).

**Acceptance Criteria:**

**Given** une réponse JSON de l'IA
**When** le système parse la réponse
**Then** le champ supplier_name est extrait
**And** une recherche est effectuée dans res.partner (name, jsocr_aliases)
**And** si trouvé: le partner_id est associé au job
**And** si non trouvé: le champ reste vide pour correction manuelle

---

### Story 4.4: Extraction Date et Numéro Facture

As a **système**,
I want **extraire la date et le numéro de facture**,
So that **les champs obligatoires soient pré-remplis** (FR13, FR14).

**Acceptance Criteria:**

**Given** une réponse JSON de l'IA
**When** le système parse la réponse
**Then** invoice_date est extrait et converti en date Odoo
**And** invoice_number est extrait (référence fournisseur)
**And** les formats de date FR/DE/EN sont supportés (DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD)
**And** les valeurs sont stockées dans le job

---

### Story 4.5: Extraction Lignes de Facture

As a **système**,
I want **extraire les lignes de produits/services**,
So that **les lignes de facture soient pré-remplies** (FR15).

**Acceptance Criteria:**

**Given** une réponse JSON de l'IA
**When** le système parse la réponse
**Then** chaque ligne contient: description, quantity, unit_price, amount
**And** les lignes sont stockées dans le job (JSON)
**And** les montants sont parsés correctement (virgule/point décimal)

---

### Story 4.6: Extraction Montants

As a **système**,
I want **extraire les montants HT, TVA et TTC**,
So that **les totaux soient vérifiables** (FR16).

**Acceptance Criteria:**

**Given** une réponse JSON de l'IA
**When** le système parse la réponse
**Then** amount_untaxed, amount_tax, amount_total sont extraits
**And** les montants sont convertis en float
**And** une vérification de cohérence est effectuée (HT + TVA ≈ TTC)
**And** un warning est loggué si incohérence > 1%

---

### Story 4.7: Calcul Indices de Confiance

As a **système**,
I want **calculer un indice de confiance pour chaque champ extrait**,
So that **l'utilisateur sache quels champs vérifier** (FR17).

**Acceptance Criteria:**

**Given** une extraction IA terminée
**When** le système calcule les indices
**Then** chaque champ a un score 0-100%
**And** le score dépend de: présence du champ, cohérence des données, historique fournisseur
**And** les indices sont stockés en JSON dans confidence_data
**And** un indice global est calculé (moyenne pondérée)

---

### Story 4.8: Création Facture Brouillon

As a **système**,
I want **créer une facture fournisseur brouillon dans Odoo**,
So that **l'utilisateur puisse valider et compléter** (FR18).

**Acceptance Criteria:**

**Given** un job avec données extraites complètes
**When** le système crée la facture
**Then** une account.move de type 'in_invoice' est créée en état 'draft'
**And** le partner_id est associé si trouvé (FR19)
**And** la date et référence fournisseur sont remplies
**And** la création prend < 5 secondes (NFR4)

---

### Story 4.9: Pré-remplissage Lignes Facture

As a **système**,
I want **pré-remplir les lignes de la facture brouillon**,
So that **l'utilisateur n'ait pas à saisir manuellement** (FR20).

**Acceptance Criteria:**

**Given** une facture brouillon créée
**When** les lignes sont ajoutées
**Then** chaque ligne extraite devient une account.move.line
**And** le compte de charge par défaut du fournisseur est utilisé si configuré
**And** sinon un compte de charge générique est utilisé
**And** les quantités et prix unitaires sont remplis

---

### Story 4.10: Attachement PDF Source

As a **système**,
I want **attacher le PDF source à la facture créée**,
So that **l'utilisateur puisse consulter l'original** (FR21).

**Acceptance Criteria:**

**Given** une facture brouillon créée
**When** le PDF est attaché
**Then** un ir.attachment est créé avec le PDF
**And** l'attachment est lié à la facture (res_model, res_id)
**And** le PDF est également stocké dans account.move.jsocr_source_pdf

---

### Story 4.11: Traitement Asynchrone Queue Job

As a **système**,
I want **traiter les factures en arrière-plan via queue_job**,
So that **le serveur Odoo reste réactif** (FR32).

**Acceptance Criteria:**

**Given** un job en état 'pending'
**When** le traitement est déclenché
**Then** un queue.job OCA est créé
**And** l'état passe à 'processing'
**And** le traitement s'exécute en arrière-plan
**And** un échec ne bloque pas les autres jobs (NFR10)

---

### Story 4.12: Gestion des Erreurs et Retry

As a **système**,
I want **gérer les erreurs avec retry automatique**,
So that **les erreurs transitoires soient récupérées**.

**Acceptance Criteria:**

**Given** un job en traitement qui échoue
**When** l'erreur est transitoire (timeout, connexion)
**Then** le job est retenté 3 fois avec backoff (5s, 15s, 30s)
**And** après 3 échecs, l'état passe à 'failed'
**And** le message d'erreur est stocké
**And** les erreurs permanentes (parsing) passent directement à 'error'

---

### Story 4.13: Vue Liste des Jobs

As a **utilisateur OCR**,
I want **voir la liste des jobs d'importation**,
So that **je suive l'avancement des traitements** (FR33).

**Acceptance Criteria:**

**Given** je suis connecté avec le groupe OCR
**When** j'accède au menu OCR IA > Jobs d'import
**Then** je vois une liste avec: nom fichier, date création, état, fournisseur détecté
**And** je peux filtrer par état
**And** je peux cliquer pour voir les détails

---

### Story 4.14: Affichage Statut Job

As a **utilisateur OCR**,
I want **voir le statut de chaque job avec indicateur visuel**,
So that **je sache rapidement où en est le traitement** (FR34).

**Acceptance Criteria:**

**Given** je consulte la liste des jobs
**When** je regarde la colonne état
**Then** chaque état a une couleur: draft (gris), pending (bleu), processing (orange), done (vert), error (rouge), failed (rouge foncé)
**And** un badge indique le nombre de tentatives restantes si en retry

---

### Story 4.15: Notification Factures Prêtes

As a **utilisateur OCR**,
I want **être notifié quand des factures sont prêtes à valider**,
So that **je puisse agir rapidement** (FR35).

**Acceptance Criteria:**

**Given** un job passe à l'état 'done'
**When** la facture brouillon est créée
**Then** une notification Odoo est envoyée à l'utilisateur assigné
**And** la notification indique: "X factures prêtes à valider"
**And** un clic sur la notification ouvre la liste des factures à valider

---

### Story 4.16: Analyse Historique Factures Fournisseur

As a **système**,
I want **analyser les 10 dernières factures validées d'un fournisseur**,
So that **je puisse prédire les comptes de charge appropriés pour les nouvelles factures**.

**Acceptance Criteria:**

**Given** un fournisseur identifié pour une nouvelle facture
**When** le système prépare la création des lignes de facture
**Then** les 10 dernières factures validées (état 'posted') du fournisseur sont récupérées
**And** toutes les lignes de ces factures sont extraites avec leur description et compte de charge
**And** les données sont structurées pour le matching (description → account_id)
**And** si moins de 10 factures existent, toutes les factures disponibles sont utilisées
**And** seuls les comptes de type 'expense' sont considérés

---

### Story 4.17: Matching Intelligent Description → Compte

As a **système**,
I want **prédire le compte de charge le plus probable pour chaque ligne de facture basé sur la similarité des descriptions**,
So that **les lignes soient pré-remplies avec le bon compte**.

**Acceptance Criteria:**

**Given** une ligne de facture à créer avec une description
**And** l'historique des lignes du fournisseur (Story 4.16)
**When** le système calcule le compte à utiliser
**Then** la description de la ligne actuelle est comparée aux descriptions historiques
**And** l'algorithme utilise:
  - Correspondance exacte (priorité maximale)
  - Mots-clés communs normalisés (sans accents, minuscules)
  - Score de similarité basé sur le nombre de mots communs
**And** le compte le plus fréquent pour les descriptions similaires est retourné
**And** un score de confiance (0-100%) est calculé basé sur:
  - Nombre de matches trouvés
  - Fréquence du compte dans les matches
  - Qualité de la similarité
**And** si aucun match n'est trouvé (confiance < 30%), le fallback _get_expense_account() est utilisé

---

### Story 4.18: Stockage Patterns Compte par Fournisseur

As a **système**,
I want **mémoriser les associations description/compte apprises**,
So that **les prédictions s'améliorent avec le temps sans recalcul**.

**Acceptance Criteria:**

**Given** une facture validée avec des lignes
**When** la facture passe en état 'posted'
**Then** pour chaque ligne, l'association (partner_id, keywords, account_id) est enregistrée ou mise à jour
**And** le modèle jsocr.account.pattern stocke:
  - partner_id (Many2one res.partner)
  - keywords (Char) - mots-clés normalisés de la description
  - account_id (Many2one account.account)
  - usage_count (Integer) - incrémenté à chaque utilisation
  - last_used (Datetime)
**And** les patterns sont utilisés en priorité avant l'analyse historique complète
**And** un pattern avec usage_count élevé a plus de poids dans la prédiction

---

### Story 4.19: Affichage Confiance Compte sur Lignes Facture

As a **utilisateur OCR**,
I want **voir la confiance de prédiction du compte sur chaque ligne de facture**,
So that **je sache quelles lignes vérifier en priorité**.

**Acceptance Criteria:**

**Given** une facture brouillon créée par OCR avec lignes
**When** j'affiche le formulaire de la facture
**Then** chaque ligne affiche un indicateur de confiance pour le compte:
  - 🟢 Vert (≥80%) : "Compte prédit avec haute confiance"
  - 🟡 Orange (50-79%) : "Compte suggéré - à vérifier"
  - 🔴 Rouge (<50%) : "Compte par défaut - vérification requise"
**And** au survol, le détail de la prédiction est affiché (source: historique/pattern/défaut)
**And** le champ jsocr_account_confidence est ajouté à account.move.line

---

### Story 4.20: Apprentissage des Corrections de Compte par Ligne

As a **système**,
I want **apprendre quand l'utilisateur corrige le compte d'une ligne**,
So that **les prochaines prédictions soient plus précises**.

**Acceptance Criteria:**

**Given** une facture brouillon où l'utilisateur modifie le compte d'une ligne
**When** la facture est validée
**Then** si le compte final diffère du compte prédit:
  - Une jsocr.correction est créée (type: line_account)
  - Le pattern jsocr.account.pattern est mis à jour ou créé
  - Le usage_count du nouveau pattern est incrémenté
**And** les corrections répétées augmentent le poids du pattern
**And** un pattern corrigé 3+ fois devient prioritaire sur l'historique

---

## Epic 5: Validation & Indicateurs

**Goal:** Permettre à l'utilisateur de valider les factures brouillon avec des indicateurs visuels de confiance et des alertes sur les montants.

**FRs:** FR22, FR23, FR24, FR42, FR43, FR45, FR46

### Story 5.1: Vue Formulaire Facture avec PDF

As a **utilisateur OCR**,
I want **voir la facture brouillon avec le PDF source à côté**,
So that **je puisse vérifier les données extraites**.

**Acceptance Criteria:**

**Given** je suis sur une facture brouillon créée par OCR
**When** j'ouvre le formulaire
**Then** le formulaire Odoo standard est affiché à gauche
**And** le PDF source est affiché à droite (viewer intégré)
**And** je peux zoomer et naviguer dans le PDF
**And** l'interface répond en < 1 seconde (NFR2)

---

### Story 5.2: Badges de Confiance par Champ

As a **utilisateur OCR**,
I want **voir l'indice de confiance de chaque champ extrait**,
So that **je sache quels champs vérifier en priorité** (FR22, FR45).

**Acceptance Criteria:**

**Given** une facture brouillon avec confidence_data
**When** j'affiche le formulaire
**Then** chaque champ OCR a un badge coloré: vert (≥80%), orange (50-79%), rouge (<50%)
**And** le badge affiche le pourcentage au survol
**And** les champs à faible confiance sont visuellement mis en avant

---

### Story 5.3: Alerte Montant Élevé

As a **utilisateur OCR**,
I want **voir une alerte si le montant total dépasse le seuil configuré**,
So that **je vérifie attentivement les grosses factures** (FR46).

**Acceptance Criteria:**

**Given** une facture avec amount_total > alert_amount_threshold
**When** j'affiche le formulaire
**Then** le champ montant total est encadré en rouge
**And** un bandeau d'alerte apparaît: "Attention: montant supérieur à X CHF"
**And** l'alerte ne bloque pas la validation

---

### Story 5.4: Édition des Champs Pré-remplis

As a **utilisateur OCR**,
I want **corriger les champs pré-remplis avant validation**,
So that **je puisse rectifier les erreurs d'extraction** (FR23).

**Acceptance Criteria:**

**Given** une facture brouillon OCR
**When** je modifie un champ (fournisseur, date, lignes, montants)
**Then** la modification est enregistrée
**And** le formulaire Odoo standard permet l'édition
**And** les lignes de facture sont éditables (ajout, modification, suppression)

---

### Story 5.5: Validation Facture Brouillon

As a **utilisateur OCR**,
I want **valider une facture brouillon pour la comptabiliser**,
So that **la facture soit enregistrée officiellement** (FR24).

**Acceptance Criteria:**

**Given** une facture brouillon complète et vérifiée
**When** je clique sur "Confirmer"
**Then** la facture passe en état "posted"
**And** les écritures comptables sont générées
**And** le job d'import associé reste en état "done"

---

### Story 5.6: Droits Utilisateur Standard

As a **utilisateur OCR standard**,
I want **voir et valider uniquement mes propres factures OCR**,
So that **je ne voie que ce qui me concerne** (FR42).

**Acceptance Criteria:**

**Given** je suis connecté avec jsocr.group_user uniquement
**When** j'accède à la liste des factures OCR
**Then** je vois uniquement les factures que j'ai créées ou qui me sont assignées
**And** je peux les valider
**And** je ne vois pas les factures des autres utilisateurs

---

### Story 5.7: Droits Manager

As a **manager OCR**,
I want **voir et valider toutes les factures OCR**,
So that **je puisse superviser le travail de l'équipe** (FR43).

**Acceptance Criteria:**

**Given** je suis connecté avec jsocr.group_manager
**When** j'accède à la liste des factures OCR
**Then** je vois toutes les factures OCR de tous les utilisateurs
**And** je peux les valider ou les réassigner
**And** je peux filtrer par utilisateur créateur

---

## Epic 6: Apprentissage & Corrections

**Goal:** Permettre au système d'apprendre des corrections utilisateur pour améliorer la précision future.

**FRs:** FR25, FR26, FR27, FR28, FR29, FR30, FR31

### Story 6.1: Enregistrement Correction Fournisseur (Alias)

As a **système**,
I want **mémoriser quand un utilisateur corrige le fournisseur détecté**,
So that **la même correction soit appliquée automatiquement à l'avenir** (FR25, FR31).

**Acceptance Criteria:**

**Given** une facture brouillon avec fournisseur incorrect ou manquant
**When** l'utilisateur sélectionne le bon fournisseur et sauvegarde
**Then** une jsocr.correction est créée (type: supplier_alias)
**And** le nom extrait par l'IA est ajouté aux jsocr_aliases du fournisseur
**And** les prochaines factures avec ce nom seront automatiquement associées

---

### Story 6.2: Enregistrement Correction Compte de Charge

As a **système**,
I want **mémoriser le compte de charge utilisé pour un fournisseur**,
So that **les prochaines factures utilisent ce compte par défaut** (FR26).

**Acceptance Criteria:**

**Given** une facture où l'utilisateur modifie le compte de charge d'une ligne
**When** la facture est validée
**Then** une jsocr.correction est créée (type: charge_account)
**And** le compte est enregistré comme défaut pour ce fournisseur (jsocr_default_account_id)
**And** les prochaines factures de ce fournisseur utiliseront ce compte

---

### Story 6.3: Amélioration Précision via Historique

As a **système**,
I want **utiliser l'historique des corrections pour améliorer l'extraction**,
So that **la précision augmente avec le temps** (FR27).

**Acceptance Criteria:**

**Given** des corrections passées pour un fournisseur
**When** une nouvelle facture de ce fournisseur est traitée
**Then** le système consulte les corrections passées
**And** les alias connus sont utilisés pour la détection fournisseur
**And** le compte de charge par défaut est pré-sélectionné
**And** l'indice de confiance est ajusté (bonus si fournisseur connu)

---

### Story 6.4: Vue Historique des Corrections

As a **administrateur**,
I want **voir l'historique de toutes les corrections effectuées**,
So that **je puisse auditer et comprendre l'apprentissage** (FR28).

**Acceptance Criteria:**

**Given** je suis connecté en tant qu'admin OCR
**When** j'accède au menu OCR IA > Historique Corrections
**Then** je vois une liste avec: date, utilisateur, type correction, valeur originale, valeur corrigée, fournisseur concerné
**And** je peux filtrer par type, utilisateur, fournisseur
**And** je peux exporter la liste en CSV

---

### Story 6.5: Stockage Masques par Fournisseur

As a **système**,
I want **stocker des masques d'extraction spécifiques par fournisseur**,
So that **les formats de facture récurrents soient mieux traités** (FR29).

**Acceptance Criteria:**

**Given** un fournisseur avec des factures au format constant
**When** un masque est créé/généré
**Then** le masque est stocké dans jsocr.mask avec partner_id
**And** le champ mask_data contient les zones d'extraction en JSON
**And** le masque est utilisé pour les prochaines factures de ce fournisseur
**And** le usage_count est incrémenté à chaque utilisation

---

### Story 6.6: Vue Gestion des Masques

As a **administrateur**,
I want **voir et gérer les masques d'extraction existants**,
So that **je puisse les modifier ou supprimer si nécessaire** (FR30).

**Acceptance Criteria:**

**Given** je suis connecté en tant qu'admin OCR
**When** j'accède au menu OCR IA > Masques
**Then** je vois la liste des masques avec: nom, fournisseur, actif, nombre d'utilisations
**And** je peux activer/désactiver un masque
**And** je peux supprimer un masque obsolète
**And** je peux voir le détail JSON du masque

---

### Story 6.7: Génération Automatique de Masque

As a **système**,
I want **générer un masque automatiquement après plusieurs factures similaires**,
So that **l'apprentissage soit automatisé**.

**Acceptance Criteria:**

**Given** 3+ factures d'un même fournisseur traitées avec succès
**When** le système détecte un pattern récurrent
**Then** un masque est généré automatiquement
**And** le masque capture les positions relatives des champs détectés
**And** le masque est créé en état actif
**And** un log JSOCR: indique la création du masque

---

## Récapitulatif Global

| Epic | Stories | FRs Couverts |
|------|---------|--------------|
| Epic 1: Fondations & Installation | 7 | NFR13, NFR16, NFR19, NFR20 |
| Epic 2: Configuration & Connectivité | 6 | FR5, FR10-11, FR36-41, FR44 |
| Epic 3: Ingestion PDF & OCR | 7 | FR1-4, FR6-9 |
| Epic 4: Analyse IA & Création Factures | 20 | FR12-21, FR32-35, FR26-27 (prédiction compte) |
| Epic 5: Validation & Indicateurs | 7 | FR22-24, FR42-43, FR45-46 |
| Epic 6: Apprentissage & Corrections | 7 | FR25-31 |
| **Total** | **54 stories** | **46 FRs couverts** |

