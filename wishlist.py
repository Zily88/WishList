from PyQt5 import QtWidgets, QtCore, QtGui, QtSql
from sqlalchemy import Column, Integer, String, Numeric, create_engine, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists


# Многовато инита. Ещё бы чуть чуть и вынес в методы...
class MyWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.wishlist = []  # Наш вишлист, собственной персоной.
        # self.wishlist = [['Компьютер', '50000', 'http://www.anything', 'Супер комп!'], ['Телефон', '30000',
        #                 'http://www.somthingelse', 'Хочу 2!']]
        self.sql()
        self.get_wish_list()
        self.table = QtWidgets.QTableView()
        self.vbox = QtWidgets.QVBoxLayout()
        self.hbox = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton('Сохранить')
        self.btn_exit = QtWidgets.QPushButton('Выход')
        self.btn_save.clicked.connect(self.save_wish_list)
        self.btn_exit.clicked.connect(QtWidgets.qApp.quit)
        self.hbox.addWidget(self.btn_save)
        self.hbox.addWidget(self.btn_exit)
        self.table_model = QtGui.QStandardItemModel()
        self.table_model.setColumnCount(4)
        self.table_model.setRowCount(self.get_rows())
        self.table_model.setHorizontalHeaderLabels(['Название', 'Цена', 'Ссылка', 'Примечание'])
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(1)
        self.table.setModel(self.table_model)
        self.vbox.addWidget(self.table)
        self.vbox.addLayout(self.hbox)
        self.setLayout(self.vbox)
        self.table.selectionModel().selectionChanged.connect(self.select_handler)
        self.fill_table()

    # Забираем количество строк для создания таблицы
    def get_rows(self):
        if self.wishlist:
            return len(self.wishlist) + 1
        return 1

    # Забираем данные из б.д.
    def get_wish_list(self):
        for wish in self.session.query(Wish):
            self.wishlist.append([wish.name, str(wish.price), wish.link, wish.notice])

    # Заполняет наш виджет таблицу.
    def fill_table(self):
        for num, lst in enumerate(self.wishlist):
            for i in range(self.table_model.columnCount()):
                if i == 1:
                    self.table_model.setItem(num, i, QtGui.QStandardItem(self.validate_price(lst[i])))
                else:
                    self.table_model.setItem(num, i, QtGui.QStandardItem(lst[i]))

    # Слот кнопочки 'сохранить'. Составляет вишлист и передаёт управление методу записи в б.д.
    def save_wish_list(self):
        self.wishlist.clear()
        for row in range(self.table_model.rowCount()):
            row_in_list = []
            for column in range(self.table_model.columnCount()):
                if self.table_model.item(row, column):
                    if column == 1:
                        text = self.validate_price(self.table_model.item(row, column).text())
                    else:
                        text = self.table_model.item(row, column).text()
                    if text:
                        row_in_list.append(text)
                    else:
                        row_in_list.append(None)
                else:
                    row_in_list.append(None)
            if row_in_list.count(None) < 4:
                self.wishlist.append(row_in_list)
        self.save_in_db()

    # Проверка формата цены
    def validate_price(self, price):
        price = price.replace(',', '.')
        try:
            price = float(price)
        except:
            return ''
        price = round(price, 2)
        return str(price)

    # Непосредственное сохранение в базу. С устаревшими проверками походу.
    def save_in_db(self):
        for wish in self.session.query(Wish):
            if wish:
                self.session.delete(wish)
        self.session.commit()
        for wish_lst in self.wishlist:
            if wish_lst:
                wish = Wish(wish_lst[0], wish_lst[1], wish_lst[2], wish_lst[3])
                self.session.add(wish)
        self.session.commit()

    # Обработчик выделений основной таблицы
    def select_handler(self, a, b):
        row = a.indexes()[0].row()
        row_count = self.table_model.rowCount()
        if row == row_count - 1:
            self.table_model.appendRow([QtGui.QStandardItem(), QtGui.QStandardItem(), QtGui.QStandardItem(),
                                        QtGui.QStandardItem()])

    # Cоздаём соединение с базой через SQLAlchemy. PyQtSQL както не заводится.
    def sql(self):
        engine = create_engine('mysql+mysqlconnector://zily:Gp57ae7f8@91.245.227.206/farma_db')
        # engine = create_engine('mysql+mysqlconnector://root:Пз57фу7а8@localhost/farma_db')
        if not database_exists(engine.url):
            create_database(engine.url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()


# Декларативная база в алхимии
Base = declarative_base()


class Wish(Base):
    __tablename__ = 'wishes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    price = Column(Numeric(10, 2))
    link = Column(String(100))
    notice = Column(Text)

    def __init__(self, name, price, link, notice):
        self.name = name
        self.price = price
        self.link = link
        self.notice = notice


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.setWindowTitle('Wish List')
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec_())
