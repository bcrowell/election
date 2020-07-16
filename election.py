import math,random,statistics

def main():
  electoral_votes = {'az':11,'fl':29,'nc':15,'wi':10,'mi':16,
      'pa':20,'mn':10,'nh':4,'nv':6,
      'ga':16,'ia':6,'oh':18,'tx':38}

  # 2020 jul 15, http://insideelections.com/ratings/president
  lean = {
      'az':0,'fl':0,'nc':0,'wi':0,
      'mi':1,'pa':1,
      'mn':2,'nh':2,
      'nv':3,
      'ga':-1,'ia':-1,'oh':-2,'tx':-2
      }
  # tweaks in cases where these expert opinions don't seem consistent with polls and predictit:
  lean['oh'] += 0.5
  lean['wi'] += 0.5

  # Probability that democrats win the state according to
  # predictit, 2020 jul 15.
  # Not used in calculations, only in output, to help me adjust parameters.
  predictit_prob = {
      'az':0.64,'wi':0.72,'pa':0.76,'fl':0.62,'mi':0.75,'mn':0.81,
      'nh':0.77,'nc':0.58,'oh':0.45,'ia':0.43,'ga':0.46,'tx':0.37,
      'nv':0.82
  }

  # Polling advantage for democrats, 2020 jul 16, fivethirtyeight.com.
  # Not used in simulations, only in output.
  # Used for two purposes: (1) small tweaks to the "lean" stats, (2) helping me to adjust c parameter.
  poll = {
    'az':2.6,'nv':8.5,'pa':7.7,'fl':6.8,'wi':7.6,'mi':9.1,'mn':10,
    'nh':8.0,'nc':2.9,'oh':2.2,'ia':-0.7,'ga':0.9,'tx':-0.3
  }

  # list of states, sorted in order by probability on predictit
  states = list(electoral_votes.keys())
  states.sort(key=lambda s:predictit_prob[s])

  safe_d = 212 # includes 3 electoral votes from maine

  safe_r = 127 # includes 1 electoral vote from maine

  n = len(electoral_votes)
  if n!=len(lean):
    die('n does not match')

  tot = safe_d + safe_r
  for state, v in electoral_votes.items():
    tot = tot+v
  if tot!=538:
    die("tot does not equal 538")

  poll_sd = statistics.stdev(list(poll.values()))
  lean_sd = statistics.stdev(list(lean.values()))
  print("sd(polls)=",poll_sd,", sd(lean)=",lean_sd, "c=",c,", poll/lean=",poll_sd/lean_sd)

  # Parameters a, c, and offset are all in units of percentage points. An overall normalization doesn't affect who wins, but
  # does affect predictions of vote share, and getting it right makes it easier to think abot whether numbers are reasonable.
  a = 17.0 # std dev of popular-vote shift between now and election day; adjust so that dems' prob of winning roughly matches betfair's .64
           # ... but can't realistically get it to go that low
  # correlations among states, see https://projects.economist.com/us-2020-forecast/president/how-this-works
  rho1 = 0.75 # northeastern swing states, i.e., all but NV and FL
  rho2 = 0.5 # florida
  rho3 = 0.25 # nevada
  c = 5 # bias per unit of "lean;" adjust so that scatter among probabilities roughly matches predictit
  offset = 0.8 # add this to "lean" values, otherwise significantly off compared to predictit (and polling)

  ind = {} # uncorrelated std dev of each state
  for state in electoral_votes:
    ind[state] = a*correlation_to_weight(rho1)
  ind['fl'] = a*correlation_to_weight(rho2)
  ind['nv'] = a*correlation_to_weight(rho3)

  k = 10000 # number of trials to run
  d_wins = 0
  state_d_wins = {}
  for state in electoral_votes:
    state_d_wins[state] = 0
  for i in range(k):
    d = safe_d
    pop = a*normal()
    for state, v in electoral_votes.items():
      x = pop+ind[state]*normal()+c*(lean[state]+offset)
      if x>0.0:
        d = d+v
        state_d_wins[state] += 1
    if d>tot*0.5:
      # fixme: handle the case of a tie in the electoral college
      d_wins = d_wins+1

  print("prob of D win=",d_wins/k)
  print("     predictit   sim    polls")
  for state in states:
    print(state," ",lean[state]," ",predictit_prob[state]," ",state_d_wins[state]/k," ",poll[state])

def correlation_to_weight(rho):
  return math.sqrt(rho**-0.5-1)

def normal():
  return random.normalvariate(0,1)

def die(message):
  print(message)

main()
