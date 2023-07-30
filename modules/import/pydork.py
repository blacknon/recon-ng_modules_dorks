#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2023 Blacknon. All rights reserved.
# Use of this source code is governed by an MIT license
# that can be found in the LICENSE file.
# =======================================================

"""pydork.py

全検索エンジンに対して処理を行うモジュール.
また、本リポジトリ内全体で必要となる処理をまとめて実施させる(例: テーブル作成など).
"""

from recon.core.module import BaseModule


class Module(BaseModule):
    # metaデータ
    meta = {
        'name': 'import from [pydork](https://github.com/blacknon/pydork) result json.',
        'author': 'blacknon - blacknon@orebibou.com',
        'version': '0.1',
        'description': '',
        'options': (
            ('filename', None, True, 'path and filename for list input'),
        ),
        'dependencies': ['pydork'],
    }

    def module_run(self):
        with open(self.options['filename'], 'rt') as f:
            data = f.read()

        for d in data:
            self.verbose(d)
