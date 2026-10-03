---
name: antigravity-dev
description: >-
  Acelera o ciclo de desenvolvimento de software aplicando os padrões e princípios do Antigravity
  e Agentic Coding: Spec-First, TDD, decomposição atômica, arquitetura limpa e verificação autônoma.
  Ative ao implementar novas features, refatorar código, planejar arquitetura, diagnosticar bugs
  complexos ou gerar testes automatizados.
---

# Antigravity Dev Accelerator

Guia operacional para conduzir desenvolvimento de software orientado a agentes no Antigravity, maximizando autonomia, precisão arquitetural, robustez de testes e prevenção de regressões.

---

## 🎯 Quando Ativar Esta Skill

Ative ou invoque esta skill (`/antigravity-dev`) quando o objetivo envolver:

- **Novas Funcionalidades (Features)**: Planejamento, design de contratos e implementação ponta a ponta.
- **Refatoração & Arquitetura**: Modernização de código, desacoplamento (Clean Architecture, SOLID) e otimização de I/O / concorrência.
- **Engenharia Reversa & Diagnóstico de Bugs**: Investigação sistemática de causa-raiz, análise sintomática e reprodução via testes.
- **Qualidade & Testes (TDD/Contract-First)**: Criação de suítes de testes unitários, de integração e validação de contratos OpenAPI/DTOs.

> [!TIP]
> **Quando NÃO usar:** Para dúvidas conceituais rápidas, correções triviais de uma linha (typos) ou leitura direta de arquivos sem modificação estrutural.

---

## 🧠 Princípios Fundamentais do Agentic Coding

1. **Investigação Antes da Modificação (Spec-First)**: Nunca assuma o comportamento de um código sem antes inspecionar seus arquivos, dependências e interfaces.
2. **Decomposição em Blocos Atômicos**: Divida demandas grandes em tarefas isoladas e verificáveis. Cada passo deve deixar a aplicação em estado funcional.
3. **Validação Ativa & Autônoma**: O código só é considerado concluído após validação real via execução de comandos (testes, linters, checagem de tipos).
4. **Isolamento de Escopo (Zero Scope Creep)**: Altere única e exclusivamente o necessário para a demanda. Preserve comentários, estilos e contratos não relacionados.
5. **Autocorreção em Loop**: Se um teste ou comando falhar, capture o traceback, analise a causa fundamental e corrija sem adivinhações.

---

## 🔄 Fluxo de Execução em 5 Fases

```mermaid
flowchart LR
    A["1. Spec & Contexto"] --> B["2. Plano Atômico"]
    B --> C["3. Contratos & TDD"]
    C --> D["4. Implementação"]
    D --> E["5. Verificação Real"]
    E -- "Falha no teste" --> D
    E -- "Sucesso" --> F["Concluído"]
```

### Fase 1: Reconhecimento & Especificação (Spec-First)
- **Mapeamento de Impacto**: Identifique contratos de API, schemas (Pydantic/DTOs), endpoints e serviços afetados.
- **Checagem de Restrições**: Verifique versões de bibliotecas, configurações de ambiente (`.env`, settings), arquitetura existente e compatibilidade de SO (Windows/Linux).
- **Inspeção de Contratos**: Se a demanda envolver APIs (ex: FastAPI/Django), garanta que os schemas de entrada/saída estejam estritamente tipados.

### Fase 2: Decomposição & Plano Atômico
- Crie um plano passo a passo ordenado logicamente:
  1. Contratos, Schemas e Modelos de Dados
  2. Suíte de Testes (Casos felizes + Casos de borda)
  3. Camada de Serviço e Regra de Negócio
  4. Integração (Rotas, Controladores, Middlewares)
- Para tarefas complexas ou arquiteturais, utilize artefatos estruturados para registrar o plano e alinhá-lo antes da execução.

### Fase 3: Contratos & Testes (TDD / Contract-First)
- **Crie ou adapte os testes primeiro**:
  - Para novas features: garanta que os testes cubram os critérios de aceitação.
  - Para correção de bugs: escreva um teste que reproduza a falha antes de consertá-la.
- Garanta testes unitários e de integração mockando serviços externos ou I/O pesado (ex: subprocessos, banco, Redis, APIs externas).

### Fase 4: Implementação Limpa & Modular
- **Padrões de Código**:
  - Aplique Princípio da Responsabilidade Única (SRP) e baixo acoplamento.
  - Tipagem estrita e type hints em todas as funções/métodos.
  - Tratamento defensivo de exceções e logs sem expor credenciais ou dados sensíveis.
- **Edições Cirúrgicas**: Faça alterações limpas e contíguas, evitando reformatar trechos irrelevantes do arquivo.

### Fase 5: Verificação Autônoma & Conclusão
- **Execução Real**: Execute no terminal os comandos de validação do projeto (ex: `pytest`, `mypy`, `ruff`, `python -m unittest`).
- **Loop de Correção**: Se houver falha, inspecione a saída do comando, faça o ajuste fino e reexecute até obter 100% de aprovação.
- **Sincronização de Docs**: Atualize documentações (ex: `documentacao.md`, docstrings, contratos OpenAPI) caso novos endpoints ou comandos tenham sido introduzidos.

---

## ⚠️ Checklist Anti-Falhas (Gotchas)

- [ ] **Não adivinhe erros:** Sempre execute o teste ou linter para ver a saída real do terminal.
- [ ] **Atenção ao Windows:** Observe paths com barras invertidas vs normais, subprocessos que exigem `.exe` ou políticas de shell do PowerShell.
- [ ] **Serviços em Background:** Processos de longa duração (ex: servidores Uvicorn, background workers) devem ser gerenciados de forma assíncrona, sem bloquear o terminal.
- [ ] **Preservação de Código:** Nunca sobrescreva arquivos inteiros se apenas uma função ou classe precisa ser ajustada.
