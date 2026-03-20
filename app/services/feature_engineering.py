# app/services/feature_engineering.py
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import logging
import re

logger = logging.getLogger(__name__)

class FeatureEngineering:
    """
    Creates predictive features from raw campaign data
    """
    
    def __init__(self):
        self.label_encoders = {}
        self.feature_stats = {}
        self.selected_features = []
        self.is_fitted = False
        
    def engineer_features(self, df, for_training=True):
        """Main method to create all features"""
        
        data = df.copy()
        logger.info("Starting feature engineering...")
        
        # 1. First clean all columns (IMPROVED VERSION)
        data = self._clean_all_columns(data)
        
        # 2. Create efficiency metrics
        data = self._create_efficiency_metrics(data)
        
        # 3. Create interaction features
        data = self._create_interaction_features(data, for_training)
        
        # 4. Create segment-based features
        data = self._create_segment_features(data)
        
        # 5. Create channel-specific features
        data = self._create_channel_features(data)
        
        # 6. Encode categorical variables
        data = self._encode_categorical(data, for_training)
        
        # 7. Select final features
        data = self._select_features(data, for_training)
        
        if for_training:
            self.is_fitted = True
            
        logger.info(f"Feature engineering complete. Final features: {len(self.selected_features)}")
        
        return data
    
    def _clean_all_columns(self, data):
        """Clean all columns first - IMPROVED VERSION with better string cleaning"""
        
        # ===== CLEAN ACQUISITION COST (MOST IMPORTANT) =====
        if 'Acquisition_Cost' in data.columns:
            logger.info(f"Cleaning Acquisition_Cost. Sample values: {data['Acquisition_Cost'].head(3).tolist()}")
            
            # Convert to string first
            data['Acquisition_Cost'] = data['Acquisition_Cost'].astype(str)
            
            # Remove $ and commas using regex
            data['Acquisition_Cost'] = data['Acquisition_Cost'].apply(
                lambda x: re.sub(r'[\$,]', '', x)
            )
            
            # Convert to float
            data['Acquisition_Cost'] = pd.to_numeric(data['Acquisition_Cost'], errors='coerce')
            
            # Fill NaN with median
            data['Acquisition_Cost'] = data['Acquisition_Cost'].fillna(data['Acquisition_Cost'].median())
            
            logger.info(f"After cleaning. Sample: {data['Acquisition_Cost'].head(3).tolist()}")
        
        # Clean Clicks
        if 'Clicks' in data.columns:
            data['Clicks'] = pd.to_numeric(data['Clicks'], errors='coerce').fillna(0).astype(int)
        
        # Clean Impressions
        if 'Impressions' in data.columns:
            data['Impressions'] = pd.to_numeric(data['Impressions'], errors='coerce').fillna(0).astype(int)
        
        # Clean Engagement Score
        if 'Engagement_Score' in data.columns:
            data['Engagement_Score'] = pd.to_numeric(data['Engagement_Score'], errors='coerce').fillna(0).astype(int)
        
        # Clean ROI
        if 'ROI' in data.columns:
            data['ROI'] = pd.to_numeric(data['ROI'], errors='coerce').fillna(0)
        
        # Clean Conversion Rate
        if 'Conversion_Rate' in data.columns:
            data['Conversion_Rate'] = pd.to_numeric(data['Conversion_Rate'], errors='coerce').fillna(0)
        
        # Handle Duration
        if 'Duration' in data.columns:
            # Extract numeric part from strings like "30 days"
            data['Duration_days'] = data['Duration'].astype(str).str.extract(r'(\d+)').astype(float)
            data['Duration_days'] = data['Duration_days'].fillna(30)
        elif 'Duration_days' not in data.columns:
            data['Duration_days'] = 30
        
        # Fill any remaining NaN values with 0
        data = data.fillna(0)
        
        return data
    
    def _create_efficiency_metrics(self, data):
        """Create features that measure efficiency"""
        
        # Ensure numeric columns for calculations
        data['Acquisition_Cost'] = data['Acquisition_Cost'].astype(float)
        data['Clicks'] = data['Clicks'].astype(float)
        data['Impressions'] = data['Impressions'].astype(float)
        
        # Cost per click (avoid division by zero)
        data['cost_per_click'] = 0.0
        mask = data['Clicks'] > 0
        data.loc[mask, 'cost_per_click'] = data.loc[mask, 'Acquisition_Cost'] / data.loc[mask, 'Clicks']
        data['cost_per_click'] = data['cost_per_click'].replace([np.inf, -np.inf], 0).clip(upper=1000)
        
        # Cost per impression (CPM)
        data['cpm'] = 0.0
        mask = data['Impressions'] > 0
        data.loc[mask, 'cpm'] = (data.loc[mask, 'Acquisition_Cost'] / data.loc[mask, 'Impressions']) * 1000
        data['cpm'] = data['cpm'].replace([np.inf, -np.inf], 0).clip(upper=1000)
        
        # Engagement rate
        data['engagement_rate'] = 0.0
        mask = data['Impressions'] > 0
        data.loc[mask, 'engagement_rate'] = (data.loc[mask, 'Engagement_Score'] / data.loc[mask, 'Impressions']) * 10000
        data['engagement_rate'] = data['engagement_rate'].replace([np.inf, -np.inf], 0)
        
        # Click-through rate
        data['CTR'] = 0.0
        mask = data['Impressions'] > 0
        data.loc[mask, 'CTR'] = (data.loc[mask, 'Clicks'] / data.loc[mask, 'Impressions']) * 100
        data['CTR'] = data['CTR'].replace([np.inf, -np.inf], 0)
        
        return data
    
    def _create_interaction_features(self, data, for_training):
        """Create features that capture interactions"""
        
        # For training, calculate group statistics
        if for_training and 'ROI' in data.columns:
            # Channel performance
            if 'Channel_Used' in data.columns:
                channel_stats = data.groupby('Channel_Used')['ROI'].agg(['mean', 'std', 'count']).reset_index()
                channel_stats.columns = ['Channel_Used', 'channel_roi_mean', 'channel_roi_std', 'channel_count']
                data = data.merge(channel_stats, on='Channel_Used', how='left')
            
            # Campaign type performance
            if 'Campaign_Type' in data.columns:
                type_stats = data.groupby('Campaign_Type')['ROI'].agg(['mean', 'std', 'count']).reset_index()
                type_stats.columns = ['Campaign_Type', 'type_roi_mean', 'type_roi_std', 'type_count']
                data = data.merge(type_stats, on='Campaign_Type', how='left')
            
            # Segment performance
            if 'Customer_Segment' in data.columns:
                segment_stats = data.groupby('Customer_Segment')['ROI'].agg(['mean', 'std', 'count']).reset_index()
                segment_stats.columns = ['Customer_Segment', 'segment_roi_mean', 'segment_roi_std', 'segment_count']
                data = data.merge(segment_stats, on='Customer_Segment', how='left')
        
        return data
    
    def _create_segment_features(self, data):
        """Create features based on customer segments"""
        
        if 'Customer_Segment' not in data.columns:
            return data
        
        # Define segment characteristics
        b2b_segments = ['Tech Enthusiasts', 'Business', 'Business Professionals']
        b2c_segments = ['Health & Wellness', 'Fashionistas', 'Foodies', 'Outdoor Adventurers']
        high_value_segments = ['Tech Enthusiasts', 'Business', 'Luxury']
        
        # Create segment type
        data['is_b2b'] = data['Customer_Segment'].isin(b2b_segments).astype(int)
        data['is_b2c'] = data['Customer_Segment'].isin(b2c_segments).astype(int)
        data['is_high_value'] = data['Customer_Segment'].isin(high_value_segments).astype(int)
        
        return data
    
    def _create_channel_features(self, data):
        """Create channel-specific features"""
        
        # Channel-type match
        if 'Channel_Used' in data.columns and 'Campaign_Type' in data.columns:
            # Search ads work well on Google
            data['is_good_match'] = (
                ((data['Channel_Used'] == 'Google Ads') & (data['Campaign_Type'] == 'Search')) |
                ((data['Channel_Used'] == 'Instagram') & (data['Campaign_Type'].isin(['Carousel', 'Video']))) |
                ((data['Channel_Used'] == 'Email') & (data['Campaign_Type'] == 'Email')) |
                ((data['Channel_Used'] == 'YouTube') & (data['Campaign_Type'] == 'Video'))
            ).astype(int)
        
        return data
    
    def _encode_categorical(self, data, for_training=True):
        """Encode categorical variables"""
        
        categorical_cols = ['Channel_Used', 'Campaign_Type', 'Customer_Segment', 'Location', 'Language']
        
        for col in categorical_cols:
            if col in data.columns:
                # Convert to string first
                data[col] = data[col].astype(str).fillna('Unknown')
                
                if for_training:
                    # Create new encoder for training
                    le = LabelEncoder()
                    data[f'{col}_encoded'] = le.fit_transform(data[col])
                    self.label_encoders[col] = le
                else:
                    # Use existing encoder for prediction
                    if col in self.label_encoders:
                        le = self.label_encoders[col]
                        # Handle unknown categories
                        data[f'{col}_encoded'] = data[col].apply(
                            lambda x: le.transform([x])[0] if x in le.classes_ else -1
                        )
                    else:
                        data[f'{col}_encoded'] = 0
        
        return data
    
    def _select_features(self, data, for_training=True):
        """Select final set of features for modeling"""
        
        # Define numerical features to use
        numerical_features = [
            'Duration_days', 'Acquisition_Cost', 'Clicks', 'Impressions',
            'Engagement_Score', 'CTR', 'cost_per_click', 'cpm', 'engagement_rate',
            'is_b2b', 'is_b2c', 'is_high_value', 'is_good_match'
        ]
        
        # Filter to only existing numerical features
        numerical_features = [f for f in numerical_features if f in data.columns]
        
        # Add encoded categorical features
        categorical_encoded = []
        for col in ['Channel_Used', 'Campaign_Type', 'Customer_Segment', 'Location']:
            encoded_col = f'{col}_encoded'
            if encoded_col in data.columns:
                categorical_encoded.append(encoded_col)
        
        # Add group statistics if they exist
        group_stats = []
        for col in data.columns:
            if '_mean' in col or '_std' in col or '_count' in col:
                group_stats.append(col)
        
        # Combine all features
        all_features = numerical_features + categorical_encoded + group_stats
        
        # Filter to only available columns
        available_features = [f for f in all_features if f in data.columns]
        
        if for_training:
            self.selected_features = available_features
            logger.info(f"Selected {len(available_features)} features for modeling")
        
        return data