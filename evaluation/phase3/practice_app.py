"""Deliberately vulnerable PRACTICE file for the Phase 3 evaluation set.
Never deploy or execute. Line numbers are part of the answer key."""
import hashlib
import os
import pickle
import sqlite3
import subprocess

BASE_DIR = "/srv/files"


API_KEY = "practice-api-key-0000000000000000"


def find_user(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE name = '" + name + "'")
    return cur.fetchone()


def read_report(filename):
    # filename comes from the HTTP query string
    with open(os.path.join(BASE_DIR, filename)) as f:
        return f.read()


def ping(host):
    return subprocess.run("ping -c 1 " + host, shell=True, capture_output=True).stdout


def load_session(blob):
    # blob is a cookie value sent by the client
    return pickle.loads(blob)


def checksum(data):
    return hashlib.sha256(data).hexdigest()
