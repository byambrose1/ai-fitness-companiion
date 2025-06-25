
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

## Features

- ✅ Strong password validation (12+ chars, mixed case, numbers, symbols)
- ✅ Welcome email automation
- ✅ Mailchimp integration for user management
- ✅ Enhanced menstrual cycle tracking
- ✅ AI-powered personalized insights
- ✅ Comprehensive food database search (UK & US foods)
- ✅ AI food analysis and recommendations
- ✅ Multiple free food database integrations
- ✅ Subscription management with Stripe
- ✅ PWA with offline capabilities
- ✅ GDPR compliance and data protection
