from gw2api import GuildWars2Client
import shelve
from enum import Enum
import argh
from argh import arg
import csv
from io import StringIO
import os
import yaml

class GW2:
  races = ['Asura', 'Charr', 'Norn', 'Human', 'Sylvari']
  genders = ['Male', 'Female']
  professions = ['Warrior', 'Ranger', 'Revenant', 'Thief', 'Elementalist', 'Mesmer', 'Engineer', 'Guardian', 'Necromancer']

  def __init__(self, load="cache", filename='shelve2'):
    self.config = load_config()
    self.gw2_clients = []
    for account in self.config['accounts']:
      self.gw2_clients.append({'name': account['name'], 'client': GuildWars2Client(api_key=account['key'])})
    self.reduced = {}
    load = self.config['cache']['load']
    filename = self.config['cache']['filename']

    if load == "refresh":
      self._load_refresh(filename)
    elif load == "cache":
      self._load_cache(filename)
    else:
      self._load_merge(filename)
    
  def _load_merge(self, filename):
    with shelve.open(filename) as db:
      for k, v in db.items():
        self.reduced[k] = v
      for account in self.gw2_clients:
        characters = account['client'].characters.get()
        for name in characters:
          if name not in db:
            print("{} is new".format(name))
            c = account['client'].characters.get(id=name)
            self.reduced[name] = { 
              'name': c['name'],
              'race': c['race'],
              'gender': c['gender'],
              'profession': c['profession'],
              'account': account['name'],
              'created': c['created']
            }
            db[name] = self.reduced[name]

  def _load_refresh(self, filename):
    self.reduced = {}
    for account in self.gw2_clients:
      characters = account['client'].characters.get()
      info = {
        x['name']: x for x in (
          account['client'].characters.get(id=c) for c in characters)
      }
      # import json
      # print(json.dumps(info))
      # exit(1)
      self.reduced.update({x['name']: { 
        'name': x['name'], 
        'race': x['race'], 
        'gender': x['gender'], 
        'profession': x['profession'],
        'account': account['name'],
        'created': x['created']
      } for x in info.values()})
      with shelve.open(filename, flag='n') as db:
        for k, v in self.reduced.items():
          db[k] = v

  def _load_cache(self, filename):
    self.reduced = {}
    with shelve.open(filename) as db:
      for k, v in db.items():
        self.reduced[k] = v

  def find(self, race, gender, profession, all=False):
    ret = []
    for c in self.reduced.values():
      if c['race'] == race and c['gender'] == gender and c['profession'] == profession:
        if all:
          ret.append(c)
        else:
          return c
    if all:
      return ret
    return False

  def find_missing(self, profession):
    missing = []
    for race in self.races:
      for gender in self.genders:
        if not self.find(race, gender, profession):
          missing.append((race, gender, profession))
    return missing

  def represent(self):
    reps = {}
    for race in GW2.races:
      reps[race] = {}
      for gender in GW2.genders:
        reps[race][gender] = []
    for c in self.reduced.values():
      reps[c['race']][c['gender']].append((c['profession'], c['name']))
    return reps

@arg('profession', choices=GW2.professions, help='The profession of interest')
def find(profession):
  """Find missing race, gender combinations for a given profession."""
  gw2 = GW2("merge")
  missing = gw2.find_missing(profession)
  for m in missing:
    print(m)

def find_all():
  """Find the missing race, gender combinations for each profession."""
  for profession in GW2.professions:
    print(profession)
    find(profession)

def represent():
  """Find how many of each race, gender combination you have."""
  gw2 = GW2("merge")
  rep = gw2.represent()
  for race in GW2.races:
    for gender in GW2.genders:
      print(race, gender, len(rep[race][gender]), rep[race][gender])

#@arg('filename', help='The name of the csv to generate. This is not a good csv for columner data, but a nice table')
def grid(filename=''):
  table = generate_table()
  if filename:
    with open(filename, 'w') as csvfile:
      generate_csv(csvfile, table)
  else:
    csvstream = StringIO()
    generate_csv(csvstream, table)
    print(csvstream.getvalue())
    csvstream.close()

def generate_table():
  gw2 = GW2("merge")
  table = {}
  for profession in GW2.professions:
    table[profession] = {}
    for race in GW2.races:
      table[profession][race] = {}
      for gender in GW2.genders:
        table[profession][race][gender] = [c['name'] for c in gw2.find(race, gender, profession, True)]  
  return table

def generate_csv(writable, table):
    writer = csv.writer(writable)
    row = ['race', 'gender', *GW2.professions]
    writer.writerow(row)
    for race in GW2.races:
      for gender in GW2.genders:
        row = [race, gender, *[', '.join(table[profession][race][gender]) for profession in GW2.professions]]
        writer.writerow(row)

def load_config():
  found = False
  config_file = ''
  for try_config in ['/etc/gw2/config.yml', 'config.yml']:
    if os.path.isfile(try_config):
      found = True
      config_file = try_config
      break
  if found:
    with open(config_file, 'r') as conf:
      return yaml.load(conf, yaml.SafeLoader)
  else:
    print('Cannot find config')
    return {}

def birthdays():
  """lists all characters sorted by birth date (month and day) and puts a marker on the one closest to today"""
  from datetime import date
  from datetime import datetime
  gw2 = GW2()
  list_of_characters = list(gw2.reduced.values())
  def keyfun(c):
    dt = datetime.strptime(c['created'], "%Y-%m-%dT%H:%M:%SZ")
    return (dt.month, dt.day, dt.hour, dt.minute, dt.second)
  list_of_characters = sorted(list_of_characters, key=keyfun)
  today = date.today()
  found = False
  first = False
  for c in list_of_characters:
    if first and found:
      first = False
    if not first and not found and today > datetime.strptime(c['created'], "%Y-%m-%dT%H:%M:%SZ").date().replace(year=today.year):
      first = True
      found = True
    prefix = '*' if first else ' '
    print(prefix + str(c))


parser = argh.ArghParser()
parser.add_commands([find, find_all, represent, grid, birthdays])

if __name__ == '__main__':
  parser.dispatch()
