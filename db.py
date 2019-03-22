import records

db = records.Database('sqlite:///bt.db')


def create_tables():
    db.query('DROP TABLE IF EXISTS orders')
    db.query('CREATE TABLE orders (id INTEGER PRIMARY KEY AUTOINCREMENT, price float, amount float, commission float, order_type text, date int)')


def create_order(price, amount, commission, order_type, date):
    db.query(
        'INSERT INTO orders (price, amount, commission, order_type, date) VALUES(:price, :amount, :commission, :order_type, strftime("%s",:date))',
             price=price, amount=amount, commission=commission, order_type=order_type, date=date
    )


if __name__ == '__main__':
    create_tables()
    # create_order(12.40, 0.34, 0.55, 'sell', '2018-01-01T12:00:00')
