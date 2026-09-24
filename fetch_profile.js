#!/usr/bin/env node
/**
 * Разведка: тянет посты чужого публичного Threads-аккаунта БЕЗ логина (та же
 * библиотека, что проверена на асассине). Честное ограничение: анонимный
 * доступ даёт только текст/дату/лайки/ссылку на пост - реплаи/репосты/цитаты
 * чужих постов Threads анонимному наблюдателю не отдаёт вообще (в отличие от
 * официального API для СВОЕГО аккаунта). Печатает один JSON в stdout.
 * Использование: node fetch_profile.js <username>
 */
const { ThreadsAPI } = require("threads-api");

async function main() {
  const username = process.argv[2];
  if (!username) {
    console.log(JSON.stringify({ ok: false, error: "не указан username" }));
    process.exit(1);
  }
  const api = new ThreadsAPI({ verbose: false });
  try {
    const userID = await api.getUserIDfromUsername(username);
    if (!userID) throw new Error("не нашла такой аккаунт");
    const threads = await api.getUserProfileThreads(userID);

    const posts = (threads || []).map((t) => {
      const item = t.thread_items ? t.thread_items[0] : t;
      const post = item.post || item;
      return {
        post_id: String(post.pk || post.id || ""),
        text: post.caption ? post.caption.text || "" : "",
        timestamp: post.taken_at ? post.taken_at * 1000 : null,
        permalink: post.code ? `https://www.threads.com/@${username}/post/${post.code}` : null,
        likes: post.like_count || 0,
      };
    }).filter((p) => p.post_id);

    console.log(JSON.stringify({ ok: true, username, posts }));
  } catch (e) {
    console.log(JSON.stringify({ ok: false, error: e.message || String(e) }));
    process.exit(1);
  }
}

main();
