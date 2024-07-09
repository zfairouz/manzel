from flask import Flask, flash, render_template, request, redirect, url_for, jsonify
from flask_mysqldb import MySQL
from flask_wtf import FlaskForm
from wtforms import FileField, SubmitField
from werkzeug.utils import secure_filename
import os
# import joblib

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/images/'

app.config['SECRET_KEY'] = 'superfast'


#MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flaskapp'

mysql = MySQL(app)

# Load the trained model
# model = joblib.load('Housing.csv.joblib')


# home page
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT h.houses, h.title, h.id, h.price, h.location, c.name AS category_name
        FROM houses h
        JOIN categories c ON h.categories_id = c.id
        LIMIT 6;
    """)
    fetchdata = cur.fetchall()
    cur.close()
    return render_template('index.html', data=fetchdata)

@app.route('/admin', methods=['GET'])
def admin():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT h.houses, h.title, h.id, h.price, h.location, c.name AS category_name
        FROM houses h
        JOIN categories c ON h.categories_id = c.id;
    """)
    fetchdata = cur.fetchall()
    cur.close()
    
    return render_template('admin.html', data=fetchdata)  # Pass fetchdata as data

# update houses
@app.route('/update_houses/<int:id>', methods=['GET', 'POST'])
def update_houses(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM `houses` WHERE id = %s", (id,))
    house = cur.fetchone()
    
    if request.method == 'POST':
        file = request.files['houses']
        title = request.form['title']
        price = request.form['price']
        location = request.form['location']
        categories_id = request.form['categories_id']
        description = request.form['description'] 

        if file :
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
            
        else:
            filename = house[0]
        cur.execute("""UPDATE `houses` SET Houses = %s, Title = %s, Price = %s, 
            Location = %s, Categories_Id = %s, Description = %s
            WHERE Id = %s""", (filename, title, price, location, categories_id, description,  id))
        mysql.connection.commit()
        cur.close() 
        return redirect(url_for('index'))

        
    return render_template('update_houses.html', house=house)

# delete houses
@app.route('/delete_houses/<int:id>', methods=['POST'])
def delete_houses(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM `houses` WHERE Id = %s", (id,))
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('index'))

# add house 
@app.route('/add_house', methods=['GET', 'POST'])
def add_house():
        if request.method == 'POST':
            # Debugging print statement
            print("Form submitted")  
            file = request.files['houses']
            title = request.form['title']
            price = request.form['price']
            location = request.form['location']
            categories_id = request.form['categories_id']
            description = request.form['description']
            if file :
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename)))
                filename = secure_filename(file.filename)
    
            # Insert data into MySQL
            try:
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO `houses` (houses, title, id, price, location, categories_id, description ) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                            ( filename, title, id, price, location, categories_id, description))
                mysql.connection.commit()
                cur.close()
                # Debugging print statement
                print("Data inserted successfully")  
            except Exception as e:
                # Printing any SQL errors
                print(f"Error inserting data: {e}")  
            return redirect(url_for('index'))
        return render_template('add_house.html')

# How_we_are_page page
@app.route('/who', methods=['GET'])
def who():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT h.houses, h.title, h.id, h.price, h.location, c.name AS category_name
        FROM houses h
        JOIN categories c ON h.categories_id = c.id;
    """)
    fetchdata = cur.fetchall()
    cur.close()
    
    return render_template('who.html', data=fetchdata)

# Details
@app.route('/details/<int:id>')
def details(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT h.houses, h.title, h.location, h.description FROM `houses` h WHERE h.id = %s", (id,))
    house = cur.fetchone()
    cur.close()
    
    if house:
        return render_template('details.html', house=house)
    else:
        return "House not found", 404

@app.route('/search_in_offers', methods=['GET'])
def search_in_offers():
    cur = mysql.connection.cursor()
    
    # Fetch all categories for the filter dropdown
    cur.execute("SELECT id, name FROM categories")
    categories = cur.fetchall()
    
    # Get the selected category and page number from query parameters
    selected_category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    per_page = 12  # Number of cards to show per page
    
    # Base query
    
    query = """
        SELECT h.id, h.houses, h.title, h.price, h.location, c.name AS category_name
        FROM houses h
        JOIN categories c ON h.categories_id = c.id
    """
    
    # If a category is selected, add a WHERE clause
    if selected_category:
        query += " WHERE c.id = %s"
        cur.execute(query, (selected_category,))
    else:
        cur.execute(query)
    
    all_houses = cur.fetchall()
    cur.close()
    
    # Paginate the results
    start = (page - 1) * per_page
    end = start + per_page
    houses = all_houses[start:end]
    
    has_more = len(all_houses) > end
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # If it's an AJAX request, return JSON data
        return jsonify({
            'houses': houses,
            'has_more': has_more
        })
    
    return render_template('search_in_offers.html', 
                           data=houses, 
                           categories=categories, 
                           selected_category=selected_category,
                           has_more=has_more,
                           page=page)


if __name__ == "__main__":
    app.run(debug=True)