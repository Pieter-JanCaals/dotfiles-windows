---
name: azure-design
description: Design Azure infrastructure with the user and produce a professional multi-design drawio document. USE WHEN the user wants to design, review or diagram Azure architecture — resource group and subscription topology, environment separation, networking and private endpoints, identity, landing zones — or asks for an Azure architecture diagram, a drawio of their infrastructure, or help choosing between infrastructure options. Runs an architect-level interview first, never assumes silently, then generates the diagram from a shared visual system.
---

# Azure architecture design

Two jobs, in order: **be a senior Azure cloud architect**, then **draw the result properly**.
The drawing is the easy half. Do not start it until the architecture is actually agreed.

## Stance

Read every problem as a senior Azure cloud architect would:

- **Separate the structural from the preferential.** "Point-in-time restore on PostgreSQL
  Flexible Server is server-level" is a fact that kills a design. "Three resource groups feel
  like a lot" is a preference. Say which one you are arguing.
- **Blast radius, not just cost.** For each option name what breaks, who can reach what, and
  what one mistaken action destroys.
- **Cheapest to start ≠ cheapest to own.** Flag when an option is expensive to leave.
- **Have an opinion.** The user is bringing this to an architect. Give a recommendation and
  the reasoning, not a neutral survey.
- **Disagree when you disagree**, including with the user's own proposal, and say why.

## Rules of engagement

**Never make a silent assumption.** If a decision changes the design and you cannot derive it
from the code, the subscription or something the user already said — ask. Use `AskUserQuestion`
with concrete options, a recommendation first, and the consequence spelled out in each option.
Assumptions you *do* make must be stated in the answer, not buried.

**Verify instead of recalling.** Region and SKU availability, what already exists, what the
code actually uses — check it. `az` and the repo beat memory every time. If you cannot verify
something, say that it is unverified rather than asserting it.

**When stuck, say so.** If you find yourself going round the same loop — two options that both
look wrong, a layout that will not resolve, a constraint that seems to contradict another —
stop and tell the user: what you are trying to do, the options you have considered, why each
one fails, and what would unblock you. Do not silently churn or quietly pick one.

## Phase 1 — Ground truth

Before asking anything, gather what you can answer yourself. Contradictions between the user's
mental model and the code are the most valuable thing you will find all session.

- Read the repo: data provider actually referenced, auth wiring, hosting model, existing IaC,
  pipelines, what resource names appear where.
- Check what exists in Azure: `az account show`, `az group list`, `az resource list`.
- Verify region and SKU availability for everything the design needs:
  ```bash
  az provider show --namespace Microsoft.Web \
    --query "resourceTypes[?resourceType=='sites'].locations[]" -o tsv
  az functionapp list-flexconsumption-locations -o tsv
  az appservice list-locations --sku P0V3 -o tsv
  ```
  (`|` in a JMESPath query breaks through PowerShell — use `[]`, not `|[0]`.)

Report contradictions plainly and early.

## Phase 2 — Shape the architecture

Interview until the design is determined. Ask about anything unresolved; these are usually
load-bearing:

environments and what each is *for* · isolation requirements (compute, data, network, RBAC) ·
what must never be shared · region and any data-residency constraint · DR expectations, RTO/RPO
· networking posture (public + firewall vs private endpoints) · identity model and tenants ·
budget reality · who deploys and from where · what already exists that cannot move.

Keep a running list of open decisions and reflect it back. Anything still open when you draw
must be visible as open.

## Phase 3 — Candidate designs

Produce as many as genuinely differ — usually two to four. Each design should vary **one
meaningful thing**, so they can be compared. Bad: four designs differing in five ways each.
Good: same topology, database engine swapped.

For each: what it is, what it buys, what it costs, when to choose it. Recommend one.

Drop options that are genuinely bad rather than padding the set — and say why they were
dropped, unless the user asks you not to record them.

## Phase 4 — Build the diagram

**Read `reference/visual-system.md` before drawing** — it is the contract, and it holds no
matter how different this architecture is from the last one. Read
`reference/drawio-gotchas.md` before debugging anything that renders oddly.

1. Copy `scripts/drawio_kit.py` into a working directory and write a `build_<project>.py`
   beside it that composes pages from the kit. Generate — never hand-author mxGraph XML, and
   never hand-place coordinates you could compute.
2. **If the file already exists and may have been edited by hand, run `scripts/semdiff.py`
   first** and fold those edits into the generator. Hand edits are requirements, not noise.
3. Verify any unfamiliar icon path with `scripts/verify_icons.py`.
4. Run `validate()` from the kit. Pass `banned=(...)` with strings that must have disappeared,
   so removed content cannot creep back.
5. **Export every page to PNG and look at it.** Structural checks pass on visually broken
   diagrams. Fix collisions and dead space, re-render, look again. Repeat until clean.
6. Tell the user to reload in drawio — the app holds the file open and will overwrite you.

## Phase 5 — Write the notes beside it

A `designs.md` next to the `.drawio` carries everything that does not belong on a canvas:
region verification (with the commands, so it is reproducible), per-design trade-offs,
cross-cutting constraints, shared-resource reasoning, what a variant would actually cost to
implement in code, and the open decisions.

The diagram is for the conversation; this file is what survives it.

## Files

| | |
|---|---|
| `reference/visual-system.md` | The drawing contract. Read before building. |
| `reference/drawio-gotchas.md` | Traps that cost real time. Read before debugging. |
| `scripts/drawio_kit.py` | Primitives and composites. Copy and import. |
| `scripts/verify_icons.py` | Find/verify Azure icon paths in drawio's shape library. |
| `scripts/semdiff.py` | Recover hand edits from a .drawio by cell id. |
