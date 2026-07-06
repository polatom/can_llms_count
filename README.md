# Can LLMs Count?

Research project at ÚFAL evaluating LLM capabilities on counting/agreement phenomena.
See [experiment_01/docs/METHODOLOGY.md](experiment_01/docs/METHODOLOGY.md) for the science;
this README documents repository conventions and workflows.

## Repository layout

```
experiment_XX/          one directory per experiment
├── src/                pipeline code
├── config/             experiment configuration
├── data/               eval sets (raw data & large intermediates are gitignored)
├── results/            run outputs, metrics, error analyses
├── docs/               methodology, implementation notes, results, reports
├── conclusions/        evaluation writeups
└── paper/              local working draft of the paper for this experiment
paper/                  Overleaf project clone — NOT part of this repo (gitignored)
```

## Git conventions

- Canonical repository: **`github.com/ufal/can_llms_count`** (private). A personal
  mirror may exist at `polatom/can_llms_count`; the ufal repo is the source of truth.
- All commits to this project use the **`polatom`** GitHub identity
  (`Tomas Polak <polak.t@gmail.com>`), not any work account. This is enforced with
  repo-local config on a fresh clone:

  ```bash
  git clone git@github.com:ufal/can_llms_count.git
  cd can_llms_count
  git config user.name "Tomas Polak"
  git config user.email "polak.t@gmail.com"
  # pin the ssh key that maps to the polatom account:
  git config core.sshCommand "ssh -i ~/.ssh/id_rsa_polatom -o IdentitiesOnly=yes"
  ```

## Paper workflow (Overleaf ↔ git)

The **canonical paper lives in Overleaf**
(project `6a284a16d7d23bcc2719516f`), where supervisor and colleagues edit via the
Overleaf UI. Locally it is cloned at `./paper/` through Overleaf's git bridge and
deliberately kept out of this repository (see `.gitignore`) so the two histories
never mix. Do not add it as a submodule — Overleaf git tokens are per-user.

Per-experiment flow:

1. Each experiment develops a **local working draft** in `experiment_XX/paper/`,
   committed to this repo like any other artifact. It may freely diverge from the
   canonical paper while results are still moving.
2. When ready to share: `git -C paper pull` to pick up colleagues' Overleaf edits,
   incorporate the experiment's content into the canonical sources, then
   `git -C paper push`.
3. New experiments start their working draft **from the current canonical paper**,
   not from a previous experiment's draft. (`experiment_01/paper/` predates this
   convention and was never merged; `experiment_02` onwards should follow it.)

Overleaf git bridge rules: single branch, no force-push, and every UI edit by a
colleague becomes a commit — **always pull before pushing**.

### One-time setup on a new machine

1. Create a git authentication token in Overleaf → Account Settings →
   [Git integration tokens](https://www.overleaf.com/learn/how-to/Git_integration_authentication_tokens)
   (tokens expire after 1 year).
2. Put it in `.env` (see below) and clone:
   ```bash
   git clone https://git.overleaf.com/<OVERLEAF_PROJECT_ID> paper
   # username: git, password: the token — or store it in a credential helper,
   # e.g. ~/.overleaf-git-credentials with `store --file=...` (chmod 600)
   ```

## Environment (`.env`, gitignored — never commit)

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER`, `<PROVIDER>_ENDPOINT/_MODEL/_APIKEY` | LLM API access for experiment runs |
| `OVERLEAF_GIT_TOKEN` | Overleaf git bridge auth (yearly expiry) |
| `OVERLEAF_PROJECT_ID` | Overleaf project id of the paper |
