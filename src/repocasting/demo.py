"""Example inputs for the same planner used by arbitrary CLI requests."""

from .workflow import plan

TASKS = {
    "sort": "Corrigir a ordenação numérica da tabela de entregas.",
    "export": "Exportar em CSV a tabela de entregas.",
}


def simulate(scenario: str, answer: str = "") -> dict:
    return {"scenario": scenario, **plan(TASKS[scenario], answer)}


def render(result: dict) -> None:
    print("SIMULAÇÃO | Nenhum agente foi executado e nenhum arquivo foi alterado.")
    print(f"Tarefa: {result['task']}")
    if result["question"]:
        print("Aguardando decisão. Nenhum especialista foi acionado.")
        print(result["question"])
        return
    if result["permission"]:
        print("Regra informada: só administradores podem exportar.")
    print(f"Motivo: {result['reason']}")
    if not result["handoffs"]:
        return
    print("Ordem proposta:", " → ".join(step["role"] for step in result["handoffs"]))
    for step in result["handoffs"]:
        print(f"  {step['role']} [sugestão]: {step['suggestion']}")
