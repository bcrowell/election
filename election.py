import math,random,statistics,sys

def main():

  """
  Number of electoral votes for each swing state, for 2010-2020.
  Any state on this list must also have data in lean_raw[], predictit_prob[], and poll[].
  """
  electoral_votes = {'az':11,'fl':29,'nc':15,'wi':10,'mi':16,
      'pa':20,'mn':10,'nh':4,'nv':6,
      'ga':16,'ia':6,'oh':18,'tx':38,
      'mt':3,'in':11,'nm':5,'nj':14
    }
  safe_d = 193 # includes 3 electoral votes from maine
  safe_r = 113 # includes 1 electoral vote from maine


  # Semi-quantitative rankings of how much each state leans toward one party or another.
  # Positive = democratic.
  # 2020 jul 15, http://insideelections.com/ratings/president
  lean_raw = {
      'az':0,'fl':0,'nc':0,'wi':0,
      'mi':1,'pa':1,
      'mn':2,'nh':2,
      'nv':3,
      'ga':-1,'ia':-1,'oh':-2,'tx':-2,
       # my own additions:
      'mt':-4,'in':-4,'nm':4,'nj':4
      }
  # My tweaks in cases where these expert opinions don't seem consistent with polls and predictit:
  lean_tweaks = {
      'oh':0.5,'wi':0.5,'nv':-0.5,'nh':-0.5,'mn':-0.5,'ia':-0.5
      }
  # In addition to these per-state tweaks, all values have the parameter k added to them later.
  lean = {}
  for state in lean_raw:
    lean[state] = lean_raw[state]
    if state in lean_tweaks:
      lean[state] += lean_tweaks[state]

  """
  Probability that democrats win the state according to
  predictit, 2020 jul 15.
  Not used in calculations, only in output, to help me adjust parameters.
  """
  predictit_prob = {
      'az':0.64,'wi':0.72,'pa':0.76,'fl':0.62,'mi':0.75,'mn':0.81,
      'nh':0.77,'nc':0.58,'oh':0.45,'ia':0.43,'ga':0.46,'tx':0.37,
      'nv':0.82,'mt':0.18,'in':0.15,'nm':0.91,'nj':0.94
  }

  """
  Polling advantage for democrats, 2020 jul 16, fivethirtyeight.com.
  Used for two purposes: (1) used automatically to normalize the c parameter;
  (2) helps me to decide on lean_tweaks[].
  """
  poll = {
    'az':2.6,'nv':8.5,'pa':7.7,'fl':6.8,'wi':7.6,'mi':9.1,'mn':10,
    'nh':8.0,'nc':2.9,'oh':2.2,'ia':-0.7,'ga':0.9,'tx':-0.3,
    'mt':-9.3,'in':-11.5,'nm':14,'nj':22
  }

  # list of states, sorted in order by probability on predictit
  states = list(electoral_votes.keys())
  states.sort(key=lambda s:predictit_prob[s])

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
  Set adjustable parameters. The main parameters that it makes sense to fiddle with are A, k, and d.
  A = std dev of popular-vote shift between now and election day
  k = offset to lean[] values; setting this to a positive value means I don't believe experts who are saying election is close
  s = a fudge factor for variability of state votes, see below
  Parameters A and c are in units of percentage points. An overall normalization doesn't affect who wins, but
  does affect predictions of vote share, and getting it right makes it easier to think about whether numbers are reasonable.
  A should go down to about 5% by the week before election day.

  What are a priori reasonable values of A and k?

  For A, a poll in Nov 2019 showed that 65% of voters would "definitely vote" for one candidate or the other, and another
  19% said there was "not really any chance" they would vote for the other. 
      https://www.statista.com/chart/19872/voters-2020-election-undecided/
  Although turnout is unpredictable, it doesn't seem like there's room for more than 35% of voters to change
  their minds, and among those who do change their minds, there is likely to be a lot of cancellation. So I don't see how
  A can be greater than ~25%.

  "[State polls taken during the last 21 days before election day] had a weighted average error of 5.3 points"
  https://fivethirtyeight.com/features/how-accurate-have-state-polls-been/
  This is about double the error for national polls. That partly means that states are really more variable, and
  partly that state polling isn't as good or intensive.

  For national popular-vote polls, twelve months out, the average absolute error is about 12%, 4 months out is 9%,
  and in the final month 2.5%.
  https://politics.stackexchange.com/questions/54680/historical-data-on-how-the-reliability-of-polling-data-depends-on-time-remaining

  So reasonable estimates for A, which measures national vote uncertainty, are: July 9%, November 2.5%.

  For k, setting it to more than ~1 unit means disagreeing significantly with experts, who seem to be expecting reversion
  to the mean of states' past behavior.

  The rho values I'm using are correlations are state A with state B. I want mine to be state with national, but that should be about the same.
  However, if I just take the per-state variation to be what would mathematically reproduce these rho values, then
  the per-state variation only turns out to contribute about half the variance. This is too small, since state polling
  generally has about twice the error of national polling, and therefore we want per-state variation to be about twice
  as big as we would get from the rho values. This is the reason for including the fudge factor s and setting it to
  about 2. The effect of making s>1 is to make the underdog less likely to win. The reason for this is that if the
  underdog is to win, there has to be a big nationwide change, but for larger s, variability of each state makes this
  impossible because states' randomness swamps any such "cooperation."
  """
  a = 9.0 # see above for how this should go down over time
  k = 0.5 # see above
  s = 2.0
  # correlations among states, see https://projects.economist.com/us-2020-forecast/president/how-this-works
  rho1 = 0.75 # northeastern swing states, i.e., all but NV and FL
  rho2 = 0.5 # florida
  rho3 = 0.25 # nevada
  # calibration of "lean" data to give % units
  c = poll_sd/lean_sd

  ind = {} # uncorrelated std dev of each state
  for state in electoral_votes:
    ind[state] = correlation_to_weight(rho1)
  ind['fl'] = correlation_to_weight(rho2)
  ind['nv'] = correlation_to_weight(rho3)
  for state in electoral_votes:
    ind[state] *= (a*s)

  n_trials = 10000 # number of trials to run
  d_wins = 0
  state_d_wins = {}
  rcl = {} # republican win conditioned on losing this state
  for state in electoral_votes:
    state_d_wins[state] = 0
    rcl[state] = 0
  for i in range(n_trials):
    d = safe_d
    pop = a*normal()
    x = {}
    for state, v in electoral_votes.items():
      x[state] = pop+ind[state]*normal()+c*(lean[state]+k)
      if x[state]>0.0:
        d = d+v
        state_d_wins[state] += 1
    if d>tot*0.5:
      # fixme: handle the case of a tie in the electoral college
      d_wins = d_wins+1
    else:
      for state in electoral_votes:
        if x[state]>0.0:
          rcl[state] += 1
  prob = {}
  for state in states:
    prob[state] = state_d_wins[state]/n_trials

  print("A=",f1(a),", k=",f1(k),", s=",f1(s))
  predictit_mean = statistics.mean(list(predictit_prob.values()))
  prob_mean = statistics.mean(list(prob.values()))
  print("mean(simulation)-mean(predictit)=",f2(prob_mean-predictit_mean),"; if predictit data are current, this can be used to adjust the parameter k")

  print("prob of D win=",d_wins/n_trials)
  print("           predictit   sim   polls     RCL")
  for state in states:
    print(state," ",f1(lean[state]),"   ",f2(predictit_prob[state])," ",f2(prob[state])," ",f1(poll[state])," ",f2(rcl[state]/n_trials))

def correlation_to_weight(rho):
  return math.sqrt(rho**-0.5-1)

def normal():
  return random.normalvariate(0,1)

def die(message):
  sys.exit(message)

def f1(x):
  return ("%4.1f") % x

def f2(x):
  return ("%5.2f") % x

main()
