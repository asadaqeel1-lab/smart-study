from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.decomposition import TruncatedSVD
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import sqlite3, os, pickle, warnings, json, re
from datetime import datetime

warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
CSV_PATH  = os.path.join(BASE_DIR, "final_dataset_fixed.csv")
DB_PATH   = os.path.join(BASE_DIR, "study_recommender.db")
MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

# ─── Load & clean dataset ────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)
df["title"]   = df["title"].fillna("").astype(str).str.strip()
df["level"]   = df["level"].fillna("All Levels").astype(str).str.strip()
df["topic"]   = df["topic"].fillna("").astype(str).str.strip()
df["subject"] = df["subject"].fillna("").astype(str).str.strip()
df["type"]    = df["type"].fillna("Course").astype(str).str.strip()
df["link"]    = df["link"].fillna("").astype(str).str.strip()
df["content"] = df["title"] + " " + df["topic"] + " " + df["subject"] + " " + df["level"]
print(f"[INFO] Dataset: {len(df)} rows")

# ─── TF-IDF vectorizer ───────────────────────────────────────────────────────
vectorizer   = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=20000)
tfidf_matrix = vectorizer.fit_transform(df["content"])

# ─── Database ────────────────────────────────────────────────────────────────
def get_conn(): return sqlite3.connect(DB_PATH)

def normalize_search_value(value, fallback=""):
    text = " ".join(str(value or "").strip().split())
    return text or fallback

def migrate_search_logs(conn):
    cols = {row[1] for row in conn.execute("PRAGMA table_info(search_logs)").fetchall()}
    if "search_count" not in cols:
        conn.execute("ALTER TABLE search_logs ADD COLUMN search_count INTEGER DEFAULT 1")

    duplicate_groups = conn.execute("""
        SELECT LOWER(TRIM(query)) AS query_key,
               LOWER(TRIM(COALESCE(level, ''))) AS level_key,
               SUM(COALESCE(search_count, 1)) AS total_count,
               COUNT(*) AS row_count
        FROM search_logs
        GROUP BY query_key, level_key
        HAVING row_count > 1
    """).fetchall()

    for query_key, level_key, total_count, _ in duplicate_groups:
        rows = conn.execute("""
            SELECT id, query, level, results, timestamp
            FROM search_logs
            WHERE LOWER(TRIM(query)) = ?
              AND LOWER(TRIM(COALESCE(level, ''))) = ?
            ORDER BY datetime(timestamp) DESC, id DESC
        """, (query_key, level_key)).fetchall()
        if not rows:
            continue
        keep_id, query, level, results, timestamp = rows[0]
        conn.execute("""
            UPDATE search_logs
            SET query=?, level=?, results=?, timestamp=?, search_count=?
            WHERE id=?
        """, (query, level, results, timestamp, int(total_count or len(rows)), keep_id))
        conn.executemany("DELETE FROM search_logs WHERE id=?", [(row[0],) for row in rows[1:]])

def migrate_trending_cache(conn):
    duplicate_groups = conn.execute("""
        SELECT LOWER(TRIM(query)) AS query_key,
               SUM(COALESCE(search_count, 1)) AS total_count,
               COUNT(*) AS row_count
        FROM trending_cache
        GROUP BY query_key
        HAVING row_count > 1
    """).fetchall()

    for query_key, total_count, _ in duplicate_groups:
        rows = conn.execute("""
            SELECT id, query, last_searched
            FROM trending_cache
            WHERE LOWER(TRIM(query)) = ?
            ORDER BY datetime(last_searched) DESC, id DESC
        """, (query_key,)).fetchall()
        if not rows:
            continue
        keep_id, query, last_searched = rows[0]
        conn.execute("""
            UPDATE trending_cache
            SET query=?, search_count=?, last_searched=?
            WHERE id=?
        """, (query, int(total_count or len(rows)), last_searched, keep_id))
        conn.executemany("DELETE FROM trending_cache WHERE id=?", [(row[0],) for row in rows[1:]])

def migrate_result_feedback(conn):
    cols = {row[1] for row in conn.execute("PRAGMA table_info(result_feedback)").fetchall()}
    if "rank_score" not in cols:
        conn.execute("ALTER TABLE result_feedback ADD COLUMN rank_score REAL DEFAULT NULL")

def init_db():
    conn = get_conn(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT NOT NULL,
        level TEXT, results INTEGER, timestamp TEXT, search_count INTEGER DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS result_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, query TEXT NOT NULL,
        course_title TEXT NOT NULL, course_level TEXT, tfidf_score REAL, gb_score REAL,
        rank_score REAL, clicked INTEGER DEFAULT 0, rating INTEGER DEFAULT NULL, timestamp TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS model_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT NOT NULL,
        metric_name TEXT NOT NULL, metric_value REAL NOT NULL, trained_at TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT,
        course_title TEXT NOT NULL, course_level TEXT, course_topic TEXT,
        course_link TEXT, score REAL, added_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS trending_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT NOT NULL,
        search_count INTEGER DEFAULT 1, last_searched TEXT)""")
    migrate_search_logs(conn)
    migrate_trending_cache(conn)
    migrate_result_feedback(conn)
    c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_search_logs_query_level
        ON search_logs (LOWER(TRIM(query)), LOWER(TRIM(COALESCE(level, ''))))""")
    c.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_trending_cache_query
        ON trending_cache (LOWER(TRIM(query)))""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS trg_search_logs_upsert
        BEFORE INSERT ON search_logs
        WHEN EXISTS (
            SELECT 1 FROM search_logs
            WHERE LOWER(TRIM(query)) = LOWER(TRIM(NEW.query))
              AND LOWER(TRIM(COALESCE(level, ''))) = LOWER(TRIM(COALESCE(NEW.level, '')))
        )
        BEGIN
            UPDATE search_logs
            SET query=NEW.query,
                level=NEW.level,
                results=NEW.results,
                timestamp=NEW.timestamp,
                search_count=COALESCE(search_count, 1) + COALESCE(NEW.search_count, 1)
            WHERE id = (
                SELECT id FROM search_logs
                WHERE LOWER(TRIM(query)) = LOWER(TRIM(NEW.query))
                  AND LOWER(TRIM(COALESCE(level, ''))) = LOWER(TRIM(COALESCE(NEW.level, '')))
                ORDER BY datetime(timestamp) DESC, id DESC
                LIMIT 1
            );
            SELECT RAISE(IGNORE);
        END""")
    conn.commit(); conn.close()

def log_search(query, level, count):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = normalize_search_value(query)
    level = normalize_search_value(level, "All Levels")
    conn = get_conn()

    existing_log = conn.execute("""
        SELECT id, search_count
        FROM search_logs
        WHERE LOWER(TRIM(query))=LOWER(TRIM(?))
          AND LOWER(TRIM(COALESCE(level, '')))=LOWER(TRIM(?))
    """, (query, level)).fetchone()
    if existing_log:
        conn.execute("""
            UPDATE search_logs
            SET query=?, level=?, results=?, timestamp=?, search_count=?
            WHERE id=?
        """, (query, level, count, ts, int(existing_log[1] or 1) + 1, existing_log[0]))
    else:
        conn.execute("""INSERT INTO search_logs
            (query,level,results,timestamp,search_count) VALUES (?,?,?,?,?)""",
            (query, level, count, ts, 1))

    existing = conn.execute("SELECT id,search_count FROM trending_cache WHERE LOWER(TRIM(query))=LOWER(TRIM(?))", (query,)).fetchone()
    if existing:
        conn.execute("UPDATE trending_cache SET search_count=?, last_searched=? WHERE id=?",
                     (existing[1]+1, ts, existing[0]))
    else:
        conn.execute("INSERT INTO trending_cache (query,search_count,last_searched) VALUES (?,?,?)", (query, 1, ts))
    conn.commit(); conn.close()

def log_results(session_id, query, results):
    conn = get_conn(); ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for r in results:
        conn.execute("""INSERT INTO result_feedback
            (session_id,query,course_title,course_level,tfidf_score,gb_score,rank_score,timestamp)
            VALUES (?,?,?,?,?,?,?,?)""",
            (session_id, query, r["title"], r["level"],
             r.get("tfidf_score", 0.0), r.get("gb_score", 0.0),
             r.get("rank_score", r.get("score", 0.0)), ts))
    conn.commit(); conn.close()

def save_model_metrics(model_name, metrics, extra_json=None):
    conn = get_conn(); ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Remove old metrics for this model
    conn.execute("DELETE FROM model_metrics WHERE model_name=?", (model_name,))
    for k, v in metrics.items():
        conn.execute("INSERT INTO model_metrics (model_name,metric_name,metric_value,trained_at) VALUES (?,?,?,?)",
                     (model_name, k, float(v), ts))
    conn.commit(); conn.close()

def get_logs():
    conn = get_conn()
    rows = conn.execute("""SELECT query,level,results,timestamp,COALESCE(search_count, 1)
        FROM search_logs ORDER BY datetime(timestamp) DESC, id DESC LIMIT 100""").fetchall()
    conn.close()
    return [{"query":r[0],"level":r[1],"results":r[2],"timestamp":r[3],"search_count":r[4]} for r in rows]

def get_model_metrics():
    conn = get_conn()
    rows = conn.execute("SELECT model_name,metric_name,metric_value,trained_at FROM model_metrics ORDER BY model_name,metric_name").fetchall()
    conn.close()
    return [{"model":r[0],"metric":r[1],"value":round(r[2],6),"trained_at":r[3]} for r in rows]

def get_trending(n=10):
    conn = get_conn()
    rows = conn.execute("SELECT query,search_count,last_searched FROM trending_cache ORDER BY search_count DESC LIMIT ?", (n,)).fetchall()
    conn.close()
    return [{"query":r[0],"count":r[1],"last":r[2]} for r in rows]

init_db()
print(f"[INFO] SQLite DB ready: {DB_PATH}")

# ─── LEVEL helpers ───────────────────────────────────────────────────────────
ALL_LEVELS = {"", "all", "all levels"}
TOKEN_RE = re.compile(r"[a-z0-9+#.]+")
REGRESSION_FEATURES = ["tfidf_similarity", "title_match", "topic_match", "phrase_match", "level_match"]

def is_all_level(level):
    return normalize_search_value(level, "All Levels").lower() in ALL_LEVELS

def query_tokens(text):
    return {tok for tok in TOKEN_RE.findall(str(text or "").lower()) if len(tok) > 1}

def token_overlap(text, tokens):
    if not tokens:
        return 0.0
    text_tokens = query_tokens(text)
    return len(tokens & text_tokens) / len(tokens) if text_tokens else 0.0

def phrase_match(text, query):
    query_norm = normalize_search_value(query).lower()
    if len(query_norm) < 3:
        return 0.0
    text_norm = normalize_search_value(text).lower()
    return 1.0 if query_norm in text_norm else 0.0

def ranking_features(candidates, query, requested_level="All Levels"):
    tokens = query_tokens(query)
    tfidf_scores = candidates["tfidf_score"].values.astype(float)
    tfidf_norm = tfidf_scores / (tfidf_scores.max() + 1e-9)

    title_overlap = candidates["title"].apply(lambda value: token_overlap(value, tokens)).values
    topic_overlap = candidates["topic"].apply(lambda value: token_overlap(value, tokens)).values
    title_phrase = candidates["title"].apply(lambda value: phrase_match(value, query)).values
    topic_phrase = candidates["topic"].apply(lambda value: phrase_match(value, query)).values
    phrase_boost = np.maximum(title_phrase, topic_phrase)

    if is_all_level(requested_level):
        level_match = np.zeros(len(candidates), dtype=float)
    else:
        req_level = normalize_search_value(requested_level).lower()
        level_match = (candidates["level"].str.lower() == req_level).astype(float).values

    return np.column_stack([tfidf_norm, title_overlap, topic_overlap, phrase_boost, level_match])

def train_linear_regression_ranker():
    training_rows = np.array([
        [1.00, 1.00, 1.00, 1.00, 1.00],
        [0.95, 1.00, 0.80, 1.00, 0.00],
        [0.85, 0.75, 0.75, 0.00, 1.00],
        [0.75, 0.50, 0.50, 0.00, 1.00],
        [0.65, 1.00, 0.20, 0.00, 0.00],
        [0.55, 0.40, 0.60, 0.00, 1.00],
        [0.45, 0.30, 0.30, 0.00, 0.00],
        [0.30, 0.10, 0.20, 0.00, 1.00],
        [0.15, 0.00, 0.10, 0.00, 0.00],
        [0.00, 0.00, 0.00, 0.00, 0.00],
    ])
    target = (
        0.70 * training_rows[:, 0] +
        0.13 * training_rows[:, 1] +
        0.07 * training_rows[:, 2] +
        0.05 * training_rows[:, 3] +
        0.05 * training_rows[:, 4]
    )
    model = LinearRegression()
    model.fit(training_rows, target)
    save_model_metrics("LinearRegressionRanker", {
        "r2_score": model.score(training_rows, target),
        "n_features": len(REGRESSION_FEATURES),
        "training_examples": len(training_rows),
        "intercept": float(model.intercept_),
    })
    return model

linear_ranker = train_linear_regression_ranker()

def linear_regression_score_results(candidates, query, requested_level="All Levels"):
    features = ranking_features(candidates, query, requested_level)
    scores = linear_ranker.predict(features)
    return np.clip(scores, 0.0, 1.0)

# ─────────────────────────────────────────────────────────────────────────────
#  ML MODEL 1 — Random Forest Classifier
# ─────────────────────────────────────────────────────────────────────────────
RF_PATH = os.path.join(MODEL_DIR, "rf_level_classifier.pkl")

def train_random_forest():
    print("[ML-1] Training Random Forest Level Classifier ...")
    le = LabelEncoder(); y = le.fit_transform(df["level"])
    svd = TruncatedSVD(n_components=150, random_state=42)
    X_lsa = svd.fit_transform(tfidf_matrix)
    X_tr, X_te, y_tr, y_te = train_test_split(X_lsa, y, test_size=0.2, random_state=42, stratify=y)
    rf = RandomForestClassifier(n_estimators=200, max_depth=20, min_samples_split=5,
        class_weight="balanced", n_jobs=-1, random_state=42)
    rf.fit(X_tr, y_tr)
    y_pred = rf.predict(X_te)
    acc = accuracy_score(y_te, y_pred)
    cm  = confusion_matrix(y_te, y_pred).tolist()
    cr  = classification_report(y_te, y_pred, target_names=le.classes_, output_dict=True)
    print(f"[ML-1] RF Accuracy: {acc:.4f}")
    bundle = {"model": rf, "svd": svd, "le": le, "accuracy": acc,
              "confusion_matrix": cm, "classification_report": cr,
              "classes": le.classes_.tolist()}
    with open(RF_PATH, "wb") as f: pickle.dump(bundle, f)
    save_model_metrics("RandomForestClassifier", {
        "accuracy": acc, "n_estimators": 200, "n_features_lsa": 150,
        "test_size": len(y_te)})
    return bundle

def load_or_train_rf():
    if os.path.exists(RF_PATH):
        print("[ML-1] Loading RF model from disk ...")
        with open(RF_PATH, "rb") as f: return pickle.load(f)
    return train_random_forest()

rf_bundle = load_or_train_rf()
rf_model, svd_transform, label_enc = rf_bundle["model"], rf_bundle["svd"], rf_bundle["le"]

def predict_best_level(query):
    q_lsa = svd_transform.transform(vectorizer.transform([query]))
    pred  = rf_model.predict(q_lsa)[0]
    proba = rf_model.predict_proba(q_lsa)[0]
    conf  = float(proba.max())
    return label_enc.inverse_transform([pred])[0], conf

# ─────────────────────────────────────────────────────────────────────────────
#  COMBINED RECOMMENDER
# ─────────────────────────────────────────────────────────────────────────────
def recommend(query, level="All", top_n=10, session_id=None):
    if not query.strip(): return [], "All Levels", 0.0
    sim = cosine_similarity(vectorizer.transform([query]), tfidf_matrix)[0]
    requested_level = normalize_search_value(level, "All Levels")
    use_level_filter = not is_all_level(requested_level)
    level_mode = requested_level if use_level_filter else "All Levels"
    confidence = 1.0 if use_level_filter else 0.0

    tmp = df.copy(); tmp["tfidf_score"] = sim
    if use_level_filter:
        tmp = tmp[tmp["level"].str.lower() == requested_level.lower()]

    candidates = tmp[tmp["tfidf_score"] > 0].copy()
    if candidates.empty: candidates = tmp.copy()
    if candidates.empty: return [], level_mode, confidence
    pre_pool_size = min(max(top_n * 25, 200), len(candidates))
    pre_pool  = candidates.nlargest(pre_pool_size, "tfidf_score").copy()
    rank_scores = linear_regression_score_results(pre_pool, query, requested_level)
    pre_pool["rank_score"] = rank_scores
    pre_pool["gb_score"] = rank_scores
    pre_pool["final_score"] = rank_scores
    top = pre_pool.nlargest(top_n, "final_score")
    results = [{"title":r["title"],"level":r["level"],"type":r["type"],
        "subject":r["subject"],"topic":r["topic"],"link":r["link"],
        "tfidf_score":round(float(r["tfidf_score"]),4),
        "rank_score":round(float(r["rank_score"]),6),
        "gb_score":round(float(r["gb_score"]),6),
        "rank_method":"linear_regression",
        "score":round(float(r["final_score"]),4)} for _,r in top.iterrows()]
    if session_id: log_results(session_id, query, results)
    return results, level_mode, confidence

# ─────────────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({"status":"running","version":"4.0",
        "models":["TF-IDF+Cosine","LinearRegressionRanker","RandomForestClassifier"]})

@app.route("/health")
def health(): return jsonify({"status":"ok","rows":len(df)})

@app.route("/stats")
def stats():
    return jsonify({"total":len(df),"by_level":df["level"].value_counts().to_dict(),
        "by_type":df["type"].value_counts().to_dict(),
        "sample_topics":df["topic"].dropna().unique()[:20].tolist()})

@app.route("/recommend", methods=["POST"])
def get_recommendations():
    data = request.get_json(silent=True) or {}
    query, level = str(data.get("query","")).strip(), str(data.get("level","All")).strip()
    top_n = min(int(data.get("top_n",10)), 30)
    session_id = data.get("session_id")
    if not query: return jsonify({"error":"query required"}), 400
    results, predicted_level, confidence = recommend(query, level, top_n, session_id)
    log_search(query, level, len(results))
    return jsonify({"query":query,"requested_level":level,"predicted_level":predicted_level,
        "confidence":round(confidence,3),"rank_method":"linear_regression",
        "count":len(results),"results":results})

@app.route("/similar", methods=["POST"])
def similar_courses():
    """Find courses similar to a given course title."""
    data  = request.get_json(silent=True) or {}
    title = str(data.get("title","")).strip()
    top_n = min(int(data.get("top_n",5)), 10)
    if not title: return jsonify({"error":"title required"}), 400
    results, _, _ = recommend(title, "All", top_n+1)
    results = [r for r in results if r["title"].lower() != title.lower()][:top_n]
    return jsonify({"similar_to":title,"count":len(results),"results":results})

@app.route("/predict-level", methods=["POST"])
def predict_level_endpoint():
    data  = request.get_json(silent=True) or {}
    query = str(data.get("query","")).strip()
    if not query: return jsonify({"error":"query required"}), 400
    level, conf = predict_best_level(query)
    return jsonify({"query":query,"predicted_level":level,"confidence":round(conf,3)})

@app.route("/compare", methods=["POST"])
def compare_courses():
    """Compare two courses by title — returns their full details side by side."""
    data = request.get_json(silent=True) or {}
    t1, t2 = str(data.get("title1","")).strip(), str(data.get("title2","")).strip()
    if not t1 or not t2: return jsonify({"error":"title1 and title2 required"}), 400
    def find(title):
        mask = df["title"].str.lower().str.contains(title.lower(), na=False)
        rows = df[mask].head(1)
        if rows.empty: return None
        r = rows.iloc[0]
        return {"title":r["title"],"level":r["level"],"topic":r["topic"],
                "type":r["type"],"link":r["link"]}
    c1, c2 = find(t1), find(t2)
    if not c1: return jsonify({"error":f"'{t1}' not found"}), 404
    if not c2: return jsonify({"error":f"'{t2}' not found"}), 404
    return jsonify({"course1":c1,"course2":c2})

@app.route("/bookmark", methods=["POST"])
def add_bookmark():
    data = request.get_json(silent=True) or {}
    sid  = data.get("session_id","anon")
    title= data.get("course_title","").strip()
    if not title: return jsonify({"error":"course_title required"}), 400
    conn = get_conn()
    existing = conn.execute("SELECT id FROM bookmarks WHERE session_id=? AND course_title=?", (sid,title)).fetchone()
    if existing:
        conn.close(); return jsonify({"status":"already_bookmarked"})
    conn.execute("INSERT INTO bookmarks (session_id,course_title,course_level,course_topic,course_link,score,added_at) VALUES (?,?,?,?,?,?,?)",
        (sid, title, data.get("course_level",""), data.get("course_topic",""),
         data.get("course_link",""), data.get("score",0.0), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit(); conn.close()
    return jsonify({"status":"bookmarked","title":title})

@app.route("/bookmarks/<session_id>")
def get_bookmarks(session_id):
    conn = get_conn()
    rows = conn.execute("SELECT course_title,course_level,course_topic,course_link,score,added_at FROM bookmarks WHERE session_id=? ORDER BY id DESC", (session_id,)).fetchall()
    conn.close()
    return jsonify([{"title":r[0],"level":r[1],"topic":r[2],"link":r[3],"score":r[4],"added_at":r[5]} for r in rows])

@app.route("/bookmark/remove", methods=["POST"])
def remove_bookmark():
    data = request.get_json(silent=True) or {}
    sid, title = data.get("session_id","anon"), data.get("course_title","").strip()
    conn = get_conn()
    conn.execute("DELETE FROM bookmarks WHERE session_id=? AND course_title=?", (sid,title))
    conn.commit(); conn.close()
    return jsonify({"status":"removed","title":title})

@app.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}
    sid, title, rating = data.get("session_id"), data.get("course_title"), data.get("rating")
    if not sid or not title: return jsonify({"error":"session_id and course_title required"}), 400
    conn = get_conn()
    conn.execute("UPDATE result_feedback SET clicked=1, rating=? WHERE session_id=? AND course_title=?", (rating,sid,title))
    conn.commit(); conn.close()
    return jsonify({"status":"recorded"})

@app.route("/export/results", methods=["POST"])
def export_results():
    """Return search results as CSV text."""
    data = request.get_json(silent=True) or {}
    query, level = str(data.get("query","")).strip(), str(data.get("level","All")).strip()
    top_n = min(int(data.get("top_n",20)), 50)
    if not query: return jsonify({"error":"query required"}), 400
    results, predicted_level, _ = recommend(query, level, top_n)
    lines = ["title,level,topic,link,score"]
    for r in results:
        def esc(s): return f'"{str(s).replace(chr(34), chr(39))}"'
        lines.append(f'{esc(r["title"])},{esc(r["level"])},{esc(r["topic"])},{esc(r["link"])},{r["score"]}')
    return jsonify({"csv": "\n".join(lines), "count": len(results), "query": query})

@app.route("/logs")
def logs(): return jsonify(get_logs())

@app.route("/trending")
def trending():
    n = int(request.args.get("n", 10))
    return jsonify(get_trending(n))

@app.route("/model-metrics")
def model_metrics_route(): return jsonify(get_model_metrics())

@app.route("/model-details")
def model_details():
    """Return model details including the live regression ranker and diagnostics."""
    rf_data = {"name":"RandomForestClassifier","accuracy":round(rf_bundle.get("accuracy",0),4),
        "classes":rf_bundle.get("classes",[]),
        "confusion_matrix":rf_bundle.get("confusion_matrix",[]),
        "classification_report":rf_bundle.get("classification_report",{})}
    lr_data = {"name":"LinearRegressionRanker",
        "features":REGRESSION_FEATURES,
        "coefficients":[round(float(v),4) for v in linear_ranker.coef_],
        "intercept":round(float(linear_ranker.intercept_),4),
        "rank_method":"linear_regression"}
    return jsonify({"random_forest":rf_data,"linear_regression":lr_data})

@app.route("/retrain", methods=["POST"])
def retrain():
    global rf_bundle, rf_model, svd_transform, label_enc, linear_ranker
    if os.path.exists(RF_PATH):
        os.remove(RF_PATH)
    rf_bundle = train_random_forest()
    rf_model, svd_transform, label_enc = rf_bundle["model"], rf_bundle["svd"], rf_bundle["le"]
    linear_ranker = train_linear_regression_ranker()
    return jsonify({"status":"retrained","rf_accuracy":round(rf_bundle["accuracy"],4),
        "rank_method":"linear_regression"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
