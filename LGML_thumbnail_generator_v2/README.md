# BlogHeader画像等をAEテンプレートから作成する ver.2

## ツール動作仕様概要

テンプレートにコンテンツ内容を流し込み、サムネイル画像などを出力するコマンド。
tomlファイルを含むフォルダのパスを引数で受け付ける。

## テンプレートフォルダに含むファイル

* template.aep
* bg.png （ダミー用 任意）
* icon01.png, icon02.png, icon03.png, icon04.png, icon05.png （ダミー用 任意）
* icon01.png, icon02.png, icon03.png, icon04.png, icon05.png （ダミー用 任意）
* info.json （ダミー用 任意）
* その他追加アセット 任意の名前

## コンテンツフォルダに含むファイル
 
* config.toml (必須)
* bg.png (必須)
* icon01.png, icon02.png, icon03.png, icon04.png, icon05.png （任意）

## tomlファイルの内容

tomlファイルには以下の情報が含まれる。

* テンプレートフォルダパス
* タイトル文言　(必須)
* テキスト文言　(必須)
* 画像サイズ指定　(任意)
  * ブログ用ヘッダー画像サイズは 640x427 Youtube用サムネイルサイズは 1280×720
* 画像出力フォルダ　(任意)
* 画像出力ファイル名　(任意)
  * 拡張子で出力フォーマットを指定 png / jpeg
* work_dir (開発用)　(任意)
* 現在使っているAfterEffectsの西暦表記部分 ex)2023　(任意)

## デザイン面のレギュレーション

* カラー値やフォント定義などデザインに関する情報をjsonファイルに含めない。テンプレート側にデザインを配置する。
* 背景画像は少し彩度を落とす、テンプレート側で対応する。
* テンプレートはモノクロ＋テーマカラーひとつを基本とする。
* アイコンの色味や形状に関してはバラツキを認める。

## 処理の流れ

### python による前処理

* batファイル + pythonで実装 batファイルへはコンテンツフォルダのドラッグドロップをサポートするため。
* テンプレートフォルダを一時ワークフォルダにコピーする。
* ワークフォルダのアイコン画像ファイルは透明な物で5つとも上書き、または新規作成する。
* コンテンツフォルダのファイルをワークフォルダーに全てコピーする。
* タイトル・テキスト文言を含んだjsonファイルを動的に生成、ワークフォルダに配置する。
* AEのレンダリングをキックする

### AE処理

* 背景画像、アイコン画像を相対読み込みする。
* 文言はjsonから読み込む。
* 第一フレームをレンダリングする

### python による後処理

* 出力された画像サイズをリサイズする。
  * 縦横比率が合わない場合、トリムする。※ 現状ただのリサイズでトリムしていない
* 出力フォーマット指定がpng以外の場合、変換をかける。
* 出力された画像をtomlで指定されたフォルダ・ファイル名でコピーする。
  * 出力フォルダの指定がなければコンテンツフォルダの横に出力する。
  * 出力ファイル名の指定が泣ければテンプレート名とする。
* 一時ワークフォルダを破棄する。