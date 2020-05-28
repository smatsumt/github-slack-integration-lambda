# GitHub - Slack Integration with AWS Lambda

GitHub で以下のイベントが発生したときに、Slack にメンション付きメッセージを飛ばします。

- Issue, PR の本文・コメントでメンションされた
- review がリクエストされた
- review が返ってきた

AWS Lambda / API Gateway を利用しています。CloudFormation により、必要なリソースが一通りデプロイされるようにしています。

## セットアップ

### デプロイ方法

```shell
cp config-sample.json config.json
vi config.json  # GitHub ユーザ名 -> Slack メンバーID の対応を設定してください
make
```

成功すれば、"GitHubHookURL"  が画面に出力されます。

"Slack メンバー ID" は "U3KFKE98F" といった文字列です。ユーザ名ではありません（Slack API の仕様変更で、メンションをするにはメンバーIDが必須になりました。）
メンバー ID は、各ユーザのプロフィールから調べることができます。設定ファイルでは先頭に "@" をつけるようにしてください。

初回はいくつかの設定項目が聞かれます。"SlackURL" には、通知を飛ばすチャンネル用の Slack WebHook URL を指定してください。

設定をやり直す場合は、

```shell
make reconfigure
```

を実行してください。

### GitHub 設定方法

#### いくつかのリポジトリに設定する場合 (GitHub App として登録)

1. GitHub App の登録画面に進む
    1. 右上のユーザアイコンをクリックし、出てくるメニューから "Settings" をクリック
    1. 左側のメニューから "Developer settings" をクリック
    1. “New GitHub App” をクリック
1. GitHub App の設定
    1. “Git Hub App name” は適当につける
    1. “Webhook URL” に “(デプロイ時に出力される GitHubHookURL)” を設定
    1. “Repository permissions” で “Issue”, “Pull Request” を “Read-ony” に設定
    1. “Subscribe to events” に “Issue comment”, "Issues", "Pull request", "Pull request review", "Pull request review comment" をチェック
    1. "Create GitHub App" をクリック
1. private key の生成を促されるので、生成する
1. 通知を有効にするリポジトリに、設定した GitHub App をインストール
    1. 右上のユーザアイコンをクリックし、出てくるメニューから "Settings" をクリック
    1. 左側のメニューから "Developer settings" をクリック
    1. 先程作った App があるので、"Edit" をクリック
    1. 左側のメニューから "Install App" をクリック
    1. インストールするリポジトリを選択

#### 単発のリポジトリにのみ設定 (リポジトリの WebHook として登録)

1. "WebHook" を追加
1. "WebHook" の設定
    1. "Payload URL" に、“(デプロイ時に出力される GitHubHookURL)” の値を設定してください。
    1. "Content Type" には "application/json" を指定してください。
    1. "Which events would you like to trigger this webhook?" には、"Let me select individual events." を選び、"Issue comments", "Issues", "Pull requests", "Pull request reviews", "Pull request review comments" にチェックを入れてください。

## 参考情報

- Slack メッセージのフォーマット関連
    - [Sending messages using Incoming Webhooks \| Slack](https://api.slack.com/messaging/webhooks#)
    - [Creating rich message layouts \| Slack](https://api.slack.com/messaging/composing/layouts#attachments)
    - [Reference: Secondary message attachments \| Slack](https://api.slack.com/reference/messaging/attachments)
