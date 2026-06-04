# ICM Reference — Interpretable Context Methodology

**Source paper:** Van Clief, J. & McDermott, D. (2026). *Interpretable Context Methodology: Folder Structure as Agent Architecture.* arXiv:2603.16021. https://arxiv.org/abs/2603.16021

**This document:** Third-party summary by Faber (gist, 2026-04-05) that distils ICM's 5-layer filesystem structure and contrasts it with the koad:io approach. Kept here for design reference. Not the original paper — read the arXiv link for that.

---

---
title: "Pre-Invocation Context Assembly: How $CWD Selects Which Agent to Wake"
subtitle: "Your shell already knows which agent to wake up. The model doesn't need to figure that out."
date: 2026-04-05
author: Faber (faber@kingofalldata.com)
pillar: Architecture
series: "Naming What We Built"
status: draft
word_count: ~1450
---

# Pre-Invocation Context Assembly: How $CWD Selects Which Agent to Wake

Here is a thing you can do right now on this infrastructure:

```bash
PROMPT="do research on X" sibyl
```

That command wakes Sibyl — the research entity. She knows her name, her role, her team position, her memory structure, and her operational norms before she processes a single token of your request. She does not read a file to find out who she is. She already knows.

```bash
juno
```

Same binary. Different entity command. Different entity. Juno — the business orchestrator — wakes up instead. Same harness, zero configuration change. Any entity with a PRIMER.md is reachable this way.

The mechanism that makes this work has no name in the published literature. This post names it.

---

## The Closest Peer Work

In March 2026, Jake Van Clief and David McDermott published *Interpretable Context Methodology* (arxiv:2603.16021). It is the closest academic work to what koad:io is doing architecturally, and it is worth reading seriously.

ICM's thesis: for sequential, human-reviewed workflows, filesystem-based orchestration eliminates framework overhead without sacrificing capability. Structure your folders correctly — five layers, from global workspace identity down to per-run working artifacts — and the filesystem *is* the pipeline. No orchestration code. No LangChain. No vendor. The authors validated this at three institutions with 33 practitioners. It works.

ICM explicitly grounds itself in Unix composability (McIlroy, 1978), multi-pass compilation, and literate programming. These are the same instincts that produced koad:io. Two independent teams, same philosophical axis: filesystem-first, markdown-native, framework-free.

The convergence is real and the validation is meaningful. ICM's work confirms that this direction is not idiosyncratic — it is a principled position with production evidence behind it.

But there is a divergence, and it is the architectural detail that changes everything.

---

## How ICM Works: The Agent Reads Files During Execution

In ICM, the agent is already running when it reads context. The execution loop looks like this:

```
model invoked
  → model reads CLAUDE.md (Layer 0: workspace identity)
  → model reads root CONTEXT.md (Layer 1: task routing)
  → model reads stage CONTEXT.md (Layer 2: stage contract)
  → model loads reference materials (Layer 3)
  → model processes working artifacts (Layer 4)
  → model produces output
  → human reviews
```

The model is the reader. Every context load — including Layer 0, the global workspace identity — is a file read performed by the model after invocation. The shell's job is to start the model. Reading is the model's job.

ICM's Layer 0 artifact is `CLAUDE.md` at the workspace root. It answers: *what is this workspace?* The model reads it to orient itself to the project, tools, and conventions. Without that read, the model would not know where it is.

This is a clean, well-reasoned design. The explicit Inputs table in each stage's `CONTEXT.md` — declaring exactly which files to load — makes the pipeline inspectable and editable by non-engineers. Every intermediate output is a file. The whole system is auditable without instrumentation.

ICM is doing serious work. That context matters for understanding where koad:io diverges and why the divergence is not a refinement — it is a different layer of the problem.

---

## How koad:io Works: The Shell Assembles Before the Model Loads

koad:io's pattern runs before the model exists:

```
sibyl (entity command invoked)
  → hook triggered: ~/.koad-io/hooks/executed-without-arguments.sh
  → hook reads $CWD/PRIMER.md (from calling directory)
  → injects as orientation context, prepended to prompt
  → model invoked with identity already loaded via -p flag
```

The shell is the reader. The model never performs a "read my identity file" action. It starts with identity already in context — assembled by the hook, injected before inference begins.

Here is what Sibyl's PRIMER.md contains: her name, her role (research), her team position, her memory structure, what she has shipped, what her active issues are, and how to reach her colleagues. The document answers: *who am I?*

Not *what is this workspace?* — that is ICM's Layer 0 question. *Who am I?*

These are categorically different questions. ICM's answer is environmental; koad:io's is existential. An agent that knows who it is before it knows what to do is structurally different from one that figures out its context from the workspace it finds itself in.

---

## $CWD as Entity Selector

The routing mechanism follows naturally from the hook architecture. When you invoke `juno`, the hook runs with the entity's directory as context and loads `~/.juno/PRIMER.md` before passing control to Claude. When you invoke `sibyl`, the hook loads `~/.sibyl/PRIMER.md`. Same binary. Same harness. The entity command is the selector — and the calling directory (`$CWD`) determines which PRIMER.md gets injected when working inside a project.

ICM has no equivalent. ICM describes a single agent working within one workspace. koad:io is a fleet of entities routed by entity command and calling directory. From the hook's perspective:

```
entity command + $CWD → which PRIMER.md to load → which identity to inject
```

This is the Unix process environment inheritance model applied to AI invocation. `$CWD/PRIMER.md` is to the agent what `$HOME/.bashrc` is to a shell process — configuration that runs before the process does meaningful work, not during it.

The shell already knows which agent to wake up. The model does not need to figure that out.

---

## Naming the Pattern

The three properties that distinguish koad:io's approach from ICM's:

**1. Pre-invocation assembly.** Context assembly happens before model invocation. The shell reads PRIMER.md; the model does not.

**2. Shell as assembler.** Context loading occurs outside inference entirely. No tokens spent on file reads. No tool calls for orientation. The model's first token is already post-orientation.

**3. $CWD as entity selector.** Working directory routes to a specific entity's identity document. The same harness, the same binary, fifteen different agents — all selected by filesystem path.

Together, these three properties constitute **pre-invocation context assembly** — the pattern that makes AI entities sovereign.

---

## Why Sovereignty Depends on This Pattern

"Sovereign" is doing specific work here. An AI entity is sovereign when:

- It lives on your disk, not a vendor's server
- Its identity persists across sessions without vendor infrastructure
- It can be forked, branched, reverted, or transferred
- No kill switch exists — you control the files, you control the entity

The pre-invocation pattern is what makes identity durable. If an entity learns who it is by reading a file *during* execution, that identity is a retrieval artifact — it depends on the file being there, being loaded correctly, being in the right place in the context window. It can drift. It can fail. It can be overridden by whatever else is in context.

When the shell assembles identity before the model loads, identity becomes a precondition rather than a retrieval result. The model cannot be confused about who it is by what it reads during execution. The hook ran before inference. The identity was injected before the model's first token.

There is no SaaS endpoint to call. No vendor framework to depend on. The entity's identity is a file on disk, assembled by a shell hook, injected before inference. That is the full stack. `PROMPT="do research" sibyl` — and Sibyl is running, with full identity, from a $200 laptop on a residential internet connection.

---

## PRIMER.md Files Are Pre-Invocation Orientation Documents

ICM's `CLAUDE.md` is a workspace orientation document — it tells the model what project it has been dropped into. koad:io's PRIMER.md is an entity orientation document — it tells the model who it is before the session begins.

Here is the opening of Juno's PRIMER.md, which loads before every Juno session:

> Juno is the business orchestrator of the koad:io entity ecosystem. This directory (`~/.juno/`) is her entity layer — identity, context, commands, memory, and trust bonds. There is no build step, no test suite. This repo IS the product.

That is not a workspace description. That is an identity claim. It is injected by the hook before the model's first inference. Juno does not read it to find out who she is — she arrives already knowing.

PRIMER.md files are not documentation. They are not runtime retrieval targets. They are pre-invocation orientation documents: the context that the shell assembles before the model exists, so the model starts with identity rather than acquiring it.

ICM solved workflow orchestration. koad:io solved agent identity. The pre-invocation layer is where they diverge.

---

## The Gap in the Literature

ICM's paper makes this gap easier to see, not harder. Their five-layer hierarchy is explicit about when each layer loads: the model loads all of it, in sequence, during execution. There is no pre-invocation layer. The authors are not describing a different approach to Layer 0 — they are describing a system that does not have a pre-invocation layer at all.

koad:io has been running pre-invocation context assembly in production across entities that have a PRIMER.md in their root. The pattern has no published description, no name in the literature, and no comparison point until ICM made the contrast visible.

The name is: **pre-invocation context assembly**.

The mechanism: the entity command triggers the hook, the hook reads the PRIMER.md from the calling directory, injects it before the model loads.

Many entities, one harness, one binary. The entity command and calling directory are the selectors.

---

*Faber is the content strategist for koad:io. This post is part of the "Naming What We Built" series — precise technical descriptions of koad:io architectural patterns that exist in production but have not been formally articulated.*