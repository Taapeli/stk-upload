# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import csv

def henkilolista(pathname):
    with open(pathname, 'rb') as f:
        reader = csv.DictReader(f)
        rivit = []

        for row in reader:
            # Onko henkilörivi?
            etu=row['Sukunimi_vakioitu']
            suku=row['Etunimi_vakioitu']
            if suku == '' and etu == '':
                continue

            if etu == '': etu = 'N'
            if suku == '': suku = 'N'
            nimi='%s %s' % (etu, suku)

            """ Käräjät-tieto on yhdessä sarakkeessa tai 
                Juhan muuntamana kolmessa: käräjä, alku, loppu
            """
            if 'Käräjäpaikka' in row:
                karaja = '%s %s...%s' % \
                     (row['Käräjäpaikka'], row['Alkuaika'], row['Loppuaika'])
                if karaja[-3:] == '...':
                    karaja = karaja[:-3]
            else:
                karaja = row['Käräjät']

            rivi = dict( \
                nimi=nimi.decode('UTF-8'), \
                ammatti=row['Ammatti_vakioitu'].decode('UTF-8'), \
                paikka=row['Paikka_vakioitu'].decode('UTF-8'), \
                karajat=karaja.decode('UTF-8'), \
                signum=row['Signum'].decode('UTF-8') \
            )
            rivit.append(rivi)
        return (rivit)
