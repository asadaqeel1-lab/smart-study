**Smart Study Resource Recommender**

A content-based recommendation system that suggests study resources (courses, articles, videos, etc.) based on topic, subject, and difficulty level. Built with a Flask backend for ML/data logic and a Streamlit frontend for the user interface.

Features
TF-IDF based recommendations — suggests resources similar to a given query using cosine similarity over titles, topics, subjects, and levels
Difficulty level prediction — a Random Forest classifier predicts the difficulty level of a resource
Similar resource lookup — find resources related to a specific item
Resource comparison — compare multiple resources side by side
Bookmarking — save resources per session (stored in SQLite)
Feedback logging — capture user feedback on recommendations
Trending resources & stats — dataset-wide statistics and popularity tracking
Export results — download recommendation results
Model retraining endpoint — retrain the underlying ML model on demand
Power BI report (project.pbix) — supplementary analytics dashboard, opened separately in Power BI Desktop
Tech Stack
Backend: Flask, Flask-CORS
ML/Data: scikit-learn (TF-IDF, RandomForestClassifier, LinearRegression, TruncatedSVD), pandas, numpy
Frontend: Streamlit
Storage: SQLite (study_recommender.db)
Dataset: final_dataset_fixed.csv (~41,000 study resources)

**Project Structure**

Smart_study_recommender_enhanced/
├── app.py                    # Flask backend — API, ML models, data processing

├── ui.py                     # Streamlit frontend

├── final_dataset_fixed.csv   # Resource dataset

├── study_recommender.db      # SQLite database (bookmarks, logs, feedback)

├── smart_study.ipynb         # Notebook — exploration / model development

├── project.pbix              # Power BI report

└── requirements.txt          # Python dependencies
