from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from dataclasses import dataclass
from ..config import client
from typing import Any, List, Dict, Tuple, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ScoringWeights:
    DECISION_MAKER_SCORE: int = 30
    INFLUENCER_SCORE: int = 15
    EXACT_ICP_SCORE: int = 25
    ADJACENT_ICP_SCORE: int = 10
    COMPLETENESS_SCORE: int = 10
    AI_HIGH_SCORE: int = 50
    AI_MEDIUM_SCORE: int = 30
    AI_LOW_SCORE: int = 10

class Scoring:
    def __init__(self):
        self.batch_size = 10
        self.max_workers = 3
        self.weights = ScoringWeights()
        self.decision_makers = {
            'ceo', 'cto', 'cfo', 'president', 'founder', 'co-founder',
            'head of', 'director', 'vp', 'chief', 'owner'
        }
        self.influencers = {
            'manager', 'senior', 'lead', 'architect', 'principal'
        }
        self.required_fields = {'name', 'role', 'company', 'industry'}

    def _role_score(self, role: str) -> int:
        if not role:
            return 0
            
        role_clean = role.lower().strip()
        
        if any(dm in role_clean for dm in self.decision_makers):
            return self.weights.DECISION_MAKER_SCORE
            
        if any(inf in role_clean for inf in self.influencers):
            return self.weights.INFLUENCER_SCORE
            
        return 0

    def _industry_score(self, industry: str, offer_data: Dict) -> int:
        if not industry or not offer_data:
            return 0
        
        ideal_use_cases = offer_data.get('ideal_use_cases', [])
        if not ideal_use_cases:
            return 0
        
        industry_lower = industry.lower().strip()
        
        for use_case in ideal_use_cases:
            use_case_lower = str(use_case).lower().strip()
            
            if industry_lower == use_case_lower:
                return self.weights.EXACT_ICP_SCORE
            
            industry_keywords = industry_lower.split()
            use_case_keywords = use_case_lower.split()
            common_keywords = set(industry_keywords) & set(use_case_keywords)
            
            if common_keywords:
                return self.weights.ADJACENT_ICP_SCORE
            
            if any(k in use_case_lower for k in industry_keywords) or any(k in industry_lower for k in use_case_keywords):
                return self.weights.ADJACENT_ICP_SCORE
        
        return 0

    def _completeness_score(self, prospect: Dict) -> int:
        filled_count = sum(1 for field in self.required_fields 
                          if prospect.get(field, '').strip())
        
        if filled_count == len(self.required_fields):
            return self.weights.COMPLETENESS_SCORE
        return 0

    def calculate_rule_score(self, prospect: Dict, offer_data: Dict) -> int:
        role_score = self._role_score(prospect.get('role', ''))
        industry_score = self._industry_score(prospect.get('industry', ''), offer_data)
        completeness_score = self._completeness_score(prospect)
        
        total = role_score + industry_score + completeness_score
        return total

    def ai_intent_score(self, prospect: Dict, offer_data: Dict) -> Tuple[str, int, str]:
        try:
            offer_data = self._normalize_offer_data(offer_data)
            
            value_props = offer_data.get('value_props', [])
            ideal_use_cases = offer_data.get('ideal_use_cases', [])
            
            offer_info = f"""
Product: {offer_data.get('name', 'N/A')}
Value Props: {', '.join(value_props) if value_props else 'N/A'}
Ideal Use Cases: {', '.join(ideal_use_cases) if ideal_use_cases else 'N/A'}
            """.strip()
            
            linkedin_bio = str(prospect.get('linkedin_bio', 'N/A'))[:200]
            
            prompt = f"""Analyze this prospect's fit for our offer:

OFFER:
{offer_info}

PROSPECT:
Name: {prospect.get('name', 'N/A')}
Role: {prospect.get('role', 'N/A')}
Company: {prospect.get('company', 'N/A')}
Industry: {prospect.get('industry', 'N/A')}
Location: {prospect.get('location', 'N/A')}
LinkedIn Bio: {linkedin_bio}

Classify their purchase intent as HIGH, MEDIUM, or LOW based on role authority, industry fit, and likely need.

Respond with: [HIGH/MEDIUM/LOW] - [brief explanation]"""

            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.1,
                timeout=15
            )

            response = completion.choices[0].message.content.strip()
            
            if "HIGH" in response.upper():
                return ("High", self.weights.AI_HIGH_SCORE, response.split('-', 1)[-1].strip())
            elif "MEDIUM" in response.upper():
                return ("Medium", self.weights.AI_MEDIUM_SCORE, response.split('-', 1)[-1].strip())
            else:
                return ("Low", self.weights.AI_LOW_SCORE, response.split('-', 1)[-1].strip())
                
        except Exception as e:
            logger.warning(f"AI scoring failed: {str(e)}")
            return ("Low", self.weights.AI_LOW_SCORE, f"AI unavailable: {str(e)}")

    def ai_intent_score_bulk(self, prospects: List[Dict], offer_data: Dict) -> List[Tuple[str, int, str]]:
        if not prospects:
            return []
            
        offer_data = self._normalize_offer_data(offer_data)
        
        batches = [prospects[i:i + self.batch_size] 
                  for i in range(0, len(prospects), self.batch_size)]
        
        all_results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_batch = {
                executor.submit(self._process_batch, batch, offer_data): batch 
                for batch in batches
            }
            
            for future in as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    batch_results = future.result(timeout=30)
                    all_results.extend(batch_results)
                except Exception as e:
                    logger.warning(f"Batch processing failed: {str(e)}")
                    fallback_results = [
                        ("Low", self.weights.AI_LOW_SCORE, f"Batch failed: {str(e)}")
                        for _ in batch
                    ]
                    all_results.extend(fallback_results)
        
        return all_results
    
    def _process_batch(self, prospects_batch: List[Dict], offer_data: Dict) -> List[Tuple[str, int, str]]:
        try:
            prompt = self._build_batch_prompt(prospects_batch, offer_data)
            
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.1,
                timeout=30
            )

            response = completion.choices[0].message.content.strip()
            return self._parse_batch_response(response, len(prospects_batch))
            
        except Exception as e:
            logger.warning(f"Batch AI scoring failed: {str(e)}")
            return [
                ("Low", self.weights.AI_LOW_SCORE, f"AI unavailable: {str(e)}")
                for _ in prospects_batch
            ]
    
    def _build_batch_prompt(self, prospects_batch: List[Dict], offer_data: Dict) -> str:
        value_props = offer_data.get('value_props', [])
        ideal_use_cases = offer_data.get('ideal_use_cases', [])
        
        offer_info = f"""
Product: {offer_data.get('name', 'N/A')}
Value Props: {', '.join(value_props) if value_props else 'N/A'}
Ideal Use Cases: {', '.join(ideal_use_cases) if ideal_use_cases else 'N/A'}
        """.strip()
        
        prospects_info = ""
        for i, prospect in enumerate(prospects_batch, 1):
            prospects_info += f"""
PROSPECT {i}:
Name: {prospect.get('name', 'N/A')}
Role: {prospect.get('role', 'N/A')}
Company: {prospect.get('company', 'N/A')}
Industry: {prospect.get('industry', 'N/A')}
Location: {prospect.get('location', 'N/A')}
LinkedIn Bio: {str(prospect.get('linkedin_bio', 'N/A'))[:150]}...

"""
        
        prompt = f"""Analyze these prospects' fit for our offer:

OFFER:
{offer_info}

PROSPECTS:
{prospects_info}

For EACH prospect, classify their purchase intent as:
- HIGH: Perfect fit, likely decision maker, strong need indicated
- MEDIUM: Good fit with some alignment, potential interest  
- LOW: Poor fit, unlikely to be interested or able to buy

IMPORTANT: Respond with EXACTLY this format for each prospect:
PROSPECT 1: [HIGH/MEDIUM/LOW] - [brief 1-sentence explanation]
PROSPECT 2: [HIGH/MEDIUM/LOW] - [brief 1-sentence explanation]
(continue for all prospects...)

Do not include any other text or formatting."""

        return prompt
    
    def _parse_batch_response(self, response: str, expected_count: int) -> List[Tuple[str, int, str]]:
        results = []
        lines = [line.strip() for line in response.split('\n') if line.strip()]
        
        for i in range(expected_count):
            try:
                prospect_line = None
                for line in lines:
                    if f"PROSPECT {i+1}:" in line.upper():
                        prospect_line = line
                        break
                
                if prospect_line:
                    if "HIGH" in prospect_line.upper():
                        intent = "High"
                        score = self.weights.AI_HIGH_SCORE
                    elif "MEDIUM" in prospect_line.upper():
                        intent = "Medium"
                        score = self.weights.AI_MEDIUM_SCORE
                    else:
                        intent = "Low"
                        score = self.weights.AI_LOW_SCORE
                    
                    reasoning = prospect_line.split('-', 1)[-1].strip() if '-' in prospect_line else prospect_line
                    results.append((intent, score, reasoning))
                else:
                    results.append(("Low", self.weights.AI_LOW_SCORE, "Could not parse AI response"))
                    
            except Exception as e:
                logger.warning(f"Error parsing prospect {i+1}: {str(e)}")
                results.append(("Low", self.weights.AI_LOW_SCORE, f"Parse error: {str(e)}"))
        
        return results
    
    def _normalize_offer_data(self, offer_data: Any) -> Dict:
        if not isinstance(offer_data, dict):
            if hasattr(offer_data, 'name'):
                return {
                    "name": getattr(offer_data, "name", "N/A"),
                    "value_props": getattr(offer_data, "value_props", []) or [],
                    "ideal_use_cases": getattr(offer_data, "ideal_use_cases", []) or [],
                }
            elif isinstance(offer_data, list):
                return {
                    "name": "N/A",
                    "value_props": [],
                    "ideal_use_cases": offer_data,
                }
            else:
                return {
                    "name": str(offer_data),
                    "value_props": [],
                    "ideal_use_cases": [],
                }
        
        normalized_offer = dict(offer_data)
        
        value_props = normalized_offer.get('value_props', [])
        ideal_use_cases = normalized_offer.get('ideal_use_cases', [])
        
        if not isinstance(value_props, list):
            value_props = [str(value_props)] if value_props else []
        if not isinstance(ideal_use_cases, list):
            ideal_use_cases = [str(ideal_use_cases)] if ideal_use_cases else []
            
        normalized_offer['value_props'] = value_props
        normalized_offer['ideal_use_cases'] = ideal_use_cases
        
        return normalized_offer

    def final_score_bulk(self, leads: List[Dict], offer_data: Dict) -> List[Tuple[str, int, str]]:
        if not leads:
            return []
        
        offer_data = self._normalize_offer_data(offer_data)
        ai_results = self.ai_intent_score_bulk(leads, offer_data)
        
        final_results = []
        for i, (intent, ai_score, reasoning) in enumerate(ai_results):
            rule_score = self.calculate_rule_score(leads[i], offer_data)
            final_score = rule_score + ai_score
            
            logger.info(f"Lead {i+1}: {leads[i].get('name', 'Unknown')} - "
                       f"Final Score: {final_score} (Rule: {rule_score} + AI: {ai_score}) - Intent: {intent}")
            
            final_results.append((intent, final_score, reasoning))
        
        return final_results
    
    def final_score(self, prospect: Dict, offer_data: Dict) -> Tuple[str, int, str]:
        logger.info(f"Scoring: {prospect.get('name', 'Unknown')} at {prospect.get('company', 'Unknown')}")
        
        offer_data = self._normalize_offer_data(offer_data)
        rule_score = self.calculate_rule_score(prospect, offer_data)
        intent, ai_score, reasoning = self.ai_intent_score(prospect, offer_data)
        
        total_score = rule_score + ai_score
        
        logger.info(f"Final score: {total_score} (Rule: {rule_score} + AI: {ai_score}) - Intent: {intent}")
        
        return intent, total_score, reasoning