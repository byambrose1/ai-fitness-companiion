
import requests
import os
from typing import Dict, List, Optional
import json

class FoodDatabaseAPI:
    def __init__(self):
        self.usda_api_key = os.getenv('USDA_API_KEY', '')  # Optional - USDA works without key too
        self.edamam_app_id = os.getenv('EDAMAM_APP_ID', '')
        self.edamam_app_key = os.getenv('EDAMAM_APP_KEY', '')
        self.spoonacular_api_key = os.getenv('SPOONACULAR_API_KEY', '')
        
    def search_usda_foods(self, query: str, limit: int = 10) -> List[Dict]:
        """Search USDA FoodData Central - completely free"""
        try:
            url = "https://api.nal.usda.gov/fdc/v1/foods/search"
            params = {
                'query': query,
                'pageSize': limit
            }
            if self.usda_api_key:
                params['api_key'] = self.usda_api_key
                
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                foods = []
                for food in data.get('foods', []):
                    foods.append({
                        'id': food.get('fdcId'),
                        'name': food.get('description', ''),
                        'brand': food.get('brandOwner', ''),
                        'calories_per_100g': self._extract_calories(food.get('foodNutrients', [])),
                        'source': 'USDA',
                        'country': 'US'
                    })
                return foods
        except Exception as e:
            print(f"USDA API error: {e}")
        return []
    
    def search_open_food_facts(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Open Food Facts - completely free, includes UK foods"""
        try:
            url = "https://world.openfoodfacts.org/cgi/search.pl"
            params = {
                'search_terms': query,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': limit,
                'countries': 'United Kingdom,United States'  # Focus on UK/US
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                foods = []
                for product in data.get('products', []):
                    nutriments = product.get('nutriments', {})
                    foods.append({
                        'id': product.get('code'),
                        'name': product.get('product_name', ''),
                        'brand': product.get('brands', ''),
                        'calories_per_100g': nutriments.get('energy-kcal_100g', 0),
                        'protein_per_100g': nutriments.get('proteins_100g', 0),
                        'carbs_per_100g': nutriments.get('carbohydrates_100g', 0),
                        'fat_per_100g': nutriments.get('fat_100g', 0),
                        'source': 'OpenFoodFacts',
                        'country': product.get('countries', '').split(',')[0] if product.get('countries') else 'Unknown'
                    })
                return foods
        except Exception as e:
            print(f"Open Food Facts API error: {e}")
        return []
    
    def search_edamam_foods(self, query: str, limit: int = 10) -> List[Dict]:
        """Search Edamam - 1000 requests/month free"""
        if not self.edamam_app_id or not self.edamam_app_key:
            return []
            
        try:
            url = "https://api.edamam.com/api/food-database/v2/parser"
            params = {
                'app_id': self.edamam_app_id,
                'app_key': self.edamam_app_key,
                'ingr': query,
                'nutrition-type': 'cooking'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                foods = []
                for hint in data.get('hints', [])[:limit]:
                    food = hint.get('food', {})
                    nutrients = food.get('nutrients', {})
                    foods.append({
                        'id': food.get('foodId'),
                        'name': food.get('label', ''),
                        'brand': food.get('brand', ''),
                        'calories_per_100g': nutrients.get('ENERC_KCAL', 0),
                        'protein_per_100g': nutrients.get('PROCNT', 0),
                        'carbs_per_100g': nutrients.get('CHOCDF', 0),
                        'fat_per_100g': nutrients.get('FAT', 0),
                        'source': 'Edamam',
                        'country': 'US/UK'
                    })
                return foods
        except Exception as e:
            print(f"Edamam API error: {e}")
        return []
    
    def search_all_databases(self, query: str, limit_per_db: int = 5) -> List[Dict]:
        """Search all available databases and combine results"""
        all_foods = []
        
        # Search USDA (free, no limits)
        usda_foods = self.search_usda_foods(query, limit_per_db)
        all_foods.extend(usda_foods)
        
        # Search Open Food Facts (free, no limits)
        off_foods = self.search_open_food_facts(query, limit_per_db)
        all_foods.extend(off_foods)
        
        # Search Edamam if API keys available
        edamam_foods = self.search_edamam_foods(query, limit_per_db)
        all_foods.extend(edamam_foods)
        
        return all_foods[:15]  # Return top 15 results
    
    def _extract_calories(self, nutrients: List[Dict]) -> float:
        """Extract calories from USDA nutrient data"""
        for nutrient in nutrients:
            if nutrient.get('nutrientName') == 'Energy' or nutrient.get('nutrientId') == 1008:
                return nutrient.get('value', 0)
        return 0

# Nutrition calculator helper
class NutritionCalculator:
    @staticmethod
    def calculate_serving_nutrition(food_data: Dict, serving_size_grams: float) -> Dict:
        """Calculate nutrition for a specific serving size"""
        multiplier = serving_size_grams / 100  # Convert from per 100g
        
        return {
            'calories': round((food_data.get('calories_per_100g', 0) * multiplier), 1),
            'protein': round((food_data.get('protein_per_100g', 0) * multiplier), 1),
            'carbs': round((food_data.get('carbs_per_100g', 0) * multiplier), 1),
            'fat': round((food_data.get('fat_per_100g', 0) * multiplier), 1),
            'serving_size': f"{serving_size_grams}g"
        }

# Example usage function
def search_food_with_nutrition(query: str, serving_size: float = 100) -> Dict:
    """Search for food and return with nutrition info"""
    db = FoodDatabaseAPI()
    foods = db.search_all_databases(query)
    
    if foods:
        # Return first result with calculated nutrition
        food = foods[0]
        nutrition = NutritionCalculator.calculate_serving_nutrition(food, serving_size)
        return {
            'food_info': food,
            'nutrition': nutrition,
            'alternatives': foods[1:6]  # Show 5 alternatives
        }
    
    return {'error': 'No foods found'}
