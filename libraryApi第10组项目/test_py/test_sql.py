from utils.pymysql_comm import UsingMysql
import dateutil
from dateutil.parser import parse
def test():
    current_date = "2024-3-28"
    with UsingMysql() as um:
        select_borrow_sql = '''
                    SELECT reader_id,title,book.isbn,borrow_date,due_date,return_date,borrow.librarian_id,
                    DATEDIFF(%s,due_date) AS 'date_diff'
                    FROM borrow,book,cip
                    WHERE borrow.book_id=book.book_id and book.isbn=cip.isbn
        '''
        um.cursor.execute(select_borrow_sql, (current_date,))
        datas = um.cursor.fetchall()
        print(datas)

if __name__ == '__main__':
    test()
