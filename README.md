
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
- ✅ Subscription management with Stripe
- ✅ PWA with offline capabilities
- ✅ GDPR compliance and data protection
