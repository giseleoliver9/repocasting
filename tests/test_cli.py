import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "examples/dashboard/specialists.toml"


def run(*args, cwd=None, answer=None):
    return subprocess.run([sys.executable, "-m", "repocasting", *args],
                          capture_output=True, text=True, input=answer, cwd=cwd or ROOT, check=False,
                          env={**os.environ, "PYTHONPATH": str(ROOT / "src")})


def roles(result):
    return [step["role"] for step in result["handoffs"]]


class CliTests(unittest.TestCase):
    def test_demo_order_and_confirmation(self):
        result = run("demo", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        sort, blocked, allowed = json.loads(result.stdout)
        self.assertEqual(roles(sort), ["Dev", "QA"])
        self.assertEqual(blocked["question"], "Quem pode exportar?")
        self.assertEqual(roles(blocked), [])
        self.assertEqual(roles(allowed), ["Security", "Dev", "QA"])
        self.assertTrue(all(x["agents_executed"] == x["files_written"] == 0 for x in [sort, blocked, allowed]))

    def test_unknown_answer_still_blocks_and_preserves_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "painel.txt"
            marker.write_bytes(b"original")
            result = run("demo", "--scenario", "export", "--answer", "todo mundo", "--json", cwd=folder)
            self.assertEqual(result.returncode, 0, result.stderr)
            record, = json.loads(result.stdout)
            self.assertEqual(roles(record), [])
            self.assertEqual(record["question"], "Quem pode exportar?")
            self.assertEqual(sorted(Path(folder).iterdir()), [marker])
            self.assertEqual(marker.read_bytes(), b"original")

    def test_direct_export_without_permission_decision(self):
        result = run("demo", "--scenario", "export", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        record, = json.loads(result.stdout)
        self.assertEqual(record["question"], "Quem pode exportar?")
        self.assertEqual(roles(record), [])

    def test_interactive_admin_answer(self):
        result = run("demo", "--scenario", "export", "--interactive", answer="só admins\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Quem pode exportar?", result.stdout)
        self.assertIn("Security → Dev → QA", result.stdout)
        self.assertIn("SIMULAÇÃO", result.stdout)

    def test_route_score_accent_and_repetition(self):
        result = run("route", "ORDENAÇÃO ordenação", "--config", str(CONFIG), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record["recommended"], "dev")
        self.assertEqual(record["candidates"][0]["score"], 5)
        self.assertFalse(record["executed"])

    def test_route_abstains_on_ties_and_substrings(self):
        for task, expected in [("implementação", "sem-sinal"),
                               ("ordenar acesso regressão", "empate")]:
            result = run("route", task, "--config", str(CONFIG), "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(result.stdout)
            self.assertEqual(record["status"], expected)
            self.assertIsNone(record["recommended"])

    def test_invalid_config_returns_clear_error(self):
        result = run("route", "teste", "--config", "does-not-exist.toml")
        self.assertEqual(result.returncode, 2)
        self.assertIn("repocasting:", result.stderr)

    def test_demo_and_arbitrary_plan_share_policy(self):
        demo = json.loads(run("demo", "--json").stdout)
        requests = [
            ("Corrigir a ordenação numérica da tabela de entregas.", ""),
            ("Exportar em CSV a tabela de entregas.", ""),
            ("Exportar em CSV a tabela de entregas.", "só admins"),
        ]
        for record, (task, answer) in zip(demo, requests, strict=True):
            del record["scenario"]
            actual = run("plan", task, "--answer", answer, "--json")
            self.assertEqual(actual.returncode, 0, actual.stderr)
            self.assertEqual(json.loads(actual.stdout), record)

    def test_direct_plan_handles_novel_tasks_and_permissions(self):
        cases = [
            ("Ajustar ordem no calendário", [], ["Dev", "QA"]),
            ("Validar acesso à área de entregas", [], ["Security", "Dev", "QA"]),
            ("Exportar um extrato em CSV apenas admins", [], ["Security", "Dev", "QA"]),
            ("Exportar um CSV", [], []),
            ("Exportar um CSV, não só admins", [], []),
            ("Exportar um CSV só admins", ["--answer", "todo mundo"], []),
            ("Conversa sobre um filme", [], []),
        ]
        for task, args, expected in cases:
            actual = run("plan", task, *args, "--json")
            self.assertEqual(actual.returncode, 0, actual.stderr)
            result = json.loads(actual.stdout)
            self.assertEqual(roles(result), expected)
            self.assertEqual((result["agents_executed"], result["files_written"]), (0, 0))
