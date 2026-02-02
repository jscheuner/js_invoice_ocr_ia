---
stepsCompleted: [1, 2, 3, 4]
session_topic: "Addon Odoo 18 - Saisie automatisée factures fournisseurs"
session_goals: "Explorer les besoins utilisateurs, anticiper les problèmes, définir le périmètre V1"
selected_approach: "ai-recommended"
techniques_used: ["role-playing", "reverse-brainstorming", "what-if-scenarios"]
ideas_generated: 38
workflow_completed: true
---

# Session de Brainstorming - Addon OCR Factures Odoo 18

**Date :** 2026-01-28
**Projet :** Addon Odoo 18 Community - Saisie automatisée factures fournisseurs
**Contexte :** Suisse (multilingue FR/DE/EN)

---

## Résumé Exécutif

Session de brainstorming productive ayant généré **38 idées** organisées en **8 thèmes**. L'addon permettra d'automatiser la saisie des factures fournisseurs via OCR et IA, avec une architecture flexible (Cloud dev / Ollama local prod) et une intégration native Odoo.

**Points clés validés :**
- Architecture simple pour 100-500 factures/mois
- Traitement asynchrone via dossier surveillé
- Support multilingue (FR/DE/EN) et multi-pages
- Masques stockés en base Odoo
- Indices de confiance pour validation intelligente

---

## Techniques Utilisées

| Technique | Focus | Idées |
|-----------|-------|-------|
| Jeu de Rôle | Personas Marie/Patrick/Kevin | 15 |
| Brainstorming Inversé | Risques et blindages | 14 |
| Scénarios "Et Si" | Innovation et cas limites | 9 |
| **Total** | | **38** |

---

## Personas Explorés

### Marie - Comptable (utilisatrice principale)
- 200+ factures/mois, saisie répétitive
- Besoin : rapidité, fiabilité, interface connue (Odoo natif)
- Contrôle : fournisseur + total TTC + compte de charge
- Process hybride : facture papier avec numéro pièce noté

### Patrick - DAF (décideur)
- Préoccupations : fiabilité, coût, sécurité données
- Besoin : KPIs, données internes, ROI démontrable

### Kevin - Admin IT (installateur)
- Préoccupations : stabilité serveur, compatibilité, debug
- Besoin : documentation claire, logs, traitement asynchrone

---

## Inventaire Complet des Idées

### Thème 1 : Expérience Utilisateur (9 idées)

| # | Idée | Description |
|---|------|-------------|
| 1 | Mode rafale multi-PDFs | Déposer 40 PDFs, partir, revenir valider |
| 2 | Validation avec indices de confiance | Jauge vert/orange/rouge par champ |
| 3 | Compte de charge suggéré | Basé sur historique fournisseur |
| 4 | Intégration native Odoo | Pas de nouvelle UI, formulaire standard |
| 5 | Mémoire des corrections | Le système apprend des corrections manuelles |
| 15 | Notifications temps réel | "12 factures prêtes à valider" |
| 22 | Numéro pièce pour document physique | Lien papier ↔ digital |
| 23 | Affichage numéro pièce visible | Facilite notation sur papier |
| 25 | Statut visible par facture | En attente → En cours → Traité/Erreur |

### Thème 2 : Architecture & Performance (7 idées)

| # | Idée | Description |
|---|------|-------------|
| 12 | Queue asynchrone | Traitement en tâche de fond |
| 14 | Intégration OCA queue_job | Module éprouvé de l'écosystème |
| 16 | Dossier surveillé (Watch Folder) | `/factures_a_traiter/` scanné régulièrement |
| 17 | Traitement heures creuses | Option 20h-6h pour gros volumes |
| 27 | Arborescence dossiers | `a_traiter/`, `traite_ok/`, `erreur/`, `non_pdf/` |
| 28 | Déplacement auto horodaté | `traite_ok/2024-01/facture.pdf` |
| 30 | Architecture MVP | 100-500 factures/mois, 1 serveur |

### Thème 3 : Configuration IA (3 idées)

| # | Idée | Description |
|---|------|-------------|
| 7 | Architecture hybride | Cloud (dev) / Ollama local (prod) |
| 8 | Mode données internes | 100% local, zéro données sortantes |
| 9 | Config Ollama minimaliste | URL + bouton Test + dropdown modèle |

### Thème 4 : Fiabilité & Garde-fous (5 idées)

| # | Idée | Description |
|---|------|-------------|
| 6 | Plus fiable que l'humain | IA 2% erreurs signalées vs humain 5% silencieuses |
| 18 | Détection doublons | Géré par Odoo natif |
| 19 | Alertes admin email | PDF corrompu ou non-PDF → notification |
| 20 | Seuils alerte montant | >5000 CHF → champ rouge |
| 21 | Limites vraisemblance | TVA 0-25%, date pas future, etc. |

### Thème 5 : Masques & Apprentissage (2 idées)

| # | Idée | Description |
|---|------|-------------|
| 26/29 | Masques en base Odoo | Table `ocr.mask`, migration-proof |
| 38 | Profil auto-apprenant | Enrichissement après chaque validation |

### Thème 6 : Support Suisse Multilingue (4 idées)

| # | Idée | Description |
|---|------|-------------|
| 31 | Support multi-pages | Fusion lignes pages 2-3, total page 4 |
| 32 | Détection langue auto | FR/DE/EN détecté automatiquement |
| 33 | Vocabulaire multilingue | TVA/MwSt/VAT → même champ |
| 34 | Notes de crédit hors scope | Détection + message "saisie manuelle" |

### Thème 7 : Administration (4 idées)

| # | Idée | Description |
|---|------|-------------|
| 10 | Dashboard KPIs DAF | Factures traitées, taux reconnaissance, temps moyen |
| 11 | Documentation technique | README clair, prérequis, premiers pas |
| 13 | Mode debug | Logs chaque étape, case à cocher |
| 24 | Droits Odoo natifs | Utilisateur / Manager / Admin OCR |

### Thème 8 : Roadmap V2 (4 idées)

| # | Idée | Description |
|---|------|-------------|
| 35 | Ingestion email | Boîte mail dédiée → extraction PJ |
| 36 | Matching facture ↔ PO | Lien automatique avec bon de commande |
| 37 | Alerte écart PO/facture | Détection surfacturation |

---

## Priorisation V1

### Must Have (indispensable)

| # | Idée | Justification |
|---|------|---------------|
| 4 | Intégration native Odoo | Adoption utilisateur |
| 12 | Queue asynchrone | Stabilité serveur |
| 16 | Dossier surveillé | Découplage réception/traitement |
| 27 | Arborescence dossiers | Gestion fichiers propre |
| 9 | Config Ollama minimaliste | Flexibilité client |
| 2 | Validation indices confiance | UX différenciante |
| 32 | Détection langue | Contexte suisse |
| 31 | Support multi-pages | Cas réel fréquent |
| 29 | Masques en base Odoo | Persistance données |
| 24 | Droits accès Odoo | Sécurité |

### Should Have (améliore l'expérience)

| # | Idée |
|---|------|
| 1 | Mode rafale |
| 3 | Compte de charge suggéré |
| 5 | Mémoire des corrections |
| 15 | Notifications temps réel |
| 20 | Seuils alerte montant |
| 21 | Limites vraisemblance |
| 25 | Statut par facture |
| 19 | Alertes admin email |
| 33 | Vocabulaire multilingue |

### Nice to Have (si temps permet)

| # | Idée |
|---|------|
| 10 | Dashboard DAF |
| 13 | Mode debug |
| 17 | Traitement heures creuses |
| 38 | Profil auto-apprenant |

### V2 (reporté)

- Thème 8 complet (email, matching PO, alertes écart)

---

## Stack Technique Validée

| Composant | Choix |
|-----------|-------|
| Extraction PDF texte | PyMuPDF |
| OCR (PDF image) | Tesseract |
| IA (dev) | OpenAI / Claude API |
| IA (prod) | Ollama local (Llama 3 / Mistral) |
| Affichage PDF | PDF.js |
| Dessin masques | Fabric.js |
| Queue jobs | OCA queue_job |
| Framework | Odoo 18 Community + OWL |

---

## Architecture Masques (rappel doc initiale)

4 niveaux progressifs :
1. **Auto** (70%) — Détection structure automatique
2. **Famille** (20%) — 4-5 templates de layout
3. **Généré** (8%) — Créé par apprentissage corrections
4. **Manuel** (2%) — Dessin zones Fabric.js (rare)

---

## Prochaines Étapes

1. **Créer le Product Brief** — Formaliser la vision produit
2. **Rédiger le PRD** — Spécifications détaillées V1
3. **Concevoir l'Architecture** — Modèles Odoo, API, composants
4. **Développer le MVP** — Must Have uniquement
5. **Tester** — Avec vraies factures suisses FR/DE

---

## Notes de Session

**Points forts de la session :**
- Vision pragmatique : rester dans l'écosystème Odoo
- Scope maîtrisé : 100-500 factures/mois
- Contexte suisse bien intégré (multilingue, papier)
- Séparation claire V1/V2

**Décisions clés :**
- Pas de nouvelle UI, intégration native Odoo
- Traitement asynchrone obligatoire
- Données peuvent rester 100% locales
- Notes de crédit = hors scope V1
