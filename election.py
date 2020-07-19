#!/bin/python3

import math,random,statistics,sys,csv,re

def parameters():
  '''
  Set adjustable parameters. The main parameters that it makes sense to fiddle with are A, k, s, and dist.
  See README for how to decide on these values.
  The defaults below can be overridden from the command line, e.g., election.py a=10.
  Fixme: Defaults should be read from a data file.
  '''
  a = 4.5 # 9.0 # see above for how this should go down over time
  k = 0.5 # see above
  s = 2.0 # see above
  dist = 'cauchy' # can be cauchy or normal

  # correlations among states, see https://projects.economist.com/us-2020-forecast/president/how-this-works
  rho1 = 0.75 # northeastern swing states, i.e., all but NV and FL
  rho2 = 0.5 # florida
  rho3 = 0.25 # nevada

  n_trials = 10000

  pars = {'a':a,'k':k,'s':s,'dist':dist,'rho':(rho1,rho2,rho3),'n_trials':n_trials,'joint':('','')}
  pars = get_command_line_pars(pars) # override defaults

  return pars

def main():

  pars = parameters()
  (a,k,s,dist,rho,n_trials,joint) = (pars['a'],pars['k'],pars['s'],pars['dist'],pars['rho'],pars['n_trials'],pars['joint'])
  (rho1,rho2,rho3) = rho

  sd = state_data()
  (electoral_votes,lean,predictit_prob,poll,safe_d,safe_r,tot,states) = (sd['electoral_votes'],sd['lean'],sd['predictit_prob'],sd['poll'],
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
  for state in electoral_votes:
    state_d_wins[state] = 0
    rcl[state] = 0
  joint_table = [[0,0],[0,0]]
  for i in range(n_trials):
    t = do_one_trial({'safe_d':safe_d,'safe_r':safe_r,'aa':aa,'k':k,'s':s,'dist':dist,'tot':tot,'c':c,
                 'ind':ind,'electoral_votes':electoral_votes,'lean':lean})
    d_wins += t['d_win']
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
         {'d_prob':d_prob,'prob':prob,'rcl':rcl,'joint_table':joint_table},
         {'electoral_votes':electoral_votes,'lean':lean,'predictit_prob':predictit_prob,'poll':poll,
            'safe_d':safe_d,'safe_r':safe_r,'tot':tot,'states':states}
        )

def output(pars,results,sd):
  (a,k,s,dist,n_trials,joint) = (pars['a'],pars['k'],pars['s'],pars['dist'],pars['n_trials'],pars['joint'])
  (d_prob,prob,rcl,joint_table) = (results['d_prob'],results['prob'],results['rcl'],results['joint_table'])
  (electoral_votes,lean,predictit_prob,poll,safe_d,safe_r,tot,states) = (sd['electoral_votes'],sd['lean'],sd['predictit_prob'],sd['poll'],
            sd['safe_d'],sd['safe_r'],sd['tot'],sd['states'])

  print("A=",f1(a),", k=",f1(k),", s=",f1(s),", dist=",dist)
  if dist=='cauchy':
    print("Note: Since dist is Cauchy, which has fat tails, probabilities for safe states are less extreme. This is intentional.")
  predictit_mean = statistics.mean(list(predictit_prob.values()))
  prob_mean = statistics.mean(list(prob.values()))
  #print("mean(simulation)-mean(predictit)=",f2(prob_mean-predictit_mean),"; if predictit data are current, this can be used to adjust the parameter k")
  #...to be useful, this feature should restrict itself to real swing states

  print("prob of D win=",d_prob)
  print("           predictit   sim   polls     RCL")
  for state in states:
    print(state," ",f1(lean[state]),"   ",f2(predictit_prob[state])," ",f2(prob[state])," ",f1(poll[state])," ",f2(rcl[state]))

  if joint[0]!='':
    print("joint probabilities:")
    for i in range(2):
      for j in range(2):
        joint_table[i][j] *= 1.0/n_trials
    print("            D in ",joint[1])
    print("            lose     win")
    for i in range(2):
      print("  lose ",joint[0],f2(joint_table[i][0])," ",f2(joint_table[i][1]))
        

def do_one_trial(dat):
  (safe_d,safe_r,aa,k,s,dist,tot,c,ind,electoral_votes,lean) = (dat['safe_d'],dat['safe_r'],
              dat['aa'],dat['k'],dat['s'],dat['dist'],dat['tot'],dat['c'],
              dat['ind'],dat['electoral_votes'],dat['lean'])
  d = safe_d
  pop = aa*bell_curve(dist)
  x = {}
  t = {}
  t['state_d_win'] = {}
  for state, v in electoral_votes.items():
    x[state] = pop+ind[state]*bell_curve(dist)+c*(lean[state]+k)
    if x[state]>0.0:
      d = d+v
      t['state_d_win'][state] = 1
    else:
      t['state_d_win'][state] = 0
  if d>tot*0.5:
    # fixme: handle the case of a tie in the electoral college
    t['d_win'] = 1
  else:
    t['d_win'] = 0
  t['vote'] = x
  return t

def calibrate_lean_to_percent(poll,lean):
  # Calculate a measure of the spread in the lean[] values and the poll[] values, to allow the normalization parameter
  # c to be calculated. I.e., how many % points is one unit of "lean?"
  swing_poll_list = []
  swing_lean_list = []
  for state in poll:
    if abs(lean[state])<4: # Don't count states with huge lean values, not real swing states, because those values aren't carefully calibrated.
      swing_poll_list.append(poll[state])
      swing_lean_list.append(lean[state])
  poll_sd = statistics.stdev(swing_poll_list)
  lean_sd = statistics.stdev(swing_lean_list)

  # calibration of "lean" data to give % units
  c = poll_sd/lean_sd
  return c

def state_data():
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

  # list of states, sorted in order by probability on predictit
  states = list(electoral_votes.keys())
  states.sort(key=lambda s:predictit_prob[s])

  # Safe states are those that don't occur in the data file.
  safe_d =  68 # includes 3 electoral votes from maine
  safe_r = 113 # includes 1 electoral vote from maine

  # Check that the total number of electoral votes is what it should be. This value doesn't change when there's a census, because
  # it's capped by statute at this value: https://en.wikipedia.org/wiki/United_States_congressional_apportionment
  tot = safe_d + safe_r
  for state, v in electoral_votes.items():
    tot = tot+v
  if tot!=538:
    die("tot does not equal 538")

  return {'electoral_votes':electoral_votes,'lean':lean,'predictit_prob':predictit_prob,'poll':poll,
            'safe_d':safe_d,'safe_r':safe_r,'tot':tot,'states':states}

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
  if x is None:
    return "----"
  else:
    return ("%4.1f") % x

def f2(x):
  if x is None:
    return "-----"
  else:
    return ("%5.2f") % x

def get_command_line_pars(pars):
  for par in sys.argv[1:]:
    capture = re.search("(.*)=(.*)",par)
    if capture:
      p,v = capture.group(1,2)
      if p in pars:
        if p=='dist': # strings
          pars[p] = v
        else:
          if p=='n_trials':
            pars[p] = int(v)
          else:
            if p=='joint':
              capture = re.search("(.*),(.*)",v)
              j1,j2 = capture.group(1,2)
              pars['joint'] = (j1,j2)
            else:
              pars[p] = float(v)
      else:
        die("illegal parameter")
    else:
      die("syntax error in parameter")
  return pars

main()
