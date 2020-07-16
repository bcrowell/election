import math,random,statistics

def main():
  electoral_votes = {'az':11,'fl':29,'nc':15,'wi':10,'mi':16,
      'pa':20,'mn':10,'nh':4,'nv':6,
      'ga':16,'ia':6,'oh':18,'tx':38}

  # 2020 jul 15, http://insideelections.com/ratings/president
  lean_raw = {
      'az':0,'fl':0,'nc':0,'wi':0,
      'mi':1,'pa':1,
      'mn':2,'nh':2,
      'nv':3,
      'ga':-1,'ia':-1,'oh':-2,'tx':-2
      }
  # tweaks in cases where these expert opinions don't seem consistent with polls and predictit:
  lean_tweaks = {
      'oh':0.5,'wi':0.5,'nv':-0.5,'nh':-0.5,'mn':-0.5,'ia':-0.5
      }
  lean = {}
  for state in lean_raw:
    lean[state] = lean_raw[state]
    if state in lean_tweaks:
      lean[state] += lean_tweaks[state]

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
  # print("sd(polls)=",poll_sd,", sd(lean)=",lean_sd," poll/lean=",poll_sd/lean_sd)

  """
  The main parameters that it makes sense to fiddle with are A and k.
  Parameters A and c are in units of percentage points. An overall normalization doesn't affect who wins, but
  does affect predictions of vote share, and getting it right makes it easier to think about whether numbers are reasonable.
  A should go down to about 1.5% by the week before election day.

  What are a priori reasonable values of A and k?

  For A, a poll in Nov 2019 showed that 65% of voters would "definitely vote" for one candidate or the other, and another
  19% said there was "not really any chance" they would vote for the other. 
      https://www.statista.com/chart/19872/voters-2020-election-undecided/
  Although turnout is unpredictable, it doesn't seem like there's room for more than 35% of voters to change
  their minds, and among those who do change their minds, there is likely to be a lot of cancellation. So I don't see how
  A can be greater than ~25%.

  For k, setting it to more than ~1 unit means disagreeing significantly with experts, who seem to be expecting reversion
  to the mean of states' past behavior.

  As of July, setting (A,k)=(10,1) gives reasonably good agreement with predictit for swing-state probabilities, and
  with betfair for outcome. With my model, it's difficult to simultaneously reproduce predictit's high probabilities
  for Biden to win states like MN and NV with predictit and betfair's relatively low probabilities for Biden to be elected.
  Setting (A,k)=(15,0.5) gives predictions that are more like what the experts say for swing states, and reproduces
  markets' probs for outcome.
  """
  a = 15.0 # std dev of popular-vote shift between now and election day
  k = 0.5 # setting this to a positive value means I don't believe experts who are saying election is close
  # correlations among states, see https://projects.economist.com/us-2020-forecast/president/how-this-works
  rho1 = 0.75 # northeastern swing states, i.e., all but NV and FL
  rho2 = 0.5 # florida
  rho3 = 0.25 # nevada
  # calibration of "lean" data to give % units
  c = poll_sd/lean_sd

  ind = {} # uncorrelated std dev of each state
  for state in electoral_votes:
    ind[state] = a*correlation_to_weight(rho1)
  ind['fl'] = a*correlation_to_weight(rho2)
  ind['nv'] = a*correlation_to_weight(rho3)

  n_trials = 10000 # number of trials to run
  d_wins = 0
  state_d_wins = {}
  for state in electoral_votes:
    state_d_wins[state] = 0
  for i in range(n_trials):
    d = safe_d
    pop = a*normal()
    for state, v in electoral_votes.items():
      x = pop+ind[state]*normal()+c*(lean[state]+k)
      if x>0.0:
        d = d+v
        state_d_wins[state] += 1
    if d>tot*0.5:
      # fixme: handle the case of a tie in the electoral college
      d_wins = d_wins+1
  prob = {}
  for state in states:
    prob[state] = state_d_wins[state]/n_trials

  print("A=",(("%4.1f") % (a)),", k=",(("%3.1f") % (k)))
  predictit_mean = statistics.mean(list(predictit_prob.values()))
  prob_mean = statistics.mean(list(prob.values()))
  print("mean(simulation)-mean(predictit)=",(("%5.2f") % (prob_mean-predictit_mean,)),"; if predictit data are current, this can be used to adjust the parameter k")

  print("prob of D win=",d_wins/n_trials)
  print("     predictit   sim    polls")
  for state in states:
    print(state," ",lean[state]," ",predictit_prob[state]," ",prob[state]," ",poll[state])

def correlation_to_weight(rho):
  return math.sqrt(rho**-0.5-1)

def normal():
  return random.normalvariate(0,1)

def die(message):
  print(message)

main()
