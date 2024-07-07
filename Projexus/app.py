# import os
from cs50 import SQL
from datetime import date
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from fractions import Fraction
from json import loads
from math import floor, ceil
from werkzeug.security import check_password_hash, generate_password_hash


import render

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///projexus.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@render.login_required
def homepage():
    rows = db.execute(
        "SELECT employees.level FROM employees JOIN users ON users.employee_id=employees.id WHERE users.id = ?", session['user_id'])
    level = rows[0]["level"]
    # If manager
    if level == 0:
        # Determine current quarter
        today = date.today()
        y = today.year
        m = today.month
        statements = []
        # Get the monthly numbers
        for month in range(0, 3):
            # Format date-time string
            statement = {}
            if m < 10:
                dtgstring = f'{y}-0{m}'
                statement['month'] = f'0{m}'
            else:
                dtgstring = f'{y}-{m}'
                statement['month'] = m
            # Ensure proper year and month values are used
            if m == 1:
                m = 12
                y -= 1
            else:
                m -= 1
            # Get all invoices for the month
            invoices = db.execute(
                "SELECT * FROM invoices WHERE strftime('%Y-%m', dtg) = ?", dtgstring)
            ar = float(0)
            outstanding = float(0)
            ve = float(0)
            if len(invoices) >0:
                for invoice in invoices:
                    # Calculate Accounts receivable (ar) and Amount not received (outstanding)
                    ar += float(invoice['total'])
                    if invoice['status_id'] == 0:
                        outstanding += float(invoice['total'])
                    items = db.execute("SELECT * FROM items WHERE invoice_id=?", invoice['id'])
                    # Calculate Vender expenses (ve)
                    for item in items:
                        mc = float(item['material_cost'])
                        sheets = int(item['sheets'])
                        ve += mc*sheets
            # Store the numbers for use in the html
            statement['ar'] = ar
            statement['outstanding'] = outstanding
            statement['ve'] = ve
            statement['labor'] = 'coming soon'
            statement['fe'] = 'coming soon'
            statement['net'] = ar-ve
            statements.append(statement)
        # Display the homepage
        return render_template("homepage.html", statements=statements, client=session['current_client'], level=level, employee=session['employee'])
    else:
        workload = []
        return render_template("homepage.html", workload=workload, client=session['current_client'], level=level, employee=session['employee'])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render.apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render.apology("must provide password", 400)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return render.apology("invalid username or password", 401)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        employee_id=rows[0]["employee_id"]
        # Establish default client
        render.select_client()
        # Redirect user to home page
        _=db.execute("SELECT * from Employees WHERE id=?", employee_id)
        employee=_[0]
        session["employee"]=employee
        return redirect("/")

    # Get
    else:
        client = {'name': ''}
        return render_template("login.html", client=client)


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Get User provided input
        id = request.form.get("employeeId")
        pw = request.form.get("password")
        pwc = request.form.get("confirmation")
        _=db.execute("SELECT name FROM employees WHERE ID=?",id)
        first,last=_[0]["name"].split(' ')
        username=first[0].lower() + last.lower()
        # Verify Usernmae was provided
        if not username:
            return render.apology("Employee ID not Found", 401)
        # Ensure no duplication of usernames or employee accounts
        account_exists = db.execute("SELECT username FROM users WHERE employee_id=?", id)
        if len(account_exists)==1:
            return render.apology("An account for that ID already exists, contact your manager")
        else:

            n=0
            while True:
                username_exists = db.execute("SELECT username FROM users WHERE username=?", username)
                if len(username_exists)==1:
                    n+=1
                    username=username + str(n)
                else:
                    break

        # Ensure passwords match
        if not pw or pw != pwc:
            return render.apology("Could not establish password", 401)
        db.execute("INSERT INTO users (username, hash, employee_id) VALUES(?, ?, ?)",
                   username, generate_password_hash(pw), id)
        flash(f"Account Created successfully, Username is {username}")
        return render_template("login.html", username=username)
    # Get
    else:
        return render_template("register.html")


@app.route("/clients", methods=["GET", "POST"])
@render.login_required
def clients():
    if request.method == "POST":
        # Ensure a client was selected and get its id
        query = request.form.get("client_id")
        if not query:
            return render.apology('Invalid or No client selected', 401)
        # Select the client and display its page
        else:
            render.select_client(query)
            return render.client_page()
    # Get
    else:
        # Generate list of clients for user to choose from
        client_list = db.execute(
            "SELECT * FROM clients WHERE name <> 'Quick Order' ORDER BY name")
        units = render.load_units()
        return render_template("clients.html", clients=client_list, client=session['current_client'], units=units)


@app.route("/client", methods=["GET", "POST"])
@render.login_required
def client():
    # Update any information that the user requests to update
    if request.method == "POST":
        if "index" in request.form:
            next_index = int(request.form.get("index"))+20
            return render.client_page(next_index)
        ename = request.form.get("name")
        if not ename:
            flash("no name entered")
            return render.client_page()
        # Ensure data is properly formated
        try:
            euid = int(request.form.get("unitId"))
            emm = int(request.form.get("materialMarkup"))
            eam = int(request.form.get("additionalMarkup"))
            epn = request.form.get("phoneNumber")
            eba = request.form.get("billingAddress")
        except ValueError:
            flash("Something Went Wrong")
            return render.client_page()
        if request.form.get("taxOption") == "on":
            taxed = 0
        else:
            taxed = 1
        # Update the database with new values passed by the user
        db.execute("UPDATE clients SET name=?, unit_id=?, taxed=?, material_markup=?, additional_markup=?, phone_number=?, billing_address=? WHERE id=?",
                   ename, euid, taxed, emm, eam, epn, eba, session['current_client']['id'])
        # Validate data was saved correctly
        validator = db.execute("SELECT * from clients WHERE id=?",
                               session['current_client']['id'])
        if len(validator) == 1 and ename == validator[0]["name"] and euid == validator[0]["unit_id"] and emm == validator[0]["material_markup"] and eam == validator[0]["additional_markup"] and epn == validator[0]["phone_number"] and eba == validator[0]["billing_address"]:
            render.select_client(session['current_client']['id'])
            flash("Client Updated Successfully")
            return render.client_page()
        else:
            return render.apology("Something went wrong")
    # Get
    else:
        return render.client_page()

@app.route("/api/calculate_total", methods = ["POST"])
def calculate_total():
    data = request.get_json()
    checkboxes = data.get('checkboxes', [])
    totalNtax = 0
    expectedProfit = 0
    for checkbox in checkboxes:
        id = checkbox.get('id')
        excess_charged = checkbox.get('checked')
        item = db.execute("SELECT * FROM cart WHERE id = ?", id)
        if excess_charged:
            if item[0]['total']==item[0]['sub_total']:
                total = float(item[0]['sub_total']) + float(item[0]['excess_material_charge'])
                profit = float(item[0]['profit']) + float(item[0]['excess_material_charge'])
                db.execute("UPDATE cart SET profit = ?, total = ? WHERE id = ?", profit, total, id)
            else:
                total = item[0]['total']
                profit = item[0]['profit']

        else:
            total=item[0]['sub_total']
            if item[0]['total'] == total:
                profit = item[0]['profit']
            else:   
                profit = float(item[0]['profit']) - float(item[0]['excess_material_charge'])
                db.execute("UPDATE cart SET profit = ?, total = ? WHERE id = ?", profit, total, id)
            
        totalNtax +=total
        expectedProfit += profit

    totalYtax = float(1.0825*totalNtax)
    tax = float(.0825*totalNtax)
    
    return jsonify({ 'totalNtax': totalNtax, 'totalYtax': totalYtax, 'tax': tax, 'expectedProfit': expectedProfit})

@app.route("/order", methods=["GET", "POST"])
@render.login_required
def order():
    if request.method == "POST":

        # Edit the cart
        if "edit" in request.form:
            toparse = request.form.get('edit')
            action, item = toparse.split(" ")
            action = int(action)
            item = int(item)
            if action == 0:
                db.execute("DELETE FROM cart WHERE id=?", item)
                return render.order_page()
            elif action == 1:
                _ = db.execute("SELECT * FROM cart WHERE id=?", item)
                job_id = _[0]["job_id"]
                name = _[0]["name"]
                material_id = _[0]["material_id"]
                material_cost = _[0]["material_cost"]
                quantity = _[0]["units"]
                hem = _[0]["hem"]
                dimensions = _[0]["dimensions"]
                d = dimensions.split('" x ')
                d[-1] = d[-1].replace('"', '')
                folds = len(d)-1
                angles = _[0]["angles"]
                a = angles.split(', ')
                db.execute("DELETE FROM cart WHERE id=?", item)
                return render.order_page(jobId=job_id, itemName=name, materialId=material_id, materialCost=material_cost, quantity=quantity, folds=folds, hem=hem, d=d, a=a)

        # Validate job_id or add new job
        try:
            job_id = int(request.form.get('jobId'))
        except Exception:
            flash("No jobsite selected")
            return render.order_page()
        if job_id is None:
            flash('select a job id')
            return render.order_page()

        if job_id == 1:
            jobName = request.form.get('newJobName')
            jobAddress = request.form.get('newJobAddress')

            db.execute("INSERT INTO jobs (name, address) VALUES(?, ?)",
                       jobName, jobAddress)
            job_row = db.execute("SELECT last_insert_rowid()")
            job_id = job_row[0]['last_insert_rowid()']
        # Validate line item name
        name = request.form.get("itemName")
        try:
            material_id = int(request.form.get("materialId"))
        except Exception:
            return render.carterror("invalid material")
        else:
            pass
        # Validate material dimensions
        material_dimensions = request.form.get("sheetDimensions")
        material_dimensions = material_dimensions.replace(' ', '')
        material_dimensions = material_dimensions.replace('"', '')
        material_dimensions = material_dimensions.replace("'", '')
        try:
            length, width = material_dimensions.split("x")
            length = int(length)
            width = int(width)

        except ValueError:
            return render.carterror("invalid dimensions")
        # Validate the rest of user input
        try:
            material_cost = float(request.form.get("materialCost"))
            unit_id = int(request.form.get("unit"))
            quantity = int(request.form.get("quantity"))
            folds = int(request.form.get("folds"))
            hem = int(request.form.get("hem"))
        except ValueError:
            return render.carterror("invalid data submitted")
        d = []
        # Calculate the stretch (the sum of the lengths of each fold)
        stretch = 0
        for i in range(0, folds+1):
            # Get the user input for each dimension
            f = "d"+str(i)
            measurement = request.form.get(f).strip()
            # If decimal value...
            if "." in measurement:
                try:
                    stretch += float(measurement)
                    whole_number, decimal = measurement.split(".")
                    fraction = Fraction(int(decimal), 10**len(decimal))
                    d.append(whole_number + "-" + str(fraction))
                except ValueError:
                    return render.carterror('Invalid dimensional data found')
            # If mixed number...
            elif (" " in measurement or "-" in measurement) and "/" in measurement:
                try:
                    whole_number, fraction = measurement.split(" ")
                    measurement = measurement.replace(" ", "-")
                except ValueError:
                    try:
                        whole_number, fraction = measurement.split("-")
                    except ValueError:
                        return render.carterror('Invalid dimensional data found')
                numerator, denominator = fraction.split("/")
                try:
                    stretch += round(float(int(whole_number) +
                                     float(int(numerator)/int(denominator))), 2)
                    d.append(measurement)
                except ValueError:
                    return render.carterror('Invalid dimensional data found')
            # If fraction
            elif "/" in measurement:
                try:
                    numerator, denominator = measurement.split("/")
                    stretch += round(float(int(numerator)/int(denominator)), 2)
                    d.append(measurement)
                except ValueError:
                    return render.carterror('Invalid dimensional data found')
            # If whole number
            else:
                try:
                    stretch += float(measurement)
                    d.append(measurement)
                except ValueError:
                    return render.carterror('Invalid dimensional data found')
        # Convert to fraction and whole number strings for storage and for display to user
        d[-1] = str(d[-1])+'"'
        dimension_string = '" x '.join(d)
        d[-1] = d[-1].replace('"', '')

        # Angle String
        a = []
        if folds > 0:
            for i in range(0, folds):
                # Get the user input for each angle
                f = "a"+str(i)
                value = request.form.get(f).strip()
                a.append(value)
            angles = ', '.join(a)
        else:
            angles = ""
        
        # Calculate resale value
        material_resale = material_cost * \
            (1 + int(session['current_client']["material_markup"]) / 100)
        material_resale = ceil(material_resale*100)/100
        if folds >= 2:
            fold_fee = float(.1*(folds+hem-2))
        elif folds == 1 and hem == 2:
            fold_fee = float(.1)
        else:
            fold_fee = float(0)
        # per piece variable assignment
        if unit_id == 0:
            charge = 1.35 + fold_fee
            units_per_sheet = floor(length / stretch)
            unit_price = round((charge + (material_resale / units_per_sheet)), 2)
        # per foot variable assignment
        elif unit_id == 1:
            _ = db.execute("SELECT charge FROM materials WHERE id=?", material_id)
            charge = float(_[0]["charge"])+fold_fee
            units_per_sheet = floor(length / stretch)*width
            unit_price = round((charge + (material_resale / units_per_sheet))
                               * (1 + int(session['current_client']["additional_markup"]) / 100), 2)
        else:
            return render.apology("No algorithm for selected unit")

        left_over_piece = length-stretch
        sheets_required_base = float(quantity / units_per_sheet)
        sheets_required_actual = ceil(sheets_required_base)
        material_base_cost = round(sheets_required_actual*material_cost, 2)
        material_client_cost = round(sheets_required_actual*material_resale, 2)
        labor_charge = round(charge*quantity, 2)
        sub_total = unit_price * quantity
        excess_material_charge = material_resale * (sheets_required_actual - sheets_required_base)
        total = round(sub_total, 2)
        profit = round(total - material_base_cost, 2)
        # Add the item to the cart
        db.execute("INSERT INTO cart (client_id, job_id, name, material_id, material_cost, unit_id, units, dimensions, unit_price, sub_total, excess_material_charge, total, sheets, profit, hem, angles) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   session['current_client']["id"], job_id, name, material_id, material_cost, unit_id, quantity, dimension_string, unit_price, sub_total, excess_material_charge, total, sheets_required_actual, profit, hem, angles)

        reuse_item = int(request.form.get('add'))
        if reuse_item == 0:
            flash("Item Added")
            return render.order_page()
        else:
            flash("Item Added")
            return render.order_page(jobId=job_id, itemName=name, materialId=material_id, sheetDimensions=material_dimensions, materialCost=material_cost, quantity=quantity, folds=folds, hem=hem, d=d, a=a)
    else:
        if request.args.get('source') == "quick":
            render.select_client()
            return render.order_page()
        else:
            return render.order_page()


@app.route("/materials", methods=["GET", "POST"])
@render.login_required
def materials():

    if request.method == "POST":
        # Get selected material and load its page
        id = request.form.get("materialId")
        selected_material = db.execute(
            "SELECT * FROM materials WHERE id = ?", id)
        return render_template("material.html", client=session['current_client'], material=selected_material)
    # Render the list of materials
    else:
        material_list = render.load_materials()
        return render_template("materials.html", client=session['current_client'], materials=material_list)


@app.route("/material", methods=["GET", "POST"])
@render.login_required
def material():
    material_list = render.load_materials()
    if request.method == "POST":
        # Ensure requested update values are formatted properly
        try:
            id = int(request.form.get("id"))
            ename = request.form.get("name")
            egauge = int(request.form.get("gauge"))
            echarge = float(request.form.get("charge"))
        except ValueError:
            flash("Invalid data submitted, no changes saved")
            return render_template("materials.html", materials=material_list)
        # Update the materials
        db.execute("UPDATE materials SET name=?,gauge=?,charge=? WHERE id=?",
                   ename, egauge, echarge, id)
        # Validate changes
        validator = db.execute("SELECT * from materials WHERE id=?", id)
        if len(validator) == 1 and ename == validator[0]["name"] and egauge == validator[0]["gauge"] and echarge == validator[0]["charge"]:
            flash("Material Updated successfully")
            material_list = render.load_materials()
            return render_template("materials.html", materials=material_list, client=session['current_client'])
    # Allow user to add a material
    else:
        return render_template("newmaterial.html", client=session['current_client'])


@app.route("/newmaterial", methods=["GET", "POST"])
@render.login_required
def newmaterial():
    if request.method == "POST":
        material_list = render.load_materials()
        try:
            ename = request.form.get("name")
            egauge = int(request.form.get("gauge"))
            echarge = float(request.form.get("charge"))
        except ValueError:
            flash("Invalid data submitted, no changes saved")
            return render_template("materials.html", materials=materials, client=session['current_client'])
        if ename:
            db.execute("INSERT INTO materials (name, gauge, charge) VALUES(?, ?, ?)",
                       ename, egauge, echarge)
            flash("Material successfully added")
            material_list = render.load_materials()
            return render_template("materials.html", materials=material_list, client=session['current_client'])
        else:
            flash("No name provided, material not saved")
            return render_template("materials.html", materials=material_list, client=session['current_client'])
    else:
        return render_template("newmaterial.html", client=session['current_client'])


@app.route("/newclient", methods=["GET", "POST"])
@render.login_required
def newclient():
    if request.method == "POST":
        try:
            name = request.form.get("name")
            material_markup = int(request.form.get("mm"))
            additional_markup = int(request.form.get("am"))
            unit_id = request.form.get("unit_id").lower()
        except ValueError:
            return render.apology("Invalid Data Submitted", 400)
        if request.form.get("taxOption") == "on":
            taxed = 0
        else:
            taxed = 1
        billing_address = request.form.get("address")
        if not billing_address:
            billing_address="none"
        phone_number = request.form.get("phone")
        if not phone_number:
            phone_number="none"
        if unit_id is not None and name and billing_address and phone_number:
            balance = 0
            db.execute("INSERT INTO clients (name, billing_address, phone_number, material_markup, additional_markup, unit_id, taxed, balance) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                       name, billing_address, phone_number, material_markup, additional_markup, unit_id, taxed, balance)
            rows = db.execute("SELECT id FROM clients WHERE name = ?", name)
            id = rows[0]["id"]
            render.select_client(id)
            invoices = render.load_invoices()
            return render.client_page()
        else:
            return render.apology("Invalid Data Submitted", 400)
    else:
        units = render.load_units()
        return render_template("newclient.html", units=units, client=session['current_client'])


@app.route("/invoice", methods=["GET", "POST"])
@render.login_required
def invoice():
    if request.method == "POST":
        order = db.execute("SELECT * FROM cart WHERE client_id =?", session['current_client']["id"])
        try:
            delivery_fee = float(request.form.get("deliveryFee"))
        except Exception:
            flash("Couldn't Assign Delivery fee")
            return render.order_page()

        if session['current_client']["id"] == 0:
            status_id = 1
        else:
            status_id = 0
        db.execute("INSERT INTO invoices (dtg, client_id, delivery_fee, status_id) VALUES (CURRENT_TIMESTAMP,?, ?, ?)",
                   session['current_client']['id'], delivery_fee, status_id)
        invoice_row = db.execute("SELECT last_insert_rowid()")
        invoice_id = invoice_row[0]['last_insert_rowid()']
        charge = delivery_fee
        excessStateRawData = request.form.get('excessCheckStates')
        excessCheckStates = loads(excessStateRawData)

        for item in order:
            for state in excessCheckStates:
                print(state['id'])
                print(item['id'])
                print(state['checked'])
                condition = (item['id'] == state['id'])
                print(condition)
                if int(item['id']) == int(state['id']):
                    if not state['checked']:
                        item['excess_material_charge']=0
                        print(item['excess_material_charge'])
                        break
            charge += item['total']

            db.execute("INSERT INTO items (dtg, invoice_id, job_id, name, material_id, unit_id, units, dimensions, sub_total, excess_material_charge, total, unit_price, sheets, profit, hem, material_cost) VALUES(CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       invoice_id, item['job_id'], item['name'], item['material_id'], item['unit_id'], item['units'], item['dimensions'], item['sub_total'], item['excess_material_charge'], item['total'], item['unit_price'], item['sheets'], item['profit'], item['hem'], item['material_cost'])
        # send to client home with updated invoice list
        taxOption = request.form.get("taxOption")
        if taxOption == "on":
            charge = charge * 1.0825
            
        db.execute("UPDATE invoices SET total=? WHERE id=?", charge, invoice_id)
        db.execute("DELETE FROM cart WHERE client_id=?", session['current_client']['id'])
        if status_id == 0:
            client_row = db.execute("SELECT balance FROM clients WHERE id=?",
                                    session['current_client']['id'])
            balance = client_row[0]['balance']+charge
            db.execute("UPDATE clients SET balance=? WHERE id=?",
                       balance, session['current_client']['id'])
        flash("Order Placed")
        return render.client_page()


@app.route("/payinvoice", methods=["POST"])
@render.login_required
def payinvoice():
    try:
        invoices = request.form.getlist("paid")
    except ValueError:
        flash("Something Went Wrong")
        return render.invoices_page()
    for id in invoices:
        id = int(id)
        paymentr = db.execute("SELECT total FROM invoices WHERE id=?", id)
        payment = paymentr[0]['total']
        balance = float(session['current_client']['balance']) - payment
        db.execute("UPDATE clients SET balance=? WHERE id=?",
                   balance, session['current_client']['id'])
        db.execute("UPDATE invoices SET status_id='1' WHERE id=?", id)
    flash("Invoice Updated Successfully")
    site=request.form.get("site")
    if site=="invoices":
        return render.invoices_page()
    elif site=="client":
        return render.client_page()


@app.route("/ordermaterials", methods=["GET", "POST"])
@render.login_required
def ordermaterials():
    if request.method == "POST":
        selected_ids = request.form.getlist('ordered')
        if "buyAll" in request.form:
            for id in selected_ids:
                items = db.execute(
                    "UPDATE items SET material_purchase_status=1 WHERE material_id=?", id)
        if "buySome" in request.form:
            for id in selected_ids:
                items = db.execute("UPDATE items SET material_purchase_status=1 WHERE id=?", id)

        return render.order_materials_page()
    else:
        return render.order_materials_page()


@app.route("/invoices", methods=["GET", "POST"])
@render.login_required
def invoices():
    if request.method == "POST":
        return render.apology("todo")
    if request.method == "GET":
        return render.invoices_page()
