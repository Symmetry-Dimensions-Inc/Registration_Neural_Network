# DCPCR　(更新箇所特定モジュール)
DCPCR: 大規模屋外環境におけるディープ圧縮ポイントクラウド登録
この作業は、Ubuntuを使用して、RTX 3060 GPUでテストされています。

## 概要
公共交通のバスやタクシー等のモビリティに搭載されたLiDAR等で定常的に取得される点群データや、スマートフォン等で市民が日常的に取得できるデータを活用して、3D都市モデルのデータソースを取得。これに基づきアラインメント・更新箇所検出を行うA.I.モデルを及び3D都市モデルを生成する自動モデリングツールの使用方法を記載したものです。

## モジュール構成
今回、実証開発した3D都市モデル自動生成システムは、大きく4つのモジュールを6つのステップで動作させるものです。
構成モジュールは次の通りです。
* A. 点群アラインメント
* B. LOD2モデルに基づいた点群分割アルゴリズム
* C. メッシュ化
* D. 更新箇所検出 (別リポジトリ)

これらのモジュールは、次のステップで実行されます。

1. 建物のフットプリントを作成する (モジュールB)
2. フットプリントポリゴンの拡張 (モジュールB)
3. 建物の抽出とデータのアラインメント (モジュールA)
4. LiDAR データと LOD2 データの結合 (モジュールA)
5. 更新箇所検出（モジュールD）
6. iPSR アルゴリズムを使用してメッシュを作成する (モジュールC)

このリポジトリではD. 更新箇所検出のモジュールのみを公開しており、その他のモジュールについては別のリポジトリとなります。

## はじめに（Dockerを使った場合）

nvidia-dockerをインストールしてください。

## データ

圧縮されたapolloデータセットを[ここ](https://www.ipb.uni-bonn.de/html/projects/dcpcr/apollo-compressed.zip)からダウンロードして、`/dcpcr/Makefile` を設定することで、データセットをDockerコンテナにリンクさせてください。

```sh
DATA=<path-to-your-data>
```

視覚化と非圧縮データの微調整には、まずapolloデータをダウンロードし、 `/dcpcr/scripts/apollo_aggregation.py` スクリプトを使って密なポイントクラウドを計算する必要があります。これには約500 GBが必要です。圧縮データ上の登録を視覚化することもできますが、低解像度のため、見づらいです。

## Dockerコンテナのビルド

ルートディレクトリで以下を実行して、Dockerコンテナをビルドします。

```sh
make build
```

## コードの実行

最初のステップは、`dcpcr/`の中でDockerコンテナを実行することです。

```sh
make run
```
もし、Dockerコンテナの実行が次のエラーで失敗した場合（--gpuフラグのため）:
> docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]].

[ここ](https://askubuntu.com/questions/1400476/docker-error-response-from-daemon-could-not-select-device-driver-with-capab)で解決策が見つかります。

以下のコマンドは、Dockerコンテナ内で実行することを想定しています。

### トレーニング

ネットワークをトレーニングするには、まずすべてのパラメータを含む設定ファイルを作成する必要があります。  
設定ファイルのサンプルは `/dcpcr/config/config.yaml` にあります。
ネットワークをトレーニングするには、以下を実行してください。

```sh
python3 trainer -c <path-to-your-config>
```

### 評価

テストセットでのネットワークの評価は、以下のように行います。

```sh
python3 test.py -ckpt <path-to-your-checkpoint>
```

すべての結果は、`dcpcr/experiments` のディレクトリに保存されます。圧縮データで微調整するときには `-dt 1` を使用し、非圧縮データの場合は `-dt 5` を使用しました。

### 定性的な結果

`dcpcr/scripts/qualitative` には、結果を視覚化するスクリプトがいくつかあります。

### 事前学習済みモデル

モデルの事前学習済みの重みは、[ここ](https://www.ipb.uni-bonn.de/html/projects/dcpcr/model_paper.ckpt) で見つけることができます。

## はじめに（Dockerを使わない場合）

### インストール

すべての依存関係とインストール手順は、Dockerfileから導出することができます。
`pip3 install -e .` を使用して、dcpcrをインストールしてください。

### コードの実行

スクリプトは、以前と同様にDockerコンテナ内で実行することができます。ただし、`dcpcr/config/data_config.yaml` を更新する必要があるかもしれません。

## 他のポイントクラウドデータでの推論

Apollo以外のデータでモデルをテストするには、以下のスクリプトを実行できます。

データが `.pcd` 形式の場合：
```sh
python inference.py -ckpt [path_to_checkpoint] [optional] -ft False
```
データが `.las` 形式の場合：
```sh
python las_inference.py -ckpt [path_to_checkpoint] [optional] -ft False
```
推論には、事前学習済みの[モデル](https://www.ipb.uni-bonn.de/html/projects/dcpcr/model_paper.ckpt)を使用することをお勧めします。

推論スクリプトは、Dockerコンテナ内で完全には実行できません（open3dの視覚化のため）。登録結果を視覚化したい場合は、これらのスクリプトはDockerコンテナの外で実行する必要があります。

## ポイントクラウドの類似性（建物分類）
`pointcloud_similarity.py` スクリプトは、建物分類タスクを担当しています。このタスクを実行するために、DCPCRとGICPに依存しています。コードの実行方法に関する詳細は、[このリンク](https://github.com/Symmetry-Dimensions-Inc/Registration_Neural_Network/tree/main/documentation)で見つけることができます。

## ライセンス
* 本ドキュメントは[Project PLATEAUのサイトポリシー](https://www.mlit.go.jp/plateau/site-policy/)（CCBY4.0および政府標準利用規約2.0）に従い提供されています。

## 注意事項
* 本レポジトリは参考資料として提供しているものです。動作保証は行っておりません。
* 予告なく変更・削除する可能性があります。
* 本レポジトリの利用により生じた損失及び損害等について、国土交通省はいかなる責任も負わないものとします。

## 参考資料
* （近日公開）技術検証レポート: https://www.mlit.go.jp/plateau/libraries/technical-reports/
