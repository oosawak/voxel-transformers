# モデル定義の仕様（.vox＋Markdown）

変形ボクセルモデルを、ゲームやビューアで使うための定義の仕方です。
モデルは「.vox のデータ」と「Markdown の定義ファイル」の組で表します。
エンジン側は定義を読んでデータを組み立てるだけなので、モデルを増やすのにプログラムの変更はいりません。

## ファイルの置き方

- `models/<キー>_a.vox`、`<キー>_b.vox`（3形態なら `_c.vox` まで）— MagicaVoxel 形式のモデル本体
- `specs/<キー>.md` — そのモデルの定義ファイル（1モデルに1ファイル）
- `build_models.py` — 定義と .vox から `models-extra.js`（`window.EXTRA_MODELS`）を生成する変換器
- ゲームやビューアは `models-extra.js` を読み込んで使う（Voxel Valkyrie がこの形）

## 定義ファイルの書式

frontmatter（YAML）に書きます。本文は人向けの説明文に使います。

```markdown
---
key: masamune
name: 伊達政宗
order: 51
forms:
  - file: masamune_a.vox
    label: ロボット
    robot: true
  - file: masamune_b.vox
    label: ロボット改
    robot: true
  - file: masamune_c.vox
    label: 竜
    anim: flap
---

# 伊達政宗
説明文（任意）。
```

### 項目

- `key`: モデルの識別子（英小文字と数字）。ファイル名とそろえる
- `name`: 表示名
- `order`: 一覧での並び順
- `forms`: 形態の列。順番に形態ボタンになる
  - `file`: .vox のファイル名（`models/` からの名前）
  - `label`: 形態の表示名
  - `robot: true`: 人型ロボットの形態（関節アニメ＝歩行・構え・敬礼・L字・走行が付く）
  - `anim`: その形態の型アニメ（下の一覧から1つ）。`robot` とはどちらか片方を書く
- `pivot`（任意）: 関節位置の調整（ブロック単位、基準位置からのずらし）
  - `hip`（股）、`shoulder`（肩）、`elbow`（肘）、`armX`（腕の付け根の幅）

### 型アニメの一覧（anim）

- `wave` — うねり（ムカデ、鮭、蛇など長い体）
- `flap` — はばたき（竜、龍、カラスなど翼のある姿）
- `quad_cat` — 四足歩行（虎、獅子）
- `quad_deer` — 四足歩行・速い（鹿）
- `quad_small` — 四足歩行・小さい（狸、狐）
- `quad_monkey` — サルの歩行（前足は交互、後ろ足で蹴る）

## モデルの目安

- 大きさは最長辺で64ボクセル以内（例外は96まで）
- 形態どうしのボクセル数が近いほうが変形が綺麗に見える
- 形は単一のつながった塊にする

## ライセンス

モデルデータ（.vox）、定義ファイル、生成スクリプトは MIT ライセンス（Lyre3 Games）で公開しています。自分のゲームや作品に使えます。
