from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .demo import render, simulate
from .router import load_profiles, route
from .workflow import plan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="repocasting", description="Recomenda especialistas sem executar agentes.")
    commands = parser.add_subparsers(dest="command", required=True)
    routing = commands.add_parser("route", help="Explica para quem a tarefa seria encaminhada.")
    routing.add_argument("task", help="Descrição da tarefa, entre aspas.")
    routing.add_argument("--config", type=Path, required=True, help="Caminho para os perfis TOML.")
    routing.add_argument("--json", action="store_true", help="Exibe uma resposta JSON.")
    demo = commands.add_parser("demo", help="Mostra a simulação do painel fictício.")
    demo.add_argument("--scenario", choices=("all", "sort", "export"), default="all")
    demo.add_argument("--answer", help="Resposta à pergunta de exportação, por exemplo: só admins.")
    demo.add_argument("--interactive", action="store_true", help="Pergunta quem pode exportar no terminal.")
    demo.add_argument("--json", action="store_true", help="Exibe resultados em JSON, sem interação.")
    planning = commands.add_parser("plan", help="Planeja uma equipe para uma tarefa.")
    planning.add_argument("task", help="Descrição da tarefa, entre aspas.")
    planning.add_argument("--answer", default="", help="Regra de exportação, por exemplo: só admins.")
    planning.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "plan":
        try:
            if len(args.task) > 8_000 or len(args.answer) > 100:
                raise ValueError("limite: 8.000 caracteres para a tarefa e 100 para a resposta")
            result = plan(args.task, args.answer)
        except ValueError as exc:
            print(f"repocasting: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            render(result)
        return 0
    if args.command == "demo":
        if args.interactive and args.json:
            parser.error("--interactive não é compatível com --json")
        results = []
        if args.scenario in {"all", "sort"}:
            results.append(simulate("sort"))
        if args.scenario in {"all", "export"}:
            answer = args.answer
            if answer is None:
                initial = simulate("export")
                results.append(initial)
                if args.interactive:
                    for result in results:
                        render(result)
                        print()
                    results.clear()
                    try:
                        answer = input("> ")
                    except EOFError:
                        answer = None
            if answer is not None:
                results.append(simulate("export", answer))
            elif args.scenario == "all" and not args.interactive:
                results.append(simulate("export", "só admins"))
        if args.json:
            print(json.dumps(results, ensure_ascii=True, indent=2))
        else:
            for result in results:
                render(result)
                print()
        return 0
    try:
        if len(args.task) > 8_000:
            raise ValueError("limite de 8.000 caracteres por tarefa")
        result = route(args.task, load_profiles(args.config))
    except (OSError, ValueError) as exc:
        print(f"repocasting: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    print("SIMULAÇÃO DE ROTEAMENTO | Nenhum agente foi executado.")
    if result["status"] == "sem-sinal":
        print("Sem evidência suficiente. Descreva melhor a tarefa.")
    elif result["status"] == "empate":
        print("Empate no maior escore. Selecione o especialista manualmente.")
    else:
        print(f"Recomendação: {result['recommended']}")
    for item in result["candidates"]:
        reasons = ", ".join(f"{m['keyword']} (+{m['weight']})" for m in item["matches"])
        print(f"- {item['name']} [{item['id']}] — {item['score']} pontos: {reasons}")
    if result["recommended"] is not None:
        print(f"Instrução sugerida: {result['candidates'][0]['instruction']}")
    return 0
