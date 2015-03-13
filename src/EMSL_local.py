# -*- coding: utf-8 -*-

import sqlite3
import re
import sys
import os
import time

debug = True


def checkSQLite3(db_path):

    from os.path import isfile, getsize

    # Check if db file is readable
    if not os.access(db_path, os.R_OK):
        print >>sys.stderr, "Db file %s is not readable" % (db_path)
        raise IOError

    if not isfile(db_path):
        print >>sys.stderr, "Db file %s is not... a file!" % (db_path)
        raise IOError

    if getsize(db_path) < 100:  # SQLite database file header is 100 bytes
        print >>sys.stderr, "Db file %s is not a SQLite file!" % (db_path)
        raise IOError

    with open(db_path, 'rb') as fd:
        header = fd.read(100)

    if header[:16] != 'SQLite format 3\x00':
        print >>sys.stderr, "Db file %s is not in SQLiteFormat3!" % (db_path)
        raise IOError

    # Check if the file system allows I/O on sqlite3 (lustre)
    # If not, copy on /dev/shm and remove after opening
    try:
        EMSL_local(db_path=db_path).get_list_basis_available()
    except sqlite3.OperationalError:
        print >>sys.stdrerr, "I/O Error for you file system"
        print >>sys.stderr, "Try some fixe"
        new_db_path = "/dev/shm/%d.db" % (os.getpid())
        os.system("cp %s %s" % (db_path, new_db_path))
        db_path = new_db_path
    else:
        changed = False
        return db_path, changed

    # Try again to check
    try:
        EMSL_local(db_path=db_path).get_list_basis_available()
    except:
        print >>sys.stderr, "Sorry..."
        os.system("rm -f /dev/shm/%d.db" % (os.getpid()))
        raise
    else:
        print >>sys.stderr, "Working !"
        changed = True
        return db_path, changed


def cond_sql_or(table_name, l_value):

    l = []
    dmy = " OR ".join(['%s = "%s"' % (table_name, i) for i in l_value])
    if dmy:
        l.append("(%s)" % dmy)

    return l


class EMSL_local:

    def __init__(self, db_path=None):
        self.db_path = db_path

    def get_list_basis_available(self, elts=[]):

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if not elts:

            c.execute("""SELECT DISTINCT name,description, LENGTH(data)- LENGTH(REPLACE(data, X'0A', ''))
                         FROM output_tab""")
            data = c.fetchall()

        else:
            cmd = ["""SELECT name,description, LENGTH(data)- LENGTH(REPLACE(data, X'0A', ''))
                      FROM output_tab WHERE elt=?"""] * len(elts)
            cmd = " INTERSECT ".join(cmd) + ";"

            c.execute(cmd, elts)
            data = c.fetchall()

        data = [i[:] for i in data]

        conn.close()

        return data

    def get_list_element_available(self, basis_name):

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute(
            "SELECT DISTINCT elt from output_tab WHERE name=:name_us COLLATE NOCASE", {
                "name_us": basis_name})

        data = c.fetchall()

        data = [str(i[0]) for i in data]

        conn.close()
        return data

    def process_raw_data(self, l_data_raw):
        unpacked = [b[0] for b in l_data_raw]
        return unpacked

    def get_basis(self, basis_name, elts=None):
        #  __            _
        # /__  _ _|_   _|_ ._ _  ._ _     _  _. |
        # \_| (/_ |_    |  | (_) | | |   _> (_| |
        #                                     |
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if elts:
            cmd_ele = "AND " + " ".join(cond_sql_or("elt", elts))
        else:
            cmd_ele = ""

        c.execute('''SELECT DISTINCT data from output_tab
                   WHERE name="{basis_name}" COLLATE NOCASE
                   {cmd_ele}'''.format(basis_name=basis_name,
                                       cmd_ele=cmd_ele))

        l_data_raw = c.fetchall()
        conn.close()

        l_data = self.process_raw_data(l_data_raw)
        
        return l_data

if __name__ == "__main__":

    e = EMSL_local(db_path="EMSL.db")
    l = e.get_list_basis_available()
    for i in l:
        print i

    l = e.get_list_element_available("pc-0")
    print l

    l = e.get_basis("cc-pVTZ", ["H", "He"])
    for i in l:
        print i