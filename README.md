election
========

This is very simple program that simulates a US presidential election
and estimates various probabilities. The reason I wrote it is that,
although professionals publish the results of much fancier models, I
wanted to be able to estimate probabilities of more specialized things
like the probability that Trump would win the presidential election
while losing in Pennsylvania.

The design of the model makes it useful in checking whether opinion A
is consistent with opinion B. For example, on the prediction market
predictit, people are currently (July 2020) saying that Biden has a 62% chance
of winning the election, and a 76% chance of winning Pennsylvania.
The model helps me confirm my hunch that one or the other of these
opinions has to be wrong. I can adjust the amount of randomness in the
model to reproduce one of these numbers, but not both at the same time.

The model is not useful for predicting the popular vote (its expectation
value or its probability distribution). It doesn't even have data on
all the states --- small solid-red states are all lumped together, as are
small solid-blue states.

How the model works
===================

Each state has a "lean" value, usually originating from insideelections.com. Zero means
a toss-up, positive values mean it leans D. For convenience, these are multiplied by a factor to get
them in the same % units as polling results. The result is a currently estimated margin for the democrats.
(These could also have just been taken directly from polling, but I decided to put more emphasis on
experts' opinions.)

The simulation is run n times. Each time, a single random number is
generated from a bell-shaped distribution (normal or Cauchy) with
width A, and this is added onto every state's estimated margin. In
addition, every state gets its own random number added on. All these
random numbers represent both polling error and the fact that things
can happen between now and election day, e.g., a war or an epidemic.
The parameter A should be reduced as we get closer to election day;
see below.

Florida and Nevada have more individual randomness than the other swing states, as suggested
by some data I found online showing them to be not as strongly correlated with
the other swing states, which are mostly in the northeast.

The result for a particular state depends on whether the sum described above is positive (goes democratic)
or negative (republican). The state's electoral votes are counted, and the result of the election
is determined for that particular election.

Output
======
The main output is a summary of the adjustable parameters followed by
a predicted probability for the D candidate to win.

After this is some state-by-state data. Here are the first few lines of a run:

               predictit   sim   polls     RCL
    in   -4.0      0.15    0.25   -11.5    0.09
    mt   -4.0      0.18    0.25   -9.3    0.11

Four of these columns are just a recap of inputs from data.csv.
The "sim" column shows the probability from the simulation that
this state will go democratic. The RCL column gives the probability
that the R candidate will win the election, conditioned on the hypothesis
that he loses this state.

Running the program
===================
On MacOS or Linux, open a terminal windows and type `python3 election.py` to run the
program with the default parameters. The parameters are described below. The most
important ones are A and the choice of a distribution. As an example where you change
these parameters from their default values, you could do `python3 election.py a=3 dist=normal`.

To run the program on Windows, the process should be similar, but you'll have to install
Python first.

Data file and sources of data
=============================

Per-state data are in the file data.csv. States that don't appear in the file are
considered totally safe for one party, and are accounted for in the variables
safe_d and safe_r in the code. If putting a state in or taking one out, these
two variables need to be adjusted, or an error will result because the code detects
that the total number of electoral votes is wrong. Maine is counted as two separate
safe states, a safe D state with 3 electoral votes and a safe R state with 1.

electoral votes
---------------

This is for 2010-2020.

lean
----

Semi-quantitative rankings of how much each state leans toward one party or another.
Positive = democratic.

2020 jul 15, http://insideelections.com/ratings/president

I added half-unit tweaks in cases where these expert opinions didn't seem consistent with polls and predictit.
In addition to these per-state tweaks, all values have the parameter k added to them later. I also made up
values like +5 and -6 for states that insideelections simply describes as safe; these were cooked up in
order to get rough agreement with predictit.

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

k = offset to lean[] values; setting this to a positive value favors D candidate, means I don't believe experts who are saying the 2020 election is close

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

The rho values I'm using are correlations of state A with state B. I want mine to be state with national, but that should be about the same.
However, if I just take the per-state variation to be what would mathematically reproduce these rho values, then
the per-state variation only turns out to contribute about half the variance. This is too small, since state polling
generally has about twice the error of national polling, and therefore we want per-state variation to be about twice
as big as we would get from the rho values. This is the reason for including the fudge factor s and setting it to
about 2. The effect of making s>1 can counterintuitively be to make the underdog less likely to win. The reason for this is
is that (1) that variability doesn't help them much, because the underdog needs big correlated change, not uncorrelated change;
and (2) the model counts some states as safe, so in the limit as s->infty whoever has more safe electoral votes has the higher
probability of winning.
