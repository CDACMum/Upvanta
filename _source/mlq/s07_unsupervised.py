from build import *
from mlq.anims import *
from mlq.runner import mlrun, pyshow
from mlq.data import STUDENTS, data_note

S = 'Python (scikit-learn) · uses sample data'
S2 = 'Python (scikit-learn) · built-in dataset'

FEEDBACK = """
import numpy as np, pandas as pd
rng = np.random.default_rng(7)
topics = {
    'lab':       ['lab machines are slow', 'hadoop cluster keeps crashing', 'wifi in the lab drops', 'need more RAM in lab systems',
                  'software not installed on lab PCs', 'lab closes too early', 'projector in lab 3 is broken', 'spark jobs fail on lab server'],
    'faculty':   ['the faculty explains statistics clearly', 'lectures are too fast', 'sir gives great real examples', 'need more doubt sessions',
                  'ma\\'am answers every question patiently', 'the python lectures are excellent', 'faculty should share notes before class', 'teaching of ML is very clear'],
    'placement': ['need more mock interviews', 'placement drive dates are not shared', 'resume review was helpful', 'more companies should visit',
                  'aptitude training for placement is useful', 'interview preparation sessions needed', 'placement cell replies late', 'campus drive was well organised'],
}
generic = ['the timetable changes often', 'good experience overall', 'weekend classes are tiring', 'the module was hard', 'the canteen is fine']
fill = ['', 'please', 'honestly', 'this week', 'again', 'overall', 'really']
rows = []
for label, phrases in topics.items():
    others = [p for t, ps in topics.items() if t != label for p in ps]
    for _ in range(40):
        a, b = rng.choice(phrases, 2, replace=False)
        r = rng.random()
        if r > 0.75:
            b = rng.choice(others)        # comment also mentions another topic
        elif r > 0.4:
            b = rng.choice(generic)       # comment adds a generic remark
        rows.append((f'{rng.choice(fill)} {a} and {b}'.strip(), label))
fb = pd.DataFrame(rows, columns=['comment', 'topic']).sample(frac=1, random_state=0).reset_index(drop=True)
"""
FB_NOTE = note('120 synthetic student feedback comments, 40 per topic (<code>lab</code>, <code>faculty</code>, <code>placement</code>). Each starts with '
               'a phrase typical of its topic and adds either another phrase from the same topic, a generic remark, or (one comment in four) a phrase '
               'from a different topic, so some comments are genuinely mixed.', 'Data')

SECTION = dict(level='advanced', title='Unsupervised Learning & Text', questions=[

# ------------------------------------------------------------------ 31
Q('How does K-Means clustering work? How do you choose k with the elbow method and silhouette score?', 'K-Means Clustering', minutes=9, cards=[
    definition(
        defbox('<strong>K-Means</strong> partitions rows into k clusters. It places k centroids, assigns every point to the nearest centroid, moves each centroid to '
               'the mean of its points, and repeats until assignments stop changing. It minimises <strong>inertia</strong> (the within-cluster sum of squared '
               'distances). <code>n_init</code> restarts with different seeds and keeps the best; <code>k-means++</code> initialisation spreads the starting '
               'centroids.',
               'Choosing k: the <strong>elbow method</strong> (inertia keeps falling as k grows; look for the bend) and the <strong>silhouette score</strong> '
               '(−1…1: how much closer each point is to its own cluster than to the next one; higher is better). K-Means uses distances, so '
               '<strong>scale features</strong>, and it assumes round, similar-sized clusters. Clusters must be <strong>interpreted</strong> by profiling them.'),
        tags('KMeans', 'centroid', 'inertia', 'elbow method', 'silhouette_score', 'k-means++'),
    ),
    analogy('Placing k <strong>bus stops</strong> in a town: start with rough spots, let every resident walk to the nearest stop, move each stop to the middle of '
            'its riders, and repeat until nobody switches stop.'),
    kmeans_anim(),
    real_world(
        scenario('Student segments for mentoring',
                 p('The centre clusters students on attendance, study hours and mock-test score. Profiling the clusters gives named segments such as "engaged high '
                   'performers" and "low attendance, low effort", each with its own mentoring plan. The placement label is not used to build the clusters, only '
                   'afterwards to check that the segments are meaningful.')),
    ),
    example(
        data_note(),
        mlrun("""
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            from sklearn.impute import SimpleImputer
            from sklearn.pipeline import make_pipeline
            from sklearn.metrics import silhouette_score

            cols = ['attendance', 'study_hours', 'mock_test']
            prep = make_pipeline(SimpleImputer(strategy='median'), StandardScaler())
            Z = prep.fit_transform(df[cols])

            print(' k   inertia   silhouette')
            for k in range(2, 8):
                km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(Z)
                print(f'{k:2}  {km.inertia_:8.1f}   {silhouette_score(Z, km.labels_):.3f}')

            km = KMeans(n_clusters=3, n_init=10, random_state=0).fit(Z)
            df['segment'] = km.labels_
            profile = df.groupby('segment').agg(students=('placed', 'size'), attendance=('attendance', 'mean'),
                                                study_hours=('study_hours', 'mean'), mock_test=('mock_test', 'mean'),
                                                placed_rate=('placed', 'mean')).round(2)
            print(profile.sort_values('mock_test'))
            new = pd.DataFrame([[95, 12, 85], [60, 4, 50]], columns=cols)
            print('new students -> segments', km.predict(prep.transform(new)))
        """, setup=STUDENTS, title=S),
        title='Example: Elbow + Silhouette, Then Profile the Segments'),
    steps(
        ('Pick the features', 'Behaviour you want to segment on; impute and scale them.'),
        ('Try a range of k', 'Record inertia and silhouette for k = 2…8.'),
        ('Choose k', 'Elbow + silhouette + whether the segments are usable by the business.'),
        ('Fit with n_init ≥ 10', 'random_state for reproducibility.'),
        ('Profile and name clusters', 'groupby on original units; check against outcomes you did not cluster on.'),
        title='Steps to Segment with K-Means'),
    crossq(
        ('In the example, silhouette is slightly higher for k=2 (0.307) than k=3 (0.303). Why choose 3?', 'The difference is tiny, the elbow bends around 3, and three segments map to three distinct mentoring plans. Metrics guide the choice; usefulness decides it.'),
        ('Why must features be scaled for K-Means?', 'It uses Euclidean distance; a feature measured in larger units (attendance 0–100) would dominate one in smaller units (study hours 0–15).'),
        ('Does K-Means always find the same clusters?', 'No; it can converge to a local minimum depending on the start. n_init runs it several times and keeps the lowest inertia.'),
        ('When does K-Means fail?', 'Non-spherical shapes (moons, rings), very different cluster sizes or densities, and outliers, which pull centroids. Use DBSCAN or Gaussian mixtures instead.'),
        ('How do you cluster categorical data?', 'One-hot encode carefully, or use K-Modes / K-Prototypes (separate library), or Gower distance with hierarchical clustering.'),
    ),
]),

# ------------------------------------------------------------------ 32
Q('Explain hierarchical clustering and DBSCAN. When are they better than K-Means?', 'Hierarchical Clustering & DBSCAN', minutes=8, cards=[
    definition(
        defbox('<strong>Agglomerative (hierarchical) clustering</strong> starts with every point as its own cluster and repeatedly merges the two closest clusters; '
               'the merge history is a <strong>dendrogram</strong> you can cut at any level. <strong>Linkage</strong> defines "closest": ward (minimise variance, '
               'default), complete, average, single (nearest points, can follow chains).',
               '<strong>DBSCAN</strong> groups points that have at least <code>min_samples</code> neighbours within radius <code>eps</code> (core points) and '
               'expands clusters through connected core points; points in sparse regions are labelled <strong>noise (−1)</strong>. It finds arbitrary shapes and '
               'does not need k, but eps must suit the data scale and it struggles with clusters of very different density (HDBSCAN helps).'),
        tags('AgglomerativeClustering', 'dendrogram', 'linkage', 'DBSCAN', 'eps', 'min_samples', 'noise'),
    ),
    analogy('Hierarchical clustering is a <strong>family tree</strong> built bottom-up: individuals, then siblings, then cousins. DBSCAN is finding '
            '<strong>crowds at a fair</strong>: people standing close together form a crowd however oddly shaped, and lone wanderers are nobody\'s crowd.'),
    density_anim(),
    real_world(
        scenario('Spotting odd groups and loners',
                 p('Clustering login locations or lab-usage patterns: DBSCAN finds dense, oddly shaped hot spots and marks isolated sessions as noise, which is '
                   'exactly what the IT team wants to review. A dendrogram of courses by syllabus similarity lets the academic team choose how many groups to merge.')),
    ),
    example(
        mlrun("""
            from sklearn.datasets import make_moons
            from sklearn.cluster import KMeans, AgglomerativeClustering, DBSCAN
            from sklearn.metrics import adjusted_rand_score
            from scipy.cluster.hierarchy import linkage, fcluster

            X, y = make_moons(n_samples=300, noise=0.06, random_state=0)
            models = {'KMeans k=2': KMeans(2, n_init=10, random_state=0),
                      'Agglomerative ward': AgglomerativeClustering(2, linkage='ward'),
                      'Agglomerative single': AgglomerativeClustering(2, linkage='single'),
                      'DBSCAN eps=0.2': DBSCAN(eps=0.2, min_samples=5)}
            print('agreement with the true moons (adjusted Rand index, 1 = perfect)')
            for name, m in models.items():
                lab = m.fit_predict(X)
                print(f'  {name:22} ARI {adjusted_rand_score(y, lab):.3f}   clusters {len(set(lab) - {-1})}  noise {(lab == -1).sum()}')

            for eps in [0.05, 0.1, 0.2, 0.5]:
                lab = DBSCAN(eps=eps, min_samples=5).fit_predict(X)
                print(f'eps {eps:4}: clusters {len(set(lab) - {-1})}, noise points {(lab == -1).sum()}')

            Zl = linkage(X[:12], method='ward')
            print('last 3 merges (cluster a, cluster b, distance, size):')
            print(Zl[-3:].round(2))
            print('cut into 2 groups:', fcluster(Zl, 2, criterion='maxclust'))
        """, title=S2),
        title='Example: Two Moons — K-Means vs Agglomerative vs DBSCAN'),
    steps(
        ('Scale the features', 'Both methods are distance-based.'),
        ('Hierarchical: choose linkage', 'Ward for compact groups; draw the dendrogram (scipy) to choose the cut.'),
        ('DBSCAN: choose min_samples', 'Rule of thumb ≈ 2 × number of features.'),
        ('DBSCAN: choose eps', 'Plot sorted k-nearest-neighbour distances and pick the knee.'),
        ('Inspect noise and clusters', 'Count label −1; profile each cluster.'),
        title='Steps to Use Hierarchical Clustering or DBSCAN'),
    crossq(
        ('Why can\'t K-Means separate the two moons?', 'It draws straight boundaries between centroids (Voronoi cells), so it cuts each moon in half. Density or single-linkage methods follow the shape.'),
        ('What does eps too small / too large do?', 'Too small: most points become noise or many tiny clusters. Too large: everything merges into one cluster.'),
        ('Does DBSCAN have predict()?', 'No; it only labels the data it was fitted on. To assign new points, train a classifier (e.g. KNN) on the clustered points.'),
        ('How does hierarchical clustering scale?', 'Roughly O(n²) memory and worse time, so it suits thousands of rows, not millions.'),
    ),
]),

# ------------------------------------------------------------------ 33
Q('What is PCA? How do you choose the number of components and when should you use it?', 'PCA (Dimensionality Reduction)', minutes=9, cards=[
    definition(
        defbox('<strong>Principal Component Analysis</strong> finds new axes (principal components) that are linear combinations of the original features, ordered '
               'by how much variance they capture, and mutually uncorrelated. Projecting onto the first few components keeps most of the information in fewer '
               'columns. <code>explained_variance_ratio_</code> gives each component\'s share; <code>components_</code> holds the loadings (weights).',
               'Uses: visualising high-dimensional data in 2-D, removing correlated/noisy features, speeding up models, compression. Always '
               '<strong>standardise</strong> first (PCA is variance-based). <code>PCA(n_components=0.95)</code> keeps enough components for 95 % of the variance. '
               'Costs: components are harder to interpret, and PCA is unsupervised, so it can discard directions that matter for the target.'),
        tags('PCA', 'explained_variance_ratio_', 'components_', 'dimensionality reduction', 'loadings', 't-SNE/UMAP'),
    ),
    analogy('PCA is <strong>choosing the best camera angle</strong> for a 3-D sculpture: from one angle the photo shows almost all the shape, from another it is a '
            'flat line. PCA finds the angles that show the most spread.'),
    pca_anim(),
    real_world(
        scenario('Visualising 13 lab measurements',
                 p('A food lab measures 13 chemical properties of wine samples. Projecting onto two principal components produces a scatter plot where the three '
                   'cultivars separate clearly, and a classifier on just 2 components loses very little accuracy compared with all 13.')),
    ),
    example(
        mlrun("""
            from sklearn.datasets import load_wine
            from sklearn.decomposition import PCA
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import make_pipeline
            from sklearn.linear_model import LogisticRegression
            from sklearn.model_selection import cross_val_score

            data = load_wine(as_frame=True)
            X, y = data.data, data.target
            print('shape', X.shape)

            pca = make_pipeline(StandardScaler(), PCA()).fit(X)
            ratio = pca[-1].explained_variance_ratio_
            print('variance share   ', ratio[:5].round(3))
            print('cumulative       ', ratio.cumsum()[:5].round(3))
            print('components for 90 %:', make_pipeline(StandardScaler(), PCA(0.90)).fit(X)[-1].n_components_)

            load = pd.Series(pca[-1].components_[0], index=X.columns)
            print('PC1 strongest loadings:')
            print(load.reindex(load.abs().sort_values(ascending=False).index)[:4].round(2))

            X2 = make_pipeline(StandardScaler(), PCA(2)).fit_transform(X)
            print(pd.DataFrame(X2, columns=['PC1', 'PC2']).groupby(y.values).mean().round(2))

            for n in [1, 2, 5, None]:
                steps = [StandardScaler()] + ([PCA(n)] if n else []) + [LogisticRegression(max_iter=1000)]
                acc = cross_val_score(make_pipeline(*steps), X, y, cv=5).mean()
                print(f'{"all 13 features" if n is None else f"PCA {n} components":17} CV accuracy {acc:.3f}')
        """, title=S2),
        title='Example: Explained Variance, Loadings and Accuracy with Fewer Components'),
    steps(
        ('Standardise', 'StandardScaler inside a pipeline.'),
        ('Fit PCA with all components', 'Look at explained_variance_ratio_ and its cumulative sum.'),
        ('Choose the count', '90–95 % variance, an elbow, or CV score of the downstream model.'),
        ('Interpret loadings', 'Which original features drive each component.'),
        ('Use in a pipeline', 'PCA fitted on training folds only.'),
        title='Steps to Apply PCA'),
    crossq(
        ('Is PCA feature selection?', 'No; it creates new features (combinations of all originals). Feature selection keeps a subset of the original columns.'),
        ('Why standardise before PCA?', 'PCA maximises variance; unscaled, the feature with the largest units (e.g. proline in hundreds) would dominate PC1.'),
        ('PCA vs t-SNE/UMAP?', 'PCA is linear, fast, deterministic and can transform new data. t-SNE/UMAP are non-linear, better for visualising clusters, but distances between clusters are not meaningful.'),
        ('Can PCA hurt a model?', 'Yes, if the low-variance directions it discards carry the signal for the target. Validate the downstream model with CV.'),
    ),
]),

# ------------------------------------------------------------------ 34
Q('How do you detect anomalies with Isolation Forest and Local Outlier Factor?', 'Anomaly Detection', minutes=8, cards=[
    definition(
        defbox('<strong>Isolation Forest</strong> builds random trees that split on random features at random thresholds. Anomalies are few and different, so they '
               'are <strong>isolated in fewer splits</strong> (short average path length). <code>decision_function</code> gives a score (lower = more abnormal); '
               '<code>predict</code> returns −1 for anomalies and 1 for normal points, based on <code>contamination</code> (the expected share of anomalies).',
               '<strong>Local Outlier Factor (LOF)</strong> compares a point\'s local density with that of its neighbours; much lower density means outlier. Other '
               'options: One-Class SVM, z-scores/IQR for single features, EllipticEnvelope for Gaussian data. Anomaly detection is mostly unsupervised, so results '
               'need review by someone who knows the domain.'),
        tags('IsolationForest', 'LocalOutlierFactor', 'contamination', 'decision_function', 'outliers'),
    ),
    analogy('Playing <strong>"Guess who?"</strong>: an ordinary person needs many questions to be singled out, but someone with a top hat, a parrot and a cape is '
            'identified in two questions. Isolation Forest counts the questions.'),
    isolation_anim(),
    real_world(
        scenario('Catching suspicious records',
                 p('The exam cell runs Isolation Forest on attendance, study hours and mock-test scores to flag records worth checking: a 98 in the mock test with '
                   '0 study hours and 30 % attendance may be a data-entry error or something to investigate. Flags go to a human, not to automatic action.')),
    ),
    example(
        data_note(),
        mlrun("""
            from sklearn.ensemble import IsolationForest
            from sklearn.neighbors import LocalOutlierFactor
            from sklearn.preprocessing import StandardScaler

            cols = ['attendance', 'study_hours', 'mock_test']
            odd = pd.DataFrame({'attendance': [31, 99, 45, 100, 28], 'study_hours': [0.0, 0.5, 14.5, 0.0, 13.0], 'mock_test': [98, 30, 99, 97, 25]})
            data = pd.concat([df[cols].dropna(), odd], ignore_index=True)
            is_odd = np.r_[np.zeros(len(data) - 5, bool), np.ones(5, bool)]
            Z = StandardScaler().fit_transform(data)

            iso = IsolationForest(n_estimators=300, contamination=0.02, random_state=0).fit(Z)
            flag = iso.predict(Z) == -1
            print(f'Isolation Forest flagged {flag.sum()} rows; injected oddities caught {flag[is_odd].sum()} of 5')
            data['score'] = iso.decision_function(Z).round(3)
            print(data.sort_values('score').head(8))

            lof = LocalOutlierFactor(n_neighbors=20, contamination=0.02)
            flag2 = lof.fit_predict(Z) == -1
            print(f'LOF flagged {flag2.sum()} rows; injected oddities caught {flag2[is_odd].sum()} of 5')
            print('both methods agree on', (flag & flag2).sum(), 'rows')
        """, setup=STUDENTS, title=S),
        title='Example: Find Five Planted Suspicious Records'),
    steps(
        ('Choose features where anomalies show', 'Scale them if using distance-based methods (LOF).'),
        ('Fit IsolationForest', 'Set contamination to the share you can review, or keep "auto" and use scores.'),
        ('Rank by decision_function', 'Review the lowest scores first.'),
        ('Cross-check with LOF', 'Rows flagged by both are stronger candidates.'),
        ('Close the loop', 'Record reviewers\' verdicts; with enough labels, train a supervised model.'),
        title='Steps to Detect Anomalies'),
    crossq(
        ('What does contamination do?', 'It only sets the threshold on the anomaly score so that roughly that share of training rows is flagged; it does not change the scores themselves.'),
        ('Anomaly detection vs imbalanced classification?', 'If you have labelled fraud cases, a supervised classifier usually wins. Anomaly detection is for when labels are missing or new kinds of anomalies appear.'),
        ('Why is a single-feature z-score not enough?', 'A record can look normal on each feature yet be odd in combination (high mock score with zero study hours). Multivariate methods catch that.'),
    ),
]),

# ------------------------------------------------------------------ 35
Q('How do you classify text with scikit-learn? Explain bag-of-words, TF-IDF and Naive Bayes.', 'Text Classification (TF-IDF)', minutes=9, cards=[
    definition(
        defbox('Models need numbers, so text is vectorised. <strong>Bag-of-words</strong> (<code>CountVectorizer</code>) counts how often each vocabulary word '
               'appears, ignoring order. <strong>TF-IDF</strong> (<code>TfidfVectorizer</code>) multiplies term frequency by inverse document frequency, so words '
               'that appear in every document ("the", "and") get low weight and distinctive words get high weight. Options: <code>ngram_range=(1, 2)</code>, '
               '<code>stop_words="english"</code>, <code>min_df</code>, <code>max_features</code>. The result is a sparse matrix.',
               '<strong>Multinomial Naive Bayes</strong> is a fast, strong baseline for word counts: it assumes words are independent given the class and '
               'multiplies per-class word probabilities. <strong>Linear models</strong> (LogisticRegression, LinearSVC) on TF-IDF are often a little more '
               'accurate. For meaning beyond words, use embeddings or transformer models (outside scikit-learn).'),
        tags('TfidfVectorizer', 'CountVectorizer', 'MultinomialNB', 'n-grams', 'sparse matrix', 'stop words'),
    ),
    analogy('TF-IDF is a <strong>highlighter</strong>: words every comment uses ("the", "and") barely get colour, while words that appear often in a few comments '
            '("hadoop", "interview") are highlighted, because they tell you what the comment is about.'),
    text_anim(),
    real_world(
        scenario('Routing student feedback',
                 p('Hundreds of feedback comments arrive after each module. A TF-IDF + Naive Bayes model routes each one to the lab team, the faculty coordinator or '
                   'the placement cell, and the most informative words per topic show each team what students talk about.')),
    ),
    example(
        FB_NOTE,
        mlrun("""
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import make_pipeline
            from sklearn.model_selection import cross_val_score

            print(fb.head(3).to_string(), '\\n')
            vec = TfidfVectorizer(stop_words='english')
            M = vec.fit_transform(fb['comment'])
            print('matrix', M.shape, f'non-zero {M.nnz} ({M.nnz / (M.shape[0] * M.shape[1]):.1%})')
            first = pd.Series(M[0].toarray()[0], index=vec.get_feature_names_out())
            print('TF-IDF weights of comment 0:', first[first > 0].round(2).sort_values(ascending=False).to_dict())

            for name, clf in [('Naive Bayes', MultinomialNB()), ('Logistic', LogisticRegression(max_iter=1000))]:
                pipe = make_pipeline(TfidfVectorizer(stop_words='english'), clf)
                print(f'{name:12} CV accuracy {cross_val_score(pipe, fb["comment"], fb["topic"], cv=5).mean():.3f}')

            nb = make_pipeline(TfidfVectorizer(stop_words='english'), MultinomialNB()).fit(fb['comment'], fb['topic'])
            new = ['the lab server crashed again', 'please arrange more mock interviews', 'statistics lectures were very clear', 'teacher was late to the lab']
            for text, label, p in zip(new, nb.predict(new), nb.predict_proba(new).max(1)):
                print(f'{text:38} -> {label:9} ({p:.2f})')

            words = nb[0].get_feature_names_out()
            for i, topic in enumerate(nb[-1].classes_):
                print(f'{topic:9} top words:', ', '.join(words[np.argsort(nb[-1].feature_log_prob_[i])[-5:][::-1]]))
        """, setup=FEEDBACK, title=S),
        title='Example: TF-IDF Matrix, Naive Bayes vs Logistic, Topic Words'),
    steps(
        ('Collect labelled text', 'Clean obvious noise; keep raw text in one column.'),
        ('Vectorise in a pipeline', 'TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2).'),
        ('Baseline with MultinomialNB', 'Then try LogisticRegression / LinearSVC.'),
        ('Evaluate with CV', 'Per-class precision/recall; read misclassified examples.'),
        ('Inspect informative words', 'Then deploy the pipeline (vectoriser + model) together.'),
        title='Steps to Build a Text Classifier'),
    crossq(
        ('Why fit the vectoriser only on training data?', 'The vocabulary and IDF weights are learned parameters; fitting them on test text leaks information. A pipeline handles this.'),
        ('What happens to words never seen in training?', 'They are ignored (no column exists for them). "teacher" above was unseen, so the prediction came from the other words.'),
        ('Why is it called "naive" Bayes?', 'It assumes every word is independent of the others given the class, which is false, yet the class ranking is often still right.'),
        ('When would you move beyond TF-IDF?', 'When meaning, word order or synonyms matter ("not good" vs "good"): use n-grams first, then sentence embeddings or fine-tuned transformers.'),
    ),
]),
])
