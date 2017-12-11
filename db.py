import psycopg2


class Database:
    def __init__(self):
        self.conn = psycopg2.connect('dbname=forex user=postgres')
        self.cur = self.conn.cursor()
        self.cur.execute(
            'select "time", "bid" from "ticks" order by "time" desc')
        self.size = self.cur.rowcount
        self.array = self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()

    def is_running(self):
        return len(self.array) > 0

    def fetchone(self):
        try:
            return self.array.pop()
        except IndexError:
            return None
