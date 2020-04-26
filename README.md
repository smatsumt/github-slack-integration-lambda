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

"Slack メンバー ID" は "U3KFKE98F" といった文字列です。ユーザ名ではありません（Slack API の仕様変更で、メンションをするにはメンバーIDが必須になりました。）
メンバー ID は、各ユーザのプロフィールから調べることができます。設定ファイルでは先頭に "@" をつけるようにしてください。

初回はいくつかの設定項目が聞かれます。"SlackURL" には、通知を飛ばすチャンネル用の Slack WebHook URL を指定してください。

設定をやり直す場合は、

```shell
make reconfigure
```

を実行してください。

### GitHub 設定方法

1. "WebHook" を追加します。
1. "WebHook" を設定します。
    1. "Payload URL" に、デプロイ時に出てくる "GitHubHookURL" の値を設定してください。
    1. "Content Type" には "application/json" を指定してください。
    1. "Which events would you like to trigger this webhook?" には、"Let me select individual events." を選び、"Issue comments", "Issues", "Pull requests", "Pull request reviews", "Pull request review comments" にチェックを入れてください。

