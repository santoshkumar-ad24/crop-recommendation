import os
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, balanced_accuracy_score
from sklearn.calibration import CalibratedClassifierCV
import joblib
import os

base_dir = os.path.dirname(__file__)
csv_path = os.path.abspath(os.path.join(base_dir, "..", "dataset", "Crop_recommendation.csv"))

model_destination = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crop_model.pkl")

def load_data(path):
	df = pd.read_csv(path)
	if 'label' not in df.columns:
		raise KeyError("Expected target column 'label' in dataset")
	return df


def build_pipeline():
	# For tree-based models scaling isn't necessary, but we include a simple imputer
	steps = [
		('imputer', SimpleImputer(strategy='median')),
		('clf', RandomForestClassifier(random_state=42, n_jobs=-1))
	]
	return Pipeline(steps)


def get_param_distributions():
	return {
		'clf__n_estimators': [50, 100, 200, 300],
		'clf__max_depth': [None, 8, 12, 18, 24],
		'clf__min_samples_split': [2, 4, 6, 10],
		'clf__min_samples_leaf': [1, 2, 4, 6],
		'clf__max_features': ['sqrt', 'log2', 0.5, 0.75],
		'clf__bootstrap': [True, False]
	}


def train(path=csv_path, model_out = model_destination, do_search=True, do_calibrate=True):
	os.makedirs(os.path.dirname(model_out), exist_ok=True)

	print('Loading data...')
	df = load_data(path)

	X = df.drop('label', axis=1)
	y = df['label']

	# Encode target labels if they are strings
	le = LabelEncoder()
	y_enc = le.fit_transform(y)

	# Stratified split preserves label distribution
	X_train, X_test, y_train, y_test = train_test_split(
		X, y_enc, test_size=0.2, random_state=42, stratify=y_enc)

	pipeline = build_pipeline()

	if do_search:
		print('Running randomized hyperparameter search (this may take a while)...')
		param_dist = get_param_distributions()
		cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
		search = RandomizedSearchCV(
			pipeline,
			param_distributions=param_dist,
			n_iter=8,  # reduced for quicker runs during development
			scoring='accuracy',
			n_jobs=-1,
			cv=cv,
			verbose=1,
			random_state=42
		)

		search.fit(X_train, y_train)
		best = search.best_estimator_
		print(f'Best params: {search.best_params_}')
	else:
		print('Training with default parameters...')
		best = pipeline
		best.fit(X_train, y_train)

	# Optionally calibrate predicted probabilities to improve confidence estimates
	if do_calibrate:
		print('Calibrating classifier probabilities (this may take additional time)...')
		# Extract the imputer and base classifier from the pipeline if present
		if isinstance(best, Pipeline) and 'imputer' in best.named_steps and 'clf' in best.named_steps:
			imputer = best.named_steps['imputer']
			base_clf = best.named_steps['clf']
		else:
			# Fallback to default components
			imputer = SimpleImputer(strategy='median')
			base_clf = RandomForestClassifier(random_state=42, n_jobs=-1)

		# Build a new pipeline where the classifier is wrapped by CalibratedClassifierCV
		calibrated_pipeline = Pipeline([
			('imputer', imputer),
			('clf', CalibratedClassifierCV(estimator=base_clf, cv=5, method='isotonic'))
		])

		# Fit the calibrated pipeline on the training data
		calibrated_pipeline.fit(X_train, y_train)
		best = calibrated_pipeline

	# Evaluate
	print('Evaluating on test set...')
	y_pred = best.predict(X_test)
	acc = accuracy_score(y_test, y_pred)
	bal_acc = balanced_accuracy_score(y_test, y_pred)
	report = classification_report(y_test, y_pred)

	print(f'Test accuracy: {acc:.4f} | Balanced accuracy: {bal_acc:.4f}')
	print('Classification report:\n', report)

	# Save artifacts: model and label encoder
	joblib.dump(best, model_out)
	joblib.dump(le, os.path.join(os.path.dirname(model_out), 'label_encoder.pkl'))

	# Save a small metadata file
	meta = {
		'model_path': model_out,
		'label_encoder': os.path.join(os.path.dirname(model_out), 'label_encoder.pkl'),
		'accuracy': float(acc),
		'balanced_accuracy': float(bal_acc)
	}
	with open(os.path.join(os.path.dirname(model_out), 'training_metadata.json'), 'w') as f:
		json.dump(meta, f, indent=2)

	print('✅ Model and artifacts saved to', os.path.dirname(model_out))


if __name__ == '__main__':
	# Toggle do_search to False if you want a faster run without hyperparameter tuning
	train(path=csv_path, model_out=model_destination, do_search=True)
