#!/usr/bin/env bash
# Copyright(c) 2023 Blacknon. All rights reserved.
# Use of this source code is governed by an MIT license
# that can be found in the LICENSE file.
# =============================================

# module配置用ディレクトリ(決め打ち)
RECON_DIR=~/.recon-ng

# moduleとして扱うファイルのリストを生成
#   NOTE: ./modules配下のpythonファイルを雑に投入している
files_list=($(find ./modules -name "*.py" -not -wholename "*/__pycache__/*"))

# files_listで見つかっているファイルをコピーしていく
for file in ${files_list[@]};do
    echo "copy :${file}" >& 2
    # `modules/` 配下のdirectory名を取得
    dir_name=$(dirname "${file}")
    file_name=$(basename "${file}")

    # `$MODULES_DIR` 配下にディレクトリを生成
    mkdir -p "${RECON_DIR}/${dir_name}"

    # moduleファイルのコピー
    cp "${file}" "${RECON_DIR}/${dir_name}"

    # 配置状況の確認
    ls -la "${RECON_DIR}/${dir_name}/${file_name}"
done

# keys.txtのキー名をkeys.dbに登録する
keys_list=($(cat keys.txt | grep -Ev -e"^#" -e"^$"))
for key in ${keys_list};do
    echo "INSERT or IGNORE INTO keys (name) VALUES (\"${key}\");" | sqlite3 "${RECON_DIR}/keys.db"
done

# dataの内容をコピーする
cp -r ./data/* "${RECON_DIR}/data/"
