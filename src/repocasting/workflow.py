"""Deterministic team planning; never executes a proposed step."""

from .router import words

SUGGESTIONS = {
    "Security": "Definir quem tem acesso e como verificar a autorização no backend.",
    "Dev": "Propor a menor alteração para o comportamento descrito.",
    "QA": "Propor casos de teste e checar o resultado esperado com dados fictícios.",
}
EXPORT = {"exportar", "exportacao", "export", "csv"}
RESTRICTED = {"permissao", "permissoes", "acesso", "autorizacao", "autenticacao", "privado"}
KNOWN = {"corrigir", "ordenar", "ordenacao", "implementar", "adicionar", "ajustar", "teste", "validar", "regressao"}


def plan(task: str, answer: str = "") -> dict:
    signals = set(words(task))
    if not signals:
        raise ValueError("informe uma tarefa com pelo menos uma palavra")
    export = bool(signals & EXPORT)
    restricted = bool(signals & RESTRICTED)
    admin_answers = {"so admins", "somente admins", "apenas admins", "somente administradores", "apenas administradores"}
    confirmed = " ".join(words(answer)) in admin_answers
    if not answer.strip():
        confirmed = any(phrase in f" {' '.join(words(task))} " for phrase in (" so admins ", " apenas admins ", " somente administradores ", " apenas administradores ")) and not signals.intersection({"nao", "exceto"})
    waiting = export and not confirmed
    team = [] if waiting else (
        ["Security", "Dev", "QA"] if export or restricted else
        ["Dev", "QA"] if signals & KNOWN else []
    )
    return {
        "mode": "simulacao-de-roteamento",
        "task": task,
        "status": "aguardando-decisao" if waiting else "recomendado" if team else "sem-sinal",
        "question": "Quem pode exportar?" if waiting else None,
        "permission": "somente-administradores" if export and confirmed else None,
        "reason": "Exportação exige regra de acesso." if export else
                  "A tarefa menciona controle de acesso." if restricted else
                  "Não identifiquei sinais de acesso ou exportação." if team else
                  "Não identifiquei um tipo de tarefa nas regras deste MVP.",
        "handoffs": [{"role": role, "suggestion": SUGGESTIONS[role]} for role in team],
        "agents_executed": 0,
        "files_written": 0,
    }
