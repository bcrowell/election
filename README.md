election
========

A very simple python 3 program that simulates a US presidential election and
estimates probabilities. It can be used to estimate conditional or joint probabilities,
such as the probability that Trump wins the presidential election while losing in
Pennsylvania.

Output
======
The main output is a summary of the adjustable parameters followed by
a predicted probability for the D candidate to win.

Here are some lines from the state-by-state portion of a real run:

               predictit   sim   polls     RCL
    in   -4.0      0.15    0.25   -11.5    0.09
    mt   -4.0      0.18    0.25   -9.3    0.11

Four of these columns are just a recap of inputs from data.csv.
The "sim" column shows the probability from the simulation that
this state will go democratic. The RCL column gives the probability
that the R candidate will will the election, conditioned on the hypothesis
that he loses this state.

Data file and sources of data
=============================

Per-state data are in the file data.csv.

electoral votes
---------------

This is for 2010-2020.

lean
----

Semi-quantitative rankings of how much each state leans toward one party or another.
Positive = democratic.

2020 jul 15, http://insideelections.com/ratings/president

I added half-unit tweaks in cases where these expert opinions didn't seem consistent with polls and predictit.
In addition to these per-state tweaks, all values have the parameter k added to them later.

predictit_prob
--------------

Probability that democrats win the state according to
predictit, 2020 jul 15.
Not used in calculations, only in output, to help me adjust parameters.

poll
----

Polling advantage for democrats, 2020 jul 16, fivethirtyeight.com.
Used for two purposes: (1) used automatically to normalize the c parameter;
(2) helps me to decide on small tweaks to lean[].

adjustable parameters
=====================

The main parameters that it makes sense to fiddle with are A, k, s, and dist.

A = mean absolute error of popular-vote shift between now and election day

k = offset to lean[] values; setting this to a positive value means I don't believe experts who are saying election is close

s = a fudge factor for variability of state votes, see below

dist = 'normal' or 'cauchy', controls what probability distribution is used for random fluctuations

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
