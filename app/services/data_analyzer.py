# app/services/data_analyzer.py
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class DataAnalyzer:
    """
    Analyzes historical campaign data to extract patterns and statistics
    """
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.df = None
        self.summary_stats = {}
        self.load_data()
        self.calculate_summary_stats()
        
    def load_data(self):
        """Load and clean the campaign dataset"""
        try:
            self.df = pd.read_csv(self.data_path)
            logger.info(f"✅ Loaded dataset with {len(self.df):,} records")
            logger.info(f"📊 Columns: {list(self.df.columns)}")
            
            # Clean the data
            self.df = self._clean_data(self.df)
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            raise
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare the data"""
        
        # Clean Acquisition Cost (remove $ and commas)
        if 'Acquisition_Cost' in df.columns:
            df['Acquisition_Cost'] = df['Acquisition_Cost'].astype(str).apply(
                lambda x: re.sub(r'[\$,]', '', x)
            )
            df['Acquisition_Cost'] = pd.to_numeric(df['Acquisition_Cost'], errors='coerce')
        
        # Extract duration days
        if 'Duration' in df.columns:
            df['Duration_days'] = df['Duration'].astype(str).str.extract(r'(\d+)').astype(float)
        
        # Calculate CTR
        if 'Clicks' in df.columns and 'Impressions' in df.columns:
            df['CTR'] = (df['Clicks'] / df['Impressions'].replace(0, 1)) * 100
        
        # Convert date
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Month'] = df['Date'].dt.month
            df['Quarter'] = df['Date'].dt.quarter
            df['Year'] = df['Date'].dt.year
        
        # Fill missing values
        df = df.fillna(0)
        
        logger.info("✅ Data cleaning completed")
        return df
    
    def calculate_summary_stats(self):
        """Calculate summary statistics from the data"""
        
        self.summary_stats = {
            'total_records': len(self.df),
            'date_range': {
                'start': self.df['Date'].min().strftime('%Y-%m-%d') if 'Date' in self.df.columns else None,
                'end': self.df['Date'].max().strftime('%Y-%m-%d') if 'Date' in self.df.columns else None
            },
            'roi': {
                'mean': float(self.df['ROI'].mean()),
                'std': float(self.df['ROI'].std()),
                'min': float(self.df['ROI'].min()),
                'max': float(self.df['ROI'].max()),
                'percentiles': {
                    '25': float(self.df['ROI'].quantile(0.25)),
                    '50': float(self.df['ROI'].quantile(0.5)),
                    '75': float(self.df['ROI'].quantile(0.75))
                }
            },
            'conversion_rate': {
                'mean': float(self.df['Conversion_Rate'].mean()),
                'std': float(self.df['Conversion_Rate'].std()),
                'min': float(self.df['Conversion_Rate'].min()),
                'max': float(self.df['Conversion_Rate'].max())
            },
            'channels': self.df['Channel_Used'].unique().tolist(),
            'campaign_types': self.df['Campaign_Type'].unique().tolist(),
            'product_types': self.df['Product_Type'].unique().tolist() if 'Product_Type' in self.df.columns else [],
            'customer_segments': self.df['Customer_Segment'].unique().tolist() if 'Customer_Segment' in self.df.columns else [],
            'locations': self.df['Location'].unique().tolist() if 'Location' in self.df.columns else []
        }
        
        # ROI by Channel
        self.summary_stats['roi_by_channel'] = self.df.groupby('Channel_Used')['ROI'].agg(['mean', 'std', 'count']).round(2).to_dict()
        
        # ROI by Campaign Type
        self.summary_stats['roi_by_type'] = self.df.groupby('Campaign_Type')['ROI'].agg(['mean', 'std', 'count']).round(2).to_dict()
        
        # ROI by Customer Segment
        if 'Customer_Segment' in self.df.columns:
            self.summary_stats['roi_by_segment'] = self.df.groupby('Customer_Segment')['ROI'].agg(['mean', 'std', 'count']).round(2).to_dict()

        # ROI by Product Type
        if 'Product_Type' in self.df.columns:
            self.summary_stats['roi_by_product_type'] = self.df.groupby('Product_Type')['ROI'].agg(['mean', 'std', 'count']).round(2).to_dict()
        
        logger.info("✅ Summary statistics calculated")
    
    def get_similar_campaigns(self, features: Dict, n: int = 10) -> pd.DataFrame:
        """Find similar campaigns based on features"""
        # This will be implemented with the predictor
        pass
    
    def get_insights(self) -> List[str]:
        """Generate insights from the data"""
        insights = []
        
        # Best performing channel
        best_channel = self.df.groupby('Channel_Used')['ROI'].mean().idxmax()
        best_channel_roi = self.df.groupby('Channel_Used')['ROI'].mean().max()
        insights.append(f"📈 Best performing channel: {best_channel} (ROI: {best_channel_roi:.2f})")
        
        # Best campaign type
        best_type = self.df.groupby('Campaign_Type')['ROI'].mean().idxmax()
        best_type_roi = self.df.groupby('Campaign_Type')['ROI'].mean().max()
        insights.append(f"🎯 Best campaign type: {best_type} (ROI: {best_type_roi:.2f})")
        
        # Best customer segment
        if 'Customer_Segment' in self.df.columns:
            best_segment = self.df.groupby('Customer_Segment')['ROI'].mean().idxmax()
            best_segment_roi = self.df.groupby('Customer_Segment')['ROI'].mean().max()
            insights.append(f"👥 Best customer segment: {best_segment} (ROI: {best_segment_roi:.2f})")

        # Best product type
        if 'Product_Type' in self.df.columns:
            best_product = self.df.groupby('Product_Type')['ROI'].mean().idxmax()
            best_product_roi = self.df.groupby('Product_Type')['ROI'].mean().max()
            insights.append(f"🛒 Best product type: {best_product} (ROI: {best_product_roi:.2f})")
        
        # Overall statistics
        insights.append(f"📊 Average ROI: {self.df['ROI'].mean():.2f} ± {self.df['ROI'].std():.2f}")
        insights.append(f"📊 Average Conversion Rate: {self.df['Conversion_Rate'].mean():.2%}")
        
        return insights
