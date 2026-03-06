"""
Planning Agent for AI Digital Marketing
Handles campaign creation with LLM integration and dataset analysis
"""

import pandas as pd
import google.generativeai as genai
import json
import os
from typing import Dict, Any, List
from datetime import datetime

class CampaignPlanningAgent:
    """Agent for planning marketing campaigns using LLM and dataset insights"""
    
    def __init__(self):
        """Initialize the planning agent"""
        self.api_key = os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.dataset_path = 'marketing_campaign_dataset.csv'
        self.df = None
        self._load_dataset()
    
    def _load_dataset(self):
        """Load and preprocess the marketing dataset"""
        try:
            self.df = pd.read_csv(self.dataset_path)
            print(f"✅ Dataset loaded: {len(self.df)} records")
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            self.df = None
    
    def _get_relevant_benchmarks(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get relevant benchmarks from dataset based on campaign parameters
        """
        if self.df is None:
            return {}
        
        df = self.df
        benchmarks = {}
        
        # Filter by campaign type if available
        campaign_type = campaign_data.get('product_type', '')
        if campaign_type:
            filtered_df = df[df['Campaign_Type'].str.contains(campaign_type, case=False, na=False)]
        else:
            filtered_df = df
        
        # Filter by platform/channel
        platforms = campaign_data.get('platforms', [])
        if platforms:
            platform_filter = '|'.join(platforms)
            filtered_df = filtered_df[filtered_df['Channel_Used'].str.contains(platform_filter, case=False, na=False)]
        
        # Get benchmarks
        if len(filtered_df) > 0:
            benchmarks = {
                'avg_conversion_rate': float(filtered_df['Conversion_Rate'].mean()),
                'avg_roi': float(filtered_df['ROI'].mean()),
                'avg_cac': float(filtered_df['Acquisition_Cost'].mean()),
                'avg_engagement_score': float(filtered_df['Engagement_Score'].mean()),
                'avg_ctr': float((filtered_df['Clicks'] / filtered_df['Impressions']).mean()),
                'top_channels': filtered_df['Channel_Used'].value_counts().head(3).to_dict(),
                'top_segments': filtered_df['Customer_Segment'].value_counts().head(3).to_dict(),
                'data_points_used': len(filtered_df)
            }
        
        return benchmarks
    
    def _format_llm_prompt(self, campaign_data: Dict[str, Any], benchmarks: Dict[str, Any]) -> str:
        """Format prompt for LLM with campaign context and benchmarks"""
        prompt = f"""You are an expert marketing strategist. Analyze this campaign and provide ONLY a JSON response with recommendations. NO explanations, NO markdown, NO ** symbols. Return ONLY valid JSON.

CAMPAIGN DATA:
Product: {campaign_data.get('product_name', 'N/A')}
Type: {campaign_data.get('product_type', 'N/A')}
Goal: {campaign_data.get('goal', 'N/A')}
Budget: ${campaign_data.get('budget', 0)}
Duration: {campaign_data.get('duration', 30)} days
Platforms: {', '.join(campaign_data.get('platforms', []))}
Audience: {json.dumps(campaign_data.get('audience', {}), indent=2)}

INDUSTRY BENCHMARKS (from {benchmarks.get('data_points_used', 0)} campaigns):
Conversion Rate: {benchmarks.get('avg_conversion_rate', 0):.2%}
ROI: {benchmarks.get('avg_roi', 0):.2%}
CAC: ${benchmarks.get('avg_cac', 0):.2f}
Engagement: {benchmarks.get('avg_engagement_score', 0):.2f}
CTR: {benchmarks.get('avg_ctr', 0):.2%}

Return ONLY this exact JSON structure (no additional text):
{{
  "strategy_overview": "Brief strategy (1-2 sentences)",
  "budget_allocation": {{"Platform1": amount, "Platform2": amount}},
  "kpi_targets": {{"metric": "value"}},
  "content_strategy": ["recommendation1", "recommendation2", "recommendation3"],
  "audience_refinements": ["refinement1", "refinement2"],
  "risk_assessment": ["risk1", "risk2"],
  "success_metrics": ["metric1", "metric2"]
}}"""
        return prompt
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        try:
            # Clean the response: remove ** and markdown artifacts
            cleaned_text = response_text.replace('**', '').strip()
            
            # Extract JSON (look for the first { and last })
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                return {
                    'error': 'Could not parse LLM response',
                    'raw': response_text[:200]
                }
            
            json_str = cleaned_text[json_start:json_end]
            plan = json.loads(json_str)
            
            # Clean any remaining ** in the plan
            plan = self._clean_asterisks(plan)
            
            return plan
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            return {
                'error': 'Failed to parse LLM response as JSON',
                'raw': response_text[:300]
            }
    
    def _clean_asterisks(self, obj: Any) -> Any:
        """Recursively remove ** from strings in nested structures"""
        if isinstance(obj, str):
            return obj.replace('**', '').strip()
        elif isinstance(obj, dict):
            return {k: self._clean_asterisks(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_asterisks(item) for item in obj]
        return obj
    
    def plan_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method: Execute the complete planning workflow
        
        Args:
            campaign_data: Campaign input data
        
        Returns:
            Structured campaign plan with LLM insights
        """
        try:
            print(f"\n🚀 Planning Agent Started for Campaign: {campaign_data.get('product_name')}")
            
            # Step 1: Get relevant benchmarks from dataset
            print("📊 Step 1: Analyzing dataset benchmarks...")
            benchmarks = self._get_relevant_benchmarks(campaign_data)
            print(f"✅ Found {benchmarks.get('data_points_used', 0)} relevant data points")
            
            # Step 2: Format prompt for LLM
            print("📝 Step 2: Formatting LLM prompt with context...")
            prompt = self._format_llm_prompt(campaign_data, benchmarks)
            
            # Step 3: Call LLM
            print("🤖 Step 3: Calling LLM for campaign planning...")
            llm_response = self.model.generate_content(prompt)
            response_text = llm_response.text
            print("✅ LLM response received")
            
            # Step 4: Parse and structure response
            print("🔧 Step 4: Structuring LLM response...")
            structured_plan = self._parse_llm_response(response_text)
            
            # Step 5: Combine with metadata
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'campaign_summary': {
                    'product': campaign_data.get('product_name'),
                    'goal': campaign_data.get('goal'),
                    'budget': campaign_data.get('budget'),
                    'duration': campaign_data.get('duration', 30)
                },
                'benchmarks': benchmarks,
                'plan': structured_plan,
                'raw_llm_response': response_text
            }
            
            print("✅ Planning Agent Completed Successfully\n")
            return result
            
        except Exception as e:
            print(f"❌ Error in Planning Agent: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Initialize agent
planning_agent = CampaignPlanningAgent()


def get_campaign_plan(campaign_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to get campaign plan from agent"""
    return planning_agent.plan_campaign(campaign_data)
