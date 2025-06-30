# Fitness Companion App

## Environment Variables Setup

To enable all features, add these environment variables in your Replit Secrets:

### Email Services
```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Mailchimp Integration
```
MAILCHIMP_API_KEY=your-mailchimp-api-key
MAILCHIMP_SERVER=us1
MAILCHIMP_LIST_ID=your-list-id
```

### OpenAI & Stripe
```
OPENAI_API_KEY=your-openai-api-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
```

### Food Database APIs (All Free)
```
# USDA FoodData Central (Free - Get key at https://fdc.nal.usda.gov/api-key-signup.html)
FDC_API_KEY=your-fdc-api-key

# Edamam Food Database (Free tier - 100 requests/month)
EDAMAM_APP_ID=your-edamam-app-id
EDAMAM_APP_KEY=your-edamam-app-key
```

### Food Database APIs (Optional - enhance nutrition tracking)
```
# USDA Food Data Central (Free, no key required)
USDA_API_KEY=optional-for-higher-limits

# Edamam Food Database (1000 requests/month free)
EDAMAM_APP_ID=your-edamam-app-id
EDAMAM_APP_KEY=your-edamam-app-key

# Spoonacular (150 requests/day free)
SPOONACULAR_API_KEY=your-spoonacular-key
```

### Security
```
FLASK_SECRET_KEY=your-secure-random-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password
```

### Fitness Tracker APIs (Automatic Sync)
```
# Fitbit API (Free - 150 requests/hour per user)
# Get at: https://dev.fitbit.com/apps
FITBIT_CLIENT_ID=your-fitbit-client-id
FITBIT_CLIENT_SECRET=your-fitbit-client-secret

# Oura Ring API (Free tier - 100 requests/day)
# Get at: https://cloud.ouraring.com/oauth/applications
OURA_CLIENT_ID=your-oura-client-id
OURA_CLIENT_SECRET=your-oura-client-secret

# Google Fit API (Free)
# Get at: https://console.developers.google.com/
GOOGLE_FIT_CLIENT_ID=your-google-fit-client-id
GOOGLE_FIT_CLIENT_SECRET=your-google-fit-client-secret

# Garmin Connect IQ API (Coming soon)
GARMIN_CONSUMER_KEY=your-garmin-consumer-key
GARMIN_CONSUMER_SECRET=your-garmin-consumer-secret
```

### Additional Enhancement APIs (Optional)
```
# Weather API for workout recommendations (Free - 1000 calls/day)
OPENWEATHER_API_KEY=your-openweather-api-key

# Nutrition Label API for packaged foods (Free tier - 100 calls/day)
# Get free key at: https://rapidapi.com/spoonacular/api/nutrition-label
NUTRITION_LABEL_API_KEY=your-rapidapi-key

# Nutritionix API alternative (Free tier - 200 calls/day)
# Get at: https://www.nutritionix.com/business/api
NUTRITIONIX_APP_ID=your-nutritionix-app-id
NUTRITIONIX_APP_KEY=your-nutritionix-app-key

# Google Maps API for location-based workout suggestions (Free tier)
GOOGLE_MAPS_API_KEY=your-google-maps-key
```

## Features

- ✅ Strong password validation (12+ chars, mixed case, numbers, symbols)
- ✅ Welcome email automation
- ✅ Mailchimp integration for user management
- ✅ Enhanced menstrual cycle tracking
- ✅ AI-powered personalized insights
- ✅ Comprehensive food database search (UK & US foods)
- ✅ AI food analysis and recommendations
- ✅ Multiple free food database integrations
- ✅ **Automatic fitness tracker sync** (Fitbit, Oura, Google Fit)
- ✅ **OAuth-based device connections** with secure token management
- ✅ **Real-time device data integration** for AI analysis
- ✅ Subscription management with Stripe
- ✅ PWA with offline capabilities
- ✅ GDPR compliance and data protection