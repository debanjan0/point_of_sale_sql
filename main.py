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
    

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="debanjan")

mycursor = mydb.cursor()
mycursor2= mydb.cursor(buffered=True)
today = date.today()
d1 = today.strftime("%Y/%m/%d")
body = '''Your Invoive donwload below
sicerely yours
Electronic Store
'''
sender = 'debarock900@gmail.com'
password = 'deqhdzzepowmsyzs'
cust_list = ["name", "phone", "email"]
item_list = ["item name", "price", "stock"]
sale_list = ["customer ID", "mode of payment"]

invoice_sql="SELECT t1.sale_id, t2.quantity, t3.price, t2.name\
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

cust_n_id_sql="SELECT t1.sale_id, t4.name, t4.email \
    FROM sale as t1\
    LEFT JOIN customer as t4 \
    ON t1.cust_id = t4.cust_id\
    WHERE t1.cust_id = t4.cust_id AND t1.sale_id = %s"
# format of the above sql query (sale_id, customer name)
# example above sql query (1, rohit)

def database_creation():
    sql = "CREATE DATABASE IF NOT EXISTS pos" # creats database if not exist
    mycursor.execute(sql)
    mycursor.execute("use pos")
    sql_item    ='''
                CREATE TABLE IF NOT EXISTS item
                (item_id integer primary key AUTO_INCREMENT,
                name varchar(20),
                price integer,
                stock integer));
                '''
    sql_customer='''
                CREATE TABLE IF NOT EXISTS customer
                (cust_id integer primary key AUTO_INCREMENT,
                name varchar(20),
                phone char(10),
                email varchar(30));
                '''
    sql_sale    ='''
                CREATE TABLE IF NOT EXISTS sale
                (sale_id integer primary key AUTO_INCREMENT,
                sale_data date,
                cust_id integer,
                mop char(8),
                FOREIGN KEY (cust_id) REFERENCES customer (cust_id));
                '''
    sql_sale_details='''
                CREATE TABLE IF NOT EXISTS sale_details(
                sale_id integer NOT NULL,
                name varhar(20),
                quantity integer,
                FOREIGN KEY (sale_id) REFERENCES sale (sale_id)
                FOREIGN KEY (name) REFERENCES item (name));
                '''
    mycursor.execute(sql_customer) # creats customer data table if not exist
    mycursor.execute(sql_item) # creats item marks table if not exist
    mycursor.execute(sql_sale)  # creats sale table if not exist
    mycursor.execute(sql_sale_details)  # creats sale details table if not exist


def mail_invoice(receiver):
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
    #use gmail with port
    session = smtplib.SMTP('smtp.gmail.com', 587)
    session.starttls()
    #login with mail_id and password
    session.login(sender, password)
    text = message.as_string()
    session.sendmail(sender, receiver, text)
    session.quit()
    print('Mail Sent')


def bill_gen(val):
    tuple1 = (val,)
    mycursor2.execute(cust_n_id_sql, tuple1)
    cust_n_id_sql_result = mycursor2.fetchone()
    COSTOMER_NAME = cust_n_id_sql_result[1]
    invoice_number = cust_n_id_sql_result[0]
    email=cust_n_id_sql_result[2]
    os.environ["INVOICE_LANG"] = "en"
    client = Client(COSTOMER_NAME)
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

    print("\n Bill generated as invoice.pdf \n")
    mail_invoice(email)


def item_data():
    mycursor.execute("select * from item ORDER BY item_id")
    result = mycursor.fetchall()
    return result


def cust_data():
    mycursor.execute("select * from customer ORDER BY cust_id")
    result = mycursor.fetchall()
    return result


def sale_data():
    mycursor.execute("select * from sale ORDER BY sale_id")
    result = mycursor.fetchall()
    return result


def add_item():
    tempo_list = []
    for i in item_list:
        x = input("enter the " + i + " :- ")
        tempo_list.append(x)
    sql = "INSERT INTO item (name,price,stock) VALUES (%s, %s, %s)"
    mycursor.execute(sql, tuple(tempo_list))
    mydb.commit()


def add_customer():
    tempo_list = []
    for i in cust_list:
        x = input("enter the " + i + " :- ")
        tempo_list.append(x)
    sql = "INSERT INTO customer (name,phone,email) VALUES (%s, %s, %s)"
    mycursor.execute(sql, tuple(tempo_list))
    mydb.commit()


def add_sale():
    tempo_list = [str(d1)]
    for i in sale_list:
        x = input("enter the " + i + " :- ")
        tempo_list.append(x)
    sql = "INSERT INTO sale (sale_date,cust_id,mop) VALUES (%s, %s, %s)"
    mycursor2.execute(sql, tuple(tempo_list))
    mydb.commit()
    sql1 = "SELECT * FROM sale ORDER BY sale_id DESC"
    mycursor2.execute(sql1)
    myresult = mycursor2.fetchone()
    add_order_details(myresult[0])


def add_order_details(iid):
    n = int(input("How many item do you want ? "))
    for j in range(n):
        temp_item_list = [iid]
        x_item = input("enter the item :- ")
        temp_item_list.append(x_item)
        x_quan = input("enter the quantity :- ")
        temp_item_list.append(x_quan)
        sql = "INSERT INTO sale_details (sale_id,name,quantity) VALUES (%s, %s, %s)"
        mycursor.execute(sql, tuple(temp_item_list))
        mydb.commit()

    bill_gen(iid)


while True:
    data = []
    print("1.to add_item \n"+"2.to add_sale \n"+"3.to add_customer \n"+"4.to show items \n"+"5.to show sale \n"
          +"6.to show customers \n"+"7.to find by sale id \n"+"8.to exit \n")
    n=int(input(":- "))

    if n == 1:
        add_item()
    elif n == 2:
        add_sale()
    elif n == 3:
        add_customer()
    elif n == 4:
        myresult = item_data()
        for x in myresult:
            data.append(x)
        print (tabulate(data, headers=["Item ID", "Name", "Price", "Stock"]))
    elif n == 5:
        myresult = sale_data()
        for x in myresult:
            data.append(x)
        print (tabulate(data, headers=["Sale ID", "Sale Date", "Customer ID", "Mode fo payment"]))
    elif n == 6:
        myresult = cust_data()
        for x in myresult:
            data.append(x)
        print (tabulate(data, headers=["Customer ID", "Name", "Number", "Email"]))
    elif n == 7:
        break
    elif n == 8:
        break
    else:
        print("enter a valid no")

