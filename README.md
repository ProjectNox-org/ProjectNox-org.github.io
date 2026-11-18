# Project Nox — Central Oficial

Portal institucional e diretório oficial da organização **Project Nox** (`ProjectNox-org`), uma iniciativa independente dedicada ao desenvolvimento de software livre, plataformas digitais, ferramentas e novas soluções tecnológicas para a comunidade.

## Sobre a Central Oficial

Este repositório hospeda o site estático publicado no GitHub Pages em `https://projectnox-org.github.io/`.

Sua função é apresentar a identidade institucional da organização, explicar sua política de código aberto sob **GNU AGPL-3.0**, reunir o diretório individual de todos os repositórios públicos de `ProjectNox-org` e orientar usuários finais até a instalação gratuita das extensões, abertura de tickets e acompanhamento público no Tracker.

> **Nota:** A Central Oficial (`ProjectNox-org.github.io`) é o portal institucional da organização; a plataforma web de leitura de mangás reside no repositório separado [`project-nox-manga`](https://github.com/ProjectNox-org/project-nox-manga).

## Acessos oficiais

- **Central Oficial:** https://projectnox-org.github.io/
- **Guia de instalação de extensões:** https://projectnox-org.github.io/extensoes/
- **Tracker de Extensões:** https://projectnox-org.github.io/project-nox-tracker/
- **Organização no GitHub:** https://github.com/ProjectNox-org
- **Discord oficial:** https://discord.com/invite/qNAMYUEmGj
- **Fluxer oficial:** https://web.canary.fluxer.app/invite/q456UCVt

## Estrutura do projeto

- `index.html` — Página institucional principal, trajetória, seção GNU AGPL-3.0, vitrine, diretório de repositórios, suporte e encerramento.
- `extensoes/index.html` — Guia dedicado de instalação das extensões para Mihon, Aniyomi e forks (com progressive enhancement sem JavaScript).
- `styles.css` — Sistema de design, paleta cósmica institucional, layout responsivo e suporte a `prefers-reduced-motion`.
- `app.js` — Busca sem acentos, filtros por categoria, alternância acessível de abas, navegação por hash, cópia de URLs e controle opcional de movimento ambiental.
- `data/repositories.json` — Fonte canônica dos metadados exibidos no diretório de repositórios.
- `scripts/sync-repos.py` — Script em Python (biblioteca padrão) que sincroniza metadados da API do GitHub e renderiza os cards estáticos e contagens diretamente em `index.html`.
- `tests/test_sync_repos.py` — Suíte de testes unitários para o gerador do catálogo.
- `assets/` — Emblema, banners SVG animados (`assets/brand/`), capturas otimizadas da vitrine (`assets/showcase/`), imagem Open Graph (`assets/brand/nox-og.png`) e favicons.
- `.github/workflows/sync-repos.yml` — Workflow automatizado de testes e sincronização semanal do catálogo.
- `project-nox-tracker/` e `project-nox-scan-staff/` — Redirecionamentos preservados para compatibilidade de rotas antigas.

## Arquitetura

- **Site 100% estático:** HTML, CSS e JavaScript puros, sem frameworks ou dependências de runtime no navegador.
- **Geração estática a partir de fonte canônica:** Os cards de repositórios, filtros e contagens presentes em `index.html` são gerados estaticamente a partir de `data/repositories.json` via `scripts/sync-repos.py`.
- **Zero chamadas à API do GitHub por visita:** Visitantes não disparam requisições à API do GitHub; a página funciona integralmente mesmo com JavaScript desabilitado.

## Desenvolvimento local

Com Python 3 instalado, inicie um servidor HTTP estático na raiz do repositório:

```bash
python3 -m http.server 8000
```

Acesse `http://localhost:8000/` e `http://localhost:8000/extensoes/` no navegador.

## Atualização do catálogo

Para sincronizar os metadados públicos da organização no GitHub, atualizar `data/repositories.json` e regenerar os cards em `index.html`:

```bash
python3 scripts/sync-repos.py
```

Para evitar limites de taxa da API pública do GitHub, você pode definir `GITHUB_TOKEN` (ou `GH_TOKEN`) no ambiente antes de executar o comando.

Para apenas regenerar `index.html` localmente a partir do `data/repositories.json` existente, sem chamadas de rede:

```bash
python3 scripts/sync-repos.py --render-only
```

## Testes

Execute os testes unitários do gerador de catálogo com:

```bash
python3 -m unittest discover -s tests -v
```

## Publicação

O site é publicado automaticamente pelo GitHub Pages a partir da branch `main` (diretório raiz `/`). Após um push em `main`, o status do build pode ser acompanhado nas configurações de Pages do repositório ou via API (`repos/ProjectNox-org/ProjectNox-org.github.io/pages/builds/latest`).

## Identidade visual

Os ativos em `assets/brand/` (`nox-emblem.webp`, `nox-hero-dark.svg`, `nox-hero-mobile-dark.svg`, `nox-philosophy-dark.svg`, `nox-philosophy-mobile-dark.svg`) derivam diretamente dos ativos oficiais da organização em [`ProjectNox-org/.github`](https://github.com/ProjectNox-org/.github). Não altere o emblema oficial nem substitua o banner animado por peças genéricas.

## Contribuição

Consulte o [Guia de Contribuição](https://github.com/ProjectNox-org/.github/blob/main/CONTRIBUTING.md) da organização antes de abrir issues ou pull requests.

## Licença

Este repositório é licenciado sob a **GNU Affero General Public License v3.0 (GNU AGPL-3.0)**, conforme o arquivo [`LICENSE`](LICENSE). Atribuições e licenças de terceiros aplicáveis são preservadas integralmente.
