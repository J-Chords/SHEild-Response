# SHEild Response image assets

This folder holds the final licensed photography for the public-facing pages. Every image area already has a styled, accessible CSS fallback (a gradient panel with an inline illustration), so a missing file never breaks the layout — it just shows the fallback until the real photograph is added here.

Photography should be documentary, natural and dignified: African and Black women, families and support professionals shown with strength, agency and community, not distress. Do not use images depicting physical assault, bruises, blood, visible injuries, crying victims or any other sensationalised or stereotypical victim imagery.

| Filename | Ideal subject | Ideal orientation | Recommended dimensions | Where it appears |
|---|---|---|---|---|
| `hero-women-support.jpg` | African or Black women in a calm, mutually supportive setting, communicating trust, agency and strength | Landscape or portrait crop | At least 1600 × 1200 px; keep the lower-right quiet (a quote overlays it) | Home page hero (`main/home.html`, `.photo-panel--hero`) |
| `community-support.jpg` | Community support workers or women gathering in a warm, welcoming setting, inclusive of different ages | Landscape | At least 1600 × 1000 px | Home page "Support beyond reporting" split section (`main/home.html`, `.photo-panel--community`) |
| `professional-woman.jpg` | An African female counsellor, advocate, social worker or other support professional — calm, competent, approachable | Landscape | At least 1200 × 700 px | Reserved for a future about/responder-facing panel (`.photo-panel--professional`) |
| `safe-family.jpg` | An African family in a safe, everyday setting, showing connection and dignity (not implying any depicted person is a survivor) | Landscape | At least 1400 × 900 px | Reserved for a future family-safety or referral feature |
| `support-team.jpg` | A diverse African support/response team collaborating professionally (no uniforms or branding implying a real police, hospital or NGO partnership) | Landscape | At least 1400 × 900 px | Reserved for a future about or responder-training section |

## Adding a real photograph

Drop the file into this folder using the exact filename above — no template or CSS changes are needed, the existing `url('../images/<filename>')` references in `shield/static/css/app.css` and the `role="img" aria-label="..."` placeholders in the templates pick it up automatically.

## Licensing and safety checks

Use only images with documented permission for this use. Record source, creator, licence, model-release status and any attribution requirement outside this repository. Remove embedded metadata before deployment. Never use photographs of actual clients or active cases. Do not source images from random remote placeholder APIs; only local files in this folder are referenced from production templates.
