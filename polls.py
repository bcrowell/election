#!/bin/python3

# parse a csv file in the format supplied by https://projects.fivethirtyeight.com/polls-page/president_polls.csv
# output a CSV file consisting only of polls within the last 60 days that fivethirtyeight rates at least B and that are not partisan

import math,sys,csv,re,copy,datetime,statistics

def main():
  now = datetime.datetime.now()
  infile = 'president_polls.csv'
  outfile = 'polls.csv'
  candidates = ("biden","trump")
  i_state = 0
  i_answer = 5
  i_pct = 6
  i_pollster = 7
  with open(infile, newline='') as csv_file:
    csv_reader = csv.reader(csv_file)
    titles = True
    raw_rows = []
    for row in csv_reader:
      if titles:
        titles = False
        col_map = {}
        for key in cols():
          col_map[key] = row.index(key) # throws ValueError if not found
        #print("columns: ",col_map)
        continue
      d = unpack_row(row,col_map,["state","fte_grade","office_type","end_date","partisan","answer","pct","pollster"])
      state,grade,office,date,partisan,answer,pct,pollster = d # if changing this list, change i_answer and i_state, and also change similar list later
      if  (not re.search(r"\w",state)) or (not re.search(r"\w",grade)) or (not re.search(r"president",office,re.IGNORECASE)):
        continue
      if (not re.search(r"\d",date)) or (not re.search(r"\w",answer)) or (not re.search(r"\d",pct)):
        continue
      if re.search(r"\w",partisan): # this is blank for polls from the primaries
        continue
      if (not re.search(r"[AB]",grade)) or re.search(r"(C|B\-)",grade): # reject b/c, b-, or anything that doesn't have a or b in it
        continue
      if not (answer.lower() in candidates):
        continue
      d[i_answer] = answer.lower() # candidate
      d[i_state] = state_to_abbrev(state)
      raw_rows.append(d)
    polls = {}
    # sort into groups representing single polls
    for d in raw_rows:
      state,grade,office,date,partisan,answer,pct,pollster = d
      key = state+","+date+","+pollster
      if key in polls:
        polls[key].append(d)
      else:
        polls[key] = [d]
    # once in a while we get two polls from the same pollster, with the same end date, for the same state:
    new_polls = {}
    for key in polls:
      x = polls[key]
      if len(x)==2:
        new_polls[key] = x
      else:
        for i in range(int(len(x)/2)):
          new_polls[key+","+str(i)] = [x[i],x[i+1]]
    polls = new_polls
    # extract results that are head-to-head match-ups of the two candidates we care about, and sort by state
    by_state = {}
    for key in polls:
      d1,d2 = polls[key]
      # get them in canonical order
      if d1[i_answer]==candidates[1] and d2[i_answer]==candidates[0]:
        temp = copy.deepcopy(d1)
        d1 = d2
        d2 = temp
      if d1[i_answer]==candidates[0] and d2[i_answer]==candidates[1]:
        state,grade,office,date,partisan,answer,pct,pollster = d1
        pct = float(d1[i_pct])-float(d2[i_pct])
        if not (state in by_state):
          by_state[state] = []
        by_state[state].append({'raw':d1,'date':date,'pct':pct})
      else:
        print(d1)
    states = list(by_state.keys())
    states.sort()
    with open(outfile,'w') as f:
      for state in states:
        results = []
        pollsters = [] # only take the first poll by a given pollster on a given date
        details = ''
        for poll in by_state[state]: # dict with keys raw, date, pct
          age = (now-datetime.datetime.strptime(poll['date'], '%m/%d/%y')).days
          pkey = poll['raw'][i_pollster]+","+poll['date']
          if pkey in pollsters:
            continue # only take the first poll by a given pollster on a given date
          pollsters.append(pkey)
          if age<60:
            details = details + f"    {poll['date']} {poll['pct']} {poll['raw'][i_pollster]}\n"
            results.append(poll['pct'])
        if len(results)==0:
          continue
        avg = statistics.mean(results)
        print("state=",state,", avg=",f1(avg))
        print(details)
        f.write(f'{state.lower()},{f1(avg)}\n')
  print(f"Output written to {outfile}")

def unpack_row(row,col_map,keys):
  result = []
  for key in keys:
    col = col_map[key]
    result.append(row[col])
  return result

def cols():
  return ["state","fte_grade","office_type","end_date","partisan","answer","pct","pollster"]

def state_to_abbrev(name):
  # https://gist.github.com/rogerallen/1583593 , public domain
  return {
    'Alabama': 'AL',
    'Alaska': 'AK',
    'American Samoa': 'AS',
    'Arizona': 'AZ',
    'Arkansas': 'AR',
    'California': 'CA',
    'Colorado': 'CO',
    'Connecticut': 'CT',
    'Delaware': 'DE',
    'District of Columbia': 'DC',
    'Florida': 'FL',
    'Georgia': 'GA',
    'Guam': 'GU',
    'Hawaii': 'HI',
    'Idaho': 'ID',
    'Illinois': 'IL',
    'Indiana': 'IN',
    'Iowa': 'IA',
    'Kansas': 'KS',
    'Kentucky': 'KY',
    'Louisiana': 'LA',
    'Maine': 'ME',
    'Maryland': 'MD',
    'Massachusetts': 'MA',
    'Michigan': 'MI',
    'Minnesota': 'MN',
    'Mississippi': 'MS',
    'Missouri': 'MO',
    'Montana': 'MT',
    'Nebraska': 'NE',
    'Nevada': 'NV',
    'New Hampshire': 'NH',
    'New Jersey': 'NJ',
    'New Mexico': 'NM',
    'New York': 'NY',
    'North Carolina': 'NC',
    'North Dakota': 'ND',
    'Northern Mariana Islands':'MP',
    'Ohio': 'OH',
    'Oklahoma': 'OK',
    'Oregon': 'OR',
    'Pennsylvania': 'PA',
    'Puerto Rico': 'PR',
    'Rhode Island': 'RI',
    'South Carolina': 'SC',
    'South Dakota': 'SD',
    'Tennessee': 'TN',
    'Texas': 'TX',
    'Utah': 'UT',
    'Vermont': 'VT',
    'Virgin Islands': 'VI',
    'Virginia': 'VA',
    'Washington': 'WA',
    'West Virginia': 'WV',
    'Wisconsin': 'WI',
    'Wyoming': 'WY',
    'Nebraska CD-2': 'NE-02',
    'Maine CD-1': 'ME-01',
    'Maine CD-2': 'ME-02'
  }[name]

def f1(x):
  if x is None:
    return "----"
  else:
    return ("%5.1f") % x

main()


