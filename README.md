<p align="center">
  <img src="https://raw.githubusercontent.com/ProjectNox-org/.github/main/assets/brand/nox-emblem.webp" alt="Emblema oficial do Project Nox" width="96" />
</p>

<h1 align="center">Project Nox · Central Oficial</h1>

<p align="center">
  Iniciativa independente de tecnologia e código aberto — plataformas digitais, ferramentas e soluções para a comunidade.
</p>

> [!IMPORTANT]
> [**Acessar a Central Oficial do Project Nox**](https://projectnox-org.github.io/)
>
> Este repositório hospeda o código-fonte do portal público. Para explorar os projetos, instalar extensões, buscar ajuda ou acessar nossos canais oficiais, utilize o site acima.

## O que é o Project Nox?

O **Project Nox** é uma iniciativa independente dedicada ao desenvolvimento de software livre e soluções tecnológicas abertas. Mantemos plataformas web, ferramentas para desenvolvedores, automações e recursos comunitários que podem ser utilizados, estudados e aprimorados por qualquer pessoa, respeitando as licenças aplicáveis.

Embora diversos membros conheçam o projeto pelas extensões gratuitas para mangás e animes, a organização abrange outras frentes tecnológicas e projetos independentes. Esta **Central Oficial** funciona como ponto de apresentação institucional e diretório unificado do ecossistema — aplicações específicas, como a plataforma de leitura [`project-nox-manga`](https://github.com/ProjectNox-org/project-nox-manga), residem em repositórios próprios.

## Encontre o que você procura

- **Portal e diretório de projetos:** navegue pela [Central Oficial](https://projectnox-org.github.io/) ou vá direto ao [Diretório de Projetos](https://projectnox-org.github.io/#repositorios) com busca e filtros por categoria.
- **Instalar extensões gratuitas:** siga o passo a passo no [Guia Oficial de Extensões](https://projectnox-org.github.io/extensoes/) para configurar Mihon, Aniyomi e aplicativos compatíveis.
- **Acompanhar pedidos e correções:** consulte solicitações abertas e encerradas no [Tracker de Extensões](https://projectnox-org.github.io/project-nox-tracker/).
- **Explorar repositórios no GitHub:** acesse todos os projetos públicos na organização [`ProjectNox-org`](https://github.com/ProjectNox-org).
- **Pedir ajuda e conversar:** participe da comunidade pelo [Discord oficial](https://discord.com/invite/qNAMYUEmGj) ou pelo [Fluxer oficial](https://web.canary.fluxer.app/invite/q456UCVt).

## Projetos e soluções

A organização reúne iniciativas em cinco frentes principais:

- **Plataformas e web:** painel público de demandas ([Tracker de Extensões](https://projectnox-org.github.io/project-nox-tracker/)) e plataforma web de leitura ([`project-nox-manga`](https://github.com/ProjectNox-org/project-nox-manga), *temporariamente indisponível*).
- **Extensões gratuitas:** catálogos de distribuição e código-fonte de extensões para mangás e animes, detalhados no [Guia Oficial de Extensões](https://projectnox-org.github.io/extensoes/).
- **Ferramentas para desenvolvedores:** utilitários e recursos voltados à criação e manutenção de extensões.
- **Automação e infraestrutura:** serviços e scripts responsáveis por sincronizar metadados e manter os catálogos atualizados.
- **Comunidade e identidade:** canal oficial de solicitações, documentação institucional e ativos de marca.

Como o catálogo evolui continuamente, utilize o [Diretório Oficial de Projetos](https://projectnox-org.github.io/#repositorios) na Central para consultar a lista sempre atualizada, com licenças, links de código-fonte e documentação individual.

## Comunidade e solicitações

Cada canal do Project Nox tem uma finalidade específica:

- **Discord e Fluxer ([Discord](https://discord.com/invite/qNAMYUEmGj) · [Fluxer](https://web.canary.fluxer.app/invite/q456UCVt)):** espaços para tirar dúvidas, trocar ideias e acompanhar avisos da comunidade, sem necessidade de conta no GitHub.
- **Central de Pedidos ([`project-nox-requests`](https://github.com/ProjectNox-org/project-nox-requests)):** repositório oficial para **abrir novas solicitações**, reportar falhas ou informar mudanças de domínio. Exige uma conta gratuita no GitHub e é analisado conforme a disponibilidade dos mantenedores.
- **Tracker ([projectnox-org.github.io/project-nox-tracker](https://projectnox-org.github.io/project-nox-tracker/)):** painel público para **consultar e acompanhar** o andamento dos pedidos já registrados — ele não instala extensões nos aplicativos e não exige conta para visualização (apenas para abrir tickets ou votar com `👍` no GitHub).

## Código aberto e contribuição

O Project Nox disponibiliza seus repositórios publicamente sob a licença **GNU Affero General Public License v3.0 (`AGPL-3.0`)** (consulte [`LICENSE`](LICENSE)). Isso garante a liberdade de usar, estudar, modificar e redistribuir o código-fonte, preservando atribuições e exigindo a disponibilização do código correspondente em distribuições e interações remotas por rede (Seção 13).

A licença AGPL-3.0 é compatível com diferentes usos previstos em seus termos legais; em paralelo, como política institucional do projeto, **todas as extensões oficiais do Project Nox são distribuídas gratuitamente**.

Quer colaborar com código, correções ou documentação? Leia o [Guia de Contribuição oficial](https://github.com/ProjectNox-org/.github/blob/main/CONTRIBUTING.md) antes de abrir *issues* ou *pull requests*.

## Para desenvolvedores

A Central Oficial é um site estático construído com HTML, CSS e JavaScript puros, sem frameworks e sem chamadas à API do GitHub durante a visita do usuário (com aprimoramento progressivo para busca, filtros e controle de animações). O diretório de repositórios é gerado estaticamente a partir de `data/repositories.json` e publicado automaticamente via GitHub Actions.

<details>
<summary>Desenvolvimento local, arquitetura e manutenção</summary>

### Requisitos e estrutura principal

- **Execução local e scripts:** Python 3 (`scripts/sync-repos.py` usa apenas biblioteca padrão e anotações modernas de tipo; o workflow oficial utiliza Python `3.12`).
- **Validação JavaScript:** Node.js (usado apenas na verificação de sintaxe `node --check app.js`).
- **Arquivos principais:**
  - `index.html` e `styles.css`: página institucional, seção AGPL-3.0, diretório estático, design responsivo e suporte a `prefers-reduced-motion`.
  - `extensoes/index.html`: guia de instalação para Mihon, Aniyomi e forks (funcional mesmo sem JavaScript).
  - `app.js` e `particles.js`: busca sem acentos, filtros, abas acessíveis, cópia de URLs e fundo cósmico pausável.
  - `data/repositories.json` e `scripts/sync-repos.py`: fonte canônica e gerador idempotente dos cards e contagens em `index.html`.
  - `tests/test_sync_repos.py`: suíte de testes unitários do sincronizador.
  - `.github/workflows/sync-repos.yml`: pipeline de testes, sincronização e publicação no GitHub Pages.
  - `assets/brand/`: ativos visuais oficiais derivados de `ProjectNox-org/.github` (emblema, banners e imagem Open Graph).
  - `project-nox-tracker/` e `project-nox-scan-staff/`: redirecionamentos estáticos mantidos para compatibilidade de rotas antigas.

### Execução local

Na raiz do repositório, inicie um servidor HTTP estático:

```bash
python3 -m http.server 8000
```

Acesse `http://localhost:8000/` e `http://localhost:8000/extensoes/` no navegador.

> **Nota de ambiente local:** Rotas hospedadas em outros repositórios da organização (como `/project-nox-tracker/`) são servidas em produção pelo GitHub Pages e não estão incluídas no servidor local deste repositório.

### Sincronização do catálogo

```bash
# Sincroniza metadados públicos no GitHub e atualiza data/repositories.json e index.html
python3 scripts/sync-repos.py

# Regenera apenas os blocos estáticos de index.html a partir do JSON local (sem rede)
python3 scripts/sync-repos.py --render-only
```

- **Atenção operacional:** `scripts/sync-repos.py` pode alterar arquivos versionados (`data/repositories.json` e as regiões marcadas em `index.html`). Sempre revise `git status` e `git diff` antes de realizar qualquer commit.
- **Uso de token:** para evitar limites de requisição da API pública do GitHub, defina `GITHUB_TOKEN` (ou `GH_TOKEN`) apenas como variável de ambiente na sessão; nunca salve credenciais no repositório.

### Testes e publicação

```bash
python3 -m unittest discover -s tests -v
node --check app.js
```

O workflow `.github/workflows/sync-repos.yml` executa os testes, sincroniza o catálogo, valida a idempotência (`--render-only`) e a sintaxe JavaScript, e publica os arquivos estáticos públicos (`_site/`) no GitHub Pages via `actions/deploy-pages@v4`.

</details>

## Créditos e licenciamento

Portal institucional mantido pelo **Project Nox**, iniciativa fundada por **Awerkori**.

Licenciado sob a **GNU Affero General Public License v3.0 (`AGPL-3.0`)**, conforme [`LICENSE`](LICENSE). Atribuições de terceiros aplicáveis (tipografia sob SIL Open Font License 1.1, iconografia compatível com Lucide Icons sob ISC License e menções a marcas externas) estão registradas em [`NOTICE`](NOTICE).
