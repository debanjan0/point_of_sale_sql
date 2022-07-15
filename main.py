
import os
from datetime import date
import mysql.connector
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

try:
    from tabulate import tabulate
except ModuleNotFoundError:
    os.system("pip install tabulate")
    from tabulate import tabulate

try:
    from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator
    from InvoiceGenerator.pdf import SimpleInvoice
except ModuleNotFoundError:
    os.system("pip install InvoiceGenerator")
    from InvoiceGenerator.api import Invoice, Item, Client, Provider, Creator
    from InvoiceGenerator.pdf import SimpleInvoice


u = input("Enter mySQL user name: ")
pwd = input("Enter mySQL password: ")

mydb = mysql.connector.connect(
    host="localhost",
    user=u,
    password=pwd)

print("\nWelcome to the electronic store\n")


width, lines = os.get_terminal_size()
mycursor = mydb.cursor()
mycursor2 = mydb.cursor(buffered=True)
today = date.today()
d1 = today.strftime("%Y/%m/%d")
body = '''
        Your Invoive donwload below
        sicerely yours
        Electronic Store
        '''
sender = 'email'
password = 'password'
cust_list = ["name", "phone", "email"]
item_list = ["item name", "price", "stock"]
sale_list = ["customer ID", "mode of payment"]

invoice_sql = "SELECT t1.sale_id, t2.quantity,\
                t3.price, t2.name\
                ,t4.name \
                FROM sale as t1\
                LEFT JOIN sale_details as t2\
                ON t1.sale_id = t2.sale_id\
                LEFT JOIN item as t3 \
                ON t2.name = t3.name\
                LEFT JOIN customer as t4 \
                ON t1.cust_id = t4.cust_id\
                WHERE t1.sale_id = t2.sale_id AND t1.sale_id = %s"
# format of the above sql query (sale_id, cust_id, item name, quantity, price, customer name)
# example above sql query (1, 2, 'keyboard', 1, 360, rohit)

cust_n_id_sql = "SELECT t1.sale_id, t4.name, t4.email \
                FROM sale as t1\
                LEFT JOIN customer as t4 \
                ON t1.cust_id = t4.cust_id\
                WHERE t1.cust_id = t4.cust_id AND t1.sale_id = %s"
# format of the above sql query (sale_id, customer name)
# example above sql query (1, rohit)

months_total_sale_sql="SELECT date_format(t1.sale_date, '%M'),\
                    SUM(t2.quantity*t3.price) FROM sale as t1 LEFT JOIN \
                    sale_details as t2 ON t1.sale_id = t2.sale_id LEFT JOIN \
                    item as t3  ON t2.name = t3.name \
                    GROUP BY date_format(t1.sale_date, '%M') ORDER BY t1.sale_date;"
# format of the above sql query (month, total sale)
# example above sql query (May, 5688)


def database_creation():
    """To create the database and tables"""
    sql = "CREATE DATABASE IF NOT EXISTS pos"  # creats database if not exist
    mycursor.execute(sql)
    mycursor.execute("use pos")
    sql_item = '''
                CREATE TABLE IF NOT EXISTS item
                (item_id integer primary key AUTO_INCREMENT,
                name varchar(20),
                price integer,
                stock integer
                );
                '''
    sql_customer = '''
                CREATE TABLE IF NOT EXISTS customer
                (cust_id integer primary key AUTO_INCREMENT,
                name varchar(20),
                phone char(10),
                email varchar(30)
                );
                '''
    sql_sale = '''
                CREATE TABLE IF NOT EXISTS sale
                (sale_id integer primary key AUTO_INCREMENT,
                sale_date date,
                cust_id integer,
                mop char(8),
                FOREIGN KEY (cust_id) REFERENCES customer(cust_id)
                );
                '''
    sql_sale_details = '''
                CREATE TABLE IF NOT EXISTS sale_details(
                sale_id integer NOT NULL,
                name varchar(20),
                quantity integer,
                FOREIGN KEY (sale_id) REFERENCES sale(sale_id),
                FOREIGN KEY (name) REFERENCES item(name)
                );
                '''
    mycursor.execute(sql_customer)  # creats customer data table if not exist
    mycursor.execute(sql_item)  # creats item marks table if not exist
    mycursor.execute(sql_sale)  # creats sale table if not exist
    # creats sale details table if not exist
    mycursor.execute(sql_sale_details)


def monthly_sale_graph(x):
    value = []
    months = []
    count = 0
    for x in x:
        value.append(x[1])
        months.append(x[0])
        
    for i in months:
        if count<len((i)):
            count = len((i))

    for j, val in enumerate(value):
        space = int(val/100)*">"
        if len(months[j]) < count:
            mon = months[j] + " " * (count - len(months[j]))
            print(mon, end="|")
            print(space, end="")
            print(f"({val})")
        else:
            print(months[j], end="|")
            print(space, end="")
            print(f"({val})")


def bar_graph(height,x,space=2):
    """To make a bar graph"""
    for i in range(height+1):
        print("|", end=" ")
        for j in x:
            if i > height-j:
                print("HH", end=(space*" "))
            else:
                print("  ", end=(space*" "))
        print()
    print("-"*(len(x)*(space+2)+2))


def mail_invoice(receiver):
    """To mail the invoice to the customer"""
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = receiver
    message['Subject'] = 'Your Invoive for purchase on '+d1
    message.attach(MIMEText(body, 'plain'))
    pdfname = 'invoice.pdf'
    # open the file in bynary
    binary_pdf = open(pdfname, 'rb')
    payload = MIMEBase('application', 'octate-stream', Name=pdfname)
    payload.set_payload((binary_pdf).read())
    encoders.encode_base64(payload)
    # add header with pdf name
    payload.add_header('Content-Decomposition', 'attachment', filename=pdfname)
    message.attach(payload)
    # use gmail with port
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    # login with mail_id and password
    session.login(sender, password)
    text = message.as_string()
    session.sendmail(sender, receiver, text)
    session.quit()
    print('Mail Sent')


def bill_gen(val):
    """To genetarate the bill"""
    tuple1 = (val,)
    mycursor2.execute(cust_n_id_sql, tuple1)
    cust_n_id_sql_result = mycursor2.fetchone()
    customer_name = cust_n_id_sql_result[1]
    invoice_number = cust_n_id_sql_result[0]
    email = cust_n_id_sql_result[2]
    os.environ["INVOICE_LANG"] = "en"
    client = Client(customer_name)
    provider = Provider('Electronic Store',
                        bank_account='6454-6361-217273',
                        bank_code='2022')
    creator = Creator('ONWER')
    invoice = Invoice(client, provider, creator)

    mycursor.execute(invoice_sql, tuple1)
    myresult = mycursor.fetchall()
    for x in myresult:
        invoice.add_item(Item(x[1], x[2], description=x[3]))
        COSTOMER_NAME = x[4]
        invoice_number = x[0]

    invoice.currency = "Rs."
    invoice.number = invoice_number
    docu = SimpleInvoice(invoice)
    docu.gen("invoice.pdf", generate_qr_code=True)

    print("\nBill generated as invoice.pdf \nWait for the mail to be sent\n")
    mail_invoice(email)


def report_data():
    """To get the sales data from the database for making reports"""
    report_data_sql = "select date_format(sale_date, '%M'),count(sale_id) from sale group by date_format(sale_date, '%M');"
    mycursor.execute(report_data_sql)
    result = mycursor.fetchall()
    return result

def monthly_sale_data():
    mycursor.execute(months_total_sale_sql)
    result = mycursor.fetchall()
    return result

def item_data():
    """To get the item data from the database"""
    mycursor.execute("select * from item ORDER BY item_id")
    result = mycursor.fetchall()
    return result


def cust_data():
    """To get the customer data from the database"""
    mycursor.execute("select * from customer ORDER BY cust_id")
    result = mycursor.fetchall()
    return result


def sale_data():
    """To get the sale data from the database"""
    mycursor.execute("select * from sale ORDER BY sale_id")
    result = mycursor.fetchall()
    return result


def add_item():
    """To add the item to the database"""
    tempo_list = []
    try:
        for i in item_list:
            x = input("enter the " + i + " :- ")
            tempo_list.append(x)
        sql = "INSERT INTO item (name,price,stock) VALUES (%s, %s, %s)"
        mycursor.execute(sql, tuple(tempo_list))
        mydb.commit()
    except ValueError:
        pass


def add_customer():
    """To add the customer to the database"""
    tempo_list = []
    try:
        for i in cust_list:
            x = input("enter the " + i + " :- ")
            tempo_list.append(x)
        sql = "INSERT INTO customer (name,phone,email) VALUES (%s, %s, %s)"
        mycursor.execute(sql, tuple(tempo_list))
        mydb.commit()
    except ValueError:
        pass


def add_sale():
    """To add the sale to the database"""
    tempo_list = [str(d1)]
    for i in sale_list:
        try:
            x = input("enter the " + i + " :- ")
            tempo_list.append(x)
        except ValueError:
            pass
    sql = "INSERT INTO sale (sale_date,cust_id,mop) VALUES (%s, %s, %s)"
    mycursor2.execute(sql, tuple(tempo_list))
    mydb.commit()
    sql1 = "SELECT * FROM sale ORDER BY sale_id DESC"
    mycursor2.execute(sql1)
    myresult = mycursor2.fetchone()
    add_order_details(myresult[0])


def add_order_details(iid):
    """To add the order details to the database"""
    n = int(input("How many item do you want ? "))
    for j in range(n):
        try:
            temp_item_list = [iid]
            x_item = input("enter the item :- ")
            temp_item_list.append(x_item)
            x_quan = input("enter the quantity :- ")
            temp_item_list.append(x_quan)
            sql = "INSERT INTO sale_details (sale_id,name,quantity) VALUES (%s, %s, %s)"
            mycursor.execute(sql, tuple(temp_item_list))
            mydb.commit()
        except ValueError:
            pass

    bill_gen(iid)


def add_stock(name, quan):
    """To add the stock to the database"""
    stock_add_sql = "UPDATE item SET stock = stock + %s WHERE name = %s"
    mycursor.execute(stock_add_sql, (quan, name))
    mydb.commit()


def find_sale_by_id(id):
    """To find the sale by id"""
    find_sale_by_id_sql = "SELECT * FROM sale WHERE sale_id = %s"
    mycursor.execute(find_sale_by_id_sql, (id,))
    result = mycursor.fetchall()
    return result


def find_item_by_id(id):
    """To find the item by id"""
    find_item_by_id_sql = "SELECT * FROM item WHERE item_id = %s"
    mycursor.execute(find_item_by_id_sql, (id,))
    result = mycursor.fetchall()
    return result


def find_customer_by_id(id):
    """To find the customer by id"""
    find_customer_by_id_sql = "SELECT * FROM customer WHERE cust_id = %s"
    mycursor.execute(find_customer_by_id_sql, (id,))
    result = mycursor.fetchall()
    return result


def remove_item(id):
    """To remove the item from the database"""
    remove_id_sql = "DELETE FROM item WHERE item_id = %s"
    mycursor.execute(remove_id_sql, (id,))
    mydb.commit()


def remove_customer(id):
    """To remove the customer from the database"""
    remove_id_sql = "DELETE FROM customer WHERE cust_id = %s"
    mycursor.execute(remove_id_sql, (id,))
    mydb.commit()


def add_cust_n_add_sale():
    """To add the customer and sale to the database"""
    add_customer()
    mycursor.execute("SELECT LAST_INSERT_ID();")
    result = mycursor.fetchone()
    idd = result[0]
    mop = input("enter the mode of payment :- ")
    tempo_list = [str(d1), idd, mop]
    sql = "INSERT INTO sale (sale_date,cust_id,mop) VALUES (%s, %s, %s)"
    mycursor2.execute(sql, tuple(tempo_list))
    mydb.commit()
    sql1 = "SELECT * FROM sale ORDER BY sale_id DESC"
    mycursor2.execute(sql1)
    myresult = mycursor2.fetchone()
    add_order_details(myresult[0])


def change_customer_details(id,feild,val):
    """To change the customer details"""
    change_customer_details_sql = "UPDATE customer SET %s = %s WHERE cust_id = %s"
    mycursor.execute(change_customer_details_sql, (feild,val,id))
    mydb.commit()


def change_item_details(id,feild,val):
    """Change the details of the item"""
    change_item_details_sql = "UPDATE item SET %s = %s WHERE item_id = %s"
    mycursor.execute(change_item_details_sql, (feild,val,id))
    mydb.commit()


def border_line():
    """To print the border line"""
    for i in range(width):
        print("-", end="")
    print()


database_creation()  # Creates database if not exist

while True:
    border_line()
    data = []
    print("\n1.to add_item \n"+"2.to add_sale \n"+"3.to add_customer \n"+"4.to show items \n"+"5.to show sale \n"
          +"6.to show customers \n"+"7.to update stock \n"+"8.Search by id \n"+"9.to update customer details \n"
          +"10.to update item details\n"+"11.to delete item by id\n"+"12.to delete customer by id\n"+"13.to generate reports\n"+"14.to exit\n")
    try:
        n = int(input(":- "))
        print()
    except ValueError:
        n=0
    if n == 1:
        add_item()
        border_line()

    elif n == 2:
        print("\n1.New customer \n"+"2.Old customer \n")
        try:
            n = int(input(":- "))
            print()
            if n == 1:
                add_cust_n_add_sale()
            elif n == 2:
                add_sale()
            else:
                print("Invalid input")
        except ValueError:
            print("Value Error")
            continue

    elif n == 3:
        add_customer()
        border_line()

    elif n == 4:
        myresult = item_data()
        for x in myresult:
            data.append(x)
        print(tabulate(data, headers=["Item ID", "Name", "Price", "Stock"]))
        border_line()

    elif n == 5:
        myresult = sale_data()
        for x in myresult:
            data.append(x)
        print(tabulate(data, headers=[
              "Sale ID", "Sale Date", "Customer ID", "Mode fo payment"]))
        border_line()

    elif n == 6:
        myresult = cust_data()
        for x in myresult:
            data.append(x)
        print(tabulate(data, headers=[
              "Customer ID", "Name", "Number", "Email"]))
        border_line()

    elif n == 7:
        try:
            name = input("Enter the stock name :- ")
            quan = int(input("Enter the stock quantity to be added :- "))
            add_stock(name, quan)
            print()
            border_line()
        except ValueError:
            print("Value Error")
            continue

    elif n == 8:
        print("\n1.to search sale \n"+"2.to search item \n" +
              "3.to search customer \n"+"4.to back \n")
        try:
            search = int(input("Enter the choice :- "))
            print()
            if search == 1:
                idd = int(input("Enter the sale id :- "))
                myresult = find_sale_by_id(idd)
                for x in myresult:
                    data.append(x)
                print(tabulate(data, headers=[
                      "Sale ID", "Sale Date", "Customer ID", "Mode fo payment"]))
            elif search == 2:
                idd = input("Enter the item name :- ")
                myresult = find_item_by_id(idd)
                for x in myresult:
                    data.append(x)
                print(tabulate(data, headers=[
                      "Item ID", "Name", "Price", "Stock"]))
            elif search == 3:
                idd = int(input("Enter the customer id :- "))
                myresult = find_customer_by_id(idd)
                for x in myresult:
                    data.append(x)
                print(tabulate(data, headers=[
                      "Customer ID", "Name", "Number", "Email"]))
            elif change == 4:
                pass
            else:
                print("Invalid choice")
            border_line()
        except ValueError:
            print("Value Error")
            continue

    elif n == 9:
        print("\n1.to change item name \n"+"2.to change item price \n"+"4.to back\n")
        change = int(input("Enter the choice :- "))
        print()
        if change == 1:
            id = int(input("Enter the item id :- "))
            name = input("Enter the new name :- ")
            change_item_details(id, "name", name)
            print()
            border_line()
        elif change == 2:
            id = int(input("Enter the item id :- "))
            price = int(input("Enter the new price :- "))
            change_item_details(id, "price", price)
            print()
            border_line()
        elif change == 4:
            pass
        else:
            print("Invalid choice")

    elif n == 10:
            try:
                print("\n1.to change customer name \n"+"2.to change customer number \n"
                    +"3.to change customer email \n"+"4.to back\n")
                change = int(input("Enter the choice :- "))
                print()
                if change == 1:
                    id = int(input("Enter the customer id :- "))
                    name = input("Enter the new name :- ")
                    change_customer_details(id, "name", name)
                    print()
                    border_line()
                elif change == 2:
                    id = int(input("Enter the customer id :- "))
                    number = input("Enter the new number :- ")
                    change_customer_details(id, "number", number)
                    print()
                    border_line()
                elif change == 3:
                    id = int(input("Enter the customer id :- "))
                    email = input("Enter the new email :- ")
                    change_customer_details(id, "email", email)
                    print()
                    border_line()
                elif change == 4:
                    pass
                else:
                    print("Invalid choice")
            except ValueError:
                print("Value Error")
                continue
    
    elif n == 11:
        print("currently not available")
        """
        ERROR:
        mysql.connector.errors.IntegrityError: 1451 (23000): Cannot delete or update a parent row: a foreign key constraint fails 
        """
        # try:
        #     n = int(input("Enter the item id to be removed :- "))
        #     remove_item(n)
        #     print()
        #     border_line()
        # except ValueError:
        #     print("Value Error")
        #     continue

    elif n == 12:
        print("currently not available")
        """
        ERROR:
        mysql.connector.errors.IntegrityError: 1451 (23000): Cannot delete or update a parent row: a foreign key constraint fails 
        """
        # try:
        #     n = int(input("Enter the customer id to be removed :- "))
        #     remove_customer(n)
        #     print()
        #     border_line()
        # except ValueError:
        #     print("Value Error")
        #     continue
    
    elif n == 13:
        try:
            print("\n1.to generate report of all sales in a month \n"+"2.to generate report of total sale in a month \n"+"3.to back\n")
            n = int(input("Enter the choice :- "))
            print()
        except ValueError:
            print("Value Error")
            continue
        if n == 1:
            value = []
            months = []
            x = report_data()
            for x in x:
                value.append(x[1])
                months.append(x[0])
            bar_graph(16, value, space=4)
            print("  ", end="")
            for i in months:
                print(i, end="  ")
            print()
        elif n == 2:
            x = monthly_sale_data()
            monthly_sale_graph(x)
        elif n == 3:
            pass
        else:
            print("Invalid input")

    elif n == 14:
        n = input("Are you sure you want to exit ? (Y/n) :- ")
        if n == "y":
            break
        elif n == "n":
            print("Value Error")
            continue
        elif n == "N":
            print("Value Error")
            continue
        else:
            break
    
    else:
        print("enter a valid no")





