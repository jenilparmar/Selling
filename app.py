import re
from flask import Flask, render_template, request
from dotenv import load_dotenv
import random   
import pymongo
from datetime import datetime , timedelta
import os 

load_dotenv()



TABLE_NUMBER=[]
# Flask app initialization
USERNAME = "Spider_Man"
PASSWORD = "123"
app = Flask(__name__)
connection_string = os.getenv("CONNECTIONSTRING")

# MongoDB initialization
client = pymongo.MongoClient(connection_string)
db = client["Restaurant"]
item_collection = db["Items"]
order_collection = db["Orders"]

# Retrieve existing items from the database
items_cursor = item_collection.find()
ITEMS = list(items_cursor)[0]
del ITEMS["_id"]

# Add item to database function
def AddToDatabase(thali, dish, price):
    global ITEMS
    
    if thali in ITEMS:
        ITEMS[thali][dish] = int(price)
    else:
        ITEMS[thali] = {dish: int(price)}
    
    item_collection.update_one({}, {"$set": ITEMS})
    print("Added")

# Delete item from database function
def delete_items(key1, key2):
    for category, item in zip(key1, key2):
        item_collection.update_one({}, {"$unset": {category + "." + item: ""}})
        if not item_collection.find_one({category: {"$exists": True}}):
            item_collection.update_one({}, {"$unset": {category: ""}})
    print("Deleted")
quotes = [
        "Life is uncertain. Eat dessert first.",
        "All you need is love. But a little chocolate now and then doesn't hurt.",
        "There is no sincerer love than the love of food.",
        "Cooking is like love. It should be entered into with abandon or not at all.",
        "People who love to eat are always the best people.",
        "Food is symbolic of love when words are inadequate.",
        "The only thing I like better than talking about food is eating.",
        "One cannot think well, love well, sleep well, if one has not dined well.",
        "Food is our common ground, a universal experience.",
        "Eat breakfast like a king, lunch like a prince, and dinner like a pauper."
    ]
    

@app.route('/')
def index():
    q = quotes[random.randint(0,len(quotes)-1)]
    return render_template('index.html', q=q)


@app.route('/items')
def items():
    dish = request.args.get('dish')
    if dish not in ITEMS:
        return f"Invalid Dish: {dish}"
    thali_data = ITEMS[dish]
    return render_template('Items.html', dish=dish, Thali=thali_data)

@app.route('/order_page', methods=["POST","GET"])
def order_page():
    
        # table_number = request.form['table_number']
        q = quotes[random.randint(0,len(quotes)-2)]
        # TABLE_NUMBER.clear()  # Clear the list before appending the new table number
        # TABLE_NUMBER.append(int(table_number))
        return render_template('Order.html', ITEMS={key: value for key, value in ITEMS.items() if key != '_id'}, q=q)
    


@app.route('/submit_order', methods=['POST'])
def submit_order():
    if request.method == 'POST':
        selected_items = request.form.getlist('item')
        quantities = {item: int(request.form.get(f'{item}_quantity', 0)) for item in selected_items}
        table_number = request.form["table_number"]
        order_details = {
                'table_number': int(table_number),
                'items': {item:quantity for item, quantity in quantities.items()},
                'datetime': datetime.now()  # Add current date and time
            }
        order_collection.insert_one(order_details)

        total_price = 0
        for item, quantity in quantities.items():
            for category, items in ITEMS.items():
                if item in items:
                    total_price += items[item] * quantity
                    break
        return render_template('OrderSuccess.html', quantities=quantities, total_price=total_price, ITEMS={key: value for key, value in ITEMS.items() if key != '_id'})

@app.route('/Added' ,methods=["GET","POST"])
def Added():
    if request.method=="POST":
        Thali = request.form['Thali']
        Dish = request.form['Dish']
        Price = request.form['Price']
        AddToDatabase(Thali,Dish,Price)
        return render_template('Added.html',Thali=Thali,Dish=Dish,Price=Price)
    else:
        return "Nothing To Add!!"

# Route for management page
@app.route('/Management',methods=['POST','GET'])
def Management():
    if request.method=="GET":
        return render_template('Authentication.html')
    if request.method=="POST":
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password==PASSWORD:
            return render_template('Management.html',ITEMS={key: value for key, value in ITEMS.items() if key != '_id'})
        else:
            return "Wrong UserName or Password!"
# Route for removing items
@app.route('/RemoveItem', methods=["POST"])
def RemoveItem():
    if request.method == "POST":
        removed_items = []  # Initialize a list to store removed items
        key1 = []
        key2 = []
        for key, value in request.form.items():
            if value == 'on':  # Check if the checkbox was checked
                parts = key.split("-")
                if len(parts) == 2:  # Ensure exactly two parts after splitting
                    category, item = parts
                    key1.append(category.strip())  # Strip extra spaces
                    key2.append(item.strip())      # Strip extra spaces
                    removed_items.append(item.strip())  # Add the removed item to the list
                else:
                    print(f"Illegal key format: {key}")
        delete_items(key1=key1, key2=key2)
        
        return render_template('RemoveItem.html', removed_items=removed_items)  # Pass removed_items to the template
    else:
        return "Nothing to Remove!!"
from datetime import datetime, timezone

@app.route('/Billings_and_Managements', methods=['POST', 'GET'])
def Billings_and_Managements():
    if request.method == "GET":
        return render_template('Authentication2.html')
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            # Get today's date and time in UTC
            today_datetime = datetime.now(timezone.utc)
            # Set time component to midnight
            today_datetime = today_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
            # Query orders for today
            Order_Thali = {}
            res = order_collection.find({"datetime": {"$gte": today_datetime}})
            for order in res:
                Order_Thali[order['_id']] = order
            return render_template('Billings_and_Managements.html', Order_Thali=Order_Thali)
        else:
            return "You Are Not A Owner!!"
from flask import render_template

@app.route('/view_order_details/<int:table_number>')
def view_order_details(table_number):
    print("Table Number:", table_number)
    
    # Find matching orders for the given table number
    matching_orders = order_collection.find({'table_number': table_number})
    
    # Extracting dishes and quantities from matching orders
    dishes_quantities = matching_orders[0]['items']
    
    vangi = [dish for dish, quantity in dishes_quantities.items()]
    quantities = [quantity for dish, quantity in dishes_quantities.items()]
    
    # Fetching prices of dishes
    dc = {}
    x = 0
    for i in item_collection.find():
        for j in i:
            if x == 0:
                x = 1
                continue
            for k in i[j]:
                dc[k] = i[j][k]
    
    # Calculating total amount for each dish
    total_amount = sum([dc[dish] * quantities[vangi.index(dish)] for dish in vangi])
    print(total_amount)
    return render_template('OrderSuccess2.html', orders=matching_orders, vangi=vangi, dc=dc, quantities=quantities, total_amount=total_amount)


@app.route('/delete_order/<int:table_number>')
def delete_order(table_number):
    # mydoc = order_collection.find({'table_number':table_number})
    order_collection.delete_one({"table_number":table_number})
    return f'<script>alert("Order of Table Number {table_number} is Deleted!!")</script>'
if __name__ == "__main__":
    app.run(debug=True , host='0.0.0.0')