# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


# class SigaleiPipeline:
#     def process_item(self, item, spider):
#         return item

import sqlite3
import os

class SQLlitePipeline(object):

    def open_spider(self, spider):
        self.connection = sqlite3.connect("sigalei.db")
        self.c = self.connection.cursor()
        try:
            self.c.execute('''
                CREATE TABLE IF NOT EXISTS sigalei(
                    data TEXT,
                    projeto TEXT,
                    index_projeto PRIMARY KEY,
                    md5 TEXT
                )
            ''')
            self.connection.commit()
        except sqlite3.OperationalError:
            pass

    def close_spider(self, spider):
        salva_pdf = 'salva_pdf'
        path = f'{salva_pdf}.pdf'
        os.remove(path)
        self.connection.close()

    def process_item(self, item, spider):
        self.c.execute('''
            INSERT OR IGNORE INTO sigalei (data,projeto,index_projeto,md5) VALUES(?,?,?,?)

        ''', (
            item.get('data'),
            item.get('projeto'),
            item.get('index_projeto'),
            item.get('md5')
        ))
        self.connection.commit()
        return item
