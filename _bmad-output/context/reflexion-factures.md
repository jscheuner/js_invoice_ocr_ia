
j'aimerai develloper une app pour odoo 18. je veux faire de la saisie automatique de facture fournisseur depuis des fichiers pdf text et pdf image. j'aimerai rester opensource. Il faudrai aussi ajouter une systeme de masque pour facilité la saisie des produit ou pour trouver un fournisseur le systeme de masque doit etre mis par dessin sur le pdf de facon visuel quel outils utilser pour faire cela. pour le moment devellope rien

14:23
Analyse technique pour votre module Odoo 18 de saisie automatique de factures
Excellente idée de projet ! Voici mon analyse des outils open source adaptés à chaque composant.

1. Extraction de texte depuis PDF
PDF avec texte extractible
PyMuPDF (fitz) est mon premier choix. Il est rapide, permet d'extraire le texte avec ses coordonnées exactes sur la page (indispensable pour votre système de masques), et gère bien les tableaux. Licence AGPL, compatible avec Odoo.

pdfplumber est une excellente alternative, particulièrement efficace pour extraire les tableaux structurés. Il donne aussi les coordonnées des caractères.

PDF image (scannés) - OCR
Outil	Forces	Faiblesses
Tesseract	Standard de l'industrie, très mature, 100+ langues	Configuration parfois délicate, moins bon sur documents dégradés
PaddleOCR	Excellent sur tableaux et documents structurés, très précis	Plus lourd à installer, dépendance PaddlePaddle
EasyOCR	Simple à utiliser, bon multi-langue	Plus lent, moins précis sur petits textes
docTR	Deep learning moderne, bonne précision	Plus récent, communauté plus petite
Ma recommandation : Commencez avec Tesseract (le plus documenté et intégré), avec possibilité de basculer vers PaddleOCR si vous avez beaucoup de tableaux complexes.

2. Système de masques visuels (le cœur du projet)
C'est la partie la plus innovante. Vous avez besoin de trois composants :

Affichage du PDF dans le navigateur
PDF.js (par Mozilla) est incontournable. C'est la référence open source pour le rendu PDF dans le navigateur. Il permet d'afficher le PDF page par page et de connaître les dimensions exactes pour superposer vos zones de dessin.

Dessin interactif des zones
Deux options principales :

Fabric.js — C'est mon choix recommandé. Cette librairie Canvas permet de dessiner des rectangles, de les redimensionner, les déplacer, les sélectionner. Elle gère la sérialisation JSON des objets dessinés (parfait pour sauvegarder vos masques en base). Très bien documentée et maintenue.

Konva.js — Alternative similaire, légèrement plus performante sur de nombreux objets, mais Fabric.js a une meilleure API pour le dessin libre et la sélection.

Architecture de l'interface de masques
┌─────────────────────────────────────────────────────────┐
│                    Interface OWL Odoo                    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌───────────────────────────┐ │
│  │                     │  │   Panel de configuration  │ │
│  │   PDF.js            │  │                           │ │
│  │   (rendu du PDF)    │  │   • Liste des zones       │ │
│  │                     │  │   • Type de champ associé │ │
│  │   + Fabric.js       │  │     (fournisseur, date,   │ │
│  │   (layer de dessin) │  │      montant HT, TVA...)  │ │
│  │                     │  │   • Regex de validation   │ │
│  │   ┌──────┐          │  │   • Post-traitement       │ │
│  │   │ Zone │ ←────────┼──┼── Zone sélectionnée      │ │
│  │   └──────┘          │  │                           │ │
│  │                     │  │   [Sauvegarder masque]    │ │
│  └─────────────────────┘  └───────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
3. Stack technique recommandée
Backend (Python/Odoo)
Composant	Librairie	Usage
Extraction PDF texte	PyMuPDF	Texte + coordonnées
Conversion PDF → Image	pdf2image	Préparation OCR
OCR	pytesseract + Tesseract	Reconnaissance caractères
Traitement image	Pillow, opencv-python	Amélioration avant OCR
Parsing dates/montants	dateparser, regex	Normalisation données
Frontend (JavaScript/OWL)
Composant	Librairie	Usage
Rendu PDF	PDF.js	Affichage dans canvas
Dessin zones	Fabric.js	Interface de masques
Framework	OWL (natif Odoo 18)	Composants réactifs
4. Fonctionnement du système de masques
Création d'un masque (template)
L'utilisateur uploade un PDF exemple d'un fournisseur
Le PDF s'affiche via PDF.js
L'utilisateur dessine des rectangles sur les zones d'intérêt (numéro facture, date, lignes produits, totaux...)
Pour chaque zone, il associe un champ Odoo cible
Le masque est sauvegardé avec : coordonnées normalisées (% de la page), champ cible, regex de validation optionnel
Application d'un masque
Nouvelle facture uploadée
Le système cherche un masque correspondant (par fournisseur détecté ou manuellement)
Pour chaque zone du masque, extraction du texte aux coordonnées définies
Post-traitement (nettoyage, conversion de format)
Pré-remplissage du formulaire facture Odoo
5. Modèles de données suggérés (conception)
invoice.ocr.template (Masque)
├── name
├── partner_id (fournisseur associé, optionnel)
├── detection_keywords (mots-clés pour auto-détection)
└── zone_ids (one2many)

invoice.ocr.template.zone (Zone du masque)
├── template_id
├── name (ex: "Numéro de facture")
├── field_mapping (champ Odoo cible: invoice_ref, date, amount_total...)
├── page_number
├── x, y, width, height (coordonnées en %)
├── extraction_type (text, table, amount, date)
├── regex_pattern (validation/extraction)
└── post_processing (code Python optionnel)

invoice.ocr.import (Facture importée)
├── pdf_file
├── template_id (masque utilisé)
├── extracted_data (JSON)
├── invoice_id (facture créée)
└── state (draft, extracted, validated, error)
6. Points d'attention
Performance OCR
Pensez à un système de queue (Odoo job queue) pour traiter les OCR en arrière-plan. Un PDF scanné peut prendre plusieurs secondes.

Matching fournisseur
Pour la détection automatique du fournisseur, vous pouvez combiner plusieurs approches : mots-clés dans le texte extrait, numéro SIRET/TVA, ou même signature visuelle du document.

Gestion des tableaux de lignes produits
C'est souvent le plus complexe. Prévoyez un type de zone "tableau" qui permet de définir les colonnes (description, quantité, prix unitaire, TVA...) et de les répéter sur plusieurs lignes.

Résumé des outils
Besoin	Outil recommandé	Licence
Extraction PDF texte	PyMuPDF	AGPL
OCR	Tesseract	Apache 2.0
Rendu PDF navigateur	PDF.js	Apache 2.0
Dessin zones	Fabric.js	MIT
Framework frontend	OWL (Odoo natif)	LGPL
Tous ces outils sont 100% open source et compatibles avec une distribution sous licence AGPL (celle d'Odoo Community).

Voulez-vous que j'approfondisse un aspect en particulier ? Par exemple, je peux détailler l'architecture du widget OWL pour le dessin des masques, ou la logique d'extraction avec PyMuPDF.

une fois le pdf transmis il faut cherche le fournisseur automatiquement puis si des zone de remplissage existe les charger. puis faire la reconnaissance de la facture par ocr puis si il le fuat par ia puis vlaidation des donnée json par IA ne fait pas de code pour le lmoment.

14:37
Workflow complet de traitement automatique des factures
Voici l'architecture du flux de traitement, étape par étape.

Vue d'ensemble du pipeline
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE DE TRAITEMENT                                 │
└─────────────────────────────────────────────────────────────────────────────────┘

     ┌──────────┐
     │ PDF reçu │
     └────┬─────┘
          │
          ▼
┌─────────────────────┐
│ ÉTAPE 1             │
│ Extraction brute    │──────► Texte brut + coordonnées
│ (PyMuPDF/OCR)       │        (même sans masque)
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐        ┌─────────────────────────┐
│ ÉTAPE 2             │        │ Base fournisseurs Odoo  │
│ Détection           │◄──────►│ • TVA intracom          │
│ fournisseur         │        │ • SIRET/SIREN           │
│                     │        │ • Mots-clés/Nom         │
└─────────┬───────────┘        │ • Email/domaine         │
          │                    └─────────────────────────┘
          │
          ▼
┌─────────────────────┐
│ ÉTAPE 3             │        ┌─────────────────────────┐
│ Chargement masque   │◄──────►│ Masques existants       │
│ (si existe)         │        │ liés au fournisseur     │
└─────────┬───────────┘        └─────────────────────────┘
          │
          ├─────────────────────────────────┐
          │                                 │
          ▼                                 ▼
┌─────────────────────┐         ┌─────────────────────────┐
│ ÉTAPE 4a            │         │ ÉTAPE 4b                │
│ Extraction guidée   │         │ Extraction IA           │
│ (avec masque)       │         │ (sans masque)           │
└─────────┬───────────┘         └───────────┬─────────────┘
          │                                 │
          └─────────────┬───────────────────┘
                        │
                        ▼
          ┌─────────────────────────┐
          │ ÉTAPE 5                 │
          │ Validation IA           │
          │ (cohérence + correction)│
          └───────────┬─────────────┘
                      │
                      ▼
          ┌─────────────────────────┐
          │ ÉTAPE 6                 │
          │ JSON structuré final    │
          │ → Création facture Odoo │
          └─────────────────────────┘
Étape 1 : Extraction brute du contenu
Objectif
Obtenir tout le texte du PDF, qu'il soit natif ou scanné.

Logique de décision
PDF reçu
    │
    ▼
┌─────────────────────────┐
│ Tentative extraction    │
│ texte avec PyMuPDF      │
└───────────┬─────────────┘
            │
            ▼
      ┌───────────┐
      │ Texte     │
      │ trouvé ?  │
      └─────┬─────┘
            │
     ┌──────┴──────┐
     │ OUI         │ NON (ou < seuil)
     ▼             ▼
┌──────────┐  ┌─────────────────┐
│ PDF texte│  │ PDF image       │
│ ────────►│  │ ───────────────►│
│ Extraction│  │ 1. Conversion   │
│ directe  │  │    image (300dpi)│
└──────────┘  │ 2. Prétraitement│
              │    (contraste,  │
              │    binarisation)│
              │ 3. OCR Tesseract│
              └─────────────────┘
Données produites
{
  "raw_text": "Texte complet...",
  "pages": [
    {
      "page_num": 1,
      "blocks": [
        {
          "text": "FACTURE N° 2024-001234",
          "bbox": [x0, y0, x1, y1],  // coordonnées
          "confidence": 0.95         // si OCR
        }
      ]
    }
  ],
  "source": "native" | "ocr"
}
Étape 2 : Détection automatique du fournisseur
Stratégie multi-critères avec scoring
┌─────────────────────────────────────────────────────────────────┐
│                    DÉTECTION FOURNISSEUR                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Texte brut extrait                                             │
│        │                                                        │
│        ▼                                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              EXTRACTEURS (en parallèle)                  │   │
│  ├──────────────┬──────────────┬──────────────┬────────────┤   │
│  │ N° TVA       │ SIRET/SIREN  │ IBAN         │ Email      │   │
│  │ Intracom     │              │              │ Domaine    │   │
│  │              │              │              │            │   │
│  │ Regex:       │ Regex:       │ Regex:       │ Regex:     │   │
│  │ FR[0-9]{11}  │ [0-9]{14}    │ FR[0-9]{23}  │ @(.+\..+)  │   │
│  │ DE[0-9]{9}   │ [0-9]{9}     │              │            │   │
│  │ ...          │              │              │            │   │
│  └──────┬───────┴──────┬───────┴──────┬───────┴─────┬──────┘   │
│         │              │              │             │           │
│         ▼              ▼              ▼             ▼           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                RECHERCHE ODOO                            │   │
│  │                                                          │   │
│  │  Pour chaque identifiant trouvé :                       │   │
│  │  → Recherche dans res.partner                           │   │
│  │  → Score de confiance attribué                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                SCORING                                   │   │
│  │                                                          │   │
│  │  • Match N° TVA          → +100 points (identifiant fort)│   │
│  │  • Match SIRET           → +100 points                   │   │
│  │  • Match IBAN            → +80 points                    │   │
│  │  • Match email/domaine   → +50 points                    │   │
│  │  • Match nom approché    → +30 points (fuzzy matching)   │   │
│  │  • Match adresse         → +20 points                    │   │
│  │  • Historique factures   → +10 points (déjà facturé)     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│         ┌─────────────────────────────────┐                    │
│         │ Score > seuil (ex: 80) ?        │                    │
│         └───────────────┬─────────────────┘                    │
│                         │                                       │
│              ┌──────────┴──────────┐                           │
│              │ OUI                 │ NON                        │
│              ▼                     ▼                            │
│    ┌─────────────────┐   ┌─────────────────────┐               │
│    │ Fournisseur     │   │ Fournisseur inconnu │               │
│    │ identifié       │   │ → Fallback IA       │               │
│    │ automatiquement │   │ → Ou création       │               │
│    └─────────────────┘   └─────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
Fallback IA pour fournisseur inconnu
Si aucun match fiable, l'IA peut proposer :

Extraction du nom commercial depuis l'en-tête
Suggestion de création d'un nouveau fournisseur
Recherche web du numéro de TVA pour validation
Étape 3 : Chargement du masque
Logique
┌────────────────────────────────────────────────────────────┐
│                   SÉLECTION DU MASQUE                       │
└────────────────────────────────────────────────────────────┘

Fournisseur identifié ?
        │
        ├── OUI ──►  Masque lié au fournisseur existe ?
        │                    │
        │             ┌──────┴──────┐
        │             │ OUI         │ NON
        │             ▼             ▼
        │      ┌───────────┐  ┌───────────────┐
        │      │ Charger   │  │ Mode IA pur   │
        │      │ le masque │  │ (étape 4b)    │
        │      └───────────┘  │               │
        │                     │ + Proposition │
        │                     │ de créer un   │
        │                     │ masque après  │
        │                     └───────────────┘
        │
        └── NON ──► Tentative détection masque par signature
                            │
                    ┌───────┴────────┐
                    │ Analyse layout │
                    │ du document    │
                    │ (structure,    │
                    │ positions)     │
                    └───────┬────────┘
                            │
                            ▼
                    Match avec masque existant ?
                            │
                     ┌──────┴──────┐
                     │ OUI         │ NON
                     ▼             ▼
               ┌──────────┐  ┌──────────┐
               │ Utiliser │  │ Mode IA  │
               │ ce masque│  │ pur      │
               └──────────┘  └──────────┘
Étape 4a : Extraction guidée par masque
Fonctionnement
┌─────────────────────────────────────────────────────────────────┐
│                 EXTRACTION AVEC MASQUE                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐
│           MASQUE CHARGÉ             │
│                                     │
│  Zone 1: "Numéro facture"           │
│    • Position: (10%, 5%, 30%, 8%)   │
│    • Champ: invoice_ref             │
│    • Regex: FAC[-/]?\d{4,}          │
│                                     │
│  Zone 2: "Date facture"             │
│    • Position: (70%, 5%, 95%, 8%)   │
│    • Champ: invoice_date            │
│    • Type: date                     │
│                                     │
│  Zone 3: "Total TTC"                │
│    • Position: (70%, 80%, 95%, 85%) │
│    • Champ: amount_total            │
│    • Type: amount                   │
│                                     │
│  Zone 4: "Lignes produits"          │
│    • Position: (5%, 30%, 95%, 70%)  │
│    • Type: table                    │
│    • Colonnes définies              │
└─────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────┐
│      POUR CHAQUE ZONE               │
│                                     │
│  1. Extraire texte aux coordonnées  │
│     (depuis données étape 1)        │
│                                     │
│  2. Appliquer post-traitement :     │
│     • Date → normaliser format      │
│     • Montant → parser (1.234,56)   │
│     • Texte → nettoyer              │
│     • Table → structurer lignes     │
│                                     │
│  3. Valider avec regex si défini    │
│                                     │
│  4. Marquer confiance :             │
│     • HIGH : match regex parfait    │
│     • MEDIUM : valeur plausible     │
│     • LOW : extraction incertaine   │
└─────────────────────────────────────┘
                │
                ▼
        JSON pré-structuré
        (avec niveaux de confiance)
Étape 4b : Extraction par IA (sans masque)
Outils IA open source recommandés
Outil	Description	Usage
Ollama + Llama 3	LLM local, gratuit	Extraction structurée, compréhension contexte
Ollama + Mistral	LLM local, performant	Alternative à Llama
Donut	Modèle spécialisé documents	OCR-free document understanding
LayoutLM	Microsoft, open source	Comprend la structure visuelle
Qwen2-VL	Vision-Language Model	Peut "lire" directement l'image du PDF
Architecture extraction IA
┌─────────────────────────────────────────────────────────────────┐
│                   EXTRACTION PAR IA                             │
└─────────────────────────────────────────────────────────────────┘

                    ┌─────────────────┐
                    │ Texte brut      │
                    │ (étape 1)       │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
    ┌─────────────────────┐     ┌─────────────────────────┐
    │ APPROCHE 1          │     │ APPROCHE 2              │
    │ LLM texte           │     │ Vision-Language Model   │
    │ (Llama/Mistral)     │     │ (Qwen2-VL, LLaVA)       │
    │                     │     │                         │
    │ Entrée: texte brut  │     │ Entrée: image du PDF    │
    │ + prompt structuré  │     │ + prompt                │
    └──────────┬──────────┘     └────────────┬────────────┘
               │                             │
               └──────────────┬──────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │ PROMPT TYPE             │
                 │                         │
                 │ "Extrais les infos de   │
                 │ cette facture au format │
                 │ JSON suivant:           │
                 │ - supplier_name         │
                 │ - invoice_number        │
                 │ - invoice_date          │
                 │ - lines: [              │
                 │   {description, qty,    │
                 │    unit_price, vat}     │
                 │   ]                     │
                 │ - amount_untaxed        │
                 │ - amount_tax            │
                 │ - amount_total          │
                 │ ..."                    │
                 └─────────────────────────┘
                              │
                              ▼
                     JSON extrait par IA
Recommandation modèle
Pour rester 100% local et open source, ma recommandation :

┌─────────────────────────────────────────────────────────────┐
│  STACK IA RECOMMANDÉE (100% local)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Serveur: Ollama (simple à déployer)                        │
│           └── Modèle: Llama 3.1 8B ou Mistral 7B            │
│               (bon équilibre performance/ressources)        │
│                                                             │
│  OU                                                         │
│                                                             │
│  Serveur: vLLM (plus performant, plus complexe)             │
│           └── Modèle: Qwen2-VL 7B (vision)                  │
│               (peut lire directement les images)            │
│                                                             │
│  Ressources minimales: 16 GB RAM, GPU 8GB VRAM recommandé   │
└─────────────────────────────────────────────────────────────┘
Étape 5 : Validation et correction par IA
Objectifs de la validation
┌─────────────────────────────────────────────────────────────────┐
│                    VALIDATION IA                                │
└─────────────────────────────────────────────────────────────────┘

JSON extrait (étape 4a ou 4b)
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  CONTRÔLES AUTOMATIQUES (règles)                               │
│  ─────────────────────────────────                             │
│  □ Total TTC = Total HT + TVA ?                                │
│  □ Somme des lignes = Total HT ?                               │
│  □ Date dans le passé (pas future) ?                           │
│  □ N° TVA format valide ?                                      │
│  □ IBAN format valide ?                                        │
│                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  VALIDATION IA (LLM)                                           │
│  ───────────────────                                           │
│                                                                 │
│  Prompt:                                                        │
│  "Voici les données extraites d'une facture et le texte       │
│   source. Vérifie la cohérence et corrige si nécessaire:       │
│                                                                 │
│   1. Les montants sont-ils cohérents ?                         │
│   2. Les dates sont-elles au bon format ?                      │
│   3. Les descriptions produits sont-elles complètes ?          │
│   4. Y a-t-il des données manquantes importantes ?             │
│   5. Y a-t-il des erreurs d'OCR probables ?                    │
│                                                                 │
│   Retourne le JSON corrigé avec un champ 'corrections'         │
│   listant les modifications et leur raison."                   │
│                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ENRICHISSEMENT (optionnel)                                    │
│  ─────────────────────────                                     │
│                                                                 │
│  • Matching produits Odoo existants                            │
│    (par description, référence, code-barres)                   │
│                                                                 │
│  • Suggestion compte comptable                                 │
│    (basé sur historique fournisseur)                           │
│                                                                 │
│  • Détection devise si non explicite                           │
│                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                  JSON validé et enrichi
Exemple de corrections IA
json
{
  "original": {
    "amount_untaxed": 1000.00,
    "amount_tax": 200.00,
    "amount_total": 1200.00,
    "lines": [
      {"description": "Prestation A", "amount": 500.00},
      {"description": "Prestation B", "amount": 400.00}
    ]
  },
  "corrected": {
    "amount_untaxed": 900.00,
    "amount_tax": 180.00,
    "amount_total": 1080.00,
    "lines": [
      {"description": "Prestation A", "amount": 500.00},
      {"description": "Prestation B", "amount": 400.00}
    ]
  },
  "corrections": [
    {
      "field": "amount_untaxed",
      "reason": "Somme des lignes (900€) ≠ montant extrait (1000€). Corrigé selon les lignes.",
      "confidence": "HIGH"
    },
    {
      "field": "amount_tax",
      "reason": "Recalculé: 900 × 20% = 180€",
      "confidence": "HIGH"
    }
  ],
  "warnings": [
    "Une ligne semble manquante pour atteindre le total initial. Vérification manuelle recommandée."
  ]
}
Étape 6 : Résultat final et création Odoo
Structure JSON finale
json
{
  "metadata": {
    "source_file": "facture_2024_001.pdf",
    "processing_date": "2024-01-15T10:30:00",
    "extraction_method": "mask" | "ai" | "hybrid",
    "template_used": "template_fournisseur_xyz",
    "overall_confidence": 0.92
  },
  
  "supplier": {
    "odoo_partner_id": 42,
    "name": "Fournisseur XYZ",
    "vat": "FR12345678901",
    "detection_method": "vat_number",
    "confidence": 1.0
  },
  
  "invoice": {
    "reference": "FAC-2024-001234",
    "date": "2024-01-10",
    "due_date": "2024-02-10",
    "currency": "EUR",
    "confidence": {
      "reference": 0.98,
      "date": 0.95,
      "due_date": 0.90
    }
  },
  
  "lines": [
    {
      "sequence": 1,
      "description": "Prestation de conseil",
      "quantity": 5.0,
      "unit_price": 100.00,
      "tax_percent": 20.0,
      "subtotal": 500.00,
      "matched_product_id": null,
      "suggested_account_id": 604100,
      "confidence": 0.88
    }
  ],
  
  "totals": {
    "amount_untaxed": 500.00,
    "amount_tax": 100.00,
    "amount_total": 600.00,
    "validation": {
      "lines_sum_matches": true,
      "tax_calculation_correct": true
    }
  },
  
  "validation": {
    "status": "validated" | "needs_review" | "error",
    "issues": [],
    "corrections_applied": []
  }
}
```

---

## Schéma de décision complet
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ARBRE DE DÉCISION COMPLET                                │
└─────────────────────────────────────────────────────────────────────────────────┘

                              PDF REÇU
                                  │
                                  ▼
                        ┌─────────────────┐
                        │ Extraction brute│
                        │ (PyMuPDF/OCR)   │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Détection       │
                        │ fournisseur     │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
             TROUVÉ │                         │ NON TROUVÉ
                    ▼                         ▼
           ┌────────────────┐        ┌────────────────┐
           │ Masque existe ?│        │ IA: extraire   │
           └───────┬────────┘        │ nom fournisseur│
                   │                 └───────┬────────┘
          ┌────────┴────────┐                │
          │                 │                ▼
       OUI│              NON│        ┌────────────────┐
          ▼                 │        │ Créer ou       │
   ┌─────────────┐          │        │ sélectionner   │
   │ Extraction  │          │        │ manuellement   │
   │ par masque  │          │        └───────┬────────┘
   │ (guidée)    │          │                │
   └──────┬──────┘          │                │
          │                 │                │
          │          ┌──────┴────────────────┘
          │          │
          │          ▼
          │   ┌─────────────┐
          │   │ Extraction  │
          │   │ par IA      │
          │   │ (LLM local) │
          │   └──────┬──────┘
          │          │
          └────┬─────┘
               │
               ▼
        ┌─────────────┐
        │ Validation  │
        │ IA          │
        │ (cohérence) │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │ Confiance   │
        │ globale ?   │
        └──────┬──────┘
               │
     ┌─────────┼─────────┐
     │         │         │
   HIGH     MEDIUM     LOW
     │         │         │
     ▼         ▼         ▼
┌─────────┐ ┌───────┐ ┌───────────┐
│Création │ │Review │ │ Review    │
│auto     │ │rapide │ │ détaillé  │
│facture  │ │       │ │ + alerte  │
└─────────┘ └───────┘ └───────────┘


                    ┌─────────────────────────────────┐
                    │     APPRENTISSAGE CONTINU       │
                    │                                 │
                    │  Après validation humaine :     │
                    │  • Proposer création masque     │
                    │  • Enrichir règles extraction   │
                    │  • Améliorer matching produits  │
                    └─────────────────────────────────┘
Résumé des outils par étape
Étape	Outils Open Source
1. Extraction brute	PyMuPDF, Tesseract, pdf2image
2. Détection fournisseur	Regex, RapidFuzz (fuzzy matching), recherche Odoo
3. Gestion masques	PDF.js + Fabric.js (création), PostgreSQL (stockage)
4a. Extraction masque	PyMuPDF (coordonnées), dateparser, babel (montants)
4b. Extraction IA	Ollama + Llama 3 / Mistral, ou Qwen2-VL
5. Validation IA	Même LLM, règles Python
6. Création Odoo	API Odoo native
Souhaitez-vous que je détaille davantage une étape en particulier ? Par exemple :

La logique de scoring pour la détection fournisseur
Le format des prompts IA pour l'extraction/validation
L'architecture technique du serveur IA local (Ollama)
Le workflow utilisateur côté interface Odoo
pour la création du masque avec Fabric.js on pourrai utiliser des couleurs pour les différents element. par exemple le gris pour la zone avec le nom et l'adresse du fournisseur, en rouge le total ttc de la facture en orange le montant HT de la facture ect. as-tu une autre facon pour différencier les elements du masque?

16:22
Méthodes de différenciation visuelle des zones de masque
Excellente réflexion ! La couleur seule pose des problèmes (daltonisme, trop de zones = confusion). Voici plusieurs approches complémentaires.

1. Système de couleurs enrichi
Palette par catégorie fonctionnelle
┌─────────────────────────────────────────────────────────────────┐
│                    PALETTE DE COULEURS                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  IDENTIFICATION FOURNISSEUR (tons froids)                       │
│  ┌─────────┐                                                    │
│  │  ████   │  Gris #6B7280 — Nom/Adresse fournisseur           │
│  │  ████   │  Bleu #3B82F6 — N° TVA / SIRET                    │
│  │  ████   │  Cyan #06B6D4 — IBAN / RIB                        │
│  └─────────┘                                                    │
│                                                                 │
│  IDENTIFICATION FACTURE (tons neutres)                          │
│  ┌─────────┐                                                    │
│  │  ████   │  Violet #8B5CF6 — N° de facture                   │
│  │  ████   │  Indigo #6366F1 — Date facture                    │
│  │  ████   │  Slate #64748B — Date d'échéance                  │
│  └─────────┘                                                    │
│                                                                 │
│  MONTANTS (tons chauds - attention)                             │
│  ┌─────────┐                                                    │
│  │  ████   │  Orange #F97316 — Montant HT                      │
│  │  ████   │  Amber #F59E0B — Montant TVA                      │
│  │  ████   │  Rouge #EF4444 — Total TTC                        │
│  └─────────┘                                                    │
│                                                                 │
│  LIGNES PRODUITS (tons verts)                                   │
│  ┌─────────┐                                                    │
│  │  ████   │  Vert #22C55E — Zone tableau complète             │
│  │  ████   │  Emerald #10B981 — Description produit            │
│  │  ████   │  Teal #14B8A6 — Quantité / Prix unitaire          │
│  └─────────┘                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
2. Patterns et textures (accessibilité daltonisme)
Combinaison couleur + motif
┌─────────────────────────────────────────────────────────────────┐
│                    PATTERNS PAR TYPE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────┐   FOURNISSEUR                               │
│  │ ░░░░░░░░░░░░░ │   Pointillés                                │
│  │ ░░░░░░░░░░░░░ │                                             │
│  └───────────────┘                                              │
│                                                                 │
│  ┌───────────────┐   IDENTIFICATION FACTURE                    │
│  │ ───────────── │   Lignes horizontales                       │
│  │ ───────────── │                                             │
│  └───────────────┘                                              │
│                                                                 │
│  ┌───────────────┐   MONTANTS                                  │
│  │ ╲╲╲╲╲╲╲╲╲╲╲╲╲ │   Hachures diagonales                       │
│  │ ╲╲╲╲╲╲╲╲╲╲╲╲╲ │                                             │
│  └───────────────┘                                              │
│                                                                 │
│  ┌───────────────┐   LIGNES PRODUITS                           │
│  │ ┼┼┼┼┼┼┼┼┼┼┼┼┼ │   Grille / quadrillage                      │
│  │ ┼┼┼┼┼┼┼┼┼┼┼┼┼ │                                             │
│  └───────────────┘                                              │
│                                                                 │
│  ┌───────────────┐   CHAMP LIBRE / NOTES                       │
│  │               │   Uni (sans motif)                          │
│  │               │                                              │
│  └───────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Implémentation Fabric.js des patterns
Fabric.js supporte les patterns SVG. On peut créer des motifs personnalisés pour chaque catégorie.

3. Icônes et symboles
Icône dans le coin de chaque zone
┌─────────────────────────────────────────────────────────────────┐
│                    ICÔNES PAR CHAMP                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐                                      │
│  │ 🏢 ░░░░░░░░░░░░░░░░░ │  Fournisseur (building)              │
│  └──────────────────────┘                                      │
│                                                                 │
│  ┌──────────────────────┐                                      │
│  │ 📋 ░░░░░░░░░░░░░░░░░ │  N° Facture (document)               │
│  └──────────────────────┘                                      │
│                                                                 │
│  ┌──────────────────────┐                                      │
│  │ 📅 ░░░░░░░░░░░░░░░░░ │  Date (calendrier)                   │
│  └──────────────────────┘                                      │
│                                                                 │
│  ┌──────────────────────┐                                      │
│  │ 💶 ░░░░░░░░░░░░░░░░░ │  Montant HT (euro)                   │
│  └──────────────────────┘                                      │
│                                                                 │
│  ┌──────────────────────┐                                      │
│  │ 🧾 ░░░░░░░░░░░░░░░░░ │  TVA (receipt)                       │
│  └──────────────────────┘                                      │
│                                                                 │
│  ┌──────────────────────┐                                      │
│  │ 💰 ░░░░░░░░░░░░░░░░░ │  Total TTC (money bag)               │
│  └──────────────────────┘                                      │
│                                                                 │
│  ┌──────────────────────┐                                      │
│  │ 📦 ░░░░░░░░░░░░░░░░░ │  Lignes produits (package)           │
│  └──────────────────────┘                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Alternative avec icônes Lucide (plus pro)
Champ	Icône Lucide	Nom
Fournisseur	<Building2 />	building-2
N° TVA	<BadgeCheck />	badge-check
N° Facture	<FileText />	file-text
Date	<Calendar />	calendar
Échéance	<CalendarClock />	calendar-clock
Montant HT	<Calculator />	calculator
TVA	<Percent />	percent
Total TTC	<CircleDollarSign />	circle-dollar-sign
Lignes	<Table />	table
IBAN	<CreditCard />	credit-card
4. Styles de bordure
Différenciation par le contour
┌─────────────────────────────────────────────────────────────────┐
│                    STYLES DE BORDURE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐                                       │
│  │                     │   Solide — Champs obligatoires        │
│  │                     │   (épaisseur 3px)                     │
│  └─────────────────────┘                                       │
│                                                                 │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐                                       │
│                          Tirets — Champs optionnels            │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘   (dashed)                            │
│                                                                 │
│  ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐                                       │
│  ╎                     ╎   Pointillés — Champs calculés        │
│  └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘   (dotted)                            │
│                                                                 │
│  ╔═════════════════════╗                                       │
│  ║                     ║   Double — Totaux importants          │
│  ╚═════════════════════╝                                       │
│                                                                 │
│  ┌─────────────────────┐                                       │
│  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│   Épais + ombré — Zone tableau       │
│  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│   (shadow)                           │
│  └─────────────────────┘                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
5. Labels / Étiquettes flottantes
Affichage permanent du nom du champ
┌─────────────────────────────────────────────────────────────────┐
│                    LABELS ATTACHÉS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         N° Facture                                              │
│         ▼                                                       │
│  ┌──────┴──────────────────────────────┐                       │
│  │  FAC-2024-001234                    │                       │
│  └─────────────────────────────────────┘                       │
│                                                                 │
│                                                                 │
│                                              Total TTC          │
│                                              ▼                  │
│                               ┌──────────────┴────┐            │
│                               │     1 234,56 €    │            │
│                               └───────────────────┘            │
│                                                                 │
│                                                                 │
│  Lignes produits                                                │
│  ▼                                                              │
│  ┌──────────────────────────────────────────────────┐          │
│  │  Description    │  Qté  │  PU    │  Total        │          │
│  │  ─────────────────────────────────────────────── │          │
│  │  Produit A      │  2    │ 100€   │  200€         │          │
│  │  Produit B      │  1    │  50€   │   50€         │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Options d'affichage des labels
Mode	Description	Quand l'utiliser
Toujours visible	Label affiché en permanence	Peu de zones
Au survol	Label apparaît au hover	Nombreuses zones
Icône + tooltip	Icône visible, nom au survol	Interface épurée
Badge compact	Code court (ex: "TTC", "HT")	Zones petites
6. Système de numérotation / séquence
Ordre de saisie visuel
┌─────────────────────────────────────────────────────────────────┐
│                    NUMÉROTATION                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│     ①                                          ②               │
│  ┌──────────────────────────┐    ┌────────────────────┐        │
│  │  Fournisseur XYZ         │    │  FAC-2024-001      │        │
│  │  123 rue Example         │    └────────────────────┘        │
│  └──────────────────────────┘                  ③               │
│                                      ┌────────────────────┐    │
│                                      │  15/01/2024        │    │
│                                      └────────────────────┘    │
│                                                                 │
│     ④                                                          │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  Lignes produits...                                  │      │
│  └──────────────────────────────────────────────────────┘      │
│                                                                 │
│                                      ⑤         ⑥       ⑦      │
│                               ┌────────┐ ┌────────┐ ┌────────┐ │
│                               │  HT    │ │  TVA   │ │  TTC   │ │
│                               └────────┘ └────────┘ └────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Avantage : indique aussi l'ordre de tabulation pour la validation manuelle.

7. Groupes visuels avec en-têtes
Regroupement par catégorie
┌─────────────────────────────────────────────────────────────────┐
│                    GROUPES AVEC HEADERS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─ FOURNISSEUR ────────────────────────────────────────────┐  │
│  │  ┌────────────────────────────┐  ┌────────────────────┐  │  │
│  │  │  Nom + Adresse             │  │  N° TVA            │  │  │
│  │  └────────────────────────────┘  └────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ FACTURE ────────────────────────────────────────────────┐  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │  N° Facture  │  │  Date        │  │  Échéance    │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ TOTAUX ─────────────────────────────────────────────────┐  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │  │
│  │  │  HT          │  │  TVA         │  │  TTC         │    │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
8. Formes différentes
Par type de donnée
┌─────────────────────────────────────────────────────────────────┐
│                    FORMES PAR TYPE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐                                       │
│  │                     │   Rectangle — Texte simple            │
│  └─────────────────────┘   (nom, adresse, description)         │
│                                                                 │
│  ╭─────────────────────╮                                       │
│  │                     │   Rectangle arrondi — Identifiants    │
│  ╰─────────────────────╯   (n° facture, TVA, SIRET)            │
│                                                                 │
│      ┌─────────────┐                                           │
│     ╱             ╲                                            │
│    │               │       Hexagone — Montants                 │
│     ╲             ╱                                            │
│      └─────────────┘                                           │
│                                                                 │
│  ◇─────────────────────◇                                       │
│  │                     │   Losange/diamant — Dates             │
│  ◇─────────────────────◇                                       │
│                                                                 │
│  ┌──────────────────────────────────────────────────────┐      │
│  │ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ │      │
│  │ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ │      │
│  │ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ │      │
│  └──────────────────────────────────────────────────────┘      │
│  Rectangle avec lignes internes — Tableau                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Ma recommandation : système hybride
Combinaison optimale
┌─────────────────────────────────────────────────────────────────┐
│              SYSTÈME DE DIFFÉRENCIATION RECOMMANDÉ              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NIVEAU 1 — Couleur (perception rapide)                        │
│  ─────────────────────────────────────                         │
│  • Catégorie principale = famille de couleurs                  │
│  • Bleus = fournisseur                                         │
│  • Violets = identification facture                            │
│  • Oranges/Rouges = montants                                   │
│  • Verts = lignes produits                                     │
│                                                                 │
│  NIVEAU 2 — Icône (identification précise)                     │
│  ────────────────────────────────────────                      │
│  • Petite icône en haut à gauche de chaque zone               │
│  • Permet d'identifier le champ exact                          │
│  • Accessible aux daltoniens                                   │
│                                                                 │
│  NIVEAU 3 — Bordure (importance/obligation)                    │
│  ─────────────────────────────────────────                     │
│  • Solide épaisse = obligatoire                               │
│  • Tirets = optionnel                                          │
│  • Double = validation critique (totaux)                       │
│                                                                 │
│  NIVEAU 4 — Label (clarté)                                     │
│  ────────────────────────                                      │
│  • Nom du champ au survol (tooltip)                           │
│  • Badge compact visible si espace suffisant                   │
│                                                                 │
│  NIVEAU 5 — Numéro (workflow)                                  │
│  ────────────────────────────                                  │
│  • Numéro de séquence pour ordre de vérification              │
│  • Optionnel, activable                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Exemple visuel final
┌─────────────────────────────────────────────────────────────────────────┐
│                         FACTURE EXEMPLE                                 │
│                                                                         │
│   ① 🏢                                              ② 📋               │
│   ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━┓        ╭─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─╮        │
│   ┃  Fournisseur ABC          ┃        │  FAC-2024-00123      │        │
│   ┃  15 rue de Paris          ┃        ╰─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─╯        │
│   ┃  75001 Paris              ┃                    ③ 📅               │
│   ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━┛           ┌─────────────────┐          │
│   [BLEU] [SOLIDE] [OBLIGATOIRE]           │  15/01/2024     │          │
│                                           └─────────────────┘          │
│                                           [VIOLET] [TIRETS]            │
│                                                                         │
│   ④ 📦                                                                 │
│   ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│   ┃  Description          │  Qté  │  PU HT    │  Total HT         ┃  │
│   ┃  ─────────────────────┼───────┼───────────┼─────────────────  ┃  │
│   ┃  Prestation conseil   │  5    │  100,00 € │  500,00 €         ┃  │
│   ┃  Formation            │  2    │  250,00 € │  500,00 €         ┃  │
│   ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│   [VERT] [QUADRILLÉ] [OMBRE]                                           │
│                                                                         │
│                                         ⑤ 💶         ⑥ %        ⑦ 💰 │
│                                   ┌──────────┐ ┌─────────┐ ╔═══════════╗│
│                                   │ 1000,00€ │ │ 200,00€ │ ║ 1200,00€  ║│
│                                   └──────────┘ └─────────┘ ╚═══════════╝│
│                                   [ORANGE]     [AMBER]     [ROUGE]      │
│                                   [HACHURES]   [HACHURES]  [DOUBLE]     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

LÉGENDE :
━━━ Bordure solide = Obligatoire
─ ─ Bordure tirets = Optionnel  
═══ Bordure double = Critique (vérification auto)
Configuration utilisateur suggérée
Option	Description	Défaut
Afficher les icônes	Icône dans chaque zone	✅ Oui
Afficher les numéros	Séquence de validation	❌ Non
Mode daltonien	Patterns + icônes renforcés	❌ Non
Labels permanents	Nom du champ toujours visible	❌ Non
Transparence zones	Opacité du fond (0-100%)	30%
Souhaitez-vous que je détaille l'un de ces aspects, par exemple comment implémenter les patterns dans Fabric.js, ou la structure de données pour stocker toutes ces propriétés visuelles ?

je penses qu'il faut 2 niveaux masque un premier avec 3 parties l'entete de la facture puis les lignes de facture et une partie pour les totaux et si l'ia n'arrive pas a detecter tous les champs sur certain fournisseur on fait un masque plus poussé. Il faut faire le moins de masque possible. as tu d'autre proposition?

16:27
Architecture de masques à niveaux progressifs
Excellente approche ! Minimiser les masques = moins de maintenance et plus de flexibilité. Voici comment structurer cela, avec d'autres propositions.

Votre concept : 3 zones + escalade
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NIVEAU 1 : MASQUE UNIVERSEL                          │
│                        (3 zones seulement)                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │                        ZONE ENTÊTE                                  │  │
│   │                                                                     │  │
│   │   L'IA cherche ici :                                               │  │
│   │   • Nom fournisseur, adresse                                       │  │
│   │   • N° TVA, SIRET                                                  │  │
│   │   • N° facture, date, échéance                                     │  │
│   │   • Références client                                              │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                     │  │
│   │                        ZONE LIGNES                                  │  │
│   │                                                                     │  │
│   │   L'IA cherche ici :                                               │  │
│   │   • Tableau des produits/services                                  │  │
│   │   • Descriptions, quantités, prix                                  │  │
│   │                                                                     │  │
│   │                                                                     │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                        ZONE TOTAUX                                  │  │
│   │                                                                     │  │
│   │   L'IA cherche ici : HT, TVA, TTC, acomptes, net à payer          │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    ▼
                            IA échoue sur 
                           certains champs ?
                                    │
                         ┌──────────┴──────────┐
                         │ NON                 │ OUI
                         ▼                     ▼
                   ┌───────────┐      ┌─────────────────┐
                   │ Terminé ! │      │ NIVEAU 2        │
                   │ Facture   │      │ Masque détaillé │
                   │ extraite  │      │ par fournisseur │
                   └───────────┘      └─────────────────┘
Proposition alternative : système à 4 niveaux
Encore plus progressif
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PYRAMIDE D'EXTRACTION                                   │
└─────────────────────────────────────────────────────────────────────────────┘


                              ┌───────────┐
                              │ NIVEAU 0  │
                              │ IA pure   │
                              │ (aucun    │
                              │  masque)  │
                              └─────┬─────┘
                                    │
                    Échec ou confiance < 70% ?
                                    │
                         ┌──────────┴──────────┐
                         │ NON                 │ OUI
                         ▼                     ▼
                   ┌───────────┐      ┌─────────────────┐
                   │    OK     │      │    NIVEAU 1     │
                   └───────────┘      │  3 zones        │
                                      │  (entête,       │
                                      │   lignes,       │
                                      │   totaux)       │
                                      └────────┬────────┘
                                               │
                               Échec ou confiance < 80% ?
                                               │
                                    ┌──────────┴──────────┐
                                    │ NON                 │ OUI
                                    ▼                     ▼
                              ┌───────────┐      ┌─────────────────┐
                              │    OK     │      │    NIVEAU 2     │
                              └───────────┘      │  Zones par      │
                                                 │  catégorie      │
                                                 │  (6-8 zones)    │
                                                 └────────┬────────┘
                                                          │
                                          Échec sur champs précis ?
                                                          │
                                               ┌──────────┴──────────┐
                                               │ NON                 │ OUI
                                               ▼                     ▼
                                         ┌───────────┐      ┌─────────────────┐
                                         │    OK     │      │    NIVEAU 3     │
                                         └───────────┘      │  Masque précis  │
                                                            │  champ par      │
                                                            │  champ          │
                                                            └─────────────────┘
Détail des niveaux
Niveau 0 : IA pure (pas de masque)
┌─────────────────────────────────────────────────────────────────┐
│  NIVEAU 0 — EXTRACTION IA SANS GUIDAGE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Quand l'utiliser :                                            │
│  • Première facture d'un fournisseur inconnu                   │
│  • Factures avec format "standard" bien structuré              │
│  • Test initial pour évaluer la difficulté                     │
│                                                                 │
│  Fonctionnement :                                               │
│  • Envoyer tout le texte extrait à l'IA                        │
│  • Prompt : "Extrais toutes les données de cette facture"      │
│  • L'IA se débrouille seule                                    │
│                                                                 │
│  Avantage : Aucune configuration nécessaire                    │
│  Inconvénient : Peut échouer sur formats atypiques             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Niveau 1 : 3 zones (votre proposition)
┌─────────────────────────────────────────────────────────────────┐
│  NIVEAU 1 — 3 GRANDES ZONES                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Quand l'utiliser :                                            │
│  • L'IA pure a des difficultés de localisation                 │
│  • Factures avec mise en page non standard                     │
│  • Entête à droite au lieu de gauche, etc.                     │
│                                                                 │
│  Les 3 zones :                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ENTÊTE : identité fournisseur + références facture      │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ LIGNES : tableau des produits/prestations               │   │
│  ├─────────────────────────────────────────────────────────┤   │
│  │ TOTAUX : récapitulatif financier                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  L'IA reçoit :                                                 │
│  • Le texte de chaque zone séparément                          │
│  • Instruction : "Dans cette zone ENTÊTE, trouve..."           │
│                                                                 │
│  Avantage : Guide l'IA sans travail de masque détaillé         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Niveau 2 : Zones par catégorie (6-8 zones)
┌─────────────────────────────────────────────────────────────────┐
│  NIVEAU 2 — ZONES PAR CATÉGORIE                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Quand l'utiliser :                                            │
│  • L'IA confond des zones (ex: adresse client/fournisseur)     │
│  • Informations dispersées sur la page                         │
│                                                                 │
│  Les zones :                                                    │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ 1. FOURNISSEUR       │  │ 2. CLIENT            │            │
│  │    (nom, adresse,    │  │    (si présent)      │            │
│  │    TVA, SIRET)       │  │                      │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ 3. RÉFÉRENCES        │  │ 4. DATES             │            │
│  │    (n° facture,      │  │    (facture,         │            │
│  │    n° commande)      │  │    échéance)         │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 5. LIGNES PRODUITS                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ 6. TOTAUX            │  │ 7. PAIEMENT          │            │
│  │    (HT, TVA, TTC)    │  │    (IBAN, mode)      │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Niveau 3 : Masque précis (champ par champ)
┌─────────────────────────────────────────────────────────────────┐
│  NIVEAU 3 — MASQUE COMPLET (dernier recours)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Quand l'utiliser :                                            │
│  • Fournisseur avec format très particulier                    │
│  • OCR de mauvaise qualité récurrent                           │
│  • Volume important justifiant l'investissement                │
│                                                                 │
│  Chaque champ = une zone :                                     │
│  ┌────────┐ ┌────────────────┐ ┌─────────┐ ┌─────────┐        │
│  │N° TVA  │ │Nom fournisseur │ │N° Fact  │ │ Date    │        │
│  └────────┘ └────────────────┘ └─────────┘ └─────────┘        │
│                                                                 │
│  Extraction directe par coordonnées, sans IA                   │
│  (ou IA minimale pour nettoyage)                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
Autres propositions
Proposition A : Masques par "famille de format"
┌─────────────────────────────────────────────────────────────────────────────┐
│             MASQUES PAR FAMILLE (pas par fournisseur)                       │
└─────────────────────────────────────────────────────────────────────────────┘

Au lieu de : 1 masque = 1 fournisseur
Faire :      1 masque = 1 type de layout

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  FAMILLE "CLASSIQUE"              FAMILLE "ENTÊTE DROITE"                  │
│  ┌─────────────────────┐          ┌─────────────────────┐                  │
│  │ [Fournisseur]       │          │       [Fournisseur] │                  │
│  │              [Réfs] │          │ [Réfs]              │                  │
│  │ [Lignes ...........]│          │ [Lignes ...........]│                  │
│  │ [Totaux]            │          │            [Totaux] │                  │
│  └─────────────────────┘          └─────────────────────┘                  │
│  → 60% des factures               → 20% des factures                       │
│                                                                             │
│  FAMILLE "DEUX COLONNES"          FAMILLE "COMPACT"                        │
│  ┌─────────────────────┐          ┌─────────────────────┐                  │
│  │ [Four] │ [Réfs    ] │          │ [Tout en haut     ] │                  │
│  │ [neur] │ [Lignes  ] │          │ [Lignes ...........]│                  │
│  │        │ [Totaux  ] │          │ [Tot]               │                  │
│  └─────────────────────┘          └─────────────────────┘                  │
│  → 10% des factures               → 10% des factures                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Avantage : 4-5 masques couvrent 90% des cas
           Nouveau fournisseur → associer à une famille existante
Proposition B : Auto-détection de layout + suggestion
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DÉTECTION AUTOMATIQUE DE STRUCTURE                       │
└─────────────────────────────────────────────────────────────────────────────┘

                         PDF reçu
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Analyse structure visuelle  │
              │  (blocs de texte, tableaux,  │
              │   positions relatives)       │
              └──────────────┬───────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Matching avec layouts       │
              │  connus (familles)           │
              └──────────────┬───────────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
           Match trouvé           Pas de match
                  │                     │
                  ▼                     ▼
         ┌────────────────┐    ┌────────────────────┐
         │ Utiliser ce    │    │ IA pure            │
         │ masque famille │    │ + proposition      │
         └────────────────┘    │ nouvelle famille   │
                               └────────────────────┘

L'utilisateur n'a plus qu'à confirmer ou ajuster
Proposition C : Apprentissage par correction
┌─────────────────────────────────────────────────────────────────────────────┐
│                    APPRENTISSAGE PROGRESSIF                                 │
└─────────────────────────────────────────────────────────────────────────────┘

         Facture traitée (IA pure)
                    │
                    ▼
         ┌─────────────────────────┐
         │ Validation utilisateur  │
         │ "Ce champ est faux"     │
         │ → Correction manuelle   │
         └────────────┬────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │ Système enregistre :    │
         │ • Position du champ     │
         │ • Valeur correcte       │
         │ • Contexte (fournisseur)│
         └────────────┬────────────┘
                      │
                      ▼
         ┌─────────────────────────┐
         │ Après N corrections     │
         │ sur même fournisseur :  │
         │                         │
         │ "Créer un masque        │
         │  automatiquement ?"     │
         └─────────────────────────┘

Le masque se construit tout seul à partir des corrections !
Proposition D : Zones dynamiques par détection de blocs
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DÉTECTION AUTOMATIQUE DE ZONES                           │
└─────────────────────────────────────────────────────────────────────────────┘

Plutôt que dessiner manuellement les 3 zones,
le système les détecte automatiquement :

         ┌─────────────────────────────────────────┐
         │  PDF reçu                               │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │  Analyse des blocs de texte            │
         │  (PyMuPDF donne les rectangles)        │
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │  Détection du tableau                   │
         │  (lignes répétitives, colonnes alignées)│
         └────────────────────┬────────────────────┘
                              │
                              ▼
         ┌─────────────────────────────────────────┐
         │  Classification automatique :           │
         │  • Au-dessus du tableau → ENTÊTE        │
         │  • Le tableau → LIGNES                  │
         │  • En-dessous du tableau → TOTAUX       │
         └─────────────────────────────────────────┘

Résultat : Niveau 1 automatique, sans dessin !
Ma recommandation : hybride intelligent
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE RECOMMANDÉE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  1. DÉTECTION AUTO DES 3 ZONES (pas de masque manuel)                      │
│     ─────────────────────────────────────────────────                      │
│     • Analyse structurelle du PDF                                          │
│     • Identification automatique : entête / lignes / totaux                │
│     • Fonctionne pour 70-80% des factures                                  │
│                                                                             │
│  2. BIBLIOTHÈQUE DE FAMILLES (4-5 masques niveau 1)                        │
│     ────────────────────────────────────────────────                       │
│     • Pour les formats atypiques                                           │
│     • Association fournisseur → famille                                    │
│     • Réutilisation maximale                                               │
│                                                                             │
│  3. APPRENTISSAGE PAR CORRECTION                                           │
│     ────────────────────────────────                                       │
│     • Chaque correction enrichit le système                                │
│     • Proposition auto de masque après N erreurs                           │
│     • Le masque détaillé (niveau 3) est généré, pas dessiné               │
│                                                                             │
│  4. MASQUE MANUEL = EXCEPTION                                              │
│     ─────────────────────────────                                          │
│     • Seulement si tout le reste échoue                                    │
│     • Fournisseurs très spécifiques et récurrents                         │
│     • Interface de dessin disponible mais rarement utilisée               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
Workflow utilisateur simplifié
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXPÉRIENCE UTILISATEUR                                   │
└─────────────────────────────────────────────────────────────────────────────┘

ÉTAPE 1 : Upload facture
          │
          ▼
     ┌─────────────────────────────────────────────────────────────┐
     │  "Traitement en cours..."                                   │
     │                                                             │
     │  ✓ Texte extrait                                           │
     │  ✓ Structure détectée automatiquement                      │
     │  ✓ Fournisseur identifié : ABC SARL                        │
     │  ✓ Données extraites                                       │
     └─────────────────────────────────────────────────────────────┘
          │
          ▼
ÉTAPE 2 : Validation
     ┌─────────────────────────────────────────────────────────────┐
     │                                                             │
     │  Fournisseur : [ABC SARL        ▼] ✓                       │
     │  N° Facture  : [FAC-2024-001    ] ✓                        │
     │  Date        : [15/01/2024      ] ✓                        │
     │  Total TTC   : [1 200,00 €      ] ⚠ Confiance moyenne      │
     │                                                             │
     │  [Voir le PDF]  [Corriger]  [✓ Valider]                    │
     │                                                             │
     └─────────────────────────────────────────────────────────────┘
          │
          │ Si correction nécessaire
          ▼
ÉTAPE 3 : Correction assistée
     ┌─────────────────────────────────────────────────────────────┐
     │                                                             │
     │  ┌─────────────────────┐  Total TTC incorrect ?            │
     │  │                     │                                    │
     │  │  [PDF affiché]      │  Cliquez sur la bonne valeur      │
     │  │                     │  dans le PDF                       │
     │  │    ↓ clic ici       │                                    │
     │  │  ┌─────────┐        │  → Système apprend la position    │
     │  │  │1 200,00€│        │                                    │
     │  │  └─────────┘        │                                    │
     │  └─────────────────────┘                                    │
     │                                                             │
     └─────────────────────────────────────────────────────────────┘
          │
          │ Après 3 corrections sur ce fournisseur
          ▼
ÉTAPE 4 : Proposition automatique
     ┌─────────────────────────────────────────────────────────────┐
     │                                                             │
     │  💡 Nous avons détecté des corrections récurrentes pour    │
     │     le fournisseur ABC SARL.                               │
     │                                                             │
     │     Voulez-vous créer un masque personnalisé ?             │
     │                                                             │
     │     [Non merci]  [Créer automatiquement]  [Personnaliser]  │
     │                                                             │
     └─────────────────────────────────────────────────────────────┘
Résumé : stratégie de minimisation des masques
Niveau	Déclencheur	Effort utilisateur	Couverture
Auto	Toujours (défaut)	Aucun	~70%
Famille	Format atypique détecté	Choisir parmi 4-5 options	~20%
Généré	Corrections répétées	Valider le masque proposé	~8%
Manuel	Cas très spécifique	Dessiner les zones	~2%
L'objectif : 98% des factures traitées sans jamais dessiner de masque manuellement.

Qu'en pensez-vous ? Voulez-vous que je détaille l'une de ces approches, notamment la détection automatique des 3 zones ou le système d'apprentissage par correction ?

c'est bien

16:29
Parfait ! Nous avons maintenant une architecture solide. Voici un récapitulatif de ce qu'on a défini :

Récapitulatif du projet
Composant	Choix validé
Extraction PDF texte	PyMuPDF
OCR (PDF image)	Tesseract (+ PaddleOCR en option)
IA locale	Ollama + Llama 3 / Mistral
Affichage PDF	PDF.js
Dessin masques	Fabric.js
Différenciation zones	Couleurs + icônes + bordures
Architecture des masques
┌─────────────────────────────────────────────────────┐
│                                                     │
│   AUTO          →  FAMILLE  →  GÉNÉRÉ  →  MANUEL   │
│   (détection)      (4-5)       (apprenti)  (rare)  │
│                                                     │
│   70%              20%         8%          2%      │
│                                                     │
└─────────────────────────────────────────────────────┘
Prochaines étapes possibles
Quand vous serez prêt à développer, on pourra aborder :

Structure des modèles Odoo — les tables et champs à créer
Architecture des fichiers du module — arborescence du code
Composant OWL pour l'éditeur de masques — PDF.js + Fabric.js
Prompts IA optimisés — pour l'extraction et la validation
API entre Odoo et Ollama — communication avec l'IA locale
Dites-moi quand vous voulez passer au développement ou si vous avez d'autres points à clarifier sur la conception !


