# LGML_DummyImageCreator

ダミー画像を大量に生成してくれるやつです。 
Pillowが必要です。Python3のいくつかで動きます。

## 基本的な機能

* 画像サイズ指定可能
* 画像の枚数指定可能
* ファイル名の接頭語、接尾語コントロール
* 生成枚数の指定
* 画像フォーマット指定（PILの扱えるもののみ）

## その他の機能

* タイトル文字指定可能
* 背景色指定可能
* 指定ない場合、文字色は背景色の補色に
* 中央に画像連番文字配置
* 右下に追加文字指定可能

## 注意点

* 文字列に改行埋め込み時は文字列引数を ”” でくくって下さい。

外部フォント読み込みたくないので以下の制限があります。

* テキストの大きさとフォント指定不可
* 日本語使用不可

# 更新履歴

* 2022/12/3 v1.1
  * バージョン表記を追加
  * 画面中央文字列の指定が可能に
  * 画像の中央にデフォルトで連番を表示・ななめ線描画の廃止
  * 連番数値の0のパディング数指定が可能、ファイル名にも有効
  * 各文字列で画像サイズの変数埋め込みと改行に対応
  * その他デザイン調整

* 2022/12/2 v1.0
  * 初回リリース


# コマンドヘルプ

```
usage: LGML_DummyImageCreator.py [-h] [-n NUMBER_OF_IMAGE] [-p PREFIX]
                                 [-s SUFFIX] [-fmt FORMAT] [-c COLOR]
                                 [-tc TEXT_COLOR] [-t TITLE]
                                 [-zp ZERO_PADDING]
                                 [--center_text CENTER_TEXT]
                                 [--bottom_contents BOTTOM_CONTENTS] [--force]
                                 [-V]
                                 output_path width height

指定された枚数とサイズでダミー画像を生成します。 テキスト系の指定は英語のみで、{i}は連番番号に{w}は横幅に{h}は縦幅に変換されます。
で改行指定も可能です。

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
  -tc TEXT_COLOR, --text_color TEXT_COLOR
                        文字色の指定(16進数6文字) 指定ない場合背景色の補色
  -t TITLE, --title TITLE
                        画像に埋め込むタイトル文字
  -zp ZERO_PADDING, --zero_padding ZERO_PADDING
                        画像INDEX番号を0でうめる桁数。
  --center_text CENTER_TEXT
                        画像中央に埋め込む文字
  --bottom_contents BOTTOM_CONTENTS
                        画像右下に埋め込む文字
  --force               上書き確認せずファイルを書き出すか
  -V, --version         show program's version number and exit
```

# コマンド例

* `python LGML_DummyImageCreator.py work 128 128 -n 2 --force -c ffffCC -fmt jpg`
* `python LGML_DummyImageCreator.py work 720 360 -t "Hey, dude." --force -c 000066 -tc 555555 --bottom_contents "What's up, dude?"`
* `python LGML_DummyImageCreator.py work 640 427 --force -c eeffff -t "[DUMMY IMAGE CREATOR]\n{w}px * {h}px" -p "header_" --bottom_contents "Creates dummy images easily."`
* `python LGML_DummyImageCreator.py work 1280 720 --force -c eeeeee -t "[HD SIZE]" -p hd_ --bottom_contents "A snake sneaks to seek a snack."`
* `python LGML_DummyImageCreator.py work 640 427 --force -c fff8ee -t "How much wood would\na woodchuck chuck" --center_text "Images\n#{i}" -p "sample_" --bottom_contents "if a woodchuck could\nchuck wood?"`


