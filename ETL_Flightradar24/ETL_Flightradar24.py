from FlightRadar24 import FlightRadar24API
from FlightRadar24.errors import CloudflareError
import pandas as pd
import csv
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import TimestampType,StringType, IntegerType,DoubleType,StructType
from pyspark.sql.functions import to_timestamp
from datetime import datetime
import os
import calendar
from geopy.geocoders import Nominatim
import pycountry_convert as pc
import glob
from pyspark.sql.functions import regexp_replace
from pyspark.sql.functions import to_timestamp, date_format, date_sub
from pyspark.sql.functions import max
from pyspark.sql.functions import lit
from pyspark.sql.functions import split
from pyspark.sql import functions as F
from pyspark.sql.functions import when
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window
from geopy.geocoders import Nominatim
import logging 
import sys


def country_to_continent(country_name):
    """Fonction qui permet de retourner le nom du continent.
    country_name (string): le nom du pays 
    """
    country_alpha2 = pc.country_name_to_country_alpha2(country_name)
    country_continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
    country_continent_name = pc.convert_continent_code_to_continent_name(country_continent_code)
    return country_continent_name





def dossier(date,ZoneName):

    """Fonction pour créer l'architecture

    Arguments:

        date (datetime)   : date sous format %Y-%m-%d %H:%M:%S
        ZoneName (string) : nom de la zone aérienne 
    """
    if os.path.isdir("Flights") == False:
        os.mkdir("Flights")

    if os.path.isdir("Log") == False:
        os.mkdir("Log")

    if os.path.isdir("Results") == False:
        os.mkdir("Results")

    if os.path.isdir("Results/"+str(date.year)+str(date.month).zfill(2)+str(date.day).zfill(2)) == False:
        os.mkdir("Results/"+str(date.year)+str(date.month).zfill(2)+str(date.day).zfill(2))
    
    if os.path.isdir("Log/"+str(date.year)+str(date.month).zfill(2)+str(date.day).zfill(2)) == False:
        os.mkdir("Log/"+str(date.year)+str(date.month).zfill(2)+str(date.day).zfill(2))

    if os.path.isdir("Flights/"+str(ZoneName)) == False:
        os.mkdir("Flights/"+str(ZoneName))

        if os.path.isdir("Flights/"+str(ZoneName)+'/'+str(date.year)) == False:
            os.mkdir("Flights/"+str(ZoneName)+'/'+str(date.year))

        if os.path.isdir("Flights/"+str(ZoneName)+'/'+str(date.year)+"/"+str(calendar.month_name[date.month])) == False:
            os.mkdir("Flights/"+str(ZoneName)+'/'+str(date.year)+"/"+str(calendar.month_name[date.month]))

        if os.path.isdir("Flights/"+str(ZoneName)+'/'+str(date.year)+"/"+str(calendar.month_name[date.month])+"/"+str(date.day)) == False:
            os.mkdir("Flights/"+str(ZoneName)+'/'+str(date.year)+"/"+str(calendar.month_name[date.month])+"/"+str(date.day))
    else:

        if os.path.isdir("Flights/"+str(ZoneName)+'/'+str(date.year)+"/"+str(calendar.month_name[date.month])) == False:
            os.mkdir("Flights/"+str(ZoneName)+'/'+str(date.year)+"/"+str(calendar.month_name[date.month]))

        if os.path.isdir("Flights/"+str(ZoneName)+'/'+str(date.year)+"/"+str(calendar.month_name[date.month])+"/"+str(date.day)) == False:
            os.mkdir("Flights/"+str(ZoneName)+'/'+str(date.year)+"/"+str(calendar.month_name[date.month])+"/"+str(date.day))


def zone_list():

    """Fonction qui permet de retourner la liste de noms des différentes zones et leurs limites dans le globe terrestre

    Returns:

        bound (list) : contient les limites (latitude,longitude) d'une zone 
        name (list)  : contient la liste des noms des zones aériennes
    """

    fr_api = FlightRadar24API()
    name = [ 'northamerica','europe', 'southamerica', 'oceania', 'asia', 'africa', 'atlantic', 'maldives', 'northatlantic']
    bound = []
    for n in name :
        zone = fr_api.get_zones()[n]
        bound.append(fr_api.get_bounds(zone))

    return bound,name

# def zone_list():
#Poour le test docker
#     name = ['northamerica','europe','southamerica','oceania','asia','africa','atlantic','maldives','northatlantic']
#     bound = [
#         "24,49,-125,-66",       # North America
#         "36,71,-10,40",         # Europe
#         "-55,15,-82,-34",       # South America
#         "-50,0,110,180",        # Oceania
#         "10,55,60,150",         # Asia
#         "-35,35,-20,50",        # Africa
#         "30,50,-60,-20",        # Atlantic
#         "-10,10,70,80",         # Maldives (exemple)
#         "50,70,-60,-20"         # North Atlantic
#     ]
#     return bound, name


def extract(zone,ZoneName):

    """Fonction pour extraire les données de FlightRadar24 et les stocker par région aérienne

    Arguments :

        zone (list)     : les limites de la zone aérienne (latitude, et longitude)
        ZoneName (list) : le nom de la zone aérienne
   
    Returns :

        df (dataframe) : dataframe contenant les données extraites par zone aérienne

    raises :
        KeyError : si la fonction country_to_continent(pays) ne peut pas trouver de continent à partir d'un nom de pays 
    """

    fr_api = FlightRadar24API()

    ####A Commenter pour obtenir tous les vols##########
    ######################################################
    flight_tracker = fr_api.get_flight_tracker_config()

    flight_tracker.limit = 10
    fr_api.set_flight_tracker_config(flight_tracker)
    ######################################################

    flights = fr_api.get_flights(bounds=zone) # Contient la liste des vols de la zone d'extraction
    airlines = fr_api.get_airlines() # Contient toutes les compagnies aériennes
    on_ground = [f.on_ground for f in flights]  # récupération du paramètre on_ground qui permet de savoir si l'avion est au sol ("1") ou pas ("0")
    flightID = [f.id for f in flights]          # récupération de l'identifiant du vol
    airlineicao = [f.airline_icao for f in flights]    # récupération du code icao de la compagnie aérienne associée au vol 
    destination_airport_iata = [f.destination_airport_iata for f in flights] # récupération du code iata de l'aéroport de destination 
    origin_airport_iata = [ f.origin_airport_iata for f in flights] # récupération du code iata de l'aéroport de destination 
    time = [ f.time for f in flights] # récupération de la date et heure du vol 
    depart = [ fr_api.get_flight_details(f)["time"]['real']["departure"] for f in flights] # récupération de la date et heure du vol de départ
    arrivee = [ fr_api.get_flight_details(f)["time"]['real']["arrival"] for f in flights] # récupération de la date et heure du vol d'arrivée
    model = [fr_api.get_flight_details(f)['aircraft']["model"]["text"] if "model" in fr_api.get_flight_details(f)['aircraft'].keys() else "" for f in flights] # récupération du nom du model d'avion

    origin_airport_continent=[] # récupération du nom de l'aéroport d'origine
    destination_airport_continent=[] # récupération du nom de l'aéroport de destination
    
    for iataO in origin_airport_iata:
    
        if iataO == '':
            origin_airport_continent.append("None")
        else:
            try:
                origin_airport_continent.append(country_to_continent(fr_api.get_airport_details(iataO)["airport"]['pluginData']['details']['position']["country"]["name"]))

            except KeyError as e:
                origin_airport_continent.append("None")
                continue

    for iataD in destination_airport_iata:
      
        if iataD == '':
            destination_airport_continent.append("None")
        else:
            try:
                destination_airport_continent.append(country_to_continent(fr_api.get_airport_details(iataD)["airport"]['pluginData']['details']['position']["country"]["name"]))

            except KeyError as e:
                destination_airport_continent.append("None")
                continue

    distance = [ None if len(origin_airport) == 0 or len(destination_airport) == 0  else  f.get_distance_from(fr_api.get_airport(origin_airport))+f.get_distance_from(fr_api.get_airport(destination_airport)) for f,destination_airport,origin_airport in zip(flights,destination_airport_iata,origin_airport_iata)] # récupération de la distance total du vol

 

    df_airlines = pd.DataFrame(airlines,index=range(len(airlines)))
    df_airlines = pd.concat([df_airlines, pd.DataFrame([{"Name":"N/A","Code":"N/A","ICAO":"N/A"}])], ignore_index=True)
    df_airlines = pd.concat([df_airlines, pd.DataFrame([{"Name":"N/A","Code":"N/A","ICAO":"[]"}])], ignore_index=True)

    airlineName = [None if len(df_airlines[df_airlines["ICAO"]==i]["Name"].values)==0  else df_airlines[df_airlines["ICAO"]==i]["Name"].values[0] for i in airlineicao ] # # récupération du nom de la compagnie aérienne du vol 




    # création du dataframe contenant tous les paramètres nécessaires 
    df = pd.DataFrame({  
        "on_ground":on_ground,
        "flightid":flightID, 
        "time":time,
        "airlines":airlineName,
        "model":model,
        "distance":distance,
        "depart":depart,
        "arrival":arrivee,
        "origin_continent":origin_airport_continent,
        "destination_continent":destination_airport_continent
    })


    valeur_vide = ''
    valeur_specifique = None
    df.replace({valeur_vide: valeur_specifique}, inplace=True)
    df["depart"] = df["depart"].apply(lambda x: datetime.utcfromtimestamp(x)if not pd.isnull(x) else pd.NaT)
    df["arrival"] = df["arrival"].apply(lambda x: datetime.utcfromtimestamp(x) if not pd.isnull(x) else pd.NaT)
    df["time"] = df["time"].apply(lambda x: datetime.utcfromtimestamp(x)if not pd.isnull(x) else pd.NaT)
    df["ZoneName"] = pd.Series(ZoneName, index=range(len(df)))
    df.replace({pd.NaT: None}, inplace=True)

    date = datetime.strptime(str(df["time"][0]),"%Y-%m-%d %H:%M:%S")

    dossier(date,ZoneName) # création de l'architecture du stockage de données
  
    df.to_csv("Flights/"+ZoneName+"/"+str(date.year)+"/"+str(calendar.month_name[int(date.month)])+"/"+str(date.day)+"/"+"flights"+str(date.year)+str(date.month).zfill(2)+str(date.day).zfill(2)+str(date.hour)+str(date.minute)+".csv",index=False) ### écriture du dataframe contenant les vols et leurs paramètres en format csv

    return df

def load():

    """Fonction qui permet de charger toutes les données existantes et d'afficher et stocker les résultats

    Raises :

        ValueError : si il n'y a pas de fichiers résultats pour lire les données 
    
    """

    current_datetime = datetime.now()
    formatter = logging.Formatter("%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")

    handler = logging.FileHandler("Log/"+str(current_datetime.year)+str(current_datetime.month).zfill(2)+str(current_datetime.day).zfill(2)+"/"+"LOG"+str(current_datetime.year)+str(current_datetime.month).zfill(2)+str(current_datetime.day).zfill(2)+".log", mode="a", encoding="utf-8")
    handler.setFormatter(formatter)
    logger = logging.getLogger("CHARGEMENT")
    logger.addHandler(handler)
    logger.setLevel(logging.ERROR)
    logger.setLevel(logging.INFO)


    

    year = str(current_datetime.year)
    month = str(calendar.month_name[current_datetime.month])

    try:

        zone = [ "europe",'northamerica', 'southamerica', 'oceania', 'asia', 'africa', 'atlantic', 'maldives', 'northatlantic']

        file = glob.glob("Flights/*"+"/"+year+"/"+month+"/"+"*[0-9]/"+"flights[0-9]*.csv")
        

        liste_dfs = [pd.read_csv(fichier) for fichier in file]

        # Fusionner tous les DataFrames en un seul
        df_final = pd.concat(liste_dfs, ignore_index=True)

        # Création d'une session Spark
        spark = SparkSession.builder.appName("ReadData").getOrCreate()

        # Création du dataframe
        dfs = spark.createDataFrame(df_final.astype(str))

        # Nettoyage
        dfs = dfs.withColumn("distance", col("distance").cast("double"))
        dfs = dfs.withColumn("arrival",to_timestamp(col("arrival"), "yyyy-MM-dd HH:mm:ss"))
        dfs = dfs.withColumn("depart",to_timestamp(col("depart"), "yyyy-MM-dd HH:mm:ss"))
        dfs = dfs.withColumn("time",to_timestamp(col("time"), "yyyy-MM-dd HH:mm:ss"))
        dfs = dfs.withColumn("airlines", when(dfs.airlines == 'nan', None).otherwise(dfs.airlines))
        dfs = dfs.withColumn("model", when(dfs.model== 'nan', None).otherwise(dfs.model))
        dfs = dfs.withColumn("origin_continent", when(dfs.origin_continent== 'nan', None).otherwise(dfs.origin_continent))
        dfs = dfs.withColumn("destination_continent", when(dfs.destination_continent== 'nan', None).otherwise(dfs.destination_continent))
        dfs = dfs.withColumn("origin_continent", regexp_replace("origin_continent", "North America", "America"))
        dfs = dfs.withColumn("origin_continent", regexp_replace("origin_continent", "South America", "America"))
        dfs = dfs.withColumn("destination_continent", regexp_replace("destination_continent", "North America", "America"))
        dfs = dfs.withColumn("destination_continent", regexp_replace("destination_continent", "South America", "America"))
        split_cols = split(dfs['model'], ' ')
        dfs = dfs.withColumn('manufacturer', split_cols.getItem(0))

    
        dfs = dfs.na.fill(value=0)

        ## 1) La compagnie qui le plus de vols en cours 

        df1 = dfs.filter(dfs.airlines != "NULL").filter(dfs.on_ground == "0").groupBy("airlines").count()
        df1 = df1.toPandas()

        ## 2) Pour chaque continent, la compagnie avec le + de vols régionaux actifs (continent d'origine == continent de destination)
        
        df2 = dfs.filter(col("origin_continent") == col("destination_continent")).groupby("origin_continent","airlines").agg(F.count('airlines').alias('nombre_vols'))
        windowSpec = Window.partitionBy('origin_continent').orderBy(F.col('nombre_vols').desc())
        df2 = df2.withColumn('rank', F.rank().over(windowSpec)).filter(F.col('rank') == 1)
        df2 = df2.toPandas()

        ## 3) Le vol en cours avec le trajet le plus long 

        df3 = dfs.filter(dfs.on_ground == "0").withColumn('difference', col('depart') - col('arrival')).groupby("difference").count()
        df3 = df3.toPandas()
        df3.max()

        ## 4) Pour chaque continent, la longueur de vol moyenne

        df4 = dfs.filter(dfs.distance != 0.0).groupBy("origin_continent").mean("distance")
        df4 = df4.toPandas()

        df5 = dfs.filter(dfs.distance != 0.0).groupBy("destination_continent").mean("distance")
        df5 = df5.toPandas()

        ## 5) L'entreprise constructeur d'avions avec le plus de vols actifs 

        df6 = dfs.filter(dfs.manufacturer != "NULL").groupBy("manufacturer").count()
        df6 = df6.toPandas()
        df6.max()


        #### Affichage des résultats

        print( "1) La compagnie qui le plus de vols en cours : ")
        print()
        print("La compagnie qui le plus de vols en cours est " +str(df1.max()[0])+ " avec "+ str(df1.max()[1])+' vols' )
        print()
        print()
        print("2) Pour chaque continent, la compagnie avec le + de vols régionaux actifs (continent d'origine == continent de destination) :")
        print()
        print(df2)
        print( "3) Le vol en cours avec le trajet le plus long : ")
        print()
        print("Le vol en cours est le "+str(df3.max()[0])+ " avec "+str(df3.max()[0])+" heures")
        print()
        print()
        print("4) Pour chaque continent, la longueur de vol moyenne : ")
        print()
        print(df4)
        print()
        print(df5)
        print()
        print()
        print( "5) L'entreprise constructeur d'avions avec le plus de vols : ")
        print()
        print("L'entreprise constructeur d'avions avec le plus de vols actifs est " +str(df6.max()[0])+ " avec "+ str(df6.max()[1])+' vols' )

        if os.path.isdir("Results") == False:
            os.mkdir("Results")

        current_datetime = datetime.now()


        if os.path.isdir("Results/"+str(current_datetime.year)+str(current_datetime.month).zfill(2)+str(current_datetime.day).zfill(2)) == False:
            os.mkdir("Results/"+str(current_datetime.year)+str(current_datetime.month).zfill(2)+str(current_datetime.day).zfill(2))

        chemin = 'Results/'+str(current_datetime.year)+str(current_datetime.month).zfill(2)+str(current_datetime.day).zfill(2)+"/"+"result"+str(current_datetime.year)+str(current_datetime.month).zfill(2)+str(current_datetime.day).zfill(2)+str(current_datetime.hour).zfill(2)+str(current_datetime.minute).zfill(2)+".txt"
        with open(chemin, 'w') as fichier:
            fichier.write("1) La compagnie qui le plus de vols en cours : \n")
            fichier.write("La compagnie qui le plus de vols en cours est " +str(df1.max()[0])+ " avec "+ str(df1.max()[1])+' vols\n\n')
            fichier.write("2) Pour chaque continent, la compagnie avec le + de vols régionaux actifs (continent d'origine == continent de destination) \n")
            fichier.write(str(df2))
            fichier.write("\n")
            fichier.write("La compagnie qui le plus de vols en cours est " +str(df1.max()[0])+ " avec "+ str(df1.max()[1])+' vols\n\n')
            fichier.write("3) Le vol en cours avec le trajet le plus long : \n")
            fichier.write("Le vol en cours est le "+str(df3.max()[0])+ " avec "+str(df3.max()[0])+" heures\n\n")
            fichier.write("4) Pour chaque continent, la longueur de vol moyenne : \n")
            fichier.write(str(df4))
            fichier.write("\n")
            fichier.write(str(df5))
            fichier.write("\n")
            fichier.write("5) L'entreprise constructeur d'avions avec le plus de vols : \n")
            fichier.write("L'entreprise constructeur d'avions avec le plus de vols actifs est " +str(df6.max()[0])+ " avec "+ str(df6.max()[1])+' vols')
            fichier.close()
        logger.info('Chargement des données effectué avec succès.')

    except ValueError as e:

        logger.error(f"Erreur lors du chargement des données : {str(e)}")
        raise





def extraction_transform():

    """Fonction qui permet d'extraire les données FlightRadar24

    raises:

        CloudflareError : si trop de requêtes sont effectuées

    """

    logger = logging.getLogger("EXTRACTION")
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    for i, j in zip(zone_list()[0], zone_list()[1]):
        try:
            df = extract(i, j)
            logger.info(f"Extraction OK pour {j}")
        except CloudflareError as e:
            logger.error(f"Erreur : {e}")



    for i,j in zip(zone_list()[0],zone_list()[1]):
        try:
            df=extract(i,j)
            logger.info('Extraction des données effectuée avec succès pour '+str(j))

        except CloudflareError as e:

            logger.error(f"Erreur lors de l'extraction des données : {str(e)}")
            
            pass
