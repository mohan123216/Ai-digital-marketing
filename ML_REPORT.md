# Machine Learning Report

## Overview

This project uses machine learning to predict marketing campaign performance and then generate campaign recommendations from those predictions.

The active ML pipeline contains:

1. A **Random Forest Regressor** to predict **ROI**
2. An **XGBoost Regressor** to predict **Conversion Rate**

These models are trained when the FastAPI application starts, and their outputs are used by the recommendation engine to rank the best campaign options.

## End-to-End ML Workflow

### Step 1: Load historical campaign data

The application loads the dataset from:

- `data/marketing_campaign_dataset_corrected.csv`

This happens through the `DataAnalyzer` service, which:

- reads the CSV file
- cleans numeric fields such as `Acquisition_Cost`
- extracts `Duration_days` from the `Duration` column
- calculates CTR from clicks and impressions
- converts date fields into month, quarter, and year
- fills missing values

### Step 2: Train the prediction models

At application startup, the system initializes `CampaignPredictor` and trains the ML models using the cleaned dataset.

The training flow is:

1. Prepare input features
2. Encode categorical columns
3. Scale the feature matrix
4. Split the data into training and testing sets
5. Train the ROI model
6. Train the Conversion Rate model
7. Evaluate both models
8. Save trained models to disk

### Step 3: Use predictions in recommendation generation

After training, the `RecommendationEngine` creates many possible campaign combinations across supported platforms and audience settings.

For each combination, the system:

1. builds an input feature set
2. sends it to the predictor
3. gets predicted ROI
4. gets predicted conversion rate
5. calculates a confidence score
6. ranks combinations based on campaign goal
7. returns the best recommendations

## Model 1: Random Forest Regressor for ROI Prediction

### Purpose

This model predicts the expected **Return on Investment (ROI)** of a campaign.

### Why this model fits the project

Random Forest is suitable because campaign performance depends on many interacting factors such as channel, audience, cost, clicks, impressions, and engagement. Random Forest handles nonlinear relationships well and is also robust for tabular business data.

### Input features used

The ROI model uses these features:

- `Channel_Used_encoded`
- `Customer_Segment_encoded`
- `Location_encoded`
- `Product_Type_encoded`
- `Duration_days`
- `Acquisition_Cost`
- `CTR`
- `Clicks`
- `Impressions`
- `Engagement_Score`

### Step-by-step process

1. Load the cleaned dataset.
2. Extract or create `Duration_days`.
3. Convert numeric columns to valid numbers.
4. Recalculate CTR if it is missing or zero.
5. Fill missing numeric values with `0`.
6. Encode categorical columns using `LabelEncoder`.
7. Build the feature matrix `X`.
8. Set target variable `y_roi` from the `ROI` column.
9. Split data into training and testing sets using `train_test_split`.
10. Scale features using `StandardScaler`.
11. Train `RandomForestRegressor`.
12. Predict ROI on the test set.
13. Evaluate using `RMSE`, `MAE`, and `R²`.
14. Run cross-validation using `cross_val_score`.
15. Save the trained model using `joblib`.

### Evaluation metrics used

- `RMSE` for prediction error magnitude
- `MAE` for average absolute error
- `R²` for goodness of fit
- Cross-validation `R²` mean and standard deviation

## Model 2: XGBoost Regressor for Conversion Rate Prediction

### Purpose

This model predicts the expected **Conversion Rate** of a campaign.

### Why this model fits the project

XGBoost is a strong choice for structured datasets and often performs well on regression tasks involving complex feature interactions. In this project it is used to estimate conversion performance more accurately than a simple linear model.

### Input features used

The conversion model uses the same feature set as the ROI model:

- `Channel_Used_encoded`
- `Customer_Segment_encoded`
- `Location_encoded`
- `Product_Type_encoded`
- `Duration_days`
- `Acquisition_Cost`
- `CTR`
- `Clicks`
- `Impressions`
- `Engagement_Score`

### Step-by-step process

1. Use the same prepared and encoded feature matrix created during preprocessing.
2. Set target variable `y_conversion` from the `Conversion_Rate` column.
3. Use the same train/test split as the ROI model.
4. Scale the input features using `StandardScaler`.
5. Train `XGBRegressor`.
6. Predict conversion rate on the test set.
7. Evaluate using `RMSE`, `MAE`, and `R²`.
8. Run cross-validation using `cross_val_score`.
9. Save the trained model using `joblib`.

### Evaluation metrics used

- `RMSE`
- `MAE`
- `R²`
- Cross-validation `R²` mean and standard deviation

## Preprocessing Techniques Used

The project applies the following preprocessing before training:

- cleaning currency values in `Acquisition_Cost`
- extracting numeric days from the duration field
- converting columns to numeric types
- filling missing values
- recomputing CTR from clicks and impressions when needed
- encoding categorical variables with `LabelEncoder`
- scaling features with `StandardScaler`

## How the Models Support Recommendations

The recommendation system does not directly choose campaigns using a separate ML ranking model. Instead, it uses the two trained regression models as scoring inputs.

The recommendation steps are:

1. generate possible campaign combinations
2. predict ROI for each combination
3. predict conversion rate for each combination
4. estimate confidence
5. combine the prediction values using goal-based weights
6. sort combinations by final score
7. return the best platform recommendations

## Important Implementation Note

There is also a `FeatureEngineering` class in the project that creates advanced engineered features such as:

- cost per click
- CPM
- engagement rate
- segment flags
- channel matching features

However, this class is **currently not connected to the active training flow**. The running application trains the models directly through `CampaignPredictor` without calling `FeatureEngineering`.

So, in the report, it is most accurate to say:

- the project **implements** a `FeatureEngineering` utility
- but the **active ML models currently used in production flow** are the Random Forest ROI predictor and the XGBoost Conversion Rate predictor

## Short Conclusion

This project uses supervised machine learning on historical marketing campaign data to predict future campaign performance.

The two ML models used are:

1. **Random Forest Regressor** for ROI prediction
2. **XGBoost Regressor** for Conversion Rate prediction

These predictions are then used by the recommendation engine to rank campaign options and return the best marketing strategy suggestions to the user.
