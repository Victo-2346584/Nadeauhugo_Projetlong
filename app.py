from flask import Flask, render_template, request
import mysql.connector
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Connexion à la base de données
def obtenir_db_connection():
    """
        permet la connection a la bd
    Retourne:
        mysql.connector: la connection a la bd
    """
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

@app.route('/')
def index():
    """
        ouvre index.html
    """
    return render_template('index.html')


@app.route('/commande')
def creer_ou_rechercher_client():
    croutesOptions = obtenir_croute_options()
    saucesOptions = obtenir_sauce_options()
    garnituresOptions = obtenir_garniture_options()

    return render_template('commande.html', croutes=croutesOptions, sauces=saucesOptions, garnitures=garnituresOptions)


def obtenir_croute_options():
    """
        les types de croutes dans base de donnee
    Retourne:
        tableau: nom des types croutes
    """
    conn = obtenir_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM types_croute")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def obtenir_sauce_options():
    """
        les types de sauces dans base de donnee
    Retourne:
        tableau: nom des types sauces
    """
    conn = obtenir_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM types_sauce")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def obtenir_garniture_options():
    """
        les garnitures dans base de donnee
    Retourne:
        tableau: nom des garnitures
    """
    conn = obtenir_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM garnitures")
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

@app.route('/commandeResume', methods=['POST'])
def resume_commande():
    """
        Génère un résumé de la commande avec des noms au lieu des IDs.
    """
    nom = request.form.get('nom')
    telephone = request.form.get('telephone')
    adresse = request.form.get('adresse')
    croute_id = request.form.get('croute_id')
    sauce_id = request.form.get('sauce_id')
    garnitures_ids = [
        request.form.get('garniture1'),
        request.form.get('garniture2'),
        request.form.get('garniture3'),
        request.form.get('garniture4'),
        ]
    # Récupérer les noms des croûtes, sauces et garnitures
    conn = obtenir_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nom FROM types_croute WHERE croute_id = %s", (croute_id,))
    croute_nom = cursor.fetchone()['nom']

    cursor.execute("SELECT nom FROM types_sauce WHERE sauce_id = %s", (sauce_id,))
    sauce_nom = cursor.fetchone()['nom']

    garnitures_noms = []
    for garniture_id in garnitures_ids:
        if garniture_id:  # Si une garniture est sélectionnée
            cursor.execute("SELECT nom FROM garnitures WHERE garniture_id = %s", (garniture_id,))
            garniture = cursor.fetchone()
            if garniture:
                garnitures_noms.append(garniture['nom'])

   

    # Préparer les données pour le résumé
    garnitures = []
    for garniture_id in garnitures_ids:
        if garniture_id:
            cursor.execute("SELECT nom FROM garnitures WHERE garniture_id = %s", (garniture_id,))
            garniture = cursor.fetchone()
            if garniture:
                garnitures.append((garniture_id, garniture['nom']))

    commande = {
    'nom': nom,
    'telephone': telephone,
    'adresse': adresse,
    'croute': croute_nom,
    'sauce': sauce_nom,
    'garnitures': garnitures  # Une liste de tuples (id, nom)
    }
    cursor.close()
    conn.close()
    return render_template('resume.html', commande=commande)



@app.route('/validation', methods=['POST'])
def validation():
    """
    Valide et insère les données dans la base de données, mais ignore l'ID de garniture = 1.
    """
    nom = request.form.get('nom')
    telephone = request.form.get('telephone')
    adresse = request.form.get('adresse')
    croute_nom = request.form.get('croute')
    sauce_nom = request.form.get('sauce')
    garnitures_ids = request.form.getlist('garnitures')  # Liste des IDs des garnitures

    # Connexion à la base de données
    conn = obtenir_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Récupérer les IDs des croûte et sauce depuis leurs noms
        cursor.execute("SELECT croute_id FROM types_croute WHERE nom = %s", (croute_nom,))
        croute_id = cursor.fetchone()['croute_id']

        cursor.execute("SELECT sauce_id FROM types_sauce WHERE nom = %s", (sauce_nom,))
        sauce_id = cursor.fetchone()['sauce_id']

        # Insérer le client
        cursor.execute("SELECT * FROM clients WHERE nom = %s AND telephone = %s AND adresse = %s", (nom, telephone, adresse))
        client = cursor.fetchone()

        if not client:
            cursor.execute("INSERT INTO clients (nom, telephone, adresse) VALUES (%s, %s, %s)", (nom, telephone, adresse))
            conn.commit()
            client_id = cursor.lastrowid
        else:
            client_id = client['client_id']

        # Insérer la commande
        cursor.execute("INSERT INTO commandes (client_id, date_commande) VALUES (%s, NOW())", (client_id,))
        conn.commit()
        commande_id = cursor.lastrowid

        # Insérer la pizza
        cursor.execute("INSERT INTO pizzas (commande_id, croute_id, sauce_id) VALUES (%s, %s, %s)", (commande_id, croute_id, sauce_id))
        conn.commit()
        pizza_id = cursor.lastrowid

        # Insérer les garnitures, mais ignorer celle avec l'ID = 1
        for garniture_id in garnitures_ids:
            if garniture_id != '1':  # Vérifiez si l'ID de garniture n'est pas 1
                cursor.execute("INSERT INTO pizzas_garnitures (pizza_id, garniture_id) VALUES (%s, %s)", (pizza_id, garniture_id))
                conn.commit()

    except mysql.connector.Error as err:
        print(f"Erreur MySQL: {err}")
        conn.rollback()  # Si une erreur se produit, annulez toutes les opérations
    finally:
        # Fermer le curseur et la connexion dans le bloc finally
        cursor.close()
        conn.close()

    return commandes_attente()




@app.route('/commandes_attente')
def commandes_attente():
    """
        liste les donnees en lien avec les commande en attente
    Retourne:
        page des commande en attente
    """
    conn = obtenir_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                   SELECT
                        c.nom AS client_nom,
                        c.telephone AS client_telephone,
                        c.adresse AS client_adresse,
                        co.commande_id,
                        co.date_commande,
                        tc.nom AS croute_nom,
                        ts.nom AS sauce_nom,
                        GROUP_CONCAT(g.nom ORDER BY g.nom ASC) AS garnitures,
                        ca.date_ajout AS date_ajout_attente
                    FROM
                        commandes_attente ca
                    JOIN commandes co ON ca.commande_id = co.commande_id
                    JOIN clients c ON co.client_id = c.client_id
                    JOIN pizzas p ON co.commande_id = p.commande_id
                    JOIN types_croute tc ON p.croute_id = tc.croute_id
                    JOIN types_sauce ts ON p.sauce_id = ts.sauce_id
                    JOIN pizzas_garnitures pg ON p.pizza_id = pg.pizza_id
                    JOIN garnitures g ON pg.garniture_id = g.garniture_id
                    GROUP BY
                        co.commande_id, c.nom, c.telephone, c.adresse, co.date_commande, tc.nom, ts.nom, ca.date_ajout;
                """)
    commandes = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('commandes_attente.html', commandes=commandes)

@app.route('/supprimer_commande/<int:commande_id>', methods=['POST'])
def supprimer_commande(commande_id):
    """
        suprime la commande sélectionner
    Paramètres:
        commande_id (int): id de la commande selectionner

    Retourne:
        au commande de en attente
    """
    conn = obtenir_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("DELETE FROM commandes WHERE commande_id = %s", (commande_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return commandes_attente()

if __name__ == '__main__':
    app.run(debug=True)