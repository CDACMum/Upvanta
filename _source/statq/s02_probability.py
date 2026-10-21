from build import *
from statq.anims import *
from statq.runner import strun, pyshow
from statq.data import STUDENTS, data_note

S = 'Python (pandas · NumPy) · uses sample data'
P = 'Python (NumPy · math)'

SECTION = dict(level='basic', title='Probability', questions=[

# ------------------------------------------------------------------ 6
Q('What are the basic rules of probability? Explain mutually exclusive and independent events.', 'Probability Rules', minutes=8, cards=[
    definition(
        defbox('Probability P(A) is a number between 0 and 1: the long-run share of trials in which event A happens. The <strong>complement</strong> rule: '
               'P(not A) = 1 − P(A). The <strong>addition rule</strong>: P(A or B) = P(A) + P(B) − P(A and B); for <strong>mutually exclusive</strong> events '
               '(cannot happen together) P(A and B) = 0.',
               '<strong>Independent</strong> events do not affect each other: P(A and B) = P(A) · P(B), equivalently P(A | B) = P(A). Mutually exclusive is '
               'not the same as independent: if A and B cannot occur together, knowing B happened tells you A did not, so they are strongly '
               '<strong>dependent</strong>.'),
        tags('sample space', 'complement', 'addition rule', 'multiplication rule', 'mutually exclusive', 'independent'),
    ),
    analogy('Drawing a card: "heart" and "spade" are <strong>mutually exclusive</strong> (one card cannot be both). "Heart" and "king" are '
            '<strong>independent</strong>: being a heart does not change the 1-in-13 chance of being a king.'),
    venn_anim(),
    real_world(
        scenario('Is placement independent of centre?',
                 p('If placement were independent of centre, P(placed and Pune) would equal P(placed) × P(Pune). Comparing the observed joint share with this '
                   'product is the intuition behind the chi-square test used later to decide whether a centre effect is real.')),
    ),
    example(
        data_note(),
        strun("""
            pl = df['placed'] == 1
            pune = df['centre'] == 'Pune'
            p_pl, p_pune, p_both = pl.mean(), pune.mean(), (pl & pune).mean()
            print(f'P(placed) = {p_pl:.3f}   P(Pune) = {p_pune:.3f}   P(placed and Pune) = {p_both:.3f}')
            print(f'P(not placed) = 1 - P(placed) = {1 - p_pl:.3f}')
            print(f'P(placed or Pune) = {p_pl:.3f} + {p_pune:.3f} - {p_both:.3f} = {p_pl + p_pune - p_both:.3f}  (direct count {(pl | pune).mean():.3f})')
            print(f'if independent: P(placed) x P(Pune) = {p_pl * p_pune:.3f}  vs observed {p_both:.3f}')

            # mutually exclusive events are dependent
            juhu = df['centre'] == 'Juhu'
            print(f'P(Pune and Juhu) = {(pune & juhu).mean()}  but P(Pune) x P(Juhu) = {p_pune * juhu.mean():.3f}')

            rng = np.random.default_rng(0)
            dice = rng.integers(1, 7, size=(100_000, 2))
            print(f'two dice, P(at least one six): simulated {(dice == 6).any(axis=1).mean():.4f}  exact 1 - (5/6)^2 = {1 - (5/6) ** 2:.4f}')
        """, setup=STUDENTS, title=S),
        title='Example: Rules Checked on Real Counts and a Simulation'),
    steps(
        ('Define the sample space and events', 'What is one trial? What counts as A and B?'),
        ('Estimate probabilities', 'Share of rows (boolean mask .mean()) or exact counting.'),
        ('Combine with the rules', 'Complement, addition (subtract the overlap), multiplication.'),
        ('Check independence', 'Compare P(A and B) with P(A)·P(B), or P(A|B) with P(A).'),
        ('Verify by simulation', 'NumPy random draws for anything non-trivial.'),
        title='Steps to Work With Probabilities'),
    crossq(
        ('Why subtract P(A and B) in the addition rule?', 'Outcomes in both A and B are counted once in P(A) and again in P(B); subtracting removes the double count.'),
        ('Can two events with non-zero probability be both independent and mutually exclusive?', 'No. Mutually exclusive means P(A and B) = 0, but independence requires P(A)·P(B) > 0.'),
        ('What is the "at least one" trick?', 'P(at least one) = 1 − P(none), which is usually far easier to compute.'),
        ('Does a small difference between P(A and B) and P(A)P(B) prove dependence?', 'No; sample data always differs a little. A chi-square test decides whether the difference exceeds chance.'),
    ),
]),

# ------------------------------------------------------------------ 7
Q('What is conditional probability? Explain Bayes\' theorem with an example.', 'Conditional Probability & Bayes', minutes=9, cards=[
    definition(
        defbox('<strong>Conditional probability</strong> P(A | B) = P(A and B) ÷ P(B): the probability of A <em>given</em> that B happened, i.e. within the '
               'rows where B is true. In general P(A | B) ≠ P(B | A).',
               '<strong>Bayes\' theorem</strong> reverses the condition: P(A | B) = P(B | A) · P(A) ÷ P(B), with P(B) = P(B | A)P(A) + P(B | not A)P(not A). '
               'P(A) is the <strong>prior</strong> (base rate), P(B | A) the <strong>likelihood</strong>, P(A | B) the <strong>posterior</strong>. Ignoring '
               'the base rate (the <strong>base-rate fallacy</strong>) is the classic mistake: a very accurate test for a rare condition still produces '
               'mostly false alarms.'),
        tags('conditional probability', 'Bayes theorem', 'prior', 'likelihood', 'posterior', 'base-rate fallacy'),
    ),
    analogy('A smoke alarm almost always rings during a fire, but it also rings when you burn toast. Since toast is burnt far more often than houses catch fire, '
            'a ringing alarm most likely means <strong>toast</strong>. Bayes\' theorem puts numbers on that intuition.'),
    bayes_anim(),
    real_world(
        scenario('Plagiarism checker in project evaluation',
                 p('A similarity tool flags 95 % of copied reports but also flags 4 % of honest ones, and about 3 % of reports are copied. Of the flagged reports, '
                   'less than half are actually copied, so a flag must trigger a manual review, never an automatic penalty.')),
    ),
    example(
        data_note(),
        strun("""
            ct = pd.crosstab(df['centre'], df['placed'], margins=True)
            print(ct)
            print('P(placed | centre):', pd.crosstab(df['centre'], df['placed'], normalize='index')[1].round(3).to_dict())
            print('P(centre | placed):', pd.crosstab(df['centre'], df['placed'], normalize='columns')[1].round(3).to_dict())

            # Bayes: plagiarism checker
            prior, sens, fpr = 0.03, 0.95, 0.04
            p_flag = sens * prior + fpr * (1 - prior)
            post = sens * prior / p_flag
            print(f'P(flag) = {p_flag:.4f}   P(copied | flag) = {post:.3f}')

            rng = np.random.default_rng(7)
            copied = rng.random(1_000_000) < prior
            flag = np.where(copied, rng.random(copied.size) < sens, rng.random(copied.size) < fpr)
            print(f'simulation: {flag.sum()} flagged, of which copied {copied[flag].mean():.3f}')
            print(f'second independent check also flags -> P(copied | 2 flags) = {sens**2 * prior / (sens**2 * prior + fpr**2 * (1 - prior)):.3f}')
        """, setup=STUDENTS, title=S),
        title='Example: Conditional Shares from a Crosstab, and Bayes for a Plagiarism Flag'),
    steps(
        ('Write down what is given', 'Prior P(A), likelihood P(B|A), false-positive rate P(B|not A).'),
        ('Compute the evidence', 'P(B) = P(B|A)P(A) + P(B|not A)P(not A).'),
        ('Apply Bayes', 'P(A|B) = P(B|A)P(A) / P(B).'),
        ('Sanity-check with counts', 'Imagine 10,000 cases (natural frequencies) or simulate.'),
        ('Update again with new evidence', 'Today\'s posterior becomes tomorrow\'s prior.'),
        title='Steps to Apply Bayes\' Theorem'),
    crossq(
        ('Why is P(placed | Pune) different from P(Pune | placed)?', 'They have different denominators: all Pune students vs all placed students. Confusing them is the "prosecutor\'s fallacy".'),
        ('How does a second independent test change the answer?', 'The posterior after the first flag becomes the prior for the second; two flags push the probability from about 0.42 to about 0.95 here.'),
        ('Where is Bayes used in data science?', 'Naive Bayes classifiers, spam filters, A/B testing (Bayesian), medical diagnosis, updating beliefs in Bayesian statistics.'),
    ),
]),

# ------------------------------------------------------------------ 8
Q('What is a random variable? How do you compute expected value and variance?', 'Random Variables & Expectation', minutes=8, cards=[
    definition(
        defbox('A <strong>random variable</strong> X assigns a number to each outcome of a random process. <strong>Discrete</strong> random variables have a '
               '<strong>probability mass function</strong> (P(X = x) for each value); <strong>continuous</strong> ones have a <strong>probability density '
               'function</strong>, where probabilities are areas under the curve.',
               '<strong>Expected value</strong> E[X] = Σ x · P(X = x): the long-run average. <strong>Variance</strong> Var(X) = E[(X − E[X])²] = E[X²] − E[X]². '
               'Rules: E[aX + b] = aE[X] + b, Var(aX + b) = a²Var(X), E[X + Y] = E[X] + E[Y] always, and Var(X + Y) = Var(X) + Var(Y) when X and Y are '
               'independent.'),
        tags('random variable', 'PMF', 'PDF', 'expected value', 'variance', 'linearity of expectation'),
    ),
    analogy('Expected value is the <strong>"average outcome if you could replay the situation thousands of times"</strong>. A lottery ticket has a huge possible '
            'prize, but its expected value is usually below its price; that is how lotteries stay in business.'),
    expect_anim(),
    real_world(
        scenario('Should students guess in a negative-marking exam?',
                 p('The C-CAT style rule awards +3 for a correct answer and −1 for a wrong one. With four options, a blind guess has an expected value of exactly zero, but '
                   'eliminating even one option makes it positive, which is exactly the advice mentors give before the entrance test.')),
    ),
    example(
        strun("""
            values = np.array([3, -1])                    # +3 correct, -1 wrong
            for options_left in [4, 3, 2]:
                p = np.array([1 / options_left, 1 - 1 / options_left])
                ev = (values * p).sum()
                var = ((values - ev) ** 2 * p).sum()
                print(f'{options_left} options left: E = {ev:+.3f} marks, SD = {np.sqrt(var):.3f}')

            rng = np.random.default_rng(3)
            guesses = np.where(rng.random((100_000, 20)) < 0.25, 3, -1)       # 20 blind guesses, 100,000 students
            total = guesses.sum(axis=1)
            print(f'20 blind guesses: simulated mean {total.mean():.2f} (theory {20 * 0:.2f}), SD {total.std():.2f} (theory {np.sqrt(20 * 3):.2f})')
            print(f'share of students who lose marks by guessing all 20: {(total < 0).mean():.3f}')

            die = np.arange(1, 7)
            e, e2 = die.mean(), (die ** 2).mean()
            print(f'fair die: E[X] = {e}, Var = E[X^2] - E[X]^2 = {e2:.3f} - {e ** 2} = {e2 - e ** 2:.3f}')
            print(f'sum of two dice: E = {2 * e}, Var = {2 * (e2 - e ** 2):.3f} (variances add for independent dice)')
        """, title=P),
        title='Example: Negative Marking — Expected Value of a Guess, Verified by Simulation'),
    steps(
        ('List the values and their probabilities', 'They must sum to 1.'),
        ('Expected value', 'Σ x·p (np.sum(values * p)).'),
        ('Variance and SD', 'Σ (x − E)²·p, then square root.'),
        ('Combine variables', 'Linearity of expectation; add variances only if independent.'),
        ('Check by simulation', 'Random draws and the sample mean/SD.'),
        title='Steps to Compute Expected Value and Variance'),
    crossq(
        ('With 4 options, +3/−1 gives E = 0. Is guessing pointless?', 'On average it neither gains nor loses, but it adds risk (SD ≈ 1.7 per question). Eliminating one option makes E positive (+0.33), so educated guesses pay.'),
        ('Is E[X·Y] = E[X]·E[Y]?', 'Only if X and Y are uncorrelated (e.g. independent); in general E[XY] = E[X]E[Y] + Cov(X, Y).'),
        ('Why can P(X = 70) be 0 for a continuous variable?', 'A single point has zero width, so zero area under the density; only intervals like P(69.5 < X < 70.5) have positive probability.'),
    ),
]),

# ------------------------------------------------------------------ 9
Q('How do permutations and combinations help count outcomes? Solve the birthday problem.', 'Counting: Permutations & Combinations', minutes=8, cards=[
    definition(
        defbox('<strong>Multiplication principle</strong>: k independent choices with n₁, n₂, … options give n₁·n₂·… outcomes. <strong>Permutations</strong> '
               '(order matters): choosing r of n in order = n! ÷ (n − r)!. <strong>Combinations</strong> (order does not matter): C(n, r) = n! ÷ (r!(n − r)!), '
               'i.e. permutations divided by the r! orderings of each group.',
               'With equally likely outcomes, probability = favourable ÷ total, so counting is often the whole problem. Python: <code>math.perm</code>, '
               '<code>math.comb</code>, <code>math.factorial</code>, and <code>itertools.permutations / combinations</code> to list the outcomes themselves.'),
        tags('factorial', 'permutation', 'combination', 'nPr', 'nCr', 'itertools', 'birthday problem'),
    ),
    analogy('Choosing a <strong>captain, vice-captain and wicket-keeper</strong> from 11 players is a permutation (roles differ). Choosing <strong>3 players to '
            'carry the drinks</strong> is a combination: the same three people in any order is the same group.'),
    counting_anim(),
    real_world(
        scenario('Project teams and duplicate birthdays',
                 p('The coordinator forms 3-member project teams from 10 shortlisted students (120 possible teams) and assigns a leader, coder and tester (720 '
                   'possible assignments). In a batch of 60 students, two people sharing a birthday is almost certain, a fun ice-breaker that surprises everyone.')),
    ),
    example(
        strun("""
            import math
            from itertools import combinations, permutations
            print('teams of 3 from 10 (order irrelevant):', math.comb(10, 3))
            print('leader, coder, tester from 10 (order matters):', math.perm(10, 3), '=', math.comb(10, 3), 'x 3! =', math.comb(10, 3) * math.factorial(3))
            print('first 4 teams of 3 from A-E:', [''.join(t) for t in combinations('ABCDE', 3)][:4])
            print('orderings of ABC:', [''.join(t) for t in permutations('ABC')])

            # probability by counting: 2 of the 10 shortlisted are from Pune; P(a random team of 3 has both)?
            print(f'P(team contains both Pune students) = C(8,1)/C(10,3) = {math.comb(8, 1) / math.comb(10, 3):.4f}')

            def p_shared(n):
                p_unique = 1.0
                for k in range(n):
                    p_unique *= (365 - k) / 365
                return 1 - p_unique
            for n in [10, 23, 40, 60]:
                print(f'{n} students: P(some shared birthday) = {p_shared(n):.3f}')
            rng = np.random.default_rng(5)
            bdays = rng.integers(0, 365, size=(20_000, 60))
            shared = np.array([len(set(row)) < 60 for row in bdays]).mean()
            print(f'simulated for 60 students: {shared:.3f}')
        """, title=P),
        title='Example: Teams, Roles and the Birthday Problem (Exact and Simulated)'),
    steps(
        ('Decide whether order matters', 'Roles/positions → permutation; groups → combination.'),
        ('Decide whether repetition is allowed', 'n^r with repetition (PINs), nPr / nCr without.'),
        ('Count favourable and total outcomes', 'For equally likely outcomes.'),
        ('Use complements', '"At least one" = 1 − "none" (birthday problem).'),
        ('Verify', 'itertools for small cases, simulation for big ones.'),
        title='Steps to Solve Counting Problems'),
    crossq(
        ('Why is the birthday probability so high?', 'It is about any pair sharing, not someone sharing your birthday. 60 students form C(60, 2) = 1,770 pairs.'),
        ('How many 4-digit PINs exist, and how many with all digits different?', '10⁴ = 10,000 with repetition; 10·9·8·7 = 5,040 without (a permutation).'),
        ('Relationship between nPr and nCr?', 'nPr = nCr · r!, because each group of r can be ordered in r! ways.'),
    ),
]),

# ------------------------------------------------------------------ 10
Q('What is the law of large numbers? How does Monte Carlo simulation estimate probabilities?', 'Law of Large Numbers & Simulation', minutes=8, cards=[
    definition(
        defbox('The <strong>law of large numbers</strong> (LLN): as the number of independent trials grows, the sample average converges to the expected value '
               '(and an observed proportion to the true probability). It says nothing about short runs: after five heads, the next toss is still 50/50 '
               '(the <strong>gambler\'s fallacy</strong>).',
               '<strong>Monte Carlo simulation</strong> uses this: generate many random scenarios with a random number generator, compute the quantity of '
               'interest each time, and average. The error shrinks like 1/√n, so 100× more simulations give 10× more precision. Fix the seed '
               '(<code>np.random.default_rng(seed)</code>) for reproducible results.'),
        tags('law of large numbers', 'Monte Carlo', 'simulation', 'random seed', 'gambler\'s fallacy', '1/√n'),
    ),
    analogy('Toss a coin 10 times and you might get 7 heads; toss it 10,000 times and you will be very close to half. <strong>Noise averages out</strong>, '
            'which is why insurers can predict total claims while no single policyholder is predictable.'),
    lln_anim(),
    real_world(
        scenario('Will the lab have enough machines?',
                 p('Each of 80 students independently attends an optional lab session with probability 0.6. Simulating 100,000 days estimates how often more than '
                   '55 turn up, which tells the centre whether 55 machines are enough, without any formula.')),
    ),
    example(
        strun("""
            rng = np.random.default_rng(42)
            rolls = rng.integers(1, 7, size=100_000)
            running = rolls.cumsum() / np.arange(1, rolls.size + 1)
            for n in [10, 100, 1_000, 10_000, 100_000]:
                print(f'after {n:>7,} rolls: average {running[n - 1]:.4f}   error {abs(running[n - 1] - 3.5):.4f}')

            # Monte Carlo: lab attendance
            days = rng.binomial(n=80, p=0.6, size=100_000)
            print(f'P(more than 55 students) ~ {(days > 55).mean():.4f}   mean attendance {days.mean():.2f}')
            from scipy import stats
            print(f'exact binomial answer: {stats.binom.sf(55, 80, 0.6):.4f}')

            # estimating pi: error falls like 1/sqrt(n)
            for n in [1_000, 100_000, 10_000_000]:
                xy = rng.random((n, 2))
                est = 4 * ((xy ** 2).sum(axis=1) <= 1).mean()
                print(f'n = {n:>10,}: pi ~ {est:.5f}  error {abs(est - np.pi):.5f}')
        """, title=P),
        title='Example: Running Average of Dice, Lab Capacity, Estimating π'),
    steps(
        ('Model one trial', 'Which random inputs, with which distributions?'),
        ('Vectorise many trials', 'NumPy generators produce millions of draws at once.'),
        ('Compute the statistic per trial', 'Then average (or take the share of successes).'),
        ('Check convergence', 'Increase n until the answer stabilises; report the uncertainty.'),
        ('Fix the seed', 'For reproducible reports.'),
        title='Steps for a Monte Carlo Simulation'),
    crossq(
        ('After 5 heads in a row, is tails "due"?', 'No. Independent tosses have no memory; the LLN works by swamping early deviations with many new tosses, not by correcting them.'),
        ('Why does the error shrink only like 1/√n?', 'The standard error of a mean is σ/√n; halving the error needs four times as many simulations.'),
        ('In the example the error after 10,000 rolls (0.025) was larger than after 1,000 (0.012). Does that break the law?', 'No. The LLN describes the trend: the error shrinks on average, but any single run wanders. By 100,000 rolls it was 0.0002.'),
        ('When is simulation better than a formula?', 'When the system is complex (many interacting random parts, business rules) or no closed-form answer exists; also to check formulas.'),
    ),
]),
])
