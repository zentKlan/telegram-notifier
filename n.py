import sqlite3

db = sqlite3.connect(":memory:")   # база только в памяти, файл не создаётся
db.execute("CREATE TABLE repos (name TEXT PRIMARY KEY, stars INTEGER NOT NULL)")

up = ("INSERT INTO repos(name, stars) VALUES (?, ?) "
      "ON CONFLICT(name) DO UPDATE SET stars = excluded.stars")

with db:
    db.execute(up, ("a", 3))
    db.execute(up, ("b", 5))
    db.execute(up, ("a", 10))           # обновит, а не добавит

cur = db.execute("SELECT name, stars FROM repos ORDER BY name")
print(cur.fetchone())
print(cur.fetchall())

try:
    with db:
        db.execute(up, ("c", 1))
        raise ValueError("сломалось")
except ValueError:
    pass
print(db.execute("SELECT * FROM repos").fetchall())   # есть ли 'c'?