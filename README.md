# Verse of the Day · Rise & Shine Ministries

Each morning someone from Rise & Shine enters the day's Bible verse in a small web form. A few minutes later the verse is ready in **Tamil and English** on a download page:

- a **picture** (1080×1350) per language, for feed posts,
- a **vertical video** (1080×1920) per language, for Reels, Shorts and WhatsApp Status, with the verse read aloud, each word lighting up as it is read, over soft background music,
- a **Share to Status** button per video (WhatsApp → My status) and a caption to copy.

Nothing is posted automatically; the team downloads or shares what they need.

| | Address |
|---|---|
| Download page | https://franklinis.github.io/rise-shine-verse/ |
| Form for the team | https://franklinis.github.io/rise-shine-verse/form/ |

## Entering the verse

Open the form, type the reference and press **Make today's verse**:

- English, Tamil or German book names all work: `Psalm 23:1`, `John 3:16-17`, `1 Cor 13:4`, `சங்கீதம் 23:1`, `1 கொரிந்தியர் 13:4`, `Römer 8,28` (a comma means German verse numbers).
- Up to 6 verses from one chapter.
- **Theme** (optional): a few words that guide the background picture, e.g. `hope, trust`.
- **Day**: today by default; a later day can be prepared in advance. Entering a verse again for the same day replaces it.
- The **passcode** keeps strangers out; tick *Remember* to keep it on that phone.

The form shows when it's ready (about 3–5 minutes) and links to the download page. If the reference isn't recognised, it says so; correct it and send again.

## Design

The same slide design as [clp-daily-verse](https://github.com/franklinis/clp-daily-verse): 39 colour palettes (feast-day palettes for Christmas, Easter and Pentecost), and, with `BACKGROUNDS` = `ai`, a background painted for each verse by an Azure image model (calm nature scenes; no people, text or depictions of God). The logo is `assets/logo-white.png` (a white logo on a transparent background, square); the name, titles, voices and page colours are in `church.json`.

| Language | Text | Voice |
|---|---|---|
| தமிழ் | tamil-bible.com | ta-IN Pallavi / Valluvar |
| English | King James Version (public domain, bundled) | en-GB Sonia / Ryan |

Female and male voices alternate between the languages and swap every day. The music is composed in code (`daily_verse/music.py`), so YouTube's and Meta's copyright matching can never claim it.

## How it works

1. The form posts the verse to an **Azure Logic App**, which checks the passcode and starts the GitHub workflow **Verse of the day** (`.github/workflows/verse.yml`). The passcode never reaches GitHub.
2. The workflow looks up the verse, renders the pictures and videos, rebuilds the download page and pushes everything to the [`media` branch](../../tree/media), which keeps the last 30 days. GitHub Pages serves it.
3. The form follows the run through GitHub's public API and shows when it's done.

The workflow can also be started by hand: **Actions → Verse of the day → Run workflow**. **Actions → New background** paints a new background for a day and makes it again.

## Setup

**GitHub** (Settings → Secrets and variables → Actions):

| Where | Name | Value |
|---|---|---|
| Secret | `AZURE_SPEECH_KEY` | Azure AI Speech key (read-aloud) |
| Variable | `AZURE_SPEECH_REGION` | e.g. `germanywestcentral` |
| Variable | `NARRATION` | `on` |
| Secret | `AZURE_OPENAI_KEY` | Microsoft Foundry key for the image model |
| Variable | `AZURE_OPENAI_ENDPOINT` | e.g. `https://<resource>.services.ai.azure.com` |
| Variable | `AZURE_IMAGE_DEPLOYMENT` | e.g. `gpt-image-2` |
| Variable | `BACKGROUNDS` | `ai` (leave unset for the generated mountain backgrounds) |
| Variable | `FORM_ENDPOINT` | The Logic App's HTTP URL (below) |

GitHub Pages: **Settings → Pages → Deploy from a branch → `media` / root**.

**The form's Logic App** (Azure, Consumption plan; a few cents a month). It can live in any Azure subscription; it only needs a GitHub token.

*1. A GitHub token* that can only start this repository's workflows:

1. github.com → your profile picture → **Settings** → (bottom of the left menu) **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**.
2. **Token name** `rise-shine-form`; **Expiration** the longest offered (set a reminder to renew it); **Repository access** → *Only select repositories* → `rise-shine-verse`; **Permissions → Repository permissions → Actions**: **Read and write**. Leave everything else.
3. **Generate token** and copy it (`github_pat_…`); GitHub shows it only once.

*2. The Logic App:*

1. portal.azure.com → **Create a resource** → search **Logic App** → **Create** → hosting option **Consumption** (multi-tenant).
2. **Basics**: the subscription; resource group **Create new** `rise-shine`; name `rise-shine-form`; region e.g. **Central India**; log analytics **No**. **Review + create** → **Create** → **Go to resource**.
3. Left menu **Development Tools → Logic app code view**. Replace everything with the contents of [`form/logic-app.json`](form/logic-app.json) ([raw](https://raw.githubusercontent.com/franklinis/rise-shine-verse/main/form/logic-app.json)).
4. At the bottom, replace `PASTE-THE-GITHUB-TOKEN-HERE` with the token and `CHOOSE-A-PASSCODE-HERE` with the team's passcode (keep the quotation marks). **Save**.

*3. Connect the form:*

1. Left menu **Development Tools → Logic app designer** → click the first step, **When a HTTP request is received** → copy its **HTTP URL** (long, ends with `sig=…`).
2. Save it as the repository variable `FORM_ENDPOINT`, then run **Actions → Verse of the day** once so the form picks it up.

The Logic App only answers this repository's GitHub Pages site, and refuses wrong passcodes. To change the passcode, edit it in code view and save. When the token expires, the form says GitHub didn't accept it: make a new token and replace it in code view.

## Development

```bash
pip install -r requirements.txt pytest ruff
pytest -q && ruff check .
MEDIA_DIR=/tmp/verse python -m daily_verse verse --reference "Psalm 23:1"   # renders locally, without narration
MEDIA_DIR=/tmp/verse python -m daily_verse page
```

## Licensing

The code is MIT licensed. The King James Version is in the public domain (bundled copy from eBible.org). Tamil texts are used under tamil-bible.com's terms: single verses, unaltered, never sold.
