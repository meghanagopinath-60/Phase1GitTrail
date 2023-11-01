from flask import *
import hashlib, os
from werkzeug.utils import secure_filename
os.add_dll_directory("C:\Program Files\IBM\SQLLIB\BIN")
import ibm_db

dsn_hostname = "815fa4db-dc03-4c70-869a-a9cc13f33084.bs2io90l08kqb1od8lcg.databases.appdomain.cloud" # e.g.: "54a2f15b-5c0f-46df-8954-7e38e612c2bd.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud"
dsn_uid = "qyc26916"        # e.g. "abc12345"
dsn_pwd = "csgNTN2JKKUVI84Q"      # e.g. "7dBZ3wWt9XN6$o0J"

dsn_driver = "{IBM DB2 ODBC DRIVER}"
dsn_database = "BLUDB"            # e.g. "BLUDB"
dsn_port = "30367"                # e.g. "32733"
dsn_protocol = "TCPIP"            # i.e. "TCPIP"
dsn_security = "SSL"              #i.e. "SSL"

dsn = (
    "DRIVER={0};"
    "DATABASE={1};"
    "HOSTNAME={2};"
    "PORT={3};"
    "PROTOCOL={4};"
    "UID={5};"
    "PWD={6};"
    "SECURITY={7};").format(dsn_driver, dsn_database, dsn_hostname, dsn_port, dsn_protocol, dsn_uid, dsn_pwd,dsn_security)

try:
    conn = ibm_db.connect(dsn, "", "")
    print ("Connected to database: ", dsn_database, "as user: ", dsn_uid, "on host: ", dsn_hostname)

except:
    print ("Unable to connect: ", ibm_db.conn_errormsg() )

app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = '../static/uploads'


def getLoginDetails():
        if 'email' not in session:
            loggedIn = False
            firstName = ''
            noOfItems = 0
        else:
            loggedIn = True
            sql = "SELECT userId, firstName FROM users WHERE email = ?"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt, 1, session['email'])
            if ibm_db.execute(stmt):
                row = ibm_db.fetch_assoc(stmt)
                if row:
                    userId, firstName = row['USERID'], row['FIRSTNAME']
                    sql = "SELECT count(productId) FROM kart WHERE userId = ?"
                    stmt = ibm_db.prepare(conn, sql)
                    ibm_db.bind_param(stmt, 1, userId)
                    if ibm_db.execute(stmt):
                        noOfItems = ibm_db.fetch_assoc(stmt)['1']
        return (loggedIn, firstName, noOfItems)

@app.route("/")
def root():
    conn = ibm_db.connect(dsn, "", "")
    loggedIn, firstName, noOfItems = getLoginDetails()
    itemData=[]
    stmt = ibm_db.prepare(conn, 'SELECT productId, name, price, description, image, stock FROM products')
    ibm_db.execute(stmt)
    while True:
            row = ibm_db.fetch_tuple(stmt)
            if not row:
                break
            itemData.append(row)
    stmt = ibm_db.prepare(conn, 'SELECT categoryId, name FROM categories')
    ibm_db.execute(stmt)
    categoryData = []
    while True:
            row = ibm_db.fetch_tuple(stmt)
            if not row:
                break
            categoryData.append(row)
    print(itemData)
    itemData = [itemData]  
    ibm_db.close(conn)
    return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryData=categoryData)

@app.route("/add")
def admin():
    conn = ibm_db.connect(dsn, "", "")
    categories=[]
    stmt = ibm_db.prepare(conn, "SELECT categoryId, name FROM categories")
    ibm_db.execute(stmt)
    while True:
            row = ibm_db.fetch_tuple(stmt)
            if not row:
                break
            categories.append(row)
    ibm_db.close(conn)
    return render_template('add.html', categories=categories)

@app.route("/addItem", methods=["GET", "POST"])
def addItem():
    conn = ibm_db.connect(dsn, "", "")
    ibm_db.autocommit(conn, ibm_db.SQL_AUTOCOMMIT_OFF)
    if request.method == "POST":
        productid=request.form['id']
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        stock = int(request.form['stock'])
        categoryId = int(request.form['category'])
        #Uploading image procedure
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            print(filename)
            imagename = filename
        sql = '''INSERT INTO products (productid, name, price, description, image, stock, categoryId) 
                VALUES (?, ?, ?, ?, ?, ?, ?)'''
        stmt = ibm_db.prepare(conn, sql)
        ibm_db.bind_param(stmt, 1, productid)
        ibm_db.bind_param(stmt, 2, name)
        ibm_db.bind_param(stmt, 3, price)
        ibm_db.bind_param(stmt, 4, description)
        ibm_db.bind_param(stmt, 5, imagename)
        ibm_db.bind_param(stmt, 6, stock)
        ibm_db.bind_param(stmt, 7, categoryId)
        try:
            if ibm_db.execute(stmt):
                ibm_db.commit(conn)
                print("Insert successful")
                msg="added successfully"
            else:
                print("Insert failed")
                msg="error occured"
        except Exception as e:
            print(f"Error: {e}")
            ibm_db.rollback(conn)
            msg="error occured"   
        print(msg)
    ibm_db.close(conn)
    return redirect(url_for('root'))


@app.route("/remove")
def remove():
    conn = ibm_db.connect(dsn, "", "")
    data=[]
    stmt = ibm_db.prepare(conn,'SELECT productId, name, price, description, image, stock FROM products')
    ibm_db.execute(stmt)
    while True:
            row = ibm_db.fetch_tuple(stmt)
            if not row:
                break
            data.append(row)
    ibm_db.close(conn)
    return render_template('remove.html', data=data)

@app.route("/removeItem")
def removeItem():
    conn = ibm_db.connect(dsn, "", "")
    productId = request.args.get('productId')    
    try:
        stmt = ibm_db.prepare(conn, 'DELETE FROM products WHERE productID = ?')
        ibm_db.bind_param(stmt, 1, productId)

        if ibm_db.execute(stmt):
            ibm_db.commit(conn)
            msg = "Deleted successfully"
        else:
            msg = "Deletion failed"
    except Exception as e:
        msg = f"Error occurred: {str(e)}"
        ibm_db.rollback(conn)
    finally:
        ibm_db.close(conn)
    ibm_db.close(conn)
    print(msg)
    return redirect(url_for('root'))

@app.route("/displayCategory")
def displayCategory():
        data=[]
        conn = ibm_db.connect(dsn, "", "")
        loggedIn, firstName, noOfItems = getLoginDetails()
        categoryId = request.args.get("categoryId")
        stmt = ibm_db.prepare(conn, "SELECT products.productId, products.name, products.price, products.image, categories.name FROM products, categories WHERE products.categoryId = categories.categoryId AND categories.categoryId = ?")
        ibm_db.bind_param(stmt, 1, categoryId)
        if ibm_db.execute(stmt):
            while True:
                row = ibm_db.fetch_tuple(stmt)
                if not row:
                    break
                data.append(row)
        categoryName = data[0][4]
        data = [data]
        ibm_db.close(conn)
        return render_template('displayCategory.html', data=data, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryName=categoryName)

@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    conn = ibm_db.connect(dsn, "", "")
    loggedIn, firstName, noOfItems = getLoginDetails()
    stmt = ibm_db.prepare(conn, "SELECT userId, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone FROM users WHERE email = ?")
    ibm_db.bind_param(stmt, 1, session['email'])
    if ibm_db.execute(stmt):
        profileData = ibm_db.fetch_tuple(stmt)
    print(profileData)
    ibm_db.close(conn)
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))

    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()

        stmt = ibm_db.prepare(conn, "SELECT userId, password FROM users WHERE email = ?")
        ibm_db.bind_param(stmt, 1, session['email'])
        if ibm_db.execute(stmt):
            row = ibm_db.fetch_tuple(stmt)
            userId, password = row if row else (None, None)
            if password == oldPassword:
                try:
                    stmt_update = ibm_db.prepare(conn, "UPDATE users SET password = ? WHERE userId = ?")
                    ibm_db.bind_param(stmt_update, 1, newPassword)
                    ibm_db.bind_param(stmt_update, 2, userId)

                    if ibm_db.execute(stmt_update):
                        ibm_db.commit(conn)
                        msg = "Changed successfully"
                    else:
                        msg = "Failed"
                except Exception as e:
                    print(f"Error: {e}")
                    ibm_db.rollback(conn)
                    msg = "Failed"
            else:
                msg = "Wrong password"
        else:
            msg = "User not found"
        ibm_db.close(conn)
    return render_template("changePassword.html")


@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        conn = ibm_db.connect(dsn, "", "")
        try:
            stmt = ibm_db.prepare(conn, 'UPDATE users SET firstName = ?, lastName = ?, address1 = ?, address2 = ?, zipcode = ?, city = ?, state = ?, country = ?, phone = ? WHERE email = ?')
            ibm_db.bind_param(stmt, 1, firstName)
            ibm_db.bind_param(stmt, 2, lastName)
            ibm_db.bind_param(stmt, 3, address1)
            ibm_db.bind_param(stmt, 4, address2)
            ibm_db.bind_param(stmt, 5, zipcode)
            ibm_db.bind_param(stmt, 6, city)
            ibm_db.bind_param(stmt, 7, state)
            ibm_db.bind_param(stmt, 8, country)
            ibm_db.bind_param(stmt, 9, phone)
            ibm_db.bind_param(stmt, 10, email)
            if ibm_db.execute(stmt):
                ibm_db.commit(conn)
                msg = "Saved Successfully"
            else:
                msg = "Error occurred"

        except Exception as e:
            print(f"Error: {e}")
            ibm_db.rollback(conn)
            msg = "Error occurred"
        finally:
            ibm_db.close(conn)
        print(msg)
    return redirect(url_for('editProfile'))

@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)

@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    conn = ibm_db.connect(dsn, "", "")    
    try:
        stmt = ibm_db.prepare(conn, 'SELECT productId, name, price, description, image, stock FROM products WHERE productId = ?')
        ibm_db.bind_param(stmt, 1, productId)

        if ibm_db.execute(stmt):
            productData = ibm_db.fetch_tuple(stmt)
        else:
            productData = None
    except Exception as e:
        print(f"Error: {e}")
        productData = None
    finally:
        ibm_db.close(conn)
    return render_template("productDescription.html", data=productData, loggedIn = loggedIn, firstName = firstName, noOfItems = noOfItems)

@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        productId = int(request.args.get('productId'))
        conn = ibm_db.connect(dsn, "", "")         
        try:
            stmt_select = ibm_db.prepare(conn, "SELECT userId FROM users WHERE email = ?")
            ibm_db.bind_param(stmt_select, 1, session['email'])

            if ibm_db.execute(stmt_select):
                userId = ibm_db.fetch_tuple(stmt_select)[0]
                stmt_insert = ibm_db.prepare(conn, "INSERT INTO kart (userId, productId) VALUES (?, ?)")
                ibm_db.bind_param(stmt_insert, 1, userId)
                ibm_db.bind_param(stmt_insert, 2, productId)

                if ibm_db.execute(stmt_insert):
                    ibm_db.commit(conn)
                    msg = "Added successfully"
                else:
                    msg = "Error occurred while adding to cart"
            else:
                msg = "User not found"
        except Exception as e:
            print(f"Error: {e}")
            ibm_db.rollback(conn)
            msg = "Error occurred"

        finally:
            ibm_db.close(conn)

        return redirect(url_for('root'))


@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    conn = ibm_db.connect(dsn, "", "")
    stmt = ibm_db.prepare(conn, "SELECT userId FROM users WHERE email = ?")
    ibm_db.bind_param(stmt, 1, email)
    if ibm_db.execute(stmt):
        row = ibm_db.fetch_tuple(stmt)
        if row:
            userId = row[0]
        else:
            userId = None
    products=[]
    stmt = ibm_db.prepare(conn, "SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = ?")
    ibm_db.bind_param(stmt, 1, userId)
    if ibm_db.execute(stmt):
        while True:
            row = ibm_db.fetch_tuple(stmt)
            if not row:
                break
            products.append(row)    
    totalPrice = 0
    for row in products:
        totalPrice += float(row[2])
    ibm_db.close(conn)
    return render_template("cart.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)


@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = int(request.args.get('productId'))
    conn = ibm_db.connect(dsn, "", "")
    try:
        stmt_select_user = ibm_db.prepare(conn, "SELECT userId FROM users WHERE email = ?")
        ibm_db.bind_param(stmt_select_user, 1, email)
        if ibm_db.execute(stmt_select_user):
            userId = ibm_db.fetch_tuple(stmt_select_user)[0]
            stmt_delete = ibm_db.prepare(conn, "DELETE FROM kart WHERE userId = ? AND productId = ?")
            ibm_db.bind_param(stmt_delete, 1, userId)
            ibm_db.bind_param(stmt_delete, 2, productId)
            if ibm_db.execute(stmt_delete):
                ibm_db.commit(conn)
                msg = "Removed successfully"
            else:
                msg = "Error occurred while removing from cart"
        else:
            msg = "User not found"
    except Exception as e:
        print(f"Error: {e}")
        ibm_db.rollback(conn)
        msg = "Error occurred"
    finally:
        ibm_db.close(conn)
    return redirect(url_for('root'))


@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    conn = ibm_db.connect(dsn, "", "")
    stmt = ibm_db.exec_immediate(conn, "SELECT email, password FROM users")
    data = []
    while True:
        row = ibm_db.fetch_assoc(stmt)
        if not row:
            break
        data.append((row['EMAIL'], row['PASSWORD']))
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route("/checkout", methods=['GET','POST'])
def payment():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    conn = ibm_db.connect(dsn, "", "")
    stmt = ibm_db.prepare(conn, "SELECT userId FROM users WHERE email = ?")
    ibm_db.bind_param(stmt, 1, email)
    if ibm_db.execute(stmt):
        row = ibm_db.fetch_tuple(stmt)
        if row:
            userId = row[0]    
    products = []   
    stmt = ibm_db.prepare(conn, "SELECT products.productId, products.name, products.price, products.image FROM products, kart WHERE products.productId = kart.productId AND kart.userId = ?")
    ibm_db.bind_param(stmt, 1, userId)
    if ibm_db.execute(stmt):
        while True:
            row = ibm_db.fetch_tuple(stmt)
            if not row:
                break
            products.append(row) 
    totalPrice = 0
    for row in products:
        totalPrice += float(row[2])
        print(row)
        stmt = ibm_db.prepare(conn, "INSERT INTO Orders (userId, productId) VALUES (?, ?)")
        ibm_db.bind_param(stmt, 1, userId)
        ibm_db.bind_param(stmt, 2, row[0])
        ibm_db.execute(stmt)
    stmt = ibm_db.prepare(conn, "DELETE FROM kart WHERE userId = ?")
    ibm_db.bind_param(stmt, 1, userId)
    ibm_db.execute(stmt)        
    ibm_db.commit(conn)
    ibm_db.close(conn)
    return render_template("checkout.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        #Parse form data    
        password = request.form['password']
        email = request.form['email']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        zipcode = request.form['zipcode']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        phone = request.form['phone']
        conn = ibm_db.connect(dsn, "", "")
        try:
            stmt = ibm_db.prepare(conn, "INSERT INTO users (password, email, firstName, lastName, address1, address2, zipcode, city, state, country, phone) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
            ibm_db.bind_param(stmt, 1, hashlib.md5(password.encode()).hexdigest())
            ibm_db.bind_param(stmt, 2, email)
            ibm_db.bind_param(stmt, 3, firstName)
            ibm_db.bind_param(stmt, 4, lastName)
            ibm_db.bind_param(stmt, 5, address1)
            ibm_db.bind_param(stmt, 6, address2)
            ibm_db.bind_param(stmt, 7, zipcode)
            ibm_db.bind_param(stmt, 8, city)
            ibm_db.bind_param(stmt, 9, state)
            ibm_db.bind_param(stmt, 10, country)
            ibm_db.bind_param(stmt, 11, phone)
            if ibm_db.execute(stmt):
                ibm_db.commit(conn)
                msg='Insert sucessful'
                print("Insert successful")
            else:
                msg='Insert failed'
                print("Insert failed")
        except Exception as e:
            print(f"Error: {e}")
            ibm_db.rollback(conn)
        finally:
            ibm_db.close(conn)
        return render_template("login.html", error=msg)

@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

if __name__ == '__main__':
    app.run(debug=True)
