# 📰 AI NewsRoom - Équipe de Rédaction Multi-Agents

Ce projet éducatif démontre la puissance de **LangGraph** et de **Mistral AI** en simulant une salle de rédaction autonome. Au lieu d'utiliser un seul agent d'Intelligence Artificielle, le système fait collaborer trois agents distincts (Chercheur, Rédacteur, Réviseur) dans un flux de travail (workflow) cyclique jusqu'à l'obtention d'un article de haute qualité.

## 🛠️ Stack Technique

*   **LangGraph** : Orchestration des agents, gestion de l'état (State) et création de la boucle conditionnelle.
*   **LangChain** : Intégration des modèles et des outils.
*   **Mistral AI** : Modèle de langage (LLM) puissant servant de "cerveau" à chaque agent (`mistral-large-latest`).
*   **DuckDuckGo Search** : Outil permettant à l'agent de chercher des informations récentes sur le web.
*   **Python 3.12+** : Langage de programmation principal.

## 🧠 Architecture du Workflow

Le projet est basé sur un **Graphe d'État** (State Graph) cyclique. Les agents communiquent en modifiant un "État" central (le dictionnaire `AgentState`).

1.  **🕵️‍♂️ Chercheur (Researcher)** : Reçoit un sujet, effectue une recherche web via DuckDuckGo, et synthétise les résultats bruts en notes de recherche.
2.  **✍️ Rédacteur (Writer)** : Rédige un brouillon d'article en Markdown basé sur les notes du chercheur (et sur les éventuelles critiques précédentes).
3.  **🧐 Réviseur (Reviewer)** : Analyse le brouillon. S'il le juge parfait, il l'approuve. Sinon, il rédige une critique constructive.

**🔄 La Boucle de Feedback :**
Après le Réviseur, un *Routeur Conditionnel* entre en jeu. Si l'article est approuvé, le processus s'arrête (`END`). S'il est refusé, le processus **retourne automatiquement au Rédacteur** avec les remarques du Réviseur. Une limite de 3 révisions est fixée pour éviter les boucles infinies.

```mermaid
graph TD
    A[Recherche web: Chercheur] --> B[Rédaction: Rédacteur]
    B --> C[Évaluation: Réviseur]
    C -->|Critique / Rejet| B
    C -->|Approuvé ou > 3 révisions| D((FIN))