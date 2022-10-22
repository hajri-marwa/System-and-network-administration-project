#!/usr/bin/env python3
import socket
import sqlite3   
import threading  
threadsClients = []#thread par client connecté :instance serveur

#fonction de connexion à la base de données retourne un objet de connexion et un objet de reqêtes sql
def connexionBaseDeDonnees():
	#retourne un objet de connection
	database = sqlite3.connect("banque.db")
	#retourne un objet curseur permet de faire des requêtes sql
	cursordb = database.cursor()
	return database, curseurdb

#renvoie true si le code correspond numero de compte
def testpin(numcompte, pinuser):
	database, curseurdb = connexionBaseDeDonnees()
	curseurdb.execute("SELECT PIN FROM comptes WHERE NumeroCompte = ?",(numcompte,))
	pincompte = curseurdb.fetchone()[0]
	database.close()
	if pincompte == pinuser:
		return True
	else:
		return False
	
#retouner le solde du compte de compte de code passe en parametre 
def solde(numcompte):
	baseDeDonnees, curseur = connexionBaseDeDonnees()
	curseur.execute("SELECT Solde FROM comptes WHERE NumeroCompte = ?",(numcompte,))
	soldeCompte = curseur.fetchone()[0]
	baseDeDonnees.close()
	return soldeCompte

#débiter le compte
def retrait(numcompte, montant):
	#Le montant est négatif
	baseDeDonnees, curseur = connexionBaseDeDonnees()
	montant = float(montant)
	soldeCompte = solde(numcompte)
	if soldeCompte < montant or montant >= 0:
		baseDeDonnees.close()
		return False
	else:
		nouveauSolde = soldeCompte+montant
		curseur.execute("UPDATE comptes SET Solde = ? WHERE NumeroCompte = ?",(nouveauSolde,numcompte))
		curseur.execute("INSERT INTO operations (DateOperation, NumeroCompte, LibelleOperation, Montant) VALUES (DATE('NOW'), ?, ?, ?)",(numcompte, "Retrait", montant))
		baseDeDonnees.commit()
		baseDeDonnees.close()
		return True

#transferer un montant d'un compte à un autre
def transfert(nocompteSource, nocompteDestination, montant):
	#Le montant est positif
	baseDeDonnees, curseur = connexionBaseDeDonnees()
	montant = float(montant)
	#tester si le solde du compte source est suffisant
	soldeCompteSource = solde(nocompteSource)
	if soldeCompteSource < montant or montant <= 0:
		baseDeDonnees.close()
		return False
	else:
		nouveauSoldeSource = soldeCompteSource-montant#débiter le compte source
		curseur.execute("UPDATE comptes SET Solde = ? WHERE NumeroCompte = ?",(nouveauSoldeSource,nocompteSource))
		curseur.execute("INSERT INTO operations (DateOperation, NumeroCompte, LibelleOperation, Montant) VALUES (DATE('NOW'), ?, ?, ?)",(nocompteSource, "Virement", -montant))
		#récuperer le solde de compte destination et le créditer du montant 
		soldeCompteDestination = solde(nocompteDestination)
		nouveauSoldeDestination = soldeCompteDestination+montant
		curseur.execute("UPDATE comptes SET Solde = ? WHERE NumeroCompte = ?",(nouveauSoldeDestination,nocompteDestination))
		#enregistrement du transfert comme une operation
		curseur.execute("INSERT INTO operations (DateOperation, NumeroCompte, LibelleOperation, Montant) VALUES (DATE('NOW'), ?, ?, ?)",(nocompteDestination, "Virement", montant))
		baseDeDonnees.commit()
		baseDeDonnees.close()
		return True

#créditer un compte de: montant 
def depot(nocompte, montant):
	#Le montant est positif
	baseDeDonnees, curseur = connexionBaseDeDonnees()
	montant = float(montant)
	soldeCompte = solde(nocompte)
	nouveauSolde = soldeCompte+montant
	curseur.execute("UPDATE comptes SET Solde = ? WHERE NumeroCompte = ?",(nouveauSolde,nocompte))
	#enregistrement de l'opération
	curseur.execute("INSERT INTO operations (DateOperation, NumeroCompte, LibelleOperation, Montant) VALUES (DATE('NOW'), ?, ?, ?)",(nocompte, "Dépôt", montant))
	baseDeDonnees.commit()
	baseDeDonnees.close()
	return True
#retourne l'historique des opérations d'un compte par son numero
def historique(nocompte):
	baseDeDonnees, curseur = connexionBaseDeDonnees()
	curseur.execute("SELECT DateOperation, LibelleOperation, Montant FROM operations WHERE NumeroCompte = ? ORDER BY DateOperation DESC LIMIT 10;",(nocompte,))
	historiqueCSV = "\"DateOperation\";\"LibelleOperation\";\"Montant\"\n"#formatage du resultat
	for ligne in curseur.fetchall():
		historiqueCSV += "\"" + ligne[0] + "\";\"" + ligne[1] + "\";\"" + str(ligne[2]) + "\"\n"#remplissage de format par les données 
	return historiqueCSV

#traitement effectué à chaque fois un client est accepté
def instanceServeur (client, infosClient):
	#client et infosClient venant de serveur.accept() : ip et port
	adresseIP = infosClient[0]
	port = str(infosClient[1])
	print("Instance de serveur prêt pour " + adresseIP + ":" + port)
	actif = True
	while actif:
		message = client.recv(255).decode("utf-8").upper().split(" ")#utiliser " " comme caract de séparation
		pret = False
		print(message[0])#debuggage
		if message[0] == "TESTPIN":#message  envoyé par le client :client.send(("TESTPIN " +...
			if testpin(message[1], message[2]):
				client.send("TESTPIN OK".encode("utf-8"))#reponse au client 
				message = client.recv(255).decode("utf-8").upper().split(" ")
				if message[0] == "RETRAIT":
					if retrait(message[1], message[2]):
						client.send("RETRAIT OK".encode("utf-8"))
					else:
						client.send("RETRAIT NOK".encode("utf-8"))
				elif message[0] == "DEPOT":
					depot(message[1], message[2])
					client.send("DEPOT OK".encode("utf-8"))
				elif message[0] == "SOLDE":
					soldeCompte = solde(message[1])
					client.send(("SOLDE " + str(soldeCompte)).encode("utf-8"))
				elif message[0] == "TRANSFERT":
					if transfert(message[1], message[2], message[3]):
						client.send("TRANSFERT OK".encode("utf-8"))
					else:
						client.send("TRANSFERT NOK".encode("utf-8"))
				elif message[0] == "HISTORIQUE":
					historiqueCSV = historique(message[1])
					client.send(("HISTORIQUE " + historiqueCSV).encode("utf-8"))
				else:#le client tape numero hors le menu
					client.send("ERROPERATION".encode("utf-8"))
			else:
				client.send("TESTPIN NOK".encode("utf-8"))
		else:
			client.send("ERROPERATION".encode("utf-8"))
			print("testdebug")
	print("Connexion fermée avec " + adresseIP + ":" + port)
	client.close()
#crerer une instance de serveur TCP et connecte la famille IPV4
serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#on utilise un port 500000 pour éviter la chance de tamber sur un port réservé généralement pas trop elevé
serveur.bind(('', 50000))# Écoute sur le port 50000 et le connecteur est accessible par n'importe quel machine 
serveur.listen(5)# l'argument passé à listen indique à la bibliothèque de connecteurs que nous voulons mettre en file d'attente
                 # jusqu'à 5 requêtes de connexion (le maximum normal) avant de refuser les connexions externes
while True:
	#accepter des connexions de l'extérieur
	client, infosClient = serveur.accept()
	#threading.Thread(groupe, fonction à executer, nom thread, arguments de fonction en tuple , dictionnaireArguments de la fonction à executer)
	threadsClients.append(threading.Thread(None, instanceServeur, None, (client, infosClient), {}))
	threadsClients[-1].start()
serveur.close()
