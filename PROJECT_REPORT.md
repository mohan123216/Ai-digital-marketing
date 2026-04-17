# AI Digital Marketing Agent Report

## 1. Project Title

**AI Digital Marketing Planning, Launch, and Optimization Agent**

## 2. Project Overview

This project is an AI-powered digital marketing platform that helps users plan, launch, monitor, and optimize paid advertising campaigns across multiple online channels. It combines machine learning, backend APIs, campaign workflow automation, and a frontend dashboard into one system.

The application allows a user to:

- create an account and log in securely
- submit campaign goals, audience details, product details, budget, and duration
- receive AI-generated campaign recommendations
- view predicted ROI and conversion rate for each recommendation
- launch campaigns to external ad platforms such as Google Ads and Meta Ads
- upload ad creatives and manage campaign ads
- analyze campaign scaling opportunities
- run optimization flows using real or mock platform metrics

In short, the system acts as an intelligent campaign assistant for digital marketing decision-making.

## 3. Problem Statement

Digital marketing teams often face difficulty in selecting the best advertising platform, audience segment, and budget allocation before spending money on live campaigns. Manual planning can be slow, inconsistent, and dependent on human intuition.

This project addresses that challenge by using historical campaign data and machine learning models to predict performance and recommend the most promising campaign strategy before launch. It also extends beyond recommendation by supporting campaign launch, tracking, optimization, and scale-up analysis.

## 4. Objectives

The main objectives of the project are:

1. To build a system that predicts campaign performance using historical marketing data.
2. To recommend the best advertising platforms and campaign settings for a given business goal.
3. To provide a secure full-stack application with authentication and campaign history tracking.
4. To integrate with external ad platforms for campaign launch and optimization.
5. To help users improve campaign ROI and conversion outcomes through AI-assisted decisions.

## 5. Technology Stack

### Backend

- FastAPI
- Python
- Pydantic
- Uvicorn

### Machine Learning and Data Processing

- Pandas
- NumPy
- Scikit-learn
- XGBoost
- Joblib

### Frontend

- React
- Vite
- CSS

### Database and Storage

- Supabase database
- Supabase storage

### Security and Authentication

- JWT-based authentication
- Password hashing with bcrypt/passlib

### External Platform Integrations

- Google Ads automation module
- Meta Ads automation module

## 6. System Architecture

The project follows a full-stack architecture with multiple cooperating layers:

1. **Frontend layer**
   A React-based dashboard where users sign up, log in, generate plans, launch campaigns, view history, upload ad media, and request optimization or scale-up analysis.

2. **Backend API layer**
   A FastAPI application that exposes endpoints for authentication, recommendation generation, campaign history, metrics, ad launch, optimization, and scaling analysis.

3. **Machine learning layer**
   A prediction engine trains on historical campaign data and estimates ROI and conversion rate for new campaign combinations.

4. **Data and persistence layer**
   Supabase stores user records, campaign runs, launched platform metadata, optimization logs, and uploaded campaign assets.

5. **Ad platform integration layer**
   Google Ads and Meta Ads modules support launching selected recommendations and interacting with campaign operations.

## 7. Dataset Used

The system uses the dataset:

- `data/marketing_campaign_dataset_corrected.csv`

Key facts from the implementation:

- total records: **200,000**
- used for training and recommendation scoring
- contains campaign-related business features such as:
  - channel used
  - customer segment
  - location
  - product type
  - clicks
  - impressions
  - engagement score
  - ROI
  - conversion rate
  - duration
  - acquisition cost

## 8. Data Preprocessing

The `DataAnalyzer` and `CampaignPredictor` services preprocess the raw campaign data before training and prediction.

The preprocessing steps include:

1. Cleaning currency values in `Acquisition_Cost`.
2. Extracting numeric campaign duration from the `Duration` column.
3. Converting input columns into numeric form.
4. Recomputing CTR from clicks and impressions where needed.
5. Filling missing values.
6. Encoding categorical features using `LabelEncoder`.
7. Scaling numerical features using `StandardScaler`.
8. Creating summary statistics used by the rest of the system.

## 9. Machine Learning Models Used

The project currently uses two active supervised learning models.

### 9.1 Random Forest Regressor

Purpose:

- predicts campaign **ROI**

Why used:

- works well on structured tabular data
- handles nonlinear relationships between campaign features
- is robust for business prediction tasks

### 9.2 XGBoost Regressor

Purpose:

- predicts campaign **Conversion Rate**

Why used:

- performs strongly on regression tasks for structured datasets
- handles complex feature interactions efficiently
- improves predictive power for campaign outcome estimation

## 10. Input Features for Prediction

The prediction pipeline uses these major features:

- `Channel_Used`
- `Customer_Segment`
- `Location`
- `Product_Type`
- `Duration_days`
- `Acquisition_Cost`
- `CTR`
- `Clicks`
- `Impressions`
- `Engagement_Score`

These are encoded and transformed into the final feature matrix used by the ML models.

## 11. Model Training Workflow

When the FastAPI application starts, the following workflow takes place:

1. Historical campaign data is loaded from the CSV dataset.
2. Data cleaning and feature preparation are performed.
3. The dataset is split into training and testing sets.
4. Features are scaled using `StandardScaler`.
5. The Random Forest model is trained for ROI prediction.
6. The XGBoost model is trained for conversion rate prediction.
7. Both models are evaluated using regression metrics.
8. Trained models and preprocessors are saved to the `models/` directory.
9. The recommendation engine is initialized using the trained predictor.

## 12. Recommendation Engine Logic

The recommendation engine is one of the strongest parts of the project. It does not simply return a fixed rule-based answer. Instead, it generates many possible campaign combinations and scores them using ML predictions.

Its main process is:

1. Generate campaign combinations across supported platforms.
2. Vary location, customer segment, age group, and budget candidates.
3. Estimate supporting metrics from similar historical campaigns.
4. Predict ROI and conversion rate for each combination.
5. Apply goal-based weights depending on whether the user wants ROI, traffic, leads, conversions, engagement, or brand awareness.
6. Rank combinations using prediction score and confidence.
7. Return the best platform-specific recommendations.

Supported recommendation platforms in the active logic:

- Instagram
- Facebook
- Google Ads
- LinkedIn Ads

## 13. Major Functional Modules

### 13.1 Authentication Module

The system supports:

- user signup
- user login
- JWT access token generation
- protected API endpoints
- current-user profile retrieval

User records are stored in Supabase and passwords are stored in hashed form.

### 13.2 Recommendation Module

This module accepts campaign inputs from the user and returns:

- top platform recommendations
- predicted ROI
- predicted conversion rate
- confidence level
- rationale
- risk level
- performance expectations
- A/B testing plan
- budget allocation suggestions

### 13.3 Campaign History Module

Each recommendation request is saved as a campaign run. This allows the user to:

- revisit previous plans
- check launched platforms
- track campaign outputs
- view prior optimization activity

### 13.4 Ad Launch Module

The backend includes endpoints for:

- launching recommendations to Google Ads
- launching recommendations to Meta Ads
- launching text, image, and video ads into Google Ads campaigns

The system also stores launch metadata in the database.

### 13.5 Media Upload Module

Users can upload ad media files for campaign ads. Uploaded files are validated and stored in Supabase Storage.

### 13.6 Optimization Module

The project includes optimization flows for both Google Ads and Meta Ads. These flows can:

- inspect metrics
- simulate optimization suggestions
- apply changes programmatically
- store optimization logs
- support dry-run and mock-data modes for testing

### 13.7 Scale-Up Analysis Module

The system can analyze a previously generated campaign and determine whether the user should:

- scale up the budget
- maintain current execution
- switch to a better platform
- add another platform
- launch the campaign if not yet launched

## 14. Frontend Features

The React frontend provides a user dashboard with the following pages or flows:

- landing page
- signup and login
- campaign planning form
- recommendation display
- campaign history
- ad creation and media upload
- optimization interface
- scaling analysis
- settings screen

This makes the project a complete end-to-end application rather than only an ML notebook or backend service.

## 15. API Capabilities

The backend exposes API endpoints for:

- health checking
- user authentication
- current-user profile
- recommendation generation
- campaign history retrieval
- Google Ads launch
- Meta Ads launch
- ad media upload and launch
- insights and model metrics
- channel, product type, and customer segment lookup
- optimization operations
- scale-up analysis

This API-first design also makes the project extensible for mobile apps or third-party integrations in the future.

## 16. Output Produced by the System

For a user campaign request, the system can produce:

- ranked platform recommendations
- predicted ROI values
- predicted conversion percentages
- confidence scores
- recommended platform-wise budget allocations
- performance expectation ranges
- A/B testing plans
- campaign history records
- launch status
- optimization actions and logs
- scale-up suggestions

## 17. Strengths of the Project

This project has several strong points:

1. It is a complete full-stack solution, not just a standalone model.
2. It uses real ML models in the active application flow.
3. It supports multi-platform campaign planning.
4. It stores users and workflows in a persistent backend.
5. It includes practical business features such as optimization and campaign launch.
6. It has a usable frontend for non-technical users.
7. It supports both simulation and real platform operations.

## 18. Limitations

Some current limitations observed from the implementation are:

1. LinkedIn Ads appears in the recommendation/UI flow, but launch support is not fully implemented yet.
2. A `FeatureEngineering` utility exists in the codebase, but it is not currently wired into the active training pipeline.
3. Model quality depends heavily on the quality and representativeness of the historical dataset.
4. External ad-platform integrations require valid credentials and can fail due to API constraints.
5. Startup training may take time because models are trained when the API starts.
6. Some configuration values and secrets should be managed more carefully for production deployment.

## 19. Possible Future Enhancements

The project can be improved further by adding:

1. live retraining or scheduled model retraining
2. stronger feature engineering in the active ML pipeline
3. explainable AI outputs for recommendation reasoning
4. complete LinkedIn campaign launch integration
5. richer campaign analytics dashboards
6. role-based access control for multiple team members
7. containerized deployment and CI/CD automation
8. automated monitoring for model drift and ad performance

## 20. Conclusion

This project successfully demonstrates how artificial intelligence and machine learning can be applied to digital marketing automation. It goes beyond simple prediction by offering an integrated platform for campaign planning, recommendation, launch, optimization, and scaling.

The use of a **Random Forest Regressor** for ROI prediction and an **XGBoost Regressor** for conversion rate prediction makes the recommendation engine data-driven and practical. Combined with a FastAPI backend, React frontend, Supabase persistence, and ad-platform integration, the project represents a strong real-world software engineering and AI application.

Overall, this is a valuable project that shows skills in:

- machine learning
- backend API development
- frontend development
- cloud database integration
- authentication and security
- automation of digital marketing workflows

## 21. Short Viva Summary

This project is an AI-based digital marketing agent that predicts campaign performance and recommends the best advertising strategy. It uses historical marketing data, trains two regression models for ROI and conversion prediction, and serves recommendations through a FastAPI backend and React frontend. It also supports campaign launch, optimization, ad media handling, and scale-up analysis using Supabase and ad-platform integrations.
