#!/usr/bin/env python
# coding=utf-8

import argparse
import urllib2  # python 2.7
import urllib
import sys
import io
import re
import sqlite3
import traceback
import datetime
import Image #PIL isn't yet available for Python 3
import StringIO

def compute_phone(gif_address):
  fd = urllib.urlopen(gif_address)
  image_file = io.BytesIO(fd.read())
  im = Image.open(image_file)
  pix = im.load()
  phoneNumber = ''
  width = im.size[0] #hauteur
  height = im.size[1] #largeur
  for a in range (0, 80, 8):
    if a == 16 or a == 32 or a == 48 or a == 64:
      phoneNumber = phoneNumber + '.'
    #sys.stdout.write("\n%s" % a)
    #0
    if pix[a+2, 0] >= 150 and pix[a+3, 3] <= 150 and pix[a+5, 1] >= 150 and pix[a+1, 2] >= 150 and pix[a+3, 5] <= 150 and  pix[a+5, 4] <= 150 : #colonne / ligne
      #sys.stdout.write("zero ")
      phoneNumber = phoneNumber + '0'
    #1
    elif pix[a+2, 1] >= 150 and pix[a+2, 8] >= 150 and pix[a+6, 8] >= 150:
      #sys.stdout.write("un ")
      phoneNumber = phoneNumber + '1'
    #2
    elif pix[a+6, 8] >= 150 and pix[a+4, 5] >= 150 and pix[a+4, 5] >= 150 and pix[a+1, 2] <= 150:
      #sys.stdout.write("deux ")
      phoneNumber = phoneNumber + '2'
    #3
    elif pix[a+2, 0] >= 150 and pix[a+6, 1] >= 150 and pix[a+5, 8] >= 150 and pix[a+1, 2] <= 150:
      #sys.stdout.write("trois ")
      phoneNumber = phoneNumber + '3'
    #4
    elif pix[a+5, 0] >= 150 and pix[a+1, 5] >= 150 and pix[a+5, 8] >= 150 and pix[a+1, 2] <= 150:
      #sys.stdout.write("quatre ")
      phoneNumber = phoneNumber + '4'
    #5
    elif pix[a+2, 0] >= 150 and pix[a+6, 0] >= 150 and pix[a+4, 8] >= 150:
      #sys.stdout.write("cinq ")
      phoneNumber = phoneNumber + '5'
    #6
    elif pix[a+5, 0] >= 150 and pix[a+4, 3] >= 150 and pix[a+1, 5] >= 150:
      #sys.stdout.write("six ")
      phoneNumber = phoneNumber + '6'
    #7
    elif pix[a+1, 0] >= 150 and pix[a+2, 8] >= 150:
      #sys.stdout.write("sept ")
      phoneNumber = phoneNumber + '7'
    #8
    elif pix[a+5, 4] >= 150 and pix[a+5, 8] >= 150 and pix[a+1, 7] >= 150 and pix[a+1, 6] >= 150:
      #sys.stdout.write("huit ")
      phoneNumber = phoneNumber + '8'
    #9
    if pix[a+2, 0] >= 150 and pix[a+3, 3] <= 150 and pix[a+5, 1] >= 150 and pix[a+3, 5] >= 150 and pix[a+3, 5] >= 150: #colonne / ligne
      #sys.stdout.write("neuf ")
      phoneNumber = phoneNumber + '9'
  return phoneNumber

def main():
  headers = { 'User-Agent' : 'Mozilla/5.0 (compatible; MSIE 9.0;'
                           + ' AOL 9.0; Windows NT 6.0; Trident/5.0)' } 
                                 # http://www.useragentstring.com

  parser = argparse.ArgumentParser()
  parser.add_argument('cmd')
  parser.add_argument('-d',
                      help='database name to use (default:database.db)',
                      default='database.db')
  parser.add_argument('params', nargs='*')

  args = parser.parse_args()

  print 'Commande :', args.cmd
  print 'Args :', args
  cmd = args.cmd
  database = args.d

  fgen = u'{0} {1} {2:7}€ {3:4}m² {4} {5:31} {6:26} {7}/{8}/{9} {10}'
  fdb = u'DB : ' + fgen

  if cmd == 'help':
      print 'leech [num]: download of data from page [num] to page 1 (default:1)'

  if cmd == 'list':
      conn = sqlite3.connect(database)
      c = conn.cursor()
      
      for tmp in c.execute('SELECT * FROM apparts'):
          print fdb.format(*tmp)

  if cmd == 'leech':

    try:
      page = int(args.params[0])
    except:  
      page = 1

      for x in range(page, 0, -1):
        print 'Page ', x, ' on ', page
        
        conn = sqlite3.connect(database)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS apparts (id text PRIMARY KEY,'
                  + ' telephone text, prix int, surface int, prixm2 int, cp int,' 
                  + 'ville text, nom text, jour int, mois int, annee int, heure text)')

        req = urllib2.Request(
            'http://www.leboncoin.fr/ventes_immobilieres/offres/'
            + 'provence_alpes_cote_d_azur/bouches_du_rhone/'
            + '?pe=8&sqs=6&ros=2&ret=1&ret=2&f=p&o=' + str(x), None, headers) 
        response = urllib2.urlopen(req)
        re_ids = re.compile('ventes_immobilieres/(?P<id>[0-9]+)\.htm')
        m = re_ids.finditer(response.read())

        for m2 in m:

            id = m2.group("id")
            url = 'http://www.leboncoin.fr/ventes_immobilieres/' + id + '.htm'

            c.execute('SELECT * FROM apparts WHERE id=?', (id,))
            tmp = c.fetchone()
            if(tmp):
                print fdb.format(*tmp)
                continue

            try:
                response = urllib2.urlopen(url)
            except Exception as e:
                print 'Error on url', url
                print e
                continue
            rep = response.read()

            try:
                m3 = re.findall('http://www.leboncoin.fr/pg/.*.gif', rep)
                gif_address = m3[0]
                telephone = compute_phone(gif_address)
                m3 = re.findall('class="price"\>([0-9 ]+).*\<', rep)
                prix = int(m3[0].replace(' ', ''))
                m3 = re.findall(
                    '<th>Surface : </th>\s*<td>([0-9]+) m<sup>2</sup>', rep)
                surface = int(m3[0])
                m3 = re.findall(
                    '<th>Code postal :</th>\s*<td>([0-9]+)</td>', rep)
                cp = m3[0]
                m3 = re.findall(
                    '<th>Ville :</th>\s*<td>([^<]+)</td>', rep)
                ville = m3[0].decode('cp1252')
                m3 = re.findall(
                    'Mise en ligne par <a rel="nofollow" '
                    + 'href="http://www2.leboncoin.fr/ar.ca=21_s&amp;id=[0-9]+" '
                    + 'onclick="return [^"]+">([^<]+)</a> '
                    + 'le (\d+) (.+) &agrave; (\d+:\d+). </div>', rep)
            #print m3, m3[0]
                nom = m3[0][0].decode('cp1252')
                jour = m3[0][1]
                mois = m3[0][2].decode('cp1252')
                if mois[:4] == 'janv' : mois = 1
                elif mois[0] == 'f' : mois = 2
                elif mois[:4] == 'mars' : mois = 3
                elif mois[:4] == 'avri' : mois = 4
                elif mois[:3] == 'mai' : mois = 5
                elif mois[:4] == 'juin' : mois = 6
                elif mois[:4] == 'juil' : mois = 7
                elif mois[0] == 'a' : mois = 8
                elif mois[:4] == 'sept' : mois = 9
                elif mois[:4] == 'octo' : mois = 10
                elif mois[:3] == 'nov' : mois = 11
                elif mois[:3] == 'déc' : mois = 12
                else : mois = 0
                
                ddt = datetime.datetime.today()
                annee = ddt.year
                """ Si on est en début d'année (ex: 3 jan 2014)
                et que l'annonce est d'un mois de fin d'année (ex: 20 déc)
                on corrige l'année (ex: pour avoir 20 déc 2013)"""
                if ddt.month < 6 and mois > 6:
                    annee -= 1

                heure = m3[0][3]
            except Exception as e:
                print 'Error on url', url
                traceback.print_exc()
                #print e
                continue

            prixm2 = prix / surface
            #print ville
            f = u'{0:10} {1:7}€ {2:4}m² {5:5}€/m² {3:6} {4:23} {7:21} {8}/{9}/{10}@{11} {6}'
            print f.format(
                telephone, prix, surface, cp, ville, prixm2,
                url, nom, jour, mois, annee, heure)
            c.execute('INSERT INTO apparts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', \
                      (id, telephone, prix, surface, prixm2, cp, ville, nom, jour, mois, annee, heure))

            #exit(0)

        conn.commit()

  print 'Fin.'
  
main()
