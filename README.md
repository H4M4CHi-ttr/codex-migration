# codex-migration

Codexのチャット・プロジェクト・作業ファイルを、履歴と権限を保ちながら移行するためのAgent Skillです。OneDriveからの移動記録をもとに、移行先や対象が変わっても使える判断手順をまとめました。

Agent skill for moving local Codex workspaces and chat state while preserving history, permissions, and relationships. Includes a migration playbook and read-only probes; live changes are prepared and validated for the detected Codex build.

## Codexからインストールする

Codexで次のように依頼してください。

```text
$skill-installer https://github.com/H4M4CHi-ttr/codex-migration/tree/main/skills/codex-migration をインストールして
```

インストール後は次のターンから `$codex-migration` を指定できます。環境によって一覧に反映されない場合はCodexを再起動してください。

手動で導入する場合は、このリポジトリを取得し、`skills/codex-migration` フォルダをCodexが検出するユーザースキルの場所へコピーしてください。公式ドキュメントでは `~/.agents/skills` が案内されています。組み込みインストーラーは `$CODEX_HOME/skills`（未設定なら `~/.codex/skills`）を使います。同名スキルを両方に置くと重複するため、どちらか一方を使ってください。

## 移行したい内容をそのまま依頼する

```text
$codex-migration OneDrive内のCodex作業フォルダをD:\work\Codexへ移し、既存チャットも新しい場所を参照するようにして。archiveフォルダは対象外。元データは残して。
```

```text
$codex-migration このプロジェクトだけ別のドライブへ移したい。まず影響と移行計画を調べて。変更はしないで。
```

```text
$codex-migration 別のPCへCodexのローカルチャットと作業ファイルを移したい。移行先には既存データがあるので、衝突を調べてから進めて。
```

```text
$codex-migration 以前の移行が途中で止まった。作業記録と現在の状態を調べ、履歴を失わずに再開できるか確認して。
```

移行元・移行先が分かれば、対象の調査、方式の選択、コピー検証、参照更新、復旧準備を進めます。未解決の重要な選択がある場合だけ確認します。調査だけの依頼ではデータを変更しません。

## ファイルのコピーと保存参照の更新を分けて検証する

| 目的 | スキルが扱う内容 |
| --- | --- |
| 作業フォルダを移す | 対象・除外・リンクを調べ、コピーと差分を検証する。 |
| 既存チャットを新しい場所へ向ける | cwd、複数ルート、権限、プロジェクト所属、UIや設定の参照を調べる。 |
| 古いパスも使えるようにする | 条件が合えばジャンクションやシンボリックリンクを検討する。 |
| 保存領域やPCを変える | `CODEX_HOME`、外部ファイル、起動元の設定、移行先との衝突を確認する。 |
| 移行を再開・復旧する | マニフェスト、ジャーナル、現在のハッシュから復旧可能な変更を特定する。 |

チャット本文のパスを一括置換すると、過去の記録まで変わります。スキルでは変更対象のIDとパス項目を限定し、会話履歴、親子・分岐関係、モデル設定、許可・拒否ルール、ネットワーク設定、対象外データを保持する条件を設けています。

過去に成功したオフライン編集はCodex 0.160.0向けの個別処理でした。このリポジトリではその固定パス付きスクリプトを配布せず、実行中のバージョンと保存形式に合わせて手順を検証します。一般の再開APIや設定更新APIも、副作用を確認してから使います。

## 補助スクリプトは調査だけを行う

Python 3.11以上があれば、追加パッケージなしで利用できます。移行手順そのものはPythonがなくても読み、環境にあるツールで進められます。

```powershell
python skills/codex-migration/scripts/migration_probe.py map-path --style windows --mapping 'C:\old\project' 'D:\work\project' --path 'C:\old\project\src'
python skills/codex-migration/scripts/migration_probe.py inspect-state --database 'D:\migration-snapshot\state_5.sqlite' --old-root 'C:\old\project' --style windows
```

`map-path` は区切り境界、最も長く一致する移行元、対象外パスを考慮します。`inspect-state` は指定したSQLiteの構造とcwdが一致する候補を返します。タイトル、本文、認証情報、権限の値は出力しません。移行・削除・設定更新のコマンドはありません。

調査には整合したスナップショットを使ってください。稼働中DBの読み取りは、複数ファイルの同時点の状態を保証しません。cwdの候補一覧だけでは、プロジェクトルートや権限内の参照まで調べ終えたことにはなりません。出力されるパスやIDも私的な情報として扱ってください。

## 検証範囲と制約

```text
python -m unittest discover -s tests -v
```

合成データで、パス境界・除外・Windows/POSIX形式・SQLiteの調査を検証します。GitHub ActionsでもWindowsとLinuxで同じテストを実行します。利用者の実データに対する移行や、すべてのCodexバージョンとの互換性を保証するテストではありません。

共有の書き手を止めて排他を取れない場合、保存データの編集は行えません。移行中の競合や未知の追記があれば自動復旧を止め、現在のデータを残します。ChatGPTのクラウド会話をCodexへ変換する機能、異なるアカウントの履歴を自動で統合する機能は含みません。

手順の詳細は [SKILL.md](skills/codex-migration/SKILL.md)、実例の根拠と限界は [移行記録の要約](skills/codex-migration/references/observed-case.md) を参照してください。問題を報告する場合は [Issues](https://github.com/H4M4CHi-ttr/codex-migration/issues) を使い、会話本文、実DB、認証情報、個人の絶対パスは添付しないでください。

MIT License。OpenAI公式の移行ツールではありません。スキルの構成と保存場所の案内は [公式のスキルガイド](https://learn.chatgpt.com/docs/build-skills) と [設定・保存領域の説明](https://learn.chatgpt.com/docs/config-file/config-advanced) を参照しています。
