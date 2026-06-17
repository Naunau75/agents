import os
from typing import TypedDict
from langchain_mistralai import ChatMistralAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

# --- CONFIGURATION DE L'API ---
# Remplace par ta vraie clé API Mistral ou configure la variable d'environnement avant de lancer
os.environ["MISTRAL_API_KEY"] = "TA_CLE_API_MISTRAL_ICI"

# Initialisation du modèle Mistral (mistral-large ou mistral-small selon tes crédits)
llm = ChatMistralAI(model="mistral-large-latest", temperature=0.3)

# Outil de recherche gratuit
search_tool = DuckDuckGoSearchRun()

# --- 1. DÉFINITION DE L'ÉTAT (STATE) ---
class AgentState(TypedDict):
    topic: str              # Le sujet donné par l'utilisateur
    research_notes: str     # Les notes générées par le chercheur
    draft: str              # Le brouillon d'article rédigé
    feedback: str           # Les critiques du réviseur
    revision_number: int    # Compteur de révisions pour éviter les boucles infinies


# --- 2. DÉFINITION DES NŒUDS (AGENTS) ---

def researcher_node(state: AgentState):
    """Cherche des informations sur le web et les résume."""
    print("\n🕵️‍♂️ [Chercheur] Je lance mes recherches sur le web...")
    topic = state["topic"]
    
    # Exécution de la recherche sur le web
    raw_results = search_tool.invoke(topic)
    
    # Demander à Mistral de faire une synthèse des résultats bruts
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Tu es un chercheur expert. Voici des informations brutes issues du web. "
                   "Fais-en une synthèse claire, factuelle et détaillée sous forme de notes (bullet points) "
                   "pour aider un journaliste à rédiger un article."),
        ("user", "Sujet : {topic}\n\nRésultats bruts de recherche : {results}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"topic": topic, "results": raw_results})
    
    print("🕵️‍♂️ [Chercheur] Notes de recherche terminées !")
    return {"research_notes": response.content}


def writer_node(state: AgentState):
    """Rédige l'article en se basant sur les notes et les éventuelles critiques."""
    print("\n✍️ [Rédacteur] Je rédige l'article...")
    
    topic = state["topic"]
    notes = state.get("research_notes", "")
    feedback = state.get("feedback", "")
    
    # Le prompt s'adapte selon s'il y a déjà eu un feedback du réviseur ou non
    system_prompt = "Tu es un journaliste talentueux. Tu écris un article de blog structuré et captivant basé sur les notes de recherche fournies."
    if feedback:
        system_prompt += f"\n\nATTENTION ! Ceci est une révision. Tu dois corriger ton article précédent en prenant en compte ces critiques : {feedback}"

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "Sujet : {topic}\n\nNotes de recherche : {notes}\n\nRédige l'article maintenant au format Markdown.")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"topic": topic, "notes": notes})
    
    print("✍️ [Rédacteur] Brouillon terminé !")
    return {"draft": response.content}


def reviewer_node(state: AgentState):
    """Évalue l'article et décide s'il est validé ou s'il doit être corrigé."""
    print("\n🧐 [Réviseur] Je relis et j'évalue l'article...")
    
    topic = state["topic"]
    draft = state["draft"]
    rev_num = state.get("revision_number", 0)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Tu es un éditeur en chef très exigeant. Relis l'article ci-dessous.\n"
                   "- S'il est excellent, complet, et sans faute, réponds UNIQUEMENT par le mot : APPROUVÉ\n"
                   "- S'il manque des informations, s'il est mal structuré ou trop court, rédige une critique constructive indiquant ce qui doit être changé (Ne dis surtout pas APPROUVÉ dans ce cas)."),
        ("user", "Sujet attendu : {topic}\n\nArticle rédigé : \n{draft}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"topic": topic, "draft": draft})
    feedback = response.content
    
    if "APPROUVÉ" in feedback.upper():
        print("🧐 [Réviseur] ✅ L'article est validé !")
    else:
        print("🧐 [Réviseur] ❌ L'article a besoin de corrections. Retour au rédacteur.")
        
    return {"feedback": feedback, "revision_number": rev_num + 1}


# --- 3. LOGIQUE DE ROUTAGE (ARÊTE CONDITIONNELLE) ---

def should_continue(state: AgentState):
    """Décide de la prochaine étape du flux."""
    # S'il y a le mot 'APPROUVÉ' ou si on a atteint 3 révisions (pour éviter de payer des tokens à l'infini)
    if "APPROUVÉ" in state["feedback"].upper() or state["revision_number"] >= 3:
        return "end"
    return "continue"


# --- 4. CONSTRUCTION DU GRAPHE ---

workflow = StateGraph(AgentState)

# Ajout des nœuds
workflow.add_node("researcher", researcher_node)
workflow.add_node("writer", writer_node)
workflow.add_node("reviewer", reviewer_node)

# Définition du chemin de base
workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "writer")
workflow.add_edge("writer", "reviewer")

# Ajout de la boucle conditionnelle
workflow.add_conditional_edges(
    "reviewer",         # À partir du nœud reviewer...
    should_continue,    # ...on exécute cette fonction...
    {
        "continue": "writer", # ...si "continue", on boucle vers le rédacteur
        "end": END            # ...si "end", on termine le graphe
    }
)

# Compilation du graphe
app = workflow.compile()


# --- 5. EXÉCUTION ---
if __name__ == "__main__":
    print("🚀 Démarrage de la NewsRoom IA")
    
    # On définit l'état de départ
    initial_state = {
        "topic": "Les avancées majeures des batteries solides pour véhicules électriques en 2025",
        "revision_number": 0
    }
    
    # Exécution du graphe (app.stream permet de voir l'avancement étape par étape)
    for output in app.stream(initial_state):
        # Afficher le nœud qui vient de se terminer
        for key, value in output.items():
            print(f"🔄 Étape terminée : {key}")
            print("-" * 20)
            
    # Récupération de l'état final
    final_state = app.invoke(initial_state)
    
    print("\n" + "="*50)
    print("🎉 ARTICLE FINAL :")
    print("="*50 + "\n")
    print(final_state["draft"])