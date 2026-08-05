# Repository instructions for coding agents

## Scope and intent

This file applies to the entire repository. It is the working agreement for automated agents and human contributors changing this site.

Keep changes small, preserve the site's existing URLs and content, and validate the generated site before declaring work complete. Do not treat a zero exit code as sufficient when Jekyll reports destination conflicts or other actionable warnings.

## Technology stack

- **Site generator:** Jekyll 4 with the Minimal Mistakes theme.
- **Templating and content:** Liquid, HTML5, YAML front matter, and GitHub-Flavored Markdown through Kramdown.
- **Styling:** SCSS compiled by Jekyll/Dart Sass. The repository also contains vendored Breakpoint, Susy, Font Awesome, and Academicons assets.
- **Browser code:** JavaScript, jQuery, FitVids, jQuery Smooth Scroll, Plotly, and a small custom theme/navigation layer.
- **JavaScript build:** npm and UglifyJS. `assets/js/main.min.js` is the generated, tracked bundle.
- **Utilities:** Python scripts and notebooks generate CV, publication, talk, and talk-map data. The talk-map workflow currently uses Python 3.9.
- **Local containers:** Docker Compose and the VS Code dev container.
- **Deployment:** GitHub Actions builds Jekyll and deploys `_site` to GitHub Pages on pushes to `main`.

The deployment workflow in `.github/workflows/pages.yml` is the production toolchain reference: Ruby 3.4 and Bundler 4.0.6. The current Dockerfile uses Ruby 3.2 and Bundler 2.3.26. If dependency or toolchain behavior is changed, validate both paths or align them in the same change.

`Gemfile.lock` and `package-lock.json` are currently ignored and are not available in a clean checkout. Do not assume dependency resolution is locked. Do not start tracking or updating lockfiles incidentally; make reproducibility changes explicit and update `.gitignore`, documentation, Docker, and CI together.

## Project structure

| Path | Responsibility |
| --- | --- |
| `_config.yml` | Site identity, Markdown settings, collection definitions, defaults, plugins, Sass, and URL behavior. |
| `_config_docker.yml` | Docker-only Jekyll configuration override. |
| `_posts/` | Dated technical blog posts. |
| `_pages/` | Standalone pages such as home, CV, archives, portfolio, and articles. |
| `_portfolio/`, `_publications/`, `_talks/`, `_teaching/` | Jekyll collections configured in `_config.yml`. |
| `_layouts/` | Page skeletons. Keep layout logic generic and delegate reusable fragments to includes. |
| `_includes/` | Reusable Liquid/HTML fragments, SEO, navigation, analytics, comments, and custom head/footer hooks. |
| `_data/` | Structured YAML/JSON consumed through `site.data`, including navigation, articles, authors, UI text, and generated CV data. |
| `_sass/` | Theme, layout, utility, and vendor SCSS partials. |
| `assets/css/main.scss` | Jekyll SCSS entry point. Its leading front-matter lines are required. |
| `assets/js/_main.js` | Main editable browser behavior. |
| `assets/js/theme.js` | Plotly light/dark theme definitions imported by the module bundle. |
| `assets/js/plugins/` | Third-party or theme JavaScript sources. |
| `assets/js/main.min.js` | Generated and tracked browser bundle; never edit it manually. |
| `images/`, `files/` | Published static images, documents, slide decks, and papers. |
| `scripts/` | CV Markdown-to-JSON utility and its shell wrapper. |
| `markdown_generator/` | Optional CSV/TSV/BibTeX-to-Markdown scripts and notebooks. Run them from this directory because several use relative paths. |
| `talkmap.py`, `talkmap.ipynb`, `talkmap/` | Talk-location map sources and generated/static map assets. |
| `.github/workflows/` | GitHub Pages deployment and talk-map automation. |
| `_site/`, `.jekyll-cache/`, `.sass-cache/`, `node_modules/`, `vendor/` | Generated or local-only artifacts. Never hand-edit or commit them. |

## Setup, compile, and run commands

Run commands from the repository root unless stated otherwise.

### Native setup

Use Ruby 3.4 where possible to match GitHub Pages CI.

```bash
gem install bundler -v 4.0.6
bundle config set --local path vendor/bundle
bundle install
npm install
```

The npm install is needed only for JavaScript dependency or bundle work. Do not delete dependency lockfiles as an automatic troubleshooting step; investigate the resolution problem first.

### Compile the site

```bash
bundle exec jekyll build
```

Production-style build:

```bash
JEKYLL_ENV=production bundle exec jekyll build
```

In PowerShell, set the environment variable with `$env:JEKYLL_ENV = "production"` before running the build. GitHub Actions additionally supplies the Pages base path with `--baseurl`.

### Run the development server

```bash
bundle exec jekyll serve --livereload --host localhost
```

Open `http://localhost:4000`. Restart Jekyll after changing `_config.yml`; configuration changes are not reliably picked up by watch mode.

### Docker setup, compile, and run

```bash
docker compose build
docker compose run --rm jekyll-site bundle exec jekyll build --config _config.yml,_config_docker.yml
docker compose up --build
```

The running site is available at `http://localhost:4000`. Use `docker compose down` when finished. Do not copy the README's broad `chmod -R 777 .` workaround into automation.

### Rebuild browser JavaScript

When `package.json`, `assets/js/_main.js`, or `assets/js/plugins/` changes:

```bash
npm install
npm run build:js
bundle exec jekyll build
```

For active JavaScript work, use `npm run watch:js`. Commit `assets/js/main.min.js` with the source change and inspect the generated diff. Do not run the bundle command for unrelated content-only changes.

### Regenerate CV data

When `_pages/cv.md` or relevant collection metadata changes and `_data/cv.json` must be refreshed:

```bash
python scripts/cv_markdown_to_json.py --input _pages/cv.md --output _data/cv.json --config _config.yml
```

Review the complete `_data/cv.json` diff. The wrapper `bash scripts/update_cv_json.sh` is interactive and is intended for a developer terminal, not unattended automation.

## Required development workflow

1. Read the relevant `_config.yml` section and nearby files before editing. Follow established front matter, Liquid, and naming patterns.
2. Identify the source of truth. Never fix generated output when an editable source exists.
3. Make the smallest coherent change. Avoid drive-by formatting, broad theme rewrites, or unrelated dependency upgrades.
4. Regenerate only derived artifacts affected by the change.
5. Run the validation required for the changed area and inspect warnings and diffs.
6. Report the files changed, commands run, warnings left, and any checks that could not be performed.

## Content standards

- Every Markdown page, post, or collection item starts with valid YAML front matter delimited by `---` on the first line.
- Name posts `YYYY-MM-DD-descriptive_slug.md`. Keep `date` consistent with the filename and use an intentional, stable `permalink`.
- At minimum, posts need `title`, `date`, `permalink`, and focused lowercase `tags`. Collection items need `title`, `collection`, and the fields used by their archive include.
- Quote YAML strings containing colons, quotes, hash characters, or other YAML-significant text. Indent YAML with two spaces; never use tabs.
- Before adding or changing a permalink, search the repository for the proposed URL. Permalinks must be unique and must not silently break existing inbound links.
- Prefer Markdown for prose and semantic HTML only where layout requires it. Use fenced code blocks with a language identifier.
- Preserve factual accuracy, code correctness, and the voice of surrounding content. Do not rewrite unrelated prose.
- Use HTTPS links where available. Validate URL schemes and obvious typos. HTML links opened with `target="_blank"` must also use `rel="noopener noreferrer"`.
- Add meaningful alt text to informative images. Keep headings hierarchical and ensure interactive controls remain keyboard-accessible.
- Use `{{ base_path }}`, Jekyll's `relative_url` filter, or the established include conventions for internal assets and links; avoid new root-hardcoded URLs that fail under a non-empty Pages base path.
- Update `_data/navigation.yml` only when a page should appear in navigation. Keep `_data/*.yml` entries consistently ordered and shaped for their consumers.

## Liquid, HTML, and layout standards

- Keep layouts structural. Extract repeated or independently understandable fragments into `_includes/`.
- Escape user- or data-controlled text where it enters attributes or metadata. Preserve the SEO and accessibility metadata already supplied by layouts/includes.
- Use two-space indentation for YAML, Liquid, HTML, SCSS, and JavaScript. Match surrounding Liquid whitespace conventions.
- Prefer CSS classes over inline styles. New reusable page styles belong in a purpose-specific `_sass/` partial imported by `assets/css/main.scss`.
- Do not edit minified files, font files, or `_sass/vendor/` for site-specific styling. Vendor edits make upstream maintenance unnecessarily difficult.
- Check both light and dark themes and narrow/mobile layouts for visible UI changes.

## JavaScript standards

- Edit source files, not `assets/js/main.min.js`.
- Prefer `const`; use `let` only for reassignment. Avoid adding globals and keep DOM queries and event handlers scoped.
- Preserve the existing ES-module loading model in `_includes/scripts.html` and the relative import from `_main.js` to `theme.js`.
- Guard optional DOM elements and third-party payloads. Invalid chart or content data should fail locally without breaking unrelated page behavior.
- Keep JavaScript behavior accessible and usable without depending only on pointer events.
- If the bundle inputs or dependency order changes, update the `build:js` script in `package.json` and rebuild the tracked bundle in the same change.

## SCSS standards

- Put site-specific rules in `_sass/include/`, `_sass/layout/`, or a clearly named new partial, then import it from `assets/css/main.scss` in dependency order.
- Reuse existing theme variables, breakpoint helpers, spacing, and typography before adding literal values.
- Ensure new colors have sufficient contrast in light and dark modes. Add responsive behavior for layout changes.
- Do not add site-specific rules to `assets/css/academicons.css`, `assets/css/academicons.min.css`, or vendored SCSS.
- Keep the two front-matter lines at the start of `assets/css/main.scss`; Jekyll needs them to process the file.

## Python and generator standards

- Use Python 3-compatible code, four-space indentation, UTF-8, descriptive names, docstrings for non-obvious functions, and a guarded `if __name__ == '__main__':` entry point for new command-line tools.
- Prefer `pathlib.Path` for new filesystem code and explicit UTF-8 when reading or writing text.
- Validate inputs before writing generated Markdown or JSON. Preserve deterministic ordering and line endings so generated diffs remain reviewable.
- Do not run generators that overwrite collections, CV data, notebooks, or talk maps unless those outputs are in scope. Review every generated diff afterward.
- Talk-map generation performs network geocoding and the workflow can commit generated changes. Do not invoke or redesign that side effect casually.
- When adding a third-party Python import, provide a reproducible dependency declaration and update the relevant workflow or documentation in the same change.

## Validation matrix

There is currently no dedicated automated test suite. The Jekyll build is the minimum integration check.

| Change | Required validation |
| --- | --- |
| Markdown, YAML data, configuration, includes, layouts, or SCSS | `bundle exec jekyll build`, or the Docker one-off build above. Inspect warnings. |
| JavaScript source or npm dependencies | `npm run build:js`, inspect `assets/js/main.min.js`, then build Jekyll. |
| Docker or dev-container files | `docker compose config --quiet`, then `docker compose build`. |
| CV generator or CV source | Run the explicit CV command, inspect `_data/cv.json`, then build Jekyll. |
| Publication/talk generator | Run it from `markdown_generator/` against controlled input, inspect all generated files, then build Jekyll. |
| Talk-map source/workflow | Validate Python/notebook execution only when network use and generated map updates are explicitly in scope. |
| Any change | `git diff --check` and `git status --short`; verify only intended files changed. |

For user-facing layout or interaction changes, also preview representative desktop and mobile widths, light and dark themes, navigation, internal links, and the browser console.

## Generated files and dependency policy

- Never hand-edit `_site/`, `.jekyll-cache/`, `.sass-cache/`, `node_modules/`, `vendor/`, notebook checkpoints, or minified output.
- `assets/js/main.min.js`, `_data/cv.json`, and `talkmap_out.ipynb` are tracked generated artifacts. Update them only from their source workflow and commit source plus output together.
- Keep dependency changes narrowly scoped. Explain why a dependency is needed, prefer maintained packages, and verify the production and Docker toolchains.
- Do not commit credentials, tokens, private endpoints, personal secrets, or local environment files. GitHub secrets belong in repository settings and should be referenced symbolically in workflows.

## Known baseline issues

These issues existed when this file was created. Do not normalize or expand them; remove an item when its underlying issue is fixed.

- `_publications/2024-02-17-paper-title-number-4.md` and `_publications/2025-06-08-paper-title-number-5.md` currently resolve to the same publication output path. Jekyll exits successfully but reports a destination conflict.
- The vendored Breakpoint/Susy SCSS and legacy `@import` structure emit many Dart Sass deprecation warnings. Distinguish these baseline warnings from new warnings and do not suppress them globally.
- CI and Docker use different Ruby/Bundler versions, and dependency lockfiles are ignored.
- A fresh JavaScript rebuild does not currently match the tracked `assets/js/main.min.js`; dependency ranges plus ignored lockfiles make the bundle non-reproducible.
- Site-specific `.articles-grid` and `.article-card` rules are currently appended to `assets/css/academicons.css`. New styles must go through the SCSS source structure; move the existing rules only in a focused, visually verified cleanup.
- `_data/articles.yml` contains at least one malformed `hhttps://` link. Validate article URLs when touching that data.

## Definition of done

A change is complete only when source-of-truth files were edited, affected generated artifacts were refreshed, required validation passed, Jekyll output was inspected for conflicts, the working-tree diff contains no accidental files, and the final handoff clearly states any remaining warning or unverified behavior.
