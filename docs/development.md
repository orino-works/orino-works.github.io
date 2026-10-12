# サイトの構成と更新

公開URL： https://orino-works.github.io/

- Hugo 0.167.0。外部テーマ・サブモジュール・npm・JavaScriptは使わない。
- `content/`：公開記事・固定ページ。URLはフロントマターで管理する。
- `layouts/`：自作のテンプレート。`assets/css/`：日本語のレスポンシブCSS。
- `hugo.toml`：名称、説明、公開URL、承認済みの連絡先。
- `.github/workflows/pages.yml`：PRはビルド・検査のみ。mainへの反映でビルド・Pages公開。
- `scripts/check_site.py`：生成HTMLのリンク、見出し、SEO、公開不要ファイル・秘密情報・未承認解析の検査。

## ローカル確認

```sh
hugo --gc --minify
python3 scripts/check_site.py public
```

同じHugo版を使う。公開用`public/`はコミットしない。自動検査に加え、原稿・出典・差分を人または編集担当が確認する。公開後のHTTP・実表示は別途確認する。

## GitHub Pagesの初期設定

管理者がSettings → Pages → Build and deployment → Sourceを **GitHub Actions** にする。
連携ツールが設定できない場合に限り、運営者へこの操作を依頼する。mainへの反映後にActionsの結果と実際のURLを確認する。デプロイ失敗だけで「公開済み」と扱わない。

## 名称・お問い合わせ・解析

サイト名は`hugo.toml`のtitleを変更する。お問い合わせは運営者の承認後にcontactEmailまたはcontactURLの一方を設定する。同時にprivacy.mdの受付情報を実際の処理に合わせて改訂する。GitHub Issuesへの導線も未承認では設定しない。

GA4/GSCの仮IDや、外部広告コードは入れない。導入時にプライバシー・広告表示と方針ページを同じPRで修正する。

## 安全性と保守

Actionsは公式アクションのコミットSHAを固定。Hugoの配布物もSHA256で照合する。通常の更新では新バージョンと公式情報を確認し、ビルドしてから固定値を変更する。
ビルドはcontents:read、公開ジョブだけpages:writeとid-token:write。個人トークンは使わない。
キャッシュなし、公開アーティファクト保存1日。PrivateリポジトリのCIは追加しない。

公開リポジトリには公開用のコード・内容だけを置く。非公開調査や顧客資料、個人情報をコピーしない。
