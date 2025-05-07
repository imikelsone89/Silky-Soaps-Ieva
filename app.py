from flask import Flask, render_template, request, redirect, url_for, Response
import sqlite3
from pathlib import Path
app = Flask(__name__)

def get_db_connection():
    """
    Izveido un atgriež savienojumu ar SQLite datubāzi
    """
    #Atrod ceļu uz datubāzes failu (tas atrodas tajā pašā mapē, kur šis fails)
    db = Path(__file__).parent/"silky_soaps_db.db"
    #Izveido savienojumu ar SQLite datubāzi
    conn = sqlite3.connect(db)
    #Nodrošina, ka rezultāti būs pieejami, kā vārdnīcas (piemēram: product["name"])
    conn.row_factory = sqlite3.Row
    #Atgriež savienojumu
    return conn

@app.route("/")
def home():
    return render_template("index.html")

#Maršruts, kas atbild uz pieprasījumu/produkti
@app.route("/produkti")
def products():
    conn = get_db_connection()
    products = conn.execute("""
        SELECT products.*, price.price AS price
        FROM products
        LEFT JOIN price ON products.price_id = price.id
    """).fetchall()
    conn.close()#Aizver savienojumu ar datubāzi
    #Atgriež HTML veidni "products.html", padodot produktus veidnei
    return render_template("products.html", products=products)

# Maršruts, kas atbild uz pieprasījumu, piemēram: /produkti/3
# Šeit <int:product_id> nozīmē, ka URL daļā gaidāms produkta ID kā skaitlis
@app.route("/produkti/<int:product_id>")
def products_show(product_id):
    conn = get_db_connection() # Pieslēdzas datubāzei
    # Izpilda SQL vaicājumu, kurš atgriež tikai vienu produktu pēc ID
    product = conn.execute("""
        SELECT products.*, price.price AS price, properties.properties AS properties, ingredients.ingredients AS ingredients
        FROM products
        LEFT JOIN price ON products.price_id = price.id
        LEFT JOIN properties ON products.properties_id = properties.id
        LEFT JOIN ingredients ON products.ingredients_id = ingredients.id
        WHERE products.id = ?
    """, (product_id,)).fetchone()
    if product is None:
        return "Product not found", 404
    # ? ir vieta, kur tiks ievietota vērtība – šajā gadījumā product_id
    conn.close() # Aizver savienojumu ar datubāzi
    # Atgriežam HTML veidni 'products_show.html', padodot konkrēto produktu veidnei
    return render_template("products_show.html", product=product)

@app.route("/par-mums")
def about():
    return render_template("about.html")


#Create
@app.route("/reviews/add/<int:product_id>", methods=["POST"])
def add_review(product_id):
    user_name = request.form["user_name"]
    review_text = request.form["review_text"]

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO reviews (product_id, user_name, review_text)
        VALUES (?, ?, ?)
    """, (product_id, user_name, review_text))
    conn.commit()
    conn.close()

    return redirect(url_for("products_show", product_id=product_id))


#Update
@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_db_connection()

    # Fetch product data from the database
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()

    if product is None:
        return "Product not found", 404

    if request.method == "POST":
        # Get form data
        name = request.form["name"]
        price = request.form["price"]
        scent = request.form.get("scent", product['scent'])
        color = request.form.get("color", product['color'])
        stock = request.form.get("stock", product['stock'])
        properties = request.form.get("properties", product['properties'])
        ingredients = request.form.get("ingredients", product['ingredients'])

        # Update product in the database
        conn.execute("""
            UPDATE products 
            SET name = ?, price = ?, scent = ?, color = ?, stock = ?, properties = ?, ingredients = ? 
            WHERE id = ?
        """, (name, price, scent, color, stock, properties, ingredients, product_id))

        conn.commit()
        conn.close()

        # Redirect to the updated product view page
        return redirect(url_for("products_show", product_id=product_id))

    conn.close()
    return render_template("product_edit.html", product=product)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
