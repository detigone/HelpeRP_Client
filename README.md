# HelpeRP

Бесплатный оверлей для RP-игроков: база знаний, меры, шаблоны, RAG-поиск, профили персонажей.

**Сайт:** https://yeolka-lm.github.io/HelpeRP_Client/

## Быстрый старт

```bash
pip install -r requirements.txt
py run.py
```

Файл `.helperp_dev` в корне — режим разработки без лицензии.

## Новое

- **RAG-поиск** (BM25) — умный поиск по смыслу
- **Профили персонажей** — несколько RP-персонажей
- **Шаблоны** — /me и /do без ИИ (раздел «Шаблоны»)
- **Сайт на GitHub Pages** — документация и обновления бесплатно

## Документация

| Раздел | Ссылка |
|--------|--------|
| Онлайн (сайт) | https://yeolka-lm.github.io/HelpeRP_Client/#/docs/index |
| Локально | [docs/index.md](docs/index.md) |
| В приложении | Сайдбар → Справка |

## GitHub Pages (без своего домена)

1. Репозиторий → **Settings → Pages → Source: GitHub Actions**
2. Push в `main` — workflow `.github/workflows/pages.yml` деплоит `website/`
3. URL: `https://yeolka-lm.github.io/HelpeRP_Client/`

Обновления: `https://yeolka-lm.github.io/HelpeRP_Client/updates/manifest.json`

## Сборка

```bash
py tools/build_exe.py
py tools/release.py --bump patch
```

© 2026 detigone
