#!/bin/python3

import math,random,statistics,sys,csv,re,copy

def parameters(filename):
  '''
  Set adjustable parameters. The main parameters that it makes sense to fiddle with are A, k, s, and dist.
  See README for how to decide on these values.
  The defaults can be overridden from the command line, e.g., election.py a=10.
  '''

  pars = get_defaults_from_file(filename)

  missing = set(pars.keys())-set(parameter_names())
  if not set_is_empty(missing):
    die("missing parameters: "+repr(missing))

  # correlations among states, see https://projects.economist.com/us-2020-forecast/president/how-this-works
  rho1 = 0.75 # northeastern swing states, i.e., all but NV and FL
  rho2 = 0.5 # florida
  rho3 = 0.25 # nevada

  pars['rho'] = (rho1,rho2,rho3)
  pars['joint'] = ('','')

  pars = get_command_line_pars(pars) # override defaults

  return pars

def main():

  pars = parameters('defaults.txt')
  (a,k,s,dist,rho,n_trials,joint,tie) = (pars['a'],pars['k'],pars['s'],pars['dist'],pars['rho'],pars['n_trials'],pars['joint'],pars['tie'])
  (rho1,rho2,rho3) = rho

  sd = state_data('data.csv','polls.csv')
  (electoral_votes,lean,predictit_prob,poll,undecided,safe_d,safe_r,tot,states) = (
            sd['electoral_votes'],sd['lean'],sd['predictit_prob'],sd['poll'],sd['undecided'],
            sd['safe_d'],sd['safe_r'],sd['tot'],sd['states'])

  n = len(electoral_votes) # number of swing states
  c = calibrate_lean_to_percent(poll,lean)
  aa = math.sqrt(math.pi/2.0)*a # Convert mean absolute value to std dev, assuming normal, even if normal isn't what we're actually using.
                                # See notes on how choice of distribution function affects A.

  ind = {} # uncorrelated std dev of each state
  for state in electoral_votes:
    ind[state] = correlation_to_weight(rho1)
  ind['fl'] = correlation_to_weight(rho2)
  ind['nv'] = correlation_to_weight(rho3)
  for state in electoral_votes:
    ind[state] *= (aa*s)

  d_wins = 0
  state_d_wins = {}
  rcl = {} # republican win conditioned on losing this state
  vote_avg = {}
  for state in electoral_votes:
    state_d_wins[state] = 0
    rcl[state] = 0
    vote_avg[state] = 0
  joint_table = [[0,0],[0,0]]
  electoral_college_histogram = [0] * n_predictit_bins()
  tipping_histogram = {}
  for state in electoral_votes:
    tipping_histogram[state] = 0
  for i in range(n_trials):
    t = do_one_trial({'safe_d':safe_d,'safe_r':safe_r,'aa':aa,'k':k,'s':s,'dist':dist,'tot':tot,'c':c,
                 'ind':ind,'electoral_votes':electoral_votes,'lean':lean,'tie':tie})
    d_wins += t['d_win']
    electoral_college_histogram[t['bin']] += 1
    tipping_histogram[t['tipping']] += 1
    for state in states:
      state_d_wins[state] += t['state_d_win'][state]
      if t['state_d_win'][state]==1 and t['d_win']==0:
        rcl[state] += 1
    joint_events = [0,0] 
    for i in range(2):
      if joint[i]!='' and joint[i]!='nat':
        joint_events[i] = t['state_d_win'][joint[i]]
      else:
        joint_events[i] = t['d_win']
    joint_table[joint_events[0]][joint_events[1]] += 1
    for state in states:
      vote_avg[state] += t['vote'][state]/n_trials
  prob = {}
  for state in states:
    prob[state] = state_d_wins[state]/n_trials
    if prob[state]>0.0:
      rcl[state] = rcl[state]/(n_trials*prob[state]) # number of times the joint event happened, divided by the number of times the
                                                     # even conditioned on happened
    else:
      rcl[state] = None

  d_prob = d_wins/n_trials
  output(pars,
         {'d_prob':d_prob,'prob':prob,'rcl':rcl,'joint_table':joint_table,'aa':aa,'c':c},
         {'electoral_votes':electoral_votes,'lean':lean,'predictit_prob':predictit_prob,'poll':poll,'undecided':undecided,
            'safe_d':safe_d,'safe_r':safe_r,'tot':tot,'states':states,'ind':ind,'vote_avg':vote_avg,
            'electoral_college_histogram':electoral_college_histogram,'tipping_histogram':tipping_histogram}
        )
  write_electoral_college_histogram('histogram.txt',electoral_college_histogram,n_trials)
  write_tipping_histogram('tipping.txt',tipping_histogram,n_trials,states)


def write_tipping_histogram(filename,histogram,n_trials,states):
  with open(filename,'w') as f:
    print("probabilities of tipping points:",file=f)
    for state in states:
      print(f"  {state}  {f3(histogram[state]/n_trials)}",file=f)

def write_electoral_college_histogram(filename,electoral_college_histogram,n_trials):
  with open(filename,'w') as f:
    print("probabilities of electoral college margins:",file=f)
    for b in range(n_predictit_bins()):
      r = predictit_bin_to_margin_range(b)
      print("  ",r[0],"to",r[1],", ",f2(electoral_college_histogram[b]/n_trials),file=f)

def output(pars,results,sd):
  (a,k,s,dist,n_trials,joint,swing) = (pars['a'],pars['k'],pars['s'],pars['dist'],pars['n_trials'],pars['joint'],pars['swing'])
  (d_prob,prob,rcl,joint_table,aa,c) = (results['d_prob'],results['prob'],results['rcl'],results['joint_table'],results['aa'],results['c'])
  (electoral_votes,lean,predictit_prob,poll,undecided,safe_d,safe_r,tot,states,ind,vote_avg) = (
            sd['electoral_votes'],sd['lean'],sd['predictit_prob'],sd['poll'],sd['undecided'],
            sd['safe_d'],sd['safe_r'],sd['tot'],sd['states'],sd['ind'],sd['vote_avg'])

  print("A=",f1(a),", k=",f1(k),", s=",f1(s),", dist=",dist,", c=",f1(c))
  if dist=='cauchy':
    print("Note: Since dist is Cauchy, which has fat tails, probabilities for safe states are less extreme. This is intentional.")
  if swing==1:
    print("Because swing=1, some states are omitted from the listing.")
  print("Half inter-quartile range (HIQR) of nationally correlated fluctuations = ",f2(iqr('normal')*aa/2.0)," %")
  # ... aa is defined such that if dist is normal, it's the std dev, and if dist is cauchy it's the std dev of the normal that has the same IQR
  predictit_mean = statistics.mean(list(predictit_prob.values()))
  prob_mean = statistics.mean(list(prob.values()))
  #print("mean(simulation)-mean(predictit)=",f2(prob_mean-predictit_mean),"; if predictit data are current, this can be used to adjust the parameter k")
  #...to be useful, this feature should restrict itself to real swing states

  print("prob of D win=",d_prob)
  print("             lean       predictit  sim       polls    sim      HIQR        RCL")
  for state in states:
    if swing==0 or (predictit_prob[state]>0.20 and predictit_prob[state]<0.80):
      sym = uncertainty_symbol(poll[state],undecided[state])
      print(ps(state),"      ",f1(lean[state]),"     ",f2(predictit_prob[state])," ",f2(prob[state]),"    ",
           f1(poll[state]),sym," ",f1(vote_avg[state])," ",f2(iqr('normal')*ind[state]/2.0),"    ",f2(rcl[state])
    )

  if joint[0]!='':
    print("joint probabilities:")
    for i in range(2):
      for j in range(2):
        joint_table[i][j] *= 1.0/n_trials
    print("               D in ",ps(joint[1]))
    print("               lose     win")
    for i in range(2):
      if i==0:
        descr = "lose"
      else:
        descr = " win"
      print(" ",descr,"",ps(joint[0]),f2(joint_table[i][0])," ",f2(joint_table[i][1]))
        

def do_one_trial(dat):
  (safe_d,safe_r,aa,k,s,dist,tot,c,ind,electoral_votes,lean,tie) = (dat['safe_d'],dat['safe_r'],
              dat['aa'],dat['k'],dat['s'],dat['dist'],dat['tot'],dat['c'],
              dat['ind'],dat['electoral_votes'],dat['lean'],dat['tie'])
  d = safe_d
  pop = aa*bell_curve(dist)
  x = {}
  t = {}
  t['state_d_win'] = {}
  for state, v in electoral_votes.items():
    x[state] = bell_to_200_percent_range(pop+ind[state]*bell_curve(dist)+c*(lean[state]+k))
    if x[state]>0.0:
      d = d+v
      t['state_d_win'][state] = 1
    else:
      t['state_d_win'][state] = 0
  tie = (d*2==tot)
  if d>tot*0.5 or (tie and dat['tie']==1):
    t['d_win'] = 1
  else:
    t['d_win'] = 0
  t['vote'] = x
  t['bin'] = vote_margin_to_predictit_bin(2*d-electoral_college_size())[0]
  t['tipping'] = tipping_point(safe_d,safe_r,x,electoral_votes,dat['tie'],t['d_win'],2) # 2 means use predictit's definition
  return t

def calibrate_lean_to_percent(poll,lean):
  # Calculate a measure of the spread in the lean[] values and the poll[] values, to allow the normalization parameter
  # c to be calculated. I.e., how many % points is one unit of "lean?"
  swing_poll_list = []
  swing_lean_list = []
  for state in poll:
    if abs(lean[state])<=2 and state in poll and not (poll[state] is None) and abs(poll[state]<6.0):
      # Don't count states with huge lean values L. These aren't real swing states, and those values aren't carefully calibrated and aren't
      # relevant to the outcome of the election. Exclude states with extreme polling, because they can influence c too much.
      # E.g., at the end of July 2020, PA was Biden+12 in high-quality polls (which may have been outliers), but experts were
      # giving PA a relatively small L.
      swing_poll_list.append(poll[state])
      swing_lean_list.append(lean[state])
  poll_spread = spread(swing_poll_list)
  lean_spread = spread(swing_lean_list)

  # calibration of "lean" data to give % units
  c = poll_spread/lean_spread
  return c

def state_data(filename,polls_file):
  electoral_votes = {}
  lean = {}
  predictit_prob = {}
  poll = {}
  undecided = {}
  with open(filename, newline='') as csv_file:
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
      poll[state] = None
      undecided[state] = None
  with open(polls_file, newline='') as csv_file:
    csv_reader = csv.reader(csv_file)
    titles = True
    for row in csv_reader:
      if titles:
        titles = False
        continue
      state = row[0]
      if state in lean:
        poll[state] = float(row[1])
        undecided[state] = float(row[2])

  # list of states, sorted in order by lean, and secondarily by polls, probability on predictit
  states = list(electoral_votes.keys())
  states.sort(key=lambda s:lean[s]) # rough initial sort
  states = bubble_sort(states,lean,poll,predictit_prob) # refine the sort; can't do this using python's sort

  # Safe states are those that don't occur in the data file.
  safe_d =  68 # includes 3 electoral votes from maine, but not ME-02
  safe_r =  93 # includes 4 electoral votes from nebraska, but not NE-02

  # Check that the total number of electoral votes is what it should be. 
  tot = safe_d + safe_r
  for state, v in electoral_votes.items():
    tot = tot+v
  if tot!=electoral_college_size():
    die("tot does not equal correct size for electoral college")

  return {'electoral_votes':electoral_votes,'lean':lean,'predictit_prob':predictit_prob,'poll':poll,'undecided':undecided,
            'safe_d':safe_d,'safe_r':safe_r,'tot':tot,'states':states}

# This value doesn't change when there's a census, because
# it's capped by statute at this value: https://en.wikipedia.org/wiki/United_States_congressional_apportionment
def electoral_college_size():
  return 538

def sort_order(lean,poll,predictit_prob):
  if poll is None:
    p = 0.0
  else:
    p = poll
  return (lean,p,predictit_prob)  

def bubble_sort(orig,lean,polls,prob):
  """
  For efficiency, we do this after an initial, more efficient sort using python's sort function. The problem
  with python's sort is that it doesn't allow special-casing when we lack data for a certain field.
  """
  states = copy.deepcopy(orig)
  while True:
    n_swaps = 0
    for i in range(len(states)-1):
      s1 = states[i]
      s2 = states[i+1]
      if cmp((lean[s1],polls[s1],prob[s1]),(lean[s2],polls[s2],prob[s2]))<0:
        n_swaps += 1
        temp = s1
        states[i] = s2
        states[i+1] = temp
    if n_swaps==0:
      break
  return states

def cmp(p1,p2):
  """
  Defines sort order. p1 and p2 are each 3-tuples of (lean,poll,probability).
  The poll data may be None, which is why we have to go to all this trouble.
  """
  l1,po1,pr1 = p1
  l2,po2,pr2 = p2
  if l1!=l2:
    return l2-l1
  if not ((po1 is None) or (po2 is None)):
    return po2-po1
  return pr2-pr1

def uncertainty_symbol(pp,uu):
  # pp = difference in polls
  # uu = % undecided
  if pp is None:
    return " "
  p = pp/100.0
  u =uu/100.0
  d = 1-u # fraction who have decided
  x = (d+p)/2.0 # fraction D
  y = (d-p)/2.0 # fraction R
  l = min(x,y) # lower share
  f = (0.5-l)/u # fraction of undecideds that the current loser would in order to win
  if f>0.9:
    return "!" # current loser would need 9/10 of undecideds to go to them in order to win
  if f>0.6:
    return " "
  return "?"

def tipping_point(safe_d,safe_r,margins,electoral_votes,tie,d_win,tip_definition):
  """
  tie = 0 if R's win on a tie, 1 if D's do
  d_win=0 if R won, 1 if D won
  tip_definition=1 means what really happens based on tie, 2 means predictit's definition
  """
  if d_win:
    sgn = -1
    winning_votes = safe_d
  else:
    sgn = 1
    winning_votes = safe_r
  states = list(margins.keys())
  states.sort(key=lambda state:sgn*margins[state]) # for D win, this starts from the safest blue states, like california
  if tip_definition==1:
    if (tie==0 and d_win==0) or (tie==1 and d_win==1):
      # Winner would win with a tie
      needed = electoral_college_size()/2
    else:
      needed = int(electoral_college_size()/2+1)
  else:
    needed = int(electoral_college_size()/2+1)
  for state in states:
    before = winning_votes
    after = before+electoral_votes[state]
    if before<needed and after>=needed:
      return state
    winning_votes += electoral_votes[state]
  raise Exception("tipping point not found")

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
  y = random.random() # uniform
  scale = iqr('normal')/iqr('cauchy')
  return scale*math.tan(math.pi*(y-0.5)) # this is different from the atan(...) applied elsewhere

def iqr(dist):
  """
  Return the interquartile range of normal(0,1) or Cauchy(0,1),
  """
  if dist=='normal':
    return 1.34896
  if dist=='cauchy':
    return 2
  die(f'in width_to_iqr(), illegal dist={dist}')

def bell_to_200_percent_range(x):
  """
  Input x is a random variable meant to represent a margin of victory in an election, in %, but sampled from
  a bell curve with tails that cover the whole real line. This isn't actually logically right, because you
  can't win by more than 100% or lose by less than 100%. Therefore, put x through a nonlinear transformation
  that brings it into the range of possibile values. The choice of a nonlinear function is somewhat arbitrary,
  but has to satisfy the criterion (1) that f(0)=0, so that it doesn't affect the actual outcome of
  a state primary. I would also like it to have property (2) that for a toss-up state, it doesn't change the
  input much, i.e., f'(0)=1. I chose an arctan because if the distribution of x is derived from a Cauchy distribution,
  then it's possible for the resulting distribution to be uniform. (tan(x) is Cauchy if x is uniform on -pi/2 to pi/2.)
  This means that we can get distributions for f that don't go to zero at +-100%, and I think that makes sense, e.g.,
  it is logically possible for the U.S. to become a fascist dictatorship and have 100% of votes go to the dictator
  in a fake plebiscite.
  """
  if True:
    n = 100.0/(math.pi/2)
    return n*math.atan(x/n)
  else:
    if x<-100.0:
      return -100.0
    if x>100.0:
      return 100.0
    return x

def normal():
  return random.normalvariate(0,1)

def die(message):
  sys.exit(message)

def f1(x):
  if x is None:
    return "  ---"
  else:
    return ("%5.1f") % x

def f2(x):
  if x is None:
    return "-----"
  else:
    return ("%5.2f") % x

def f3(x):
  if x is None:
    return "-----"
  else:
    return ("%6.3f") % x

def predictit_bins():
  return [0, 10, 30, 60, 100, 150, 210, 280] # special casing for 0

def predictit_bin_to_margin_range(b):
  r = raw_predictit_bin_to_margin_range(b)
  if r[0]==0:
    return(1,r[1])
  return r

def raw_predictit_bin_to_margin_range(b):
  if b<0 or b>n_predictit_bins()-1:
    print("error, illegal b=",b," in predictit_bin_to_margin_range")
    die('')
  if b<n_predictit_bins()/2:
    result = raw_predictit_bin_to_margin_range(n_predictit_bins()-b-1)
    return (-result[1],-result[0])
  k = int(b-n_predictit_bins()/2)
  if k+1<len(predictit_bins()):
    hi=predictit_bins()[k+1]-1
  else:
    hi=electoral_college_size()
  return (predictit_bins()[k],hi)

def vote_margin_to_predictit_bin(x):
  """
  returns (bin number,low,high)
  bin numbers for R go from 0 to neg values, for D from 1 to higher pos values
  """
  bins = predictit_bins()
  if x==0:
    return (0,-(bins[1]-1),0) # 0 is counted the same as a win for R in 2020
  if x<0:
    a = vote_margin_to_predictit_bin(-x)
    return (n_predictit_bins()-a[0]-1,-a[1],-a[2])
  for i in range(len(bins)-1):
    if x>=bins[i] and x<bins[i+1]:
      return (int(n_predictit_bins()/2)+i,bins[i],bins[i+1]-1)
  return (n_predictit_bins()-1,bins[len(bins)-1],electoral_college_size())

def n_predictit_bins():
  return 16

def ps(state):
  # Convert stuff like "fl" to "FL".
  if state=='m2':
    return "ME-02"
  if state=='n2':
    return "NE-02"
  if state=="nat":
    return state
  return state.upper()+"   "

def get_defaults_from_file(file):
  pars = {}
  with open(file, newline='') as par_file:
    for line in par_file:
      if re.search(r"[^\s]",line):
        pars = get_one_par(pars,line,f"reading defaults from file {file}")
  return pars

def get_command_line_pars(pars):
  for arg in sys.argv[1:]:
    pars = get_one_par(pars,arg,"reading command-line parameters")
  return pars

def get_one_par(pars,par,context_for_errors):
  capture = re.search("(.*)=(.*)",par)
  if capture:
    p,v = capture.group(1,2)
    if p in parameter_names():
      if p=='rho':
        die("Setting the rho parameters can only be done by editing the source code.")
      if p=='joint':
        capture = re.search("(.*),(.*)",v)
        j1,j2 = capture.group(1,2)
        pars['joint'] = (j1,j2)
      else:
        pars[p] = parameter_types()[p](v)
    else:
      die("illegal parameter "+str(p)+context_for_errors)
  else:
    die(f"syntax error in parameter: '{par}', {context_for_errors}")
  return pars

def parameter_names():
  return list(parameter_types().keys())

def parameter_types():
  f = lambda x:float(x)
  i = lambda x:int(x)
  s = lambda x:x # string
  b = i # boolean, treated as int
  t = s # tuple, requires some postprocessing
  return {'a':f,'k':f,'s':f,'dist':s,'n_trials':i,'joint':t,'rho':None,'swing':b,'tie':i}

def set_is_empty(s):
  return s == set()

def spread(l):
  # used in calculating the calibration coefficient c
  # Empirically, it doesn't matter much whether we use std dev or mean abs dev. Probably this is because we
  # truncate the tails of the list anyway before we calculate the spread, so extreme values can't influence the std dev much.
  #return statistics.stdev(l)
  return mean_abs_dev(l)

def mean_abs_dev(l):
  avg = statistics.mean(l)
  sum = 0
  for x in l:
    sum += abs(x-avg)
  return sum/len(l)

main()
