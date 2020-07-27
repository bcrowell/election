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

The model is not useful for predicting the popular vote. It doesn't even have data on
all the states --- small solid-red states are all lumped together, as are
small solid-blue states.

If you just want to see the model's current predictions without having
to get the code running on your own machine, go to
[this page](https://github.com/bcrowell/election/blob/master/current_results.txt).

Another amateur who has done this sort of thing is University of Alabama
student  [Jack Kersting](https://projects.jhkforecasts.com/presidential-forecast/forecast_methodology).

design goals
============

 * Make a tool that does one thing and does it well.
 * Make the simplest possible model that has any hope of doing anything reasonable.
 * Make a model that has almost no ad hoc rules and whose parameters can be estimated reliably using real-world data.

How the model works
===================

Each state has a "lean" value L, based on the consensus of several experts (Cook, insideelections, and Sabato). L=0 means
a toss-up, L>0 is favorable to the democrats. For example, a state that leans slightly to the democrats would
have L=+1, while a reasonably safe republican state like Montana is -2. These values are multiplied by a factor
that is automatically calculated so that for swing states, the standard deviation of the L values is the same
as the standard deviation of the polling results. For example, in July of 2020, this scaling factor comes out
to be 3.0, meaning that if a state has L=+1, the democratic candidate is expected to win by 3 points.
These could also have just been taken directly from polling, but I decided to put more emphasis on
experts' opinions. In July 2020, these expert opinions seem to predict that a lot of states will behave
more according to their partisan voting index than indicated by current polls, i.e.,they are expecting
a regression toward historical behavior between now and the election.

The election is run n times in a Monte Carlo simulation, with some randomness thrown in on top of each state's
expected margin. This randomness accounts for
both polling error and the fact that things
can happen between now and election day, e.g., a war or an epidemic.

For each run, a single random number is
generated from a bell-shaped distribution with
width A, and this is added onto every state's estimated margin.

In addition, every state gets its own random number added on, using the same type of
bell curve but with width B_i for the ith state. The widths B_i are not set
by the user but are instead cooked up using a method described below in the
section titled "How per-state variability is set."

The result for a particular state depends on whether the sum described above is positive (goes democratic)
or negative (republican). The state's electoral votes are counted, and the result of the election
is determined for that particular run.

By default, the bell curve used to generate these numbers is sampled
from a probability distribution called a Cauchy distribution, which
has fatter tails than a normal (Gaussian) curve, allowing for a higher
probability of "black swan" or "perfect storm" events. If the Cauchy is too spicy for your taste,
you can select the normal curve instead. The units
of the A and B_i variables should basically be interpreted as mean
absolute errors, but for those who care about mathematical details,
see the section below titled "Details about the bell curves."

Not all states are included in the simulation. Small states that are solid red or blue are
simply counted as safe electoral votes. This is mainly because there is
often no polling data for such states.

Output
======
The main output is a recap of the adjustable parameters followed by
a predicted probability for the D candidate to win.

After this is some state-by-state data, which by default is restricted only
to a short list of swing states (a shorter list than even the list that the
code considers non-safe). Here are the first few lines of a run:

                 lean       predictit  sim       polls  sim      HIQR        RCL
    AK            -1.0        0.25    0.40       -2.0    -3.1    4.65       0.07
    TX            -1.0        0.37    0.40       -0.1    -3.1    4.65       0.03
    ME-02          0.0        0.42    0.50        3.0     0.1    4.65       0.08

Four of these columns are just a recap of inputs from data.csv.
The first numerical column is the L rating for
which way the state leans.

The next two columns are the probability for D to win based on predictit
and based on the simulation.

The next three columns are the real polling data, mean election-day voting
data from the simulation, and a measure of the width of the bell curve being used to
simulate this state's uncorrelated uncertainty (in addition to the nationwide,
correlated uncertainty controlled by A). The width is described using half the
inter-quartile range (HIQR), e.g., if the HIQR is 4%, then there's a 50% chance
that the result will lie within the +-4% range.

The RCL column gives the probability
that the R candidate will win the election, conditioned on the hypothesis
that he loses this state.

A histogram of probabilities of various electoral college results is printed
to the file histogram.txt.

Running the program
===================
On MacOS or Linux, open a terminal windows and type `python3 election.py` to run the
program with the default parameters. The parameters are described below. The most
important ones are A and the choice of a distribution. As an example where you change
these parameters from their default values, you could do `python3 election.py a=3 dist=normal`.

To run the program on Windows, the process should be similar, but you'll have to install
Python first.

Tables of joint probabilities
=============================
To see a table of joint probabilities for two states, do something like
`election.py joint=pa,wi`. To use the national result in place of one of
the states, do, e.g., `election.py joint=pa,nat`.

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
Positive = democratic. These are based on the following three sets of ratings by experts:

http://insideelections.com/ratings/president

http://crystalball.centerforpolitics.org/crystalball/2020-president/

https://cookpolitical.com/

The final three columns of the spreadsheet are date-stamped compilations of these three
sets of ratings. These columns are not actually used by the program. They're there to make
it easier for me to evaluate and update the "lean" column, which is actually used.

The normalization of the "lean" column is chosen to be similar to the normalization of the
insideelections.com ratings.
All of these values have the parameter k added to them later. I also made up
values like +5 and -6 for states that experts simply describe as safe; these were cooked up in
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

A = mean absolute error of popular-vote shift between now and election day, in percentage points

k = offset to lean[] values; setting this to a positive value favors D candidate, means I don't believe experts who are saying the 2020 election is close

s = a fudge factor for variability of state votes, see below

dist = 'normal' or 'cauchy', controls what probability distribution is used for random fluctuations

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

For the last 6 elections (1996-2016), the errors have not shown much of a trend over time for the year leading up
to the election.
The absolute error in these elections tended to sit at about 5% for the whole year, and then maybe dip down to about 3% only for
the final month or two. It's unclear to me whether elections have really gotten more preditable since the 1990's or
whether it's just a coincidence that the last 6 elections all behaved this way.

https://www.thecrosstab.com/2017/01/03/history-polling-error-us-uk/

https://politics.stackexchange.com/questions/54680/historical-data-on-how-the-reliability-of-polling-data-depends-on-time-remaining

So reasonable estimates for A, which measures national vote uncertainty, are: July 7%, November 2.5%.

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

other parameters
================
If swing=1 (the default), then states are only shown if they are real swing states (probability on predictit between 0.2-0.8).
Set swing=0 to see all states that are in the model.

If tie=-1 (the default), then a tie in the electoral college goes to the republicans, who control a majority of state delegations in the house.
In the unlikely event that this ever changes, set tie=1 in defaults.txt.
The tie is settled by a vote of state delegations in the house, using the newly elected congress. If a state
delegation deadlocks, it sits out that round of voting.
[Analysis](http://centerforpolitics.org/crystalball/articles/republican-edge-in-electoral-college-tie-endures/).


How per-state variability is set
================================
The parameters B_i are cooked up based on 
[some data I found](https://projects.economist.com/us-2020-forecast/president/how-this-works)
about correlations between vote totals in various swing states. Basically most of the swing states are
in the north, and are more highly correlated, but NV and FL have a lower correlation.
Therefore those two states are special-cased.
The sizes of the B_i are set by first taking them to be the sizes that would give
the historically observed correlations (0.75), and then scaled up by a user-controlled factor s.
The default is s=2, which is meant to take into account the fact that state polls are
often rather unreliable compared to national polls.

Details about the bell curves
=============================
The A and B_i numbers describe the width of a bell curve according to a specific
definition. If the distribution is normal, then A is defined as the mean absolute value (which is
how pollsters report error) rather than the standard deviation.
If the distribution is
Cauchy, then the bell curve that is used is the one that has the same inter-quartile range
as the corresponding normal curve.

The results of the simulation are mainly sensitive to
the behavior of swing states, but some large solid-red or solid-blue states are included
as well, and when the Cauchy distribution is used, this sometimes leads to logically
impossible outcomes in which one candidate beats the other by more than 100%. The simulation
actually only cares who wins, not by how much (and it isn't designed to predict the popular
vote reliably), but to handle this in a consistent way, all simulated vote margins
(whether simulated using normal or Cauchy) are passed through the function
y=N*atan(x/N), where N=200/pi. Because x is normally pretty small, this seldom changes
things very much, e.g., a 5% margin changes to 4.99%.

As an intellectual/mathematical curiosity, this method, when used with
the Cauchy distribution, can result in a finite (but realistically
very small) probability for |y|=100. (To see this, note that a Cauchy
random variable can be generated by taking the rangent of a uniform
variable.) I think that actually makes sense, e.g., it is logically
possible (but very unlikely) for the U.S. to become a fascist
dictatorship and have 100% of votes go to the dictator in a fake
plebiscite.
