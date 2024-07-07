from functools import wraps
from cs50 import SQL
from datetime import date
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from fractions import Fraction
from math import floor, ceil
from werkzeug.security import check_password_hash, generate_password_hash

db = SQL("sqlite:///projexus.db")


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", code=code, message=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def carterror(message):
    flash(message)
    return order_page()


def select_client(id=0):
    client = db.execute("SELECT * FROM clients WHERE id = ?", (id,))
    session['current_client'] = client[0]
    return


def load_cart():
    client_id = session['current_client']['id']
    return db.execute(
        "SELECT * FROM cart WHERE client_id = ?", (client_id,))


def load_clients():
    rows = db.execute("SELECT id, name FROM clients")
    clients = []
    for client in rows:
        id = client["id"]
        name = client["name"]
        clients.append({"id": id, "name": name})
    return clients


def load_invoices(page="invoices", index=0, client=None):
    if page == "client":
        status_id = 0
        invoices = db.execute("SELECT * FROM invoices WHERE client_id=? AND status_id=? ORDER BY dtg DESC LIMIT 20 OFFSET ?",
                              session['current_client']['id'], status_id, index)

    elif page == "invoices":
        if client:
            invoices = db.execute(
                "SELECT invoices.*, clients.name AS client_name FROM invoices JOIN clients on invoices.client_id=clients.id WHERE client_id=? ORDER BY dtg DESC LIMIT 20 OFFSET ?", client, index)
        else:
            invoices = db.execute(
                "SELECT invoices.*, clients.name AS client_name FROM invoices JOIN clients on invoices.client_id=clients.id ORDER BY dtg DESC LIMIT 20 OFFSET ?", index)
    for invoice in invoices:
        datetime = invoice['dtg']
        date, time = datetime.split(" ")
        y, m, d = date.split('-')
        date = f"{m}-{d}"
        m = int(m)+3
        if m > 12:
            m = str(m-12)
            y = str(int(y)+1)
        due_date = f"{y}-{m}-10"
        invoice['due'] = due_date
        items = db.execute(
            "SELECT items.*, jobs.name AS job, jobs.address AS address, materials.name AS material FROM items JOIN jobs on items.job_id=jobs.id JOIN materials on items.material_id=materials.id WHERE invoice_id= ?", invoice['id'])
        invoice["items"] = items
    return invoices


def load_jobs():
    return db.execute("SELECT * FROM jobs")


def load_materials():
    return db.execute("SELECT * FROM materials ORDER BY name")


def load_units():
    return db.execute("SELECT * FROM units")


def get_profit(cart):
    profit = 0
    if len(cart) != 0:
        for item in cart:
            profit += float(item["profit"])
    return profit


def get_total(cart):
    totalNtax = 0
    if len(cart) != 0:
        for item in cart:
            totalNtax += float(item["total"])
    totalYtax = float(1.0825*totalNtax)
    tax = float(.0825*totalNtax)
    return tax, totalNtax, totalYtax


def client_page(invoice_index=0):
    select_client(session['current_client']['id'])
    invoices = load_invoices(page="client", index=invoice_index)
    jobs = load_jobs()
    units = load_units()
    try:
        result_count = len(invoices)
    except TypeError:
        result_count = 0
    return render_template("client.html", client=session['current_client'], units=units, invoices=invoices, jobs=jobs, resultCount=result_count)


def invoices_page(current_index=0):
    invoices = load_invoices(page="invoices", index=current_index)
    next_index_min = current_index+20
    next_index_max = next_index_min+19
    try:
        result_count = len(invoices)
    except TypeError:
        result_count = 0
    if next_index_max > result_count:
        next_index_max = result_count
    next_range = f"{next_index_min} - {next_index_max}"
    return render_template("invoices.html", client=session['current_client'], invoices=invoices, currentIndex=current_index, nextRange=next_range, resultCount=result_count)


def order_page(jobId="", itemName="", materialId="", sheetDimensions="", materialCost="", quantity=0, folds=0, hem=0, d=None, a=None):
    if not d:
        d = []
    if not a:
        a = []
    cart = load_cart()
    jobs = load_jobs()
    jobName = ""
    if jobId:
        for job in jobs:
            if job['id'] == jobId:
                jobName = job['name']
                break
    materials = load_materials()
    materialName = ""
    for material in materials:
        if material['id'] == materialId:
            materialName = material['name']
            break
    tax, totalNtax, totalYtax = get_total(cart)
    units = load_units()
    profit = get_profit(cart)
    print(jobId)
    return render_template("order.html", client=session['current_client'], materials=materials, units=units, cart=cart, tax=tax, totalNtax=totalNtax, totalYtax=totalYtax, profit=profit, jobs=jobs, jobId=jobId, jobName=jobName, itemName=itemName, materialId=materialId, materialName=materialName, sheetDimensions=sheetDimensions, materialCost=materialCost, quantity=quantity, folds=folds, hem=hem, d=d, a=a)


def order_materials_page():
    to_order_rows = db.execute(
        "SELECT id, invoice_id, name, material_id, sheets FROM items WHERE material_purchase_status=0")
    materials = load_materials()
    material_totals = []
    item_list = []
    for material in materials:
        needed = 0
        for item in to_order_rows:
            if item["material_id"] == material["id"]:
                needed += item["sheets"]
                item_list.append({"id": item["id"], "invoice_id": item["invoice_id"], "name": item["name"],
                                 "materialId": material["id"], "materialName": material["name"], "needed": item["sheets"]})
        if needed > 0:
            material_totals.append(
                {"id": material["id"], "name": material["name"], "needed": needed})

    return render_template("ordermaterials.html", client=session['current_client'], materialTotals=material_totals, itemList=item_list)
