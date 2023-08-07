#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2023 Blacknon. All rights reserved.
# Use of this source code is governed by an MIT license
# that can be found in the LICENSE file.
# =======================================================


import os
import xlsxwriter

from recon.core.module import BaseModule


class Module(BaseModule):
    meta = {
        'name': 'Reports the contents of the pages table to an xlsx file with separate sheets for each domain.',
        'author': 'blacknon - blacknon@orebibou.com',
        'version': '0.2',
        'description': 'Reports the contents of the pages table to an xlsx file with separate sheets for each domain.',
        'options': (
            (
                'filename',
                os.path.join(BaseModule.workspace, 'pages_report.xlsx'),
                True,
                'output file path.'
            ),
        ),
        'comments': (
            ''
        ),
        'dependencies': ['XlsxWriter'],
    }

    def module_run(self):
        # ファイル名を指定
        filename = self.options['filename']

        # 指定されたPATHが存在している場合、エラーとする
        if os.path.exists(filename):
            self.error("file exists.")
            return

        # 新規でxlsxファイルを作成する
        with xlsxwriter.Workbook(filename, {'strings_to_urls': False}) as workbook:
            header_format = workbook.add_format({'bold': True})
            cell_format = workbook.add_format()
            cell_format.set_valign('top')

            domain_list = list()
            domain_table_list = self.query('SELECT DISTINCT domain FROM pages')

            for domain_table_row in domain_table_list:
                domain_list.append(domain_table_row[0])

            for domain in domain_list:
                sheet_name = domain.split(":")[0]

                if len(sheet_name) > 30:
                    sheet_name = sheet_name[0:28]

                worksheet = workbook.add_worksheet(sheet_name)

                pages = self.query(
                    'SELECT DISTINCT url, title, TEXT, source FROM pages WHERE domain == ?',
                    (domain,)
                )

                # headerを追記
                header = [
                    'URL',
                    'TITLE',
                    'TEXT',
                    'SOURCE',
                ]
                for h in range(0, len(header)):
                    worksheet.write(0, h, header[h], header_format)

                for r in range(0, len(pages)):
                    for c in range(0, len(pages[r])):
                        worksheet.write(r + 1, c, pages[r][c], cell_format)

        self.output(f"All data written to '{filename}'.")
