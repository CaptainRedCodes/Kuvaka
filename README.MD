# KUVAKA:Lead Scoring Backend[Assignment]

A FastAPI backend service for intelligent lead scoring that combines rule-based filtering with AI-powered intent detection. Score and prioritize leads based on product/offer context for maximum conversion potential.

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

---

## Live Demo

- **API Base URL**: `https://kuvaka-1zia.onrender.com`
- **Interactive API Docs**: [https://kuvaka-1zia.onrender.com/docs](https://kuvaka-1zia.onrender.com/docs)
- **Alternative Docs**: [https://kuvaka-1zia.onrender.com/redoc](https://kuvaka-1zia.onrender.com/redoc)

---

## Features

- **Hybrid Scoring System**: Combines rule-based logic with AI-powered intent analysis
- **CSV Upload/Download**: Bulk lead processing with easy data export
- **RESTful API**: Clean, documented endpoints with automatic validation
- **PostgreSQL Integration**: Scalable data persistence
- **Interactive Documentation**: Auto-generated API docs with Swagger UI

---

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CSV Upload    │───▶│  Rule Engine    │───▶│   AI Scoring    │
│   (Bulk Leads)  │    │ (Role/Industry) │    │  (Intent Eval)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Final Scoring  │
                       │ & Prioritization│
                       └─────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend Framework** | FastAPI |
| **Database** | PostgreSQL[Deployed],SQLite[Local] |
| **ORM** | SQLAlchemy |
| **AI Model** | GROQ API |
| **Deployment** | Render |
| **Documentation** | Swagger UI + ReDoc |

---

##  Local Development Setup

### 1. Clone Repository
```bash
git https://github.com/CaptainRedCodes/Kuvaka
cd app
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# Activate virtual environment
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root:

```ini
# AI Configuration
GROQ_API_KEY=your_GROQ_api_key_here

# Optional Configuration
DEBUG=True
```
# Database Configuration
DATABASE_URL=sqlite:///./test.db   # Local SQLite for development
DATABASE_URL=postgresql://user:password@localhost/dbname  # PostgreSQL

### 5. Run Development Server
```bash
uvicorn app.main:app --reload
```

Navigate to `http://127.0.0.1:8000/docs` for interactive API documentation.


---

##  API Reference

### Upload Leads
Upload CSV file with lead data for processing.

**Endpoint**: `POST /upload`

```bash
curl -X POST "https://kuvaka-1zia.onrender.com/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@leads.csv"
```

**CSV Format**:
```csv
name,email,company,role,industry,location,linkedin_bio
John Doe,john@company.com,TechCorp,CEO,Technology,San Francisco,"Tech entrepreneur with 10+ years experience"
```

---

### Create Offer
Define your product/service offer for contextual scoring.

**Endpoint**: `POST /offer`

```bash
curl -X POST "https://kuvaka-1zia.onrender.com/api/offer" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI Sales Assistant",
    "value_props": ["Automates outreach", "Personalized engagement", "Increases conversion rates"],
    "ideal_use_cases": ["B2B sales teams", "Lead nurturing", "Customer acquisition"]
  }'
```

---

### Score Leads
Trigger intelligent scoring for uploaded leads against specific offer.

**Endpoint**: `POST /score`

```bash
curl -X POST "https://kuvaka-1zia.onrender.com/api/score" \
  -H "Content-Type: application/json" \
  -d '{"offer_name": 'AI Sales Assistant'}'
```

---

### Get Results
Retrieve scoring results with detailed breakdown.

**Endpoint**: `GET /results`

```bash
curl "https://kuvaka-1zia.onrender.com/api/results" \
    -H "Content-Type: application/json" \
    -d '{"offer_name": 'AI Sales Assistant'}'
```

**Response Example**:
```json
{
  "total_leads": 150,
  "high_intent": 23,
  "medium_intent": 67,
  "low_intent": 60,
  "leads": [
    {
      "name": "John Doe",
      "email": "john@company.com",
      "score": 85,
      "intent_level": "High",
      "reasoning": "CEO role (+20), Tech industry match (+10), Strong LinkedIn presence indicating authority"
    }
  ]
}
```

---

### Download Results
Export scored leads as CSV file.

**Endpoint**: `GET /download`

```bash
curl -X POST "https://kuvaka-1zia.onrender.com/api/download" \
    -H "Content-Type: application/json" \
    -d '{"offer_name": "AI Sales Assistant"}'

```


## FastAPI Documentation Features

This project leverages FastAPI's powerful auto-documentation capabilities:

###  Interactive API Documentation

FastAPI automatically generates two types of interactive documentation:

1. **Swagger UI** (`/docs`): 
   - Interactive interface to test API endpoints
   - Request/response examples
   - Built-in authentication testing
   - Real-time API exploration

2. **ReDoc** (`/redoc`):
   - Clean, print-friendly documentation
   - Detailed schema information
   - Code examples in multiple languages

### Documentation Features Used

- **Request/Response Models**: Pydantic models auto-generate schema
- **HTTP Status Codes**: Explicit response code documentation
- **Request Examples**: Sample payloads for each endpoint
- **Error Handling**: Documented error responses
- **Tags & Descriptions**: Organized endpoint grouping



## Example AI Scoring Prompt

```text
You are an expert sales lead analyst. Evaluate this lead's buying intent:

**Lead Profile:**
- Name: {name}
- Role: {role} 
- Company: {company}
- Industry: {industry}
- Location: {location}
- LinkedIn Bio: {linkedin_bio}

**Offer Context:**
- Product: {offer_name}
- Value Props: {value_propositions}
- Ideal Use Cases: {use_cases}

**Task:** 
Rate buying intent (0-50) considering role authority, industry fit, and bio indicators.
Provide specific reasoning for your score.

**Response Format:**
Score: [0-50]
Reasoning: [specific justification]
```

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Render Deployment Guide](https://render.com/docs)

---

##  Support

If you encounter any issues or have questions:

1. Check the [API Documentation](https://kuvaka-1zia.onrender.com/docs)
2. Review existing [GitHub Issues](https://github.com/CaptainRedCodes/Kuvaka)
3. Create a new issue with detailed description

---

**Built with ❤️ using FastAPI**
