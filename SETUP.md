# Setup checklist

This package is a complete repository layout. Nothing in it has touched your GitHub account. Work through the steps in order. Each step says how to tell it worked.

## What has and hasn't been tested

Tested before this was handed over:

- The script runs end to end against the two real Docker commits, with stand-in answers in place of the Claude API.
- It reads the right diffs, writes the log, replaces a lesson section, updates the source map, and produces the pull request title and body.
- It rejects a draft that contains a script, has the wrong section, or changes size too much.
- The workflow file is valid YAML.
- All three lesson files load in a browser with no script errors.

Not tested, because it needs your account:

- The real Claude API call, and the quality of Claude's triage and redraft.
- The workflow running on GitHub, including pushing a branch and opening a pull request.
- GitHub Pages.

Expect the first run on GitHub to fail once. The usual cause is step 4 below.

## 1. Put the files in your repository

The repository must contain these at its top level: `docs`, `scripts`, `prompts`, `review`, `sources`, `captures`, `benchmark`, `refresh-log`, `.github`, `source-map.json`, `README.md`, and `.gitignore`.

The `.github` folder and `.gitignore` start with a dot, and Windows or the GitHub upload page may hide or skip them. Two reliable ways:

- **With Git or Claude Code on your machine:** copy everything into your local clone, then commit and push.
- **In the browser:** upload the other folders by dragging them onto the repository page. Then choose **Add file** > **Create new file**, type `.github/workflows/refresh.yml` as the name, and paste in the contents of that file. Do the same for `.gitignore`.

It worked if the repository page shows a `.github/workflows` folder containing `refresh.yml`.

## 2. Check the API key secret

Go to **Settings** > **Secrets and variables** > **Actions**. The workflow expects a repository secret named exactly `ANTHROPIC_API_KEY`.

If the secret you created on Saturday has another name, either create a new one with this name, or change the name on the `ANTHROPIC_API_KEY:` line in `refresh.yml`.

## 3. Choose the model, if you want to

The script uses `claude-opus-5-5` unless told otherwise. To use another model, open the **Variables** tab on the same page and add a repository variable named `CLAUDE_MODEL`. Use the same model ID that worked in Saturday's test if you're unsure.

## 4. Let workflows open pull requests

Go to **Settings** > **Actions** > **General**, and scroll to **Workflow permissions**.

- Select **Read and write permissions**.
- Select **Allow GitHub Actions to create and approve pull requests**.
- Select **Save**.

Without this, the last step of the workflow fails with a message that GitHub Actions isn't permitted to create pull requests.

## 5. Run the workflow

Go to the **Actions** tab. Select **Refresh course from docs changes** in the left column. Select **Run workflow**. Leave the two commit IDs as they are, and select the green **Run workflow** button.

The two commits are the test set:

| Commit | Expected decision |
|---|---|
| `66590909f5`, the UDP log paragraph | Non-material |
| `f3b9c47090`, hostname blocking limitations | Material, affecting Lesson 1 |

It worked if the run shows a green check mark and the **Pull requests** tab shows a new pull request titled "Refresh: 1 material change in 2 upstream commits".

## 6. Review the pull request as the SME

Open the pull request. Read the description, which is the triage reasoning. Open the **Files changed** tab to see the redraft. Review it against `review/sme-checklist.md`.

Compare the workflow's draft of Lesson 1 section 4 with `benchmark/lesson-1-human-directed.html`, which holds the version written by hand on Nov. 16. The comparison is material for the case study.

Leave review comments on the lines you'd change. Merge only when you'd publish it.

## 7. Turn on GitHub Pages

Go to **Settings** > **Pages**. Under **Build and deployment**, set **Source** to **Deploy from a branch**. Choose your default branch and the `/docs` folder, then select **Save**.

It worked if, after a minute or two, the page shows the site's address and the address opens the course index.

## 8. Require review before merging

Do this after the first successful run, so a setup mistake doesn't lock you out.

Go to **Settings** > **Branches** or **Rules**, and add a rule for your default branch that requires a pull request with one approval before merging. The workflow's pull requests are authored by `github-actions[bot]`, so you can approve them yourself.

## If a step fails

| You see | Likely cause |
|---|---|
| `ANTHROPIC_API_KEY isn't set` | The secret is missing or has another name. See step 2 |
| `The Claude API returned 404` and a model error | The model ID isn't available to your key. See step 3 |
| `The Claude API returned 401` | The key is wrong or has been revoked |
| `GitHub Actions is not permitted to create or approve pull requests` | See step 4 |
| `nothing to commit` | The script changed no files. Read the **Triage and redraft** step's output |
| The pull request says a draft was "rejected" | A safety check refused Claude's draft, and the lesson is unchanged. The log says why |

## How the pieces connect

1. `refresh.yml` checks out this repository and clones the history of `docker/docs`.
2. It runs `scripts/refresh.py` with your API key.
3. For each commit, the script takes the diff of the five watched pages listed in `source-map.json`.
4. It fills `prompts/triage.md` with the rubric, the source map, and the diff, and sends it to Claude. Claude answers material or non-material, with reasons.
5. For each affected section of a material change, it fills `prompts/redraft.md` and sends it. It applies Claude's draft only if the draft passes the safety checks.
6. It writes a log entry to `refresh-log/` and updates `source-map.json`.
7. `refresh.yml` commits those changes to a new branch and opens a pull request.

To rehearse the script without the API, on a machine with Git and Python:

```
git clone --filter=blob:none --no-checkout https://github.com/docker/docs.git _upstream
set REFRESH_MOCK=1
set COMMITS=66590909f5a2f8b74ff034bcd36406788e5d9ea9 f3b9c47090031af3c486c8c871dab1045106fc60
python scripts/refresh.py
```

Stand-in answers are labeled as such in the log. Discard the changes afterward with `git checkout .`
