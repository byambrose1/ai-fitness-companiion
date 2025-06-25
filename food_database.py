
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
import requests
import json
import os
from typing import Dict, List, Optional

class FoodDatabaseService:
    def __init__(self):
        # FoodData Central (USDA) - Free, extensive US database
        self.fdc_api_key = os.getenv('FDC_API_KEY', 'DEMO_KEY')  # Get free key from https://fdc.nal.usda.gov/api-key-signup.html
        self.fdc_base_url = "https://api.nal.usda.gov/fdc/v1"
        
        # OpenFoodFacts - Free, global database with UK foods
        self.off_base_url = "https://world.openfoodfacts.org/api/v0"
        
        # Edamam - Free tier with 100 requests/month
        self.edamam_app_id = os.getenv('EDAMAM_APP_ID', '')
        self.edamam_app_key = os.getenv('EDAMAM_APP_KEY', '')
        
    def search_food_multiple_sources(self, query: str, limit: int = 10) -> List[Dict]:
        """Search across multiple food databases"""
        results = []
        
        # Search FoodData Central (USDA)
        try:
            fdc_results = self.search_fdc(query, limit//2)
            results.extend(fdc_results)
        except Exception as e:
            print(f"FDC search error: {e}")
        
        # Search OpenFoodFacts
        try:
            off_results = self.search_openfoodfacts(query, limit//2)
            results.extend(off_results)
        except Exception as e:
            print(f"OpenFoodFacts search error: {e}")
        
        # Search Edamam if credentials available
        if self.edamam_app_id and self.edamam_app_key:
            try:
                edamam_results = self.search_edamam(query, limit//3)
                results.extend(edamam_results)
            except Exception as e:
                print(f"Edamam search error: {e}")
        
        return results[:limit]
    
    def search_fdc(self, query: str, limit: int = 5) -> List[Dict]:
        """Search USDA FoodData Central"""
        url = f"{self.fdc_base_url}/foods/search"
        params = {
            'api_key': self.fdc_api_key,
            'query': query,
            'pageSize': limit,
            'dataType': ['Foundation', 'SR Legacy']
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for food in data.get('foods', []):
            nutrients = {}
            for nutrient in food.get('foodNutrients', []):
                name = nutrient.get('nutrientName', '').lower()
                value = nutrient.get('value', 0)
                unit = nutrient.get('unitName', '')
                
                if 'energy' in name or 'calorie' in name:
                    nutrients['calories'] = f"{value} {unit}"
                elif 'protein' in name:
                    nutrients['protein'] = f"{value}g"
                elif 'carbohydrate' in name:
                    nutrients['carbs'] = f"{value}g"
                elif 'fat' in name and 'total' in name:
                    nutrients['fat'] = f"{value}g"
                elif 'fiber' in name:
                    nutrients['fiber'] = f"{value}g"
            
            results.append({
                'name': food.get('description', ''),
                'source': 'USDA FoodData Central',
                'nutrients': nutrients,
                'serving_size': '100g',
                'brand': food.get('brandOwner', ''),
                'category': food.get('foodCategory', '')
            })
        
        return results
    
    def search_openfoodfacts(self, query: str, limit: int = 5) -> List[Dict]:
        """Search OpenFoodFacts database"""
        url = f"{self.off_base_url}/product/{query}.json"
        
        # For search, use the search endpoint
        search_url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            'search_terms': query,
            'search_simple': 1,
            'action': 'process',
            'json': 1,
            'page_size': limit,
            'countries': 'United Kingdom'  # Prioritize UK products
        }
        
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for product in data.get('products', []):
            nutrients = {}
            nutriments = product.get('nutriments', {})
            
            # Extract key nutritional information
            if 'energy-kcal_100g' in nutriments:
                nutrients['calories'] = f"{nutriments['energy-kcal_100g']} kcal"
            if 'proteins_100g' in nutriments:
                nutrients['protein'] = f"{nutriments['proteins_100g']}g"
            if 'carbohydrates_100g' in nutriments:
                nutrients['carbs'] = f"{nutriments['carbohydrates_100g']}g"
            if 'fat_100g' in nutriments:
                nutrients['fat'] = f"{nutriments['fat_100g']}g"
            if 'fiber_100g' in nutriments:
                nutrients['fiber'] = f"{nutriments['fiber_100g']}g"
            
            results.append({
                'name': product.get('product_name', ''),
                'source': 'OpenFoodFacts',
                'nutrients': nutrients,
                'serving_size': '100g',
                'brand': product.get('brands', ''),
                'category': product.get('categories_tags', [])
            })
        
        return results
    
    def search_edamam(self, query: str, limit: int = 3) -> List[Dict]:
        """Search Edamam Food Database"""
        url = "https://api.edamam.com/api/food-database/v2/parser"
        params = {
            'app_id': self.edamam_app_id,
            'app_key': self.edamam_app_key,
            'ingr': query,
            'limit': limit
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for hint in data.get('hints', []):
            food = hint.get('food', {})
            nutrients = food.get('nutrients', {})
            
            formatted_nutrients = {}
            if 'ENERC_KCAL' in nutrients:
                formatted_nutrients['calories'] = f"{nutrients['ENERC_KCAL']} kcal"
            if 'PROCNT' in nutrients:
                formatted_nutrients['protein'] = f"{nutrients['PROCNT']}g"
            if 'CHOCDF' in nutrients:
                formatted_nutrients['carbs'] = f"{nutrients['CHOCDF']}g"
            if 'FAT' in nutrients:
                formatted_nutrients['fat'] = f"{nutrients['FAT']}g"
            if 'FIBTG' in nutrients:
                formatted_nutrients['fiber'] = f"{nutrients['FIBTG']}g"
            
            results.append({
                'name': food.get('label', ''),
                'source': 'Edamam',
                'nutrients': formatted_nutrients,
                'serving_size': '100g',
                'brand': food.get('brand', ''),
                'category': food.get('category', '')
            })
        
        return results
    
    def get_uk_specific_foods(self, query: str) -> List[Dict]:
        """Get UK-specific food items"""
        uk_foods = [
            {
                'name': 'Tesco Chicken Breast',
                'source': 'UK Retail',
                'nutrients': {'calories': '165 kcal', 'protein': '31g', 'carbs': '0g', 'fat': '3.6g'},
                'serving_size': '100g',
                'brand': 'Tesco'
            },
            {
                'name': 'Sainsbury\'s Wholemeal Bread',
                'source': 'UK Retail',
                'nutrients': {'calories': '247 kcal', 'protein': '9g', 'carbs': '45g', 'fat': '4g'},
                'serving_size': '100g',
                'brand': 'Sainsbury\'s'
            },
            {
                'name': 'Marks & Spencer Salmon Fillet',
                'source': 'UK Retail',
                'nutrients': {'calories': '208 kcal', 'protein': '25g', 'carbs': '0g', 'fat': '12g'},
                'serving_size': '100g',
                'brand': 'M&S'
            }
        ]
        
        # Filter based on query
        filtered_foods = [food for food in uk_foods 
                         if query.lower() in food['name'].lower()]
        
        return filtered_foods
    
    def analyze_food_with_ai(self, food_name: str, context: str = "") -> Dict:
        """Use OpenAI to analyze food choices"""
        try:
            import openai
            
            prompt = f"""
            Analyze this food choice for someone on a fat loss journey:
            
            Food: {food_name}
            Context: {context}
            
            Provide a brief analysis covering:
            1. Nutritional benefits
            2. How it fits into a fat loss diet
            3. Suggested portion size
            4. Best time to eat it
            
            Keep response under 100 words, supportive tone.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150
            )
            
            return {
                'analysis': response.choices[0].message.content,
                'food': food_name,
                'timestamp': json.dumps({"timestamp": "now"})
            }
            
        except Exception as e:
            return {
                'analysis': f"Analysis unavailable: {str(e)}",
                'food': food_name,
                'timestamp': json.dumps({"timestamp": "now"})
            }

# Initialize the service
food_db = FoodDatabaseService()
