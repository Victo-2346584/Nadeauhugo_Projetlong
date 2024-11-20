Drop DATABASE IF EXISTS pizzeria;
CREATE DATABASE pizzeria
CHARACTER SET = 'utf8mb4'
COLLATE = 'utf8mb4_unicode_ci';

use pizzeria;
CREATE TABLE clients (
    client_id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50) NOT NULL,
    telephone VARCHAR(15) NOT NULL,
    adresse VARCHAR(255) NOT NULL
);

CREATE TABLE types_croute (
    croute_id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(20) NOT NULL
);

CREATE TABLE types_sauce (
    sauce_id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(20) NOT NULL
);

CREATE TABLE garnitures (
    garniture_id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(20) NOT NULL
);

CREATE TABLE commandes (
    commande_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT,
    date_commande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE TABLE pizzas (
    pizza_id INT AUTO_INCREMENT PRIMARY KEY,
    commande_id INT,
    croute_id INT,
    sauce_id INT,
    FOREIGN KEY (commande_id) REFERENCES commandes(commande_id) ON DELETE CASCADE,
    FOREIGN KEY (croute_id) REFERENCES types_croute(croute_id),
    FOREIGN KEY (sauce_id) REFERENCES types_sauce(sauce_id)
);

CREATE TABLE pizzas_garnitures (
    pizza_id INT,
    garniture_id INT,
    PRIMARY KEY (pizza_id, garniture_id),
    FOREIGN KEY (pizza_id) REFERENCES pizzas(pizza_id) ON DELETE CASCADE,
    FOREIGN KEY (garniture_id) REFERENCES garnitures(garniture_id)
);

CREATE TABLE commandes_attente (
    commande_id INT PRIMARY KEY,
    date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (commande_id) REFERENCES commandes(commande_id) ON DELETE CASCADE
);

 DROP TRIGGER if exists ajouter_commande_attente;
DELIMITER $$

CREATE TRIGGER ajouter_commande_attente
AFTER INSERT ON commandes
FOR EACH ROW
BEGIN
    INSERT INTO commandes_attente (commande_id) 
    VALUES (NEW.commande_id);
END $$

DELIMITER ;
