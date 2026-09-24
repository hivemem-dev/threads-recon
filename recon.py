#!/usr/bin/env python3
"""Бесплатная разведка конкурентов в Threads: подписчики, посты, лайки, просмотры.
Работает без логина и без официального API, только по публичным анонимным
страницам Threads. Никаких ключей/токенов не нужно.

Использование:
    python3 recon.py <username>          # снимок: подписчики + последние посты
    python3 recon.py <username> --posts  # только посты, без подписчиков

Для чтения постов нужен fetch_profile.js рядом (npm install перед первым
запуском - тянет пакет threads-api).
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.request

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)"


def parse_follower_count(abbrev):
    """'14.3K' -> 14300, '1.2M' -> 1200000, '842' -> 842. Приближённо - Threads
    сам округляет это число в профиле, точнее анонимно не получить."""
    abbrev = abbrev.strip().upper().replace(",", "")
    m = re.match(r"^([\d.]+)([KM]?)$", abbrev)
    if not m:
        return None
    num = float(m.group(1))
    mult = {"K": 1_000, "M": 1_000_000, "": 1}[m.group(2)]
    return int(num * mult)


def fetch_follower_count(username):
    url = f"https://www.threads.com/@{username}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        html = r.read().decode("utf-8", errors="ignore")
    m = re.search(r'name="description" content="([\d.]+[KM]?) Followers', html)
    if not m:
        raise RuntimeError("не нашла счётчик подписчиков на странице профиля")
    return parse_follower_count(m.group(1))


def fetch_post_view_count(permalink):
    """Просмотры чужого поста лежат прямо в анонимном HTML страницы поста,
    без логина и без библиотеки (устаревшее предположение "видно только
    автору" из статей 2023 года больше не работает - проверено вживую)."""
    if not permalink:
        return None
    req = urllib.request.Request(permalink, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        html = r.read().decode("utf-8", errors="ignore")
    m = re.search(r'"view_counts":(\d+)', html)
    return int(m.group(1)) if m else None


def fetch_posts(username):
    """До ~25-40 последних постов через fetch_profile.js (анонимная библиотека
    threads-api). Честное ограничение: реплаи/репосты/цитаты чужих постов
    Threads анонимному наблюдателю не отдаёт вообще."""
    result = subprocess.run(
        ["node", "fetch_profile.js", username],
        capture_output=True, text=True, timeout=60,
    )
    try:
        data = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        raise RuntimeError(f"скрипт не вернул JSON: {result.stdout[-300:]} {result.stderr[-300:]}")
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "неизвестная ошибка скрипта"))
    return data["posts"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("username", help="username без @")
    ap.add_argument("--posts", action="store_true", help="только посты, без подписчиков")
    ap.add_argument("--views", action="store_true", help="докачать просмотры к каждому посту (медленнее, отдельный запрос на пост)")
    args = ap.parse_args()

    out = {"username": args.username}
    if not args.posts:
        try:
            out["followers"] = fetch_follower_count(args.username)
        except Exception as e:
            out["followers_error"] = str(e)

    posts = fetch_posts(args.username)
    if args.views:
        for p in posts:
            try:
                p["views"] = fetch_post_view_count(p.get("permalink"))
            except Exception as e:
                p["views"] = None
                print(f"не удалось снять просмотры {p.get('permalink')}: {e}", file=sys.stderr)
    out["posts"] = posts

    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
