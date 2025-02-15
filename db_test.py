import psycopg2
# PostgreSQL 연결 설정
DB_HOST = "localhost"
DB_NAME = "DB"  # 사용자 DB 이름
DB_USER = "postgres"  # PostgreSQL 사용자 이름
DB_PASSWORD = "0123456789"  # PostgreSQL 비밀번호
DB_PORT = 5432  # 기본 포트

# 데이터베이스 연결 함수
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )
    return conn

def insert_data(id,name,created_at,conn):
    cur=conn.cursor()
    cur.execute("INSERT INTO test_table (id,name,created_at) VALUES (%s,%s,%s)",(2,'jaewon','2025-01-21'))
    conn.commit()
    cur.close()

conn=get_db_connection()
print(conn)
