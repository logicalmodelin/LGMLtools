# LGML_DummyImageCreator

ダミー画像を大量に生成してくれるやつです。

Pillowが必要です。Python3のいくつかで動きます。

基本的な機能

* 画像サイズ指定可能
* 画像の枚数指定可能
* ファイル名の接頭語、接尾語コントロール
* 生成枚数の指定
* 画像フォーマット指定（PILの扱えるもののみ）

その他の機能

* タイトル文字指定可能
* 背景色指定可能
* 指定ない場合、文字色は背景色の補色に
* 右下に追加文字指定可能

外部フォント読み込みたくないので以下の制限があります。

* テキストの大きさとフォント指定不可
* 日本語使用不可

コマンドヘルプそのまま

```
usage: ダミー画像を生成する。

適当な数とサイズでダミー画像を作ります。

positional arguments:
  output_path           画像をアウトプットするフォルダ
  width                 出力画像の横幅
  height                出力画像の高さ

optional arguments:
  -h, --help            show this help message and exit
  -n NUMBER_OF_IMAGE, --number_of_image NUMBER_OF_IMAGE
                        出力画像数
  -p PREFIX, --prefix PREFIX
                        出力画像名の接頭語
  -s SUFFIX, --suffix SUFFIX
                        出力画像名の接尾語
  -fmt FORMAT, --format FORMAT
                        エクスポート画像フォーマットの指定
  -c COLOR, --color COLOR
                        色の指定(16進数6文字)
  -t TITLE, --title TITLE
                        画像に埋め込むタイトル文字 英語のみ
  --text_contents TEXT_CONTENTS
                        画像右下に埋め込む本文文字 英語のみ
  --force               上書き確認せずファイルを書き出すか
```

コマンド例

* `py LGML_DummyImageCreator.py work 720 360 -t "Hi there," --force -c 000066 -tc 555555 --text_contents "How do you do today?"`
* `py LGML_DummyImageCreator.py work 128 128 -n 2 --force -c ffffCC -fmt jpg`
* `py LGML_DummyImageCreator.py work 640 427 --force -c eeffff -t "[DUMMY IMAGE CREATOR]\n{w}px / {h}px" -p header_ --text_contents "Creates dummy images easily."`
* `py LGML_DummyImageCreator.py work 1280 720 --force -c eeeeee -t "[HD SIZE]" -p hd_ --text_contents "A snake sneaks to seek a snack."`





