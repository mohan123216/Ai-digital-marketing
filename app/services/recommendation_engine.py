import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from config import settings
from ..models.schemas import ABTestPlan, CampaignInput, CampaignRecommendation, PerformanceExpectations

logger = logging.getLogger(__name__)

ALLOWED_PLATFORMS = ["Instagram", "Google Ads", "LinkedIn Ads"]


class RecommendationEngine:
    """Generate campaign recommendations based on user input and model predictions."""

    def __init__(self, data_analyzer, predictor):
        self.data_analyzer = data_analyzer
        self.predictor = predictor
        self.df = data_analyzer.df

    def generate_combinations(self, user_input: CampaignInput) -> List[Dict]:
        """Create many combinations across the three allowed platforms and audience options."""
        combinations: List[Dict] = []

        locations = [user_input.target_audience.location] if user_input.target_audience.location else self._get_top_locations()
        segments = (
            [user_input.target_audience.customer_segment]
            if user_input.target_audience.customer_segment
            else self._get_top_segments()
        )
        age_groups = [user_input.target_audience.age_range] if user_input.target_audience.age_range else self._get_top_age_groups()

        locations = [loc for loc in locations if loc][:5] or ["United States"]
        segments = [seg for seg in segments if seg][:5] or ["General"]
        age_groups = [age for age in age_groups if age][:4] or ["25-34"]

        budget_candidates = self._budget_candidates(user_input.budget_range.min, user_input.budget_range.max)

        for platform in ALLOWED_PLATFORMS:
            for location in locations:
                for segment in segments:
                    for age_group in age_groups:
                        for budget in budget_candidates:
                            product_type = self._resolve_product_type(user_input, segment)
                            similar = self._filter_similar(platform, location, segment, age_group, product_type)

                            if len(similar) > 0:
                                avg_ctr = similar["CTR"].mean() if "CTR" in similar.columns else 5.0
                                avg_clicks = int(similar["Clicks"].mean()) if "Clicks" in similar.columns else 500
                                avg_impressions = int(similar["Impressions"].mean()) if "Impressions" in similar.columns else 10000
                                avg_engagement = (
                                    float(similar["Engagement_Score"].mean()) if "Engagement_Score" in similar.columns else 5.0
                                )
                            else:
                                avg_ctr = 5.0
                                avg_clicks = 500
                                avg_impressions = 10000
                                avg_engagement = 5.0

                            features = {
                                "Channel_Used": platform,
                                "Customer_Segment": segment,
                                "Location": location,
                                "Product_Type": product_type or "Unknown",
                                "Duration_days": user_input.duration_days,
                                "Acquisition_Cost": budget,
                                "CTR": avg_ctr,
                                "Clicks": avg_clicks,
                                "Impressions": avg_impressions,
                                "Engagement_Score": avg_engagement,
                            }

                            try:
                                prediction = self.predictor.predict(features)
                                combinations.append(
                                    {
                                        "platform": platform,
                                        "location": location,
                                        "segment": segment,
                                        "product_type": product_type or "Unknown",
                                        "age_group": age_group,
                                        "budget": budget,
                                        "predicted_roi": prediction["predicted_roi"],
                                        "predicted_conversion_rate": prediction["predicted_conversion_rate"],
                                        "confidence": prediction["confidence_score"],
                                        "features": features,
                                    }
                                )
                            except Exception as exc:
                                logger.error(f"Prediction failed for {platform}/{location}/{segment}/{age_group}/{budget}: {exc}")
                                continue

        logger.info(f"Generated {len(combinations)} combinations across {len(ALLOWED_PLATFORMS)} platforms")
        return combinations

    def _budget_candidates(self, budget_min: float, budget_max: float) -> List[float]:
        if budget_min <= 0 or budget_max <= 0:
            return [2000.0, 4000.0, 6000.0]
        if budget_min == budget_max:
            return [float(budget_min)]
        points = np.linspace(float(budget_min), float(budget_max), num=5).tolist()
        return sorted(list({round(v, 2) for v in points}))

    def _filter_similar(self, platform: str, location: str, segment: str, age_group: str, product_type: str) -> pd.DataFrame:
        similar = self.df[
            (self.df["Channel_Used"] == platform)
            & (self.df["Location"] == location)
            & (self.df["Customer_Segment"] == segment)
            & (self.df["Target_Audience"].astype(str).str.contains(age_group, regex=False))
        ]
        if "Product_Type" in self.df.columns and product_type:
            narrowed = similar[similar["Product_Type"].astype(str) == str(product_type)]
            if len(narrowed) > 0:
                return narrowed
        return similar

    def _resolve_product_type(self, user_input: CampaignInput, segment: str) -> str:
        if user_input.product_category:
            requested = str(user_input.product_category).strip()
            if "Product_Type" in self.df.columns:
                known = [str(v) for v in self.df["Product_Type"].dropna().unique().tolist()]
                requested_lower = requested.lower()
                for value in known:
                    if value.lower() == requested_lower:
                        return value
                for value in known:
                    if requested_lower in value.lower() or value.lower() in requested_lower:
                        return value
            return requested

        if "Product_Type" in self.df.columns:
            segment_df = self.df[self.df["Customer_Segment"] == segment]
            if len(segment_df) > 0 and "ROI" in segment_df.columns:
                by_roi = segment_df.groupby("Product_Type")["ROI"].mean().sort_values(ascending=False)
                if len(by_roi) > 0:
                    return str(by_roi.index[0])
            by_count = self.df["Product_Type"].value_counts()
            if len(by_count) > 0:
                return str(by_count.index[0])

        return "General Products"

    def evaluate_combinations(self, combinations: List[Dict], campaign_goal: str) -> List[Dict]:
        """Evaluate combinations using weighted score."""
        weight_map = {
            "roi": (0.80, 0.20),
            "conversions": (0.30, 0.70),
            "traffic": (0.40, 0.60),
            "leads": (0.35, 0.65),
            "brand_awareness": (0.60, 0.40),
            "engagement": (0.45, 0.55),
        }
        alpha, beta = weight_map.get(campaign_goal, (0.50, 0.50))

        for combo in combinations:
            final_score = (alpha * combo["predicted_roi"]) + (beta * combo["predicted_conversion_rate"])
            combo["score"] = final_score * combo["confidence"]
            combo["alpha"] = alpha
            combo["beta"] = beta
            combo["final_score_raw"] = final_score

        combinations.sort(key=lambda item: item["score"], reverse=True)
        return combinations

    def generate_recommendations(self, user_input: CampaignInput) -> Dict[str, Any]:
        """Generate best recommendation per allowed platform."""
        logger.info(f"Generating recommendations for: {user_input.product_name}")

        combinations = self.generate_combinations(user_input)
        if not combinations:
            return self._fallback_recommendations(user_input)

        evaluated = self.evaluate_combinations(combinations, user_input.campaign_goal.value)

        best_by_platform: Dict[str, Dict[str, Any]] = {}
        for combo in evaluated:
            platform = combo["platform"]
            if platform not in best_by_platform:
                best_by_platform[platform] = combo

        top_recs = [best_by_platform[p] for p in ALLOWED_PLATFORMS if p in best_by_platform]
        if not top_recs:
            return self._fallback_recommendations(user_input)

        recommendations = []
        for rec in top_recs:
            roi_std = self.df.groupby("Channel_Used")["ROI"].std().get(rec["platform"], 1.0)
            risk_level = self._calculate_risk_level(rec["predicted_roi"], roi_std, rec["confidence"])
            rationale = self._generate_rationale(rec, user_input)

            expected_impressions = self._estimate_impressions(rec["platform"], rec["budget"])
            expected_clicks = int(expected_impressions * (rec["predicted_conversion_rate"] * 10))

            recommendations.append(
                CampaignRecommendation(
                    platform=rec["platform"],
                    target_location=rec["location"],
                    target_segment=rec["segment"],
                    target_age_group=rec["age_group"],
                    target_gender=user_input.target_audience.gender,
                    target_language=user_input.target_audience.language,
                    target_interests=user_input.target_audience.interests or [],
                    budget=f"${rec['budget']:,.0f}",
                    predicted_roi=round(rec["predicted_roi"], 2),
                    predicted_conversion_rate=round(rec["predicted_conversion_rate"] * 100, 2),
                    confidence=f"{rec['confidence']:.0%}",
                    rationale=rationale,
                    risk_level=risk_level,
                    expected_impressions=expected_impressions,
                    expected_clicks=expected_clicks,
                )
            )

        perf_expectations = self._calculate_performance_expectations(top_recs)
        ab_test_plan = self._generate_ab_test_plan(user_input, top_recs)
        insights = self._generate_insights(user_input, top_recs)
        data_quality = self._calculate_data_quality()
        budget_suggestion = self._build_budget_suggestion(top_recs)

        top_pref = recommendations[0].model_dump() if recommendations else {}
        return {
            "campaign_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "recommendations": [r.model_dump() for r in recommendations],
            "top_recommendation": top_pref,
            "top_preference": top_pref,
            "performance_expectations": perf_expectations.model_dump(),
            "ab_testing_plan": ab_test_plan.model_dump(),
            "insights": insights,
            "budget_suggestion": budget_suggestion,
            "data_quality_score": data_quality,
            "model_confidence": recommendations[0].confidence if recommendations else "0%",
        }

    def _build_budget_suggestion(self, top_recs: List[Dict[str, Any]]) -> Dict[str, Any]:
        budgets = [float(r["budget"]) for r in top_recs if r.get("budget") is not None]
        if not budgets:
            return {"recommended_min": 0, "recommended_max": 0, "platform_allocations": []}

        # ROI-weighted allocation:
        # Budget_i = (ROI_i / sum(ROI)) * Total Budget
        total_budget = float(sum(budgets))
        roi_values = [max(float(r.get("predicted_roi", 0.0)), 0.0) for r in top_recs]
        total_roi = sum(roi_values)

        allocations = []
        for rec, roi_i in zip(top_recs, roi_values):
            if total_roi > 0:
                allocated_budget = (roi_i / total_roi) * total_budget
                allocation_pct = (roi_i / total_roi) * 100
            else:
                allocated_budget = total_budget / max(len(top_recs), 1)
                allocation_pct = 100 / max(len(top_recs), 1)
            allocations.append(
                {
                    "platform": rec["platform"],
                    "recommended_budget": round(float(allocated_budget), 2),
                    "allocation_pct": round(float(allocation_pct), 1),
                    "predicted_roi": round(float(rec["predicted_roi"]), 2),
                }
            )

        allocated_values = [item["recommended_budget"] for item in allocations]
        return {
            "recommended_min": round(min(allocated_values), 2),
            "recommended_max": round(max(allocated_values), 2),
            "recommended_average": round(sum(allocated_values) / len(allocated_values), 2),
            "total_budget": round(total_budget, 2),
            "platform_allocations": allocations,
        }

    def _get_top_locations(self) -> List[str]:
        location_perf = self.df.groupby("Location")["ROI"].mean().sort_values(ascending=False)
        return location_perf.head(10).index.tolist()

    def _get_top_segments(self) -> List[str]:
        if "Customer_Segment" in self.df.columns:
            segment_perf = self.df.groupby("Customer_Segment")["ROI"].mean().sort_values(ascending=False)
            return segment_perf.head(10).index.tolist()
        return []

    def _get_top_age_groups(self) -> List[str]:
        if "Target_Audience" not in self.df.columns:
            return ["18-24", "25-34", "35-44"]

        data = self.df.copy()
        data["age_group"] = data["Target_Audience"].astype(str).str.extract(r"(\d{2}-\d{2})", expand=False)
        data = data.dropna(subset=["age_group"])
        if data.empty:
            return ["18-24", "25-34", "35-44"]

        age_perf = data.groupby("age_group")["ROI"].mean().sort_values(ascending=False)
        return age_perf.head(5).index.tolist()

    def _calculate_risk_level(self, predicted_roi: float, roi_std: float, confidence: float) -> str:
        if confidence < 0.5 or roi_std > predicted_roi * 0.5:
            return "High"
        if confidence < 0.7 or roi_std > predicted_roi * 0.3:
            return "Medium"
        return "Low"

    def _generate_rationale(self, rec: Dict, user_input: CampaignInput) -> str:
        rationales = [
            f"This {rec['platform']} setup matches {rec['segment']} audiences in {rec['location']}.",
            f"For {user_input.product_name}, this mix shows strong expected returns for {user_input.campaign_goal.value}.",
            f"{rec['platform']} is projected at {rec['predicted_conversion_rate']*100:.1f}% conversion with good confidence.",
            f"Budget and audience fit support this channel for scalable execution.",
        ]
        return np.random.choice(rationales)

    def _estimate_impressions(self, channel: str, budget: float) -> int:
        cpm_estimates = {
            "Google Ads": 30,
            "Instagram": 35,
            "LinkedIn Ads": 80,
        }
        cpm = cpm_estimates.get(channel, 35)
        return int((budget / 1000) * cpm * 1000)

    def _calculate_performance_expectations(self, top_recs: List[Dict]) -> PerformanceExpectations:
        roi_values = [r["predicted_roi"] for r in top_recs]
        conv_values = [r["predicted_conversion_rate"] for r in top_recs]
        return PerformanceExpectations(
            best_case_roi=round(max(roi_values), 2),
            average_case_roi=round(sum(roi_values) / len(roi_values), 2),
            worst_case_roi=round(min(roi_values), 2),
            best_case_conversion=round(max(conv_values) * 100, 2),
            average_case_conversion=round((sum(conv_values) / len(conv_values)) * 100, 2),
            worst_case_conversion=round(min(conv_values) * 100, 2),
            confidence_interval="95%",
            expected_roi_range=f"{min(roi_values):.1f} - {max(roi_values):.1f}",
            expected_conversion_range=f"{min(conv_values)*100:.1f}% - {max(conv_values)*100:.1f}%",
        )

    def _generate_ab_test_plan(self, user_input: CampaignInput, top_recs: List[Dict]) -> ABTestPlan:
        test_channels = [r["platform"] for r in top_recs]
        budget_per_channel = user_input.budget_range.average / max(1, len(test_channels))
        return ABTestPlan(
            recommended=len(top_recs) > 1,
            channels_to_test=test_channels,
            budget_per_channel=f"${budget_per_channel:,.0f}",
            test_duration_days=min(30, user_input.duration_days),
            success_metric=(
                "Conversion Rate improvement > 15%"
                if user_input.campaign_goal.value == "conversions"
                else "ROI improvement > 15%"
            ),
            minimum_detectable_effect=0.15,
        )

    def _generate_insights(self, user_input: CampaignInput, top_recs: List[Dict]) -> List[str]:
        insights: List[str] = []
        for rec in top_recs:
            channel = rec["platform"]
            channel_roi = self.df.groupby("Channel_Used")["ROI"].mean().get(channel, rec["predicted_roi"])
            channel_conv = self.df.groupby("Channel_Used")["Conversion_Rate"].mean().get(channel, rec["predicted_conversion_rate"])
            insights.append(f"{channel}: historical ROI {channel_roi:.1f}x, predicted conversion {channel_conv:.1%}")
        return insights[:5]

    def _calculate_data_quality(self) -> float:
        score = 0.0
        if len(self.df) > 10000:
            score += 0.3
        elif len(self.df) > 5000:
            score += 0.2
        elif len(self.df) > 1000:
            score += 0.1

        required_features = ["Channel_Used", "ROI", "Conversion_Rate"]
        if all(feature in self.df.columns for feature in required_features):
            score += 0.3

        if "Date" in self.df.columns:
            latest_date = pd.to_datetime(self.df["Date"]).max()
            if (datetime.now() - latest_date).days < 90:
                score += 0.2

        if self.predictor.is_trained:
            if self.predictor.metrics["roi"]["r2"] > 0.7:
                score += 0.2
            elif self.predictor.metrics["roi"]["r2"] > 0.5:
                score += 0.1
        return min(1.0, round(score, 2))

    def _fallback_recommendations(self, user_input: CampaignInput) -> Dict[str, Any]:
        logger.warning("Using fallback recommendations (ML unavailable)")
        budget = user_input.budget_range.average
        recommendations = []
        for channel in ALLOWED_PLATFORMS:
            recommendations.append(
                CampaignRecommendation(
                    platform=channel,
                    target_location=user_input.target_audience.location or "Major Markets",
                    target_segment=user_input.target_audience.customer_segment or "General",
                    target_age_group=self._get_top_age_groups()[0],
                    target_gender=user_input.target_audience.gender,
                    target_language=user_input.target_audience.language,
                    target_interests=user_input.target_audience.interests or [],
                    budget=f"${budget:,.0f}",
                    predicted_roi=5.0,
                    predicted_conversion_rate=2.5,
                    confidence="50%",
                    rationale="Rule-based recommendation due to temporary ML unavailability.",
                    risk_level="Medium",
                )
            )

        return {
            "campaign_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "recommendations": [r.model_dump() for r in recommendations],
            "top_recommendation": recommendations[0].model_dump(),
            "top_preference": recommendations[0].model_dump(),
            "performance_expectations": PerformanceExpectations(
                best_case_roi=6.0,
                average_case_roi=5.0,
                worst_case_roi=4.0,
                best_case_conversion=3.0,
                average_case_conversion=2.5,
                worst_case_conversion=2.0,
                confidence_interval="80%",
                expected_roi_range="4.0 - 6.0",
                expected_conversion_range="2.0% - 3.0%",
            ).model_dump(),
            "ab_testing_plan": ABTestPlan(
                recommended=True,
                channels_to_test=ALLOWED_PLATFORMS,
                budget_per_channel=f"${budget/3:,.0f}",
                test_duration_days=14,
                success_metric="ROI > 5.0",
                minimum_detectable_effect=0.2,
            ).model_dump(),
            "insights": ["Using rule-based recommendations due to limited data"],
            "data_quality_score": 0.3,
            "model_confidence": "50%",
        }
