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

import json
import tld

from recon.core.module import BaseModule


class Module(BaseModule):
    # metaデータ
    meta = {
        'name': 'import from [pydork](https://github.com/blacknon/pydork) result json.',
        'author': 'blacknon - blacknon@orebibou.com',
        'version': '0.2',
        'description': '',
        'options': (
            ('filename', None, True, 'path and filename for list input'),
            ('domain', None, False, 'domain'),
        ),
        'dependencies': ['tld'],
    }

    def module_run(self):
        with open(self.options['filename'], 'rt') as f:
            file_data = f.read()

        try:
            # fileをjsonとして読み込み
            data = json.loads(file_data)

            # pydorkのjsonとしてデータをパースしていく
            for engine, query_results in data.items():
                for query_result in query_results:
                    query = query_result['query']
                    results = query_result['result']
                    if len(results) > 0:
                        for r in results:
                            pages_data = {
                                'url': r['link'],
                                'title': r['title'],
                                'text': r['text'],
                                'source': r['source_url'],
                                'query': query,
                                'num': r['num'],
                                'engine': engine,
                                'module': self._modulename
                            }

                            if self.options.get('domain') is not None:
                                pages_data['domain'] = self.options.get(
                                    'domain')
                            else:


                            self.insert(
                                'pages',
                                pages_data
                            )

            if self.options.get('domain') is not None:
                self.insert_domains(
                    self.options.get('domain')
                )

        except Exception as e:
            self.error(e)
