#!/usr/bin/env python3
import socket
adresseIP = "127.0.0.1"	# Ici, l'ip du serveur
port = 50000	# le port à connecter
while True:
	#creer le socket client
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect((adresseIP, port))
	print("Bienvenue dans la banque Python")#message simulant un distributeur
	numcompte = input("Entrez votre numéro de compte : ")
	codepin = input("Entrez votre code PIN : ")
	client.send(("TESTPIN " + numcompte + " " + codepin).encode("utf-8"))#convertir la chaîne de caractères en flux binaire UTF-8 son émission sur le réseau
	reponse = client.recv(255).decode("utf-8")
	print(reponse)
	if reponse == "TESTPIN OK":
		print("Bienvenue ! ")
		print("  Opérations : ")
		print("1 - Dépôt")
		print("2 - Retrait")
		print("3 - Transfert")
		print("4 - Historique des opérations")
		print("5 - Solde du compte")
		operation = input("Entrez l'opération que vous souhaitez : ")
		if operation == "1":
			montant = input("Entrez le montant à déposer : ")
			client.send(("DEPOT " + numcompte + " " + montant).encode("utf-8"))
			reponse = client.recv(255).decode("utf-8")
			print("Dépot effectué")
		elif operation == "2":
			montant = input("Entrez le montant à retirer : ")
			montant = str(- float(montant))	# Le montant doit être négatif
			client.send(("RETRAIT " + numcompte + " " + montant).encode("utf-8"))
			reponse = client.recv(255).decode("utf-8")
			if reponse == "RETRAIT OK":
				print("Retrait effectué")
			else:
				print("Retrait refusé")
		elif operation == "3":
			montant = input("Entrez le montant à transferer : ")
			numcompteDestination = input("Entrez le numéro de compte du bénéficiaire : ")
			client.send(("TRANSERT " + numcompte + " " + numcompteDestination + " " + montant).encode("utf-8"))
			reponse = client.recv(255).decode("utf-8")
			if reponse == "TRANSERT OK":
				print("Transfert effectué")
			else:
				print("Transfert refusé")
		elif operation == "4":
			client.send(("HISTORIQUE " + nocompte).encode("utf-8"))
			historique = client.recv(4096).decode("utf-8").replace("HISTORIQUE ","")# On transfert un grand volume de données
			print(historique)
		elif operation == "5":
			client.send(("SOLDE " + numcompte).encode("utf-8"))
			solde = client.recv(4096).decode("utf-8").replace("SOLDE ","")
			print("Le solde du compte est de " + solde)
	else:
		print("Vos identifiants sont incorrects")
	print("Au revoir !")
	client.close()
