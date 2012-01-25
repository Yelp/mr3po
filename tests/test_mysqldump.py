# -*- coding: utf-8 -*-
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from mr3po.mysqldump import MySQLCompleteExtendedInsertProtocol
from mr3po.mysqldump import MySQLCompleteInsertProtocol
from mr3po.mysqldump import MySQLExtendedInsertProtocol
from mr3po.mysqldump import MySQLInsertProtocol



class GoodInputTestCase(unittest.TestCase):

    def test_insert(self):
        p = MySQLInsertProtocol()
        key, value = p.read(
            "INSERT INTO `user` VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL);")
        self.assertEqual(
            (key, value),
            (u'user', [1, u'David Marin', 25.25, '\xc0\xde', None]))

    def test_complete_insert(self):
        p = MySQLCompleteInsertProtocol()
        key, value = p.read(
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL);")
        self.assertEqual(
            (key, value), (u'user', {u'id': 1,
                                     u'name': u'David Marin',
                                     u'score': 25.25,
                                     u'data': '\xc0\xde',
                                     u'misc': None}))

    def test_extended_insert(self):
        p = MySQLExtendedInsertProtocol()
        key, value = p.read(
            "INSERT INTO `user` VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL),"
            " (2,'Nully Nullsworth',NULL,NULL,NULL);")
        self.assertEqual(
            (key, value),
            (u'user', [[1, u'David Marin', 25.25, '\xc0\xde', None],
                       [2, u'Nully Nullsworth', None, None, None]]))
        
        
    

class BadInputTestCase(unittest.TestCase):

    def test_empty(self):
        p = MySQLExtendedInsertProtocol()
        self.assertRaises(ValueError, p.read, '')

    def test_non_insert(self):
        p = MySQLExtendedInsertProtocol()
        self.assertRaises(ValueError, p.read, 'USE test;')

    def test_missing_close_paren(self):
        p = MySQLExtendedInsertProtocol()
        self.assertRaises(
            ValueError,
            p.read, "INSERT INTO `user` VALUES (1,'David Marin'")

    def test_rows_and_cols_dont_match(self):
        p = MySQLExtendedInsertProtocol()
        # this is a problem even if the protocol doesn't care about
        # column names
        self.assertRaises(
            ValueError,
            p.read,
            "INSERT INTO `user` (`id`) VALUES"
            " (1,'David Marin',25.25,0xC0DE,NULL);")
        
    
        
        


class EncodingTestCase(unittest.TestCase):

    def test_default_encoding(self):
        p = MySQLCompleteInsertProtocol()
        # encoded in UTF-8
        key, value = p.read(
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (3,'Paul Erdős',0,0x0E2D05,NULL);")
        self.assertEqual(
            (key, value), (u'user', {u'id': 3,
                                     u'name': u'Paul Erdős',
                                     u'score': 0,
                                     u'data': '\x0e\x2d\x05',
                                     u'misc': None,}))

        key, value = p.read(
            # encoded in latin-1, with ö instead of ő
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (3,'Paul Erd\xf6s',0,0x0E2D05,NULL);")
        self.assertEqual(
            (key, value), (u'user', {u'id': 3,
                                     u'name': u'Paul Erdös',
                                     u'score': 0,
                                     u'data': '\x0e\x2d\x05',
                                     u'misc': None,}))

    def test_alternate_encoding(self):
        p = MySQLCompleteInsertProtocol(encoding='latin-1')
        # encoded in UTF-8, but we will decode it in latin-1
        key, value = p.read(
            "INSERT INTO `user` (`id`, `name`, `score`, `data`, `misc`) VALUES"
            " (3,'Paul Erdős',0,0x0E2D05,NULL);")
        self.assertEqual(
            (key, value), (u'user', {u'id': 3,
                                     u'name': 'Paul Erdős'.decode('latin-1'),
                                     u'score': 0,
                                     u'data': '\x0e\x2d\x05',
                                     u'misc': None}))
        
        
        
        
