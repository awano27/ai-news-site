# Zenn / note 二次掲載テンプレート

Hub記事や月次digestを Zenn（エンジニア向け）・note（ビジネス層向け）に転載する際の運用ルールとテンプレ。

## なぜ二次掲載するか

- visionhub.jp だけでは**検索経由の流入しか期待できない**
- Zenn トレンド / note みんなの読み物 は**アルゴリズムで露出**が発生する
- 良質記事は1本で数千PV → 本サイトへの**リファラトラフィックと被リンク**が得られる
- 転載元（canonical）を明記すれば**重複コンテンツペナルティは発生しない**

## 転載ルール

1. **本体公開から 24h 以上経過してから転載**（本体のインデックスを先に確立）
2. **冒頭に「元記事」ブロックを必ず置く**（canonical 表明）
3. **全文転載 OK**（自分の記事なので著作権的には自由）
4. **本文中の内部リンクは可能な限り残す**（visionhub.jp への送客）
5. **図版・コードブロックはそのまま**
6. **最後に「続きを読む → 元記事」のCTA**を追加

## Zenn 用テンプレート（冒頭に貼る）

```markdown
> 📌 **この記事はもともと [visionhub.jp](https://visionhub.jp/) で公開した記事の転載です。**
> 元記事：[記事タイトル](https://visionhub.jp/presentations/hubs/XXXX.html)
> Zenn 用に一部補足を追加しています。記事本体・関連ニュースは元サイトで閲覧できます。

---

（ここに本文）
```

## note 用テンプレート

```markdown
> 💡 **元記事は [visionhub.jp](https://visionhub.jp/) に掲載しています。**
> [記事タイトル](https://visionhub.jp/presentations/hubs/XXXX.html)
> こちらでは note 読者向けに導入を柔らかく書き直しています。

---

（ここに本文）
```

## タグ / トピック選び

| プラットフォーム | 推奨タグ（2〜4 個） |
|---|---|
| Zenn | `AI`, `Claude`, `ChatGPT`, `LLM`, `生成AI` |
| note | `AI`, `生成AI`, `ChatGPT`, `Claude`, `仕事術` |

両方とも**タイトルの先頭 30 字が重要**。Zenn は 60 字、note は 50 字目安。

## 投稿頻度

- **Hub 記事公開時（月 2〜4 本）** → 3 日後に Zenn、1 週間後に note
- **月次 digest 公開時** → 当月末に Zenn のみ

過剰投稿は嫌われる（転載だらけのアカウントは後半伸びない）ので、**本体の良い記事だけ厳選**。

## トラッキング

転載記事の URL を `ops/cross-posts-log.md` にメモ：
```
2026-04-19  zenn.dev/awano27/articles/xxxx  → /presentations/hubs/claude-code-guide-2026.html
2026-04-25  note.com/awano27/n/xxxxxxxx     → /presentations/hubs/ai-model-comparison-2026.html
```

Search Console の「リンク」→「上位のリンク元サイト」で zenn.dev / note.com からの被リンクが確認できます。

## 効果測定

- GA4 で `utm_source=zenn` / `utm_source=note` を URL に付けると流入量が可視化できる
- 例: `https://visionhub.jp/presentations/hubs/claude-code-guide-2026.html?utm_source=zenn&utm_medium=cross_post`
