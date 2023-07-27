#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2023 Blacknon. All rights reserved.
# Use of this source code is governed by an MIT license
# that can be found in the LICENSE file.
# NOTE:
#   - 同じ検索エンジンに対してパラレルでクエリ投げると怒られそうなのでシングル実行とする
# =======================================================

import os

from recon.core.module import BaseModule
from pydork.engine import SearchEngine
from urllib.parse import urlparse
from jinja2 import Template

# *_dorks.pyで必要となるテーブル「pages」を作成するSQL
# - pages (TABLE): 検索でヒットしたページ(url)を格納するテーブル
#     - url (TEXT): ページのurl
#     - domain (TEXT): ページのドメイン
#     - title (TEXT): URLのテキスト
#     - text (TEXT): 検索でヒットした際のテキスト
#     - source (TEXT): 検索元URL
#     - query (TEXT): 検索時に使用したクエリ
#     - num (INT): 検索でヒットした順番
#     - module (TEXT): 当該レコードを追加したmodule
CREATE_PAGES_TABLE_SQL = '''\
    CREATE TABLE IF NOT EXISTS pages (
        url TEXT NOT NULL,
        domain TEXT,
        title TEXT,
        text TEXT,
        source TEXT,
        query TEXT,
        num INT,
        module TEXT
    )
'''

# *_dorks.pyで使用するcommon options.
DORKS_OPTIONS = (
    # querylist:
    #     検索エンジンに投げるクエリテンプレートファイルのPATH.
    (
        'querylist',
        os.path.join(BaseModule.data_path, 'dork_template.txt'),
        True,
        'path to query template list file.'
    ),
    # use_selenium:
    #     検索時にSeleniumを利用するかどうか
    (
        'use_selenium',
        True,
        True,
        'use Selenium'
    ),
    # selenium_endpoint:
    #     Seleniumを利用する際のendpoint.
    #     デフォルト値は環境変数`SELENIUM_ENDPOINT_URI`から取得させる.
    (
        'selenium_endpoint',
        os.environ.get('SELENIUM_ENDPOINT_URI'),
        True,
        'Specify the endpoint for headless browsers such as Selenium.'
    ),
    # num:
    #     検索エンジンから取得する件数.
    (
        'num',
        300,
        True,
        'Specify the number of search results to retrieve.'
    ),

)


def template_expand(template_data: str, variables: dict):
    """template_expand

    jinja2のテンプレートを展開する関数.

    Args:
        - template_data (str): 展開するjinja2のテンプレートデータ.
        - variables (dict): テンプレートデータに適用するデータ(ex. {"domain": "hogefuga.com"})

    Returns:
        - result (str): variablesの内容を適用したtemplateデータ
    """
    # レンダリング処理を実行
    tmpl = Template(template_data)
    result = tmpl.render(variables)

    return result


class Module(BaseModule):
    # metaデータ
    meta = {
        'name': 'multiplue harvester from [duckduckgo.com](https://www.duckduckgo.com/).',
        'author': 'blacknon - blacknon@orebibou.com',
        'version': '0.1',
        'description': '',
        'options': DORKS_OPTIONS,
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
        'dependencies': ['pydork'],
    }

    def __init__(self, params):
        super().__init__(params)

        # pagesテーブルが存在していない場合は作成
        self.query(CREATE_PAGES_TABLE_SQL)

    def module_run(self, domains):
        # templateファイルを開き、データを取得する
        template_data = ""
        with open(self.options['querylist']) as fp:
            template_data = fp.read()

        # search_engineを生成
        search_engine = SearchEngine()
        search_engine.set('duckduckgo')

        # optionsの指定
        # seleniumの指定(browserはfirefoxで決めうち)
        use_selenium: bool = self.options['use_selenium']
        if use_selenium:
            selenium_endpoint: str = self.options['selenium_endpoint']
            search_engine.set_selenium(selenium_endpoint, 'firefox')

        for domain in domains:
            self.heading(domain, level=0)

            # templateに適用するdictを生成
            template_variables = {"domain": domain}

            # templateを展開
            query_data = template_expand(template_data, template_variables)
            query_list = query_data.splitlines()

            for query in query_list:
                search_results = search_engine.search(
                    query, maximum=self.options['num'])

                for sr in search_results:
                    sr_url = sr['link']

                    # url
                    self.do_info(sr_url)

                    pages_data = {
                        'url': sr_url,
                        'domain': domain,
                        'title': sr['title'],
                        'text': sr['text'],
                        'source': sr['source_url'],
                        'query': query,
                        'num': sr['num'],
                        'module': self._modulename
                    }

                    # pages
                    self.insert(
                        'pages',
                        pages_data,
                        unique_columns=['url']
                    )

                    # hosts
                    self.insert_hosts(
                        urlparse(sr_url).hostname
                    )
