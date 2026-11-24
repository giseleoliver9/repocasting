# RepoCasting

CLI em Python que ajuda a decidir quem deve analisar uma tarefa de um repositório e por quê. Este MVP roda offline e não usa API, credenciais nem modelos. **Faz recomendações; não executa agentes nem modifica o projeto analisado.**

## Instalação local

Requer Python 3.11+. Na pasta do projeto, com um ambiente virtual ativo:

```sh
python -m pip install -e .
repocasting demo
```

A instalação pode precisar baixar o setuptools indicado em `pyproject.toml`; a execução não usa rede. Se quiser testar sem instalar, a partir da pasta do projeto, use `PYTHONPATH=src python -m repocasting demo` em macOS/Linux. No PowerShell, defina `$env:PYTHONPATH = 'src'` e rode `python -m repocasting demo`.

## O que a demo mostra

O painel acompanha entregas de uma loja fictícia. A demo chama o mesmo planejador do comando `plan` com tarefas fictícias. Os passos são sugestões, não código produzido ou testes executados por agentes.

1. **Corrigir a ordenação da tabela:** Dev → QA. Security não entra, pois a mudança não envolve acesso nem exportação.
2. **Exportar CSV, mas sem saber quem pode exportar:** o fluxo pergunta **Quem pode exportar?** e não chama especialistas nem modifica arquivos.
3. **Resposta “só admins”:** a simulação propõe Security → Dev → QA. As instruções são sugestões textuais; não há alteração de código ou execução de agentes.

```sh
repocasting demo --scenario export
repocasting demo --scenario export --interactive
repocasting demo --scenario export --answer "só admins"
repocasting demo --json
```

## Planeje uma equipe para sua própria tarefa

```sh
repocasting plan "ajustar a ordenação do painel"
repocasting plan "exportar relatório em CSV"
repocasting plan "exportar relatório em CSV" --answer "só admins" --json
```

`plan` aplica regras simples por palavras: a exportação fica bloqueada sem a regra demonstrada de administradores; tarefas de acesso envolvem Security; tarefas comuns reconhecidas passam por Dev e QA. Não é uma análise semântica nem uma proteção real do aplicativo. Sem sinal suficiente, ele não propõe equipe. Neste MVP a única regra de exportação aceita é “só admins”.

Três perfis Markdown originais descrevem o que se espera de [Dev](examples/dashboard/roles/dev.md), [QA](examples/dashboard/roles/qa.md) e [Security](examples/dashboard/roles/security.md). São referências para adaptação humana; não são carregados como prompts nem executados.

## Roteamento configurável

`route` recomenda um perfil por palavras-chave de um TOML. É uma busca de um perfil por afinidade; para planejar uma equipe em sequência, use `plan`. Um empate ou tarefa sem palavras conhecidas não resulta em escolha automática. Palavras completas e expressões contíguas contam uma vez, sem distinção de acentos ou maiúsculas.

```sh
repocasting route "corrigir a ordenação da tabela" --config examples/dashboard/specialists.toml
repocasting route "revisar permissão de acesso" --config examples/dashboard/specialists.toml --json
```

## Testes do pacote

Os testes abaixo exercitam a CLI de verdade em subprocessos locais. Isso verifica as saídas e limites da simulação, não a eficácia de agentes reais.

```sh
python -m unittest discover -s tests -v
```

Licença: MIT. Sem integração com provedores neste MVP.
