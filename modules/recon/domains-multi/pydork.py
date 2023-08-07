#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2023 Blacknon. All rights reserved.
# Use of this source code is governed by an MIT license
# that can be found in the LICENSE file.
# =======================================================

"""searchengine_dorks.py

検索エンジンに対し、ドメインをキーとした検索を行うためのモジュール.
"""

import os

from recon.core.module import BaseModule
from recon.mixins.threads import ThreadingMixin

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
#     - engine (TEXT): 検出した検索エンジン
#     - module (TEXT): 当該レコードを追加したmodule
CREATE_PAGES_TABLE_SQL = '''
    CREATE TABLE IF NOT EXISTS pages (
        url TEXT NOT NULL,
        domain TEXT,
        title TEXT,
        text TEXT,
        source TEXT,
        query TEXT,
        num INT,
        engine TEXT,
        module TEXT
    )
'''

# *_dorks.pyで使用するcommon options.
DORKS_OPTIONS = (
    # querylist:
    #     検索エンジンに投げるクエリテンプレートファイルのPATH.
    (
        'querylist',
        os.path.join(BaseModule.data_path, 'domain_template.txt'),
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
    # enable_baidu:
    #     baidu.comからの検索を有効にする.
    #     あまり中国への検索をすると面倒なことになるため、デフォルトでは無効としている.
    (
        'enable_baidu',
        False,
        True,
        'Search from yahoo.co.jp'
    ),
    # enable_bing:
    #     bing.comからの検索を有効にする
    (
        'enable_bing',
        True,
        True,
        'Search from bing.com'
    ),
    # enable_duckduckgo:
    #     duckduckgo.comからの検索を有効にする
    (
        'enable_duckduckgo',
        True,
        True,
        'Search from duckduckgo.com'
    ),
    # enable_google:
    #     google.comからの検索を有効にする.
    #     なお、同一IPからのアクセス数が多いとReCaptchaに飛ばされる可能性が非常に高いためデフォルトでは無効としている.
    (
        'enable_google',
        False,
        True,
        'Search from google.com'
    ),
    # enable_yahoo:
    #     yahoo.co.jpからの検索を有効にする
    (
        'enable_yahoo',
        True,
        True,
        'Search from yahoo.co.jp'
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


class Module(BaseModule, ThreadingMixin):
    # metaデータ
    meta = {
        'name': 'multiplue harvester from Search Engines.',
        'author': 'blacknon - blacknon@orebibou.com',
        'version': '0.2',
        'description': 'multiplue harvester from Search Engines.',
        'options': DORKS_OPTIONS,
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
        'comments': (
            'NOTE: Search subdomain SQL: `SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL`. '
            '      Search ip address SQL: `SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL`. '
        ),
        'dependencies': ['pydork'],
    }

    def __init__(self, params):
        super().__init__(params)

        # pagesテーブルが存在していない場合は作成
        self.query(CREATE_PAGES_TABLE_SQL)

    def module_run(self, domains):
        # 有効になっている検索エンジンを取得する
        engines = list()
        if self.options['enable_baidu']:
            engines.append('baidu')
        if self.options['enable_bing']:
            engines.append('bing')
        if self.options['enable_duckduckgo']:
            engines.append('duckduckgo')
        if self.options['enable_google']:
            engines.append('google')
        if self.options['enable_yahoo']:
            engines.append('yahoo')

        # 有効になっている検索エンジンがない場合はエラー
        if len(engines) == 0:
            self.error('There is no search destination specified.')

        # templateファイルを開き、データを取得する
        template_data = ""
        with open(self.options['querylist']) as fp:
            template_data = fp.read()

        for domain in domains:
            self.heading(domain, level=0)

            # templateに適用するdictを生成
            template_variables = {"domain": domain}

            # templateを展開
            query_data = template_expand(template_data, template_variables)
            query_list = query_data.splitlines()

            for query in query_list:
                for engine in engines:
                    try:
                        self.module_thread(engine, domain, query)
                    except Exception as e:
                        self.alert(e)

    def module_thread(self, engine, domain, query: str):
        # search_engineを生成
        search_engine = SearchEngine()
        search_engine.set(engine)

        # optionsの指定
        # seleniumの指定(browserはfirefoxで決めうち)
        use_selenium: bool = self.options['use_selenium']
        if use_selenium:
            selenium_endpoint: str = self.options['selenium_endpoint']
            search_engine.set_selenium(selenium_endpoint, 'firefox')

        if self.options.get('PROXY') is not None:
            search_engine.set_proxy(self.options['PROXY'])

        search_results = search_engine.search(
            query, maximum=self.options['num'])

        for sr in search_results:
            sr_url = sr['link']

            pages_data = {
                'url': sr_url,
                'domain': domain,
                'title': sr['title'],
                'text': sr['text'],
                'source': sr['source_url'],
                'query': query,
                'num': sr['num'],
                'engine': engine,
                'module': "{0}({1})".format(self._modulename, engine)
            }

            self.verbose(f"Hit {engine} search: {sr_url}")

            # pages
            rowcount = self.insert(
                'pages',
                pages_data,
                unique_columns=['url']
            )
            self._display(pages_data, rowcount)

            # hosts
            self.insert_hosts(
                urlparse(sr_url).hostname
            )
