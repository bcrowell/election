import math,random,statistics,sys,csv

def main():

  electoral_votes = {}
  lean = {}
  predictit_prob = {}
  poll = {}
  with open('data.csv', newline='') as csv_file:
    csv_reader = csv.reader(csv_file)
    titles = True
    for row in csv_reader:
      if titles:
        titles = False
        continue
      state = row[0]
      electoral_votes[state] = int(row[1])
      lean[state] = float(row[2])
      predictit_prob[state] = float(row[3])
      poll[state] = float(row[4])

  # Safe states are those that don't occur in the data file.
  safe_d =  68 # includes 3 electoral votes from maine
  safe_r = 113 # includes 1 electoral vote from maine

  # list of states, sorted in order by probability on predictit
  states = list(electoral_votes.keys())
  states.sort(key=lambda s:predictit_prob[s])

  n = len(electoral_votes)
  if n!=len(lean):
    die('n does not match')

  # Check that the total number of electoral votes is what it should be. This value doesn't change when there's a census, because
  # it's capped by statute at this value: https://en.wikipedia.org/wiki/United_States_congressional_apportionment
  tot = safe_d + safe_r
  for state, v in electoral_votes.items():
    tot = tot+v
  if tot!=538:
    die("tot does not equal 538")

  # Calculate a measure of the spread in the lean[] values and the poll[] values, to allow the normalization parameter
  # c to be calculated. I.e., how many % points is one unit of "lean?"
  poll_sd = statistics.stdev(list(poll.values()))
  lean_sd = statistics.stdev(list(lean.values()))

  '''
  Set adjustable parameters. The main parameters that it makes sense to fiddle with are A, k, and d.
  A = mean absolute error of popular-vote shift between now and election day
  k = offset to lean[] values; setting this to a positive value means I don't believe experts who are saying election is close
  s = a fudge factor for variability of state votes, see below
  Parameters A and c are in units of percentage points. An overall normalization doesn't affect who wins, but
  does affect predictions of vote share, and getting it right makes it easier to think about whether numbers are reasonable.

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

  All of the above assumes a normal distribution, but I doubt that real political fluctuations have tails as skinny as
  those of a normal distribution. Epidemics and volcanoes happen, etc. I currently have dist=cauchy rather than normal.
  My data sources for A express central tendency as mean absolute error, so when dist='normal', we pick the standard
  deviation sigma to reproduce this for a normal distribution. For a Cauchy distribution, the mean absolute error is
  undefined. Therefore when dist='cauchy', we pick a Cauchy distribution with the same interquartile range. In July 2020,
  this has the effect of making the per-state probabilities agree worse with predictit on "safe" states, but I think this is reasonable.

  For k, setting it to more than ~1 unit means disagreeing significantly with experts, who in July 2020 seem to be expecting reversion
  to the mean of states' past behavior.

  The rho values I'm using are correlations are state A with state B. I want mine to be state with national, but that should be about the same.
  However, if I just take the per-state variation to be what would mathematically reproduce these rho values, then
  the per-state variation only turns out to contribute about half the variance. This is too small, since state polling
  generally has about twice the error of national polling, and therefore we want per-state variation to be about twice
  as big as we would get from the rho values. This is the reason for including the fudge factor s and setting it to
  about 2. The effect of making s>1 can counterintuitively be to make the underdog less likely to win. The reason for this is
  is that (1) that variability doesn't help them much, because the underdog needs big correlated change, not uncorrelated change;
  and (2) the model counts some states as safe, so in the limit as s->infty whoever has more safe electoral votes has the higher
  probability of winning.
  '''
  a = 9.0 # see above for how this should go down over time
  k = 0.5 # see above
  s = 2.0 # see above
  dist = 'cauchy' # can be cauchy or normal
  # correlations among states, see https://projects.economist.com/us-2020-forecast/president/how-this-works
  rho1 = 0.75 # northeastern swing states, i.e., all but NV and FL
  rho2 = 0.5 # florida
  rho3 = 0.25 # nevada
  # calibration of "lean" data to give % units
  c = poll_sd/lean_sd

  aa = math.sqrt(math.pi/2.0)*a # Convert mean absolute value to std dev, assuming normal, even if normal isn't what we're actually using.
                                # See notes on how choice of distribution function affects A.

  ind = {} # uncorrelated std dev of each state
  for state in electoral_votes:
    ind[state] = correlation_to_weight(rho1)
  ind['fl'] = correlation_to_weight(rho2)
  ind['nv'] = correlation_to_weight(rho3)
  for state in electoral_votes:
    ind[state] *= (aa*s)

  n_trials = 10000 # number of trials to run
  d_wins = 0
  state_d_wins = {}
  rcl = {} # republican win conditioned on losing this state
  for state in electoral_votes:
    state_d_wins[state] = 0
    rcl[state] = 0
  for i in range(n_trials):
    d = safe_d
    pop = aa*bell_curve(dist)
    x = {}
    for state, v in electoral_votes.items():
      x[state] = pop+ind[state]*bell_curve(dist)+c*(lean[state]+k)
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
    rcl[state] = rcl[state]/(n_trials*prob[state]) # number of times the joint event happened, divided by the number of times the
                                                   # even conditioned on happened

  print("A=",f1(a),", k=",f1(k),", s=",f1(s),", dist=",dist)
  if dist=='cauchy':
    print("Note: Since dist is Cauchy, which has fat tails, probabilities for safe states are less extreme. This is intentional.")
  predictit_mean = statistics.mean(list(predictit_prob.values()))
  prob_mean = statistics.mean(list(prob.values()))
  print("mean(simulation)-mean(predictit)=",f2(prob_mean-predictit_mean),"; if predictit data are current, this can be used to adjust the parameter k")

  print("prob of D win=",d_wins/n_trials)
  print("           predictit   sim   polls     RCL")
  for state in states:
    print(state," ",f1(lean[state]),"   ",f2(predictit_prob[state])," ",f2(prob[state])," ",f1(poll[state])," ",f2(rcl[state]))

def correlation_to_weight(rho):
  return math.sqrt(rho**-0.5-1)

def bell_curve(dist):
  # See notes about how choice of dist affects A.
  if dist=='normal':
    return normal()
  if dist=='cauchy':
    return cauchy()
  die("illegal value of dist in bell_curve")

def cauchy():
  """
  Generate a Cauchy random variable with center 0 and the same interquartile range as a standard normal curve.
  Use this rather than a normal curve to get fatter tails and more spice.
  https://math.stackexchange.com/questions/484395/how-to-generate-a-cauchy-random-variable
  https://en.wikipedia.org/wiki/Cauchy_distribution
  """
  y = random.random()
  scale = 1.34896/2.0 # interquartile range of standard normal is 1.35..., of Cauchy(0,1) is 2
  return scale*math.tan(math.pi*(y-0.5))

def normal():
  return random.normalvariate(0,1)

def die(message):
  sys.exit(message)

def f1(x):
  return ("%4.1f") % x

def f2(x):
  return ("%5.2f") % x

main()
