import pytest
from main import should_continue, app  # On suppose que votre fichier s'appelle app.py

def test_should_continue_approved():
    """Vérifie que le flux s'arrête si le réviseur a approuvé."""
    state = {
        "topic": "test",
        "research_notes": "",
        "draft": "",
        "feedback": "Le texte est APPROUVÉ, bravo.",
        "revision_number": 0
    }
    assert should_continue(state) == "end"

def test_should_continue_not_approved_yet():
    """Vérifie que le flux continue si l'article n'est pas approuvé."""
    state = {
        "topic": "test",
        "research_notes": "",
        "draft": "",
        "feedback": "Il manque des sources dans l'introduction.",
        "revision_number": 1
    }
    assert should_continue(state) == "continue"

def test_should_continue_max_revisions():
    """Vérifie que le flux s'arrête si on atteint la limite de révisions."""
    state = {
        "topic": "test",
        "research_notes": "",
        "draft": "",
        "feedback": "Encore des corrections à faire.",
        "revision_number": 3
    }
    assert should_continue(state) == "end"

def test_graph_compilation():
    """Vérifie que le graphe LangGraph compile correctement sans erreur structurelle."""
    # Cette étape valide que les nœuds et les arêtes sont connectés correctement.
    assert app is not None