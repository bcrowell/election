election
========

A very simple python 3 program that simulates a US presidential election and
estimates probabilities. It can be used to estimate conditional or joint probabilities,
such as the probability that Trump wins the presidential election while losing in
Pennsylvania.


Sources of data

electoral votes
This is for 2010-2020.

lean

Semi-quantitative rankings of how much each state leans toward one party or another.
Positive = democratic.
2020 jul 15, http://insideelections.com/ratings/president
I added half-unit tweaks in cases where these expert opinions didn't seem consistent with polls and predictit.
In addition to these per-state tweaks, all values have the parameter k added to them later.

predictit_prob

  Probability that democrats win the state according to
  predictit, 2020 jul 15.
  Not used in calculations, only in output, to help me adjust parameters.

poll

  Polling advantage for democrats, 2020 jul 16, fivethirtyeight.com.
  Used for two purposes: (1) used automatically to normalize the c parameter;
  (2) helps me to decide on lean_tweaks[].

