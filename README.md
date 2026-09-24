# threads-recon

Free competitor intelligence for Threads — no login to their account, no paid
analytics tools, no official API keys. Just the public, anonymous pages
Threads already shows to anyone.

[Русская версия ниже](#русская-версия) / [Russian version below](#русская-версия)

## What it does

- Follower count for any public Threads profile.
- Up to ~25-40 of the account's latest posts: text, date, like count, direct link.
- View count for any specific post (optional, one extra request per post).

## How it works

Threads renders enough data into the plain anonymous HTML of a profile or
post page that you don't need to log in or call the official Graph API to
read it:

- **Followers** — parsed out of the page `<meta name="description">` tag on
  `https://www.threads.com/@username`.
- **Post views** — Threads ships a `"view_counts": N` field straight in the
  anonymous HTML of the post's own page. (This used to be undocumented and
  assumed "author-only" based on older articles — it isn't, not anymore.)
- **Post list** (text, date, likes, permalink) — via the small
  [`threads-api`](https://www.npmjs.com/package/threads-api) npm library,
  which talks to Threads' own public GraphQL endpoints the same way an
  anonymous mobile-web visitor would.

No official app, no developer token, no login cookie, anywhere in this repo.

## Honest limitations

- Replies, reposts and quote-posts on someone else's account are **not**
  exposed to an anonymous observer at all — Threads only hands that over
  through the official API for *your own* account.
- Follower count is a live snapshot, not a history. If you want a trend
  line, you have to poll this yourself and store the numbers over time.
- Very fresh posts may not have accumulated view counts yet.
- This scrapes public HTML/GraphQL endpoints that Threads doesn't document
  or officially support for this use — it can break if they change their
  markup. Be polite: don't hammer it, add delays between requests (see
  below), and don't use it for anything shady.

## Install

```bash
git clone https://github.com/hivemem-dev/threads-recon.git
cd threads-recon
npm install        # pulls in threads-api
```

`recon.py` only needs the Python standard library — nothing to install there.

## Use

```bash
python3 recon.py <username>           # followers + latest posts
python3 recon.py <username> --posts   # posts only, skip the follower lookup
python3 recon.py <username> --views   # also fetch view counts per post (slower, one request each)
```

Output is JSON on stdout, e.g.:

```json
{
  "username": "someaccount",
  "followers": 14300,
  "posts": [
    {"post_id": "...", "text": "...", "timestamp": 1790096360000,
     "permalink": "https://www.threads.com/@someaccount/post/...", "likes": 857}
  ]
}
```

Pipe it anywhere: `> data.json`, `| jq`, a Python script that inserts into a
database, whatever you're building.

## Turning this into your own analytics service

This repo is deliberately just the data-fetching core, not a full app — bolt
on what you actually need:

1. **Store snapshots over time.** Followers alone are a single number; the
   useful signal is the *trend*. Run `recon.py` on a schedule (cron, a
   systemd timer, GitHub Actions on a schedule) and append each run's
   `followers` value with a timestamp to a table (SQLite is plenty).
2. **Track multiple competitors.** Keep a simple list of usernames per
   niche, loop over it, be polite about it — add a short `sleep()` between
   accounts and between the per-post `--views` calls, this repo does 0.3s
   between post-view lookups by default in the dashboard version; do
   something similar in your own loop.
3. **Score posts.** Once you're storing `likes`/`views` per post over time,
   it's trivial to rank "what's actually working" for a niche: sort by
   views-per-follower or likes-per-view instead of raw counts, so a small
   account's viral post doesn't get buried under a big account's average one.
4. **Surface it.** A five-line Flask/FastAPI app that reads the SQLite table
   and renders a table or a chart is enough — you don't need much more than
   that to stop guessing and start looking at real numbers.

## License

MIT. Use it, fork it, build on it.

---

## Русская версия

Бесплатная разведка конкурентов в Threads — без логина в чужой аккаунт, без
платных сервисов аналитики, без официальных ключей API. Только то, что
Threads и так открыто показывает любому анонимному посетителю.

### Что умеет

- Число подписчиков любого публичного профиля.
- До ~25-40 последних постов аккаунта: текст, дата, лайки, прямая ссылка.
- Просмотры под конкретным постом (опционально, отдельный запрос на пост).

### Как это устроено

Threads отдаёт достаточно данных прямо в обычном анонимном HTML страницы
профиля или поста, поэтому логин и официальный Graph API не нужны:

- **Подписчики** — вытаскиваются из тега `<meta name="description">` на
  странице `https://www.threads.com/@username`.
- **Просмотры поста** — Threads прямо в анонимном HTML страницы поста
  отдаёт поле `"view_counts": N`. (Раньше это считалось недокументированным
  и "видно только автору" по старым статьям 2023 года — это устарело,
  больше не так.)
- **Список постов** (текст, дата, лайки, ссылка) — через маленькую
  npm-библиотеку [`threads-api`](https://www.npmjs.com/package/threads-api),
  которая обращается к тем же публичным GraphQL-эндпоинтам Threads, что и
  обычный анонимный посетитель с мобильного веба.

Никакого официального приложения, токена разработчика или логин-куки в этом
репозитории нет вообще.

### Честные ограничения

- Реплаи, репосты и цитаты чужого поста анонимному наблюдателю **не
  отдаются вообще** — это доступно только через официальный API для
  **своего** аккаунта.
- Подписчики — это текущий снимок, не история. Хочешь график роста —
  придётся самому опрашивать и сохранять цифры со временем.
- У совсем свежих постов просмотры ещё не успевают накопиться.
- Это чтение публичных HTML/GraphQL-эндпоинтов, которые Threads официально
  не документирует под такую задачу — может сломаться, если они поменяют
  разметку. Будь вежлив: не долби запросами часто, ставь паузы между
  запросами (см. ниже), не используй для чего-то сомнительного.

### Установка

```bash
git clone https://github.com/hivemem-dev/threads-recon.git
cd threads-recon
npm install        # подтянет threads-api
```

Для `recon.py` ничего ставить не нужно, только стандартная библиотека Python.

### Использование

```bash
python3 recon.py <username>           # подписчики + последние посты
python3 recon.py <username> --posts   # только посты, без подписчиков
python3 recon.py <username> --views   # + просмотры под каждым постом (медленнее)
```

Результат — JSON в stdout, дальше сохраняй куда угодно: в файл, в таблицу,
в свою базу.

### Как собрать из этого свой сервис аналитики

Этот репозиторий — сознательно только ядро получения данных, не готовое
приложение. Дособери то, что реально нужно:

1. **Сохраняй снимки со временем.** Число подписчиков само по себе — просто
   цифра, полезен только тренд. Запускай `recon.py` по расписанию (cron,
   systemd-таймер, запланированный GitHub Actions) и добавляй каждый
   результат `followers` с меткой времени в таблицу (хватит и SQLite).
2. **Следи за несколькими конкурентами.** Держи простой список username по
   нише, перебирай их циклом, но вежливо — ставь паузу между аккаунтами и
   между запросами `--views` на каждый пост (в версии для дашборда пауза
   0.3 секунды между постами, сделай похожую у себя).
3. **Считай рейтинг постов.** Когда лайки/просмотры по постам копятся со
   временем, легко посчитать, что реально работает в нише: сортируй не по
   сырым цифрам, а по просмотрам на подписчика или лайкам на просмотр —
   тогда вирусный пост маленького аккаунта не потеряется за средним постом
   большого.
4. **Покажи это глазами.** Простое приложение на Flask/FastAPI на пять
   строк, которое читает таблицу SQLite и рисует таблицу или график —
   этого достаточно, чтобы перестать гадать и начать смотреть на реальные
   цифры.

### Лицензия

MIT. Используй, форкай, дорабатывай.
