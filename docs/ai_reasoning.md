# AI Reasoning & Explainability

## Overview

HireLens AI's core differentiator is its explainable AI matching system. Every match score comes with a human-readable explanation that helps recruiters understand **why** a candidate is a good or bad fit.

## AI Matching Pipeline

### 1. Semantic Understanding

**Embeddings Generation:**
- Job descriptions → Vector embeddings (OpenAI `text-embedding-3-large` or Sentence Transformers)
- Candidate experience → Vector embeddings
- Skills → Normalized taxonomy

**Similarity Calculation:**
- Cosine similarity between embeddings
- Domain-specific similarity metrics
- Skill overlap analysis

### 2. Multi-Dimensional Scoring

The system calculates scores across 4 dimensions:

#### Skill Match (40% weight)
- **Required Skills Match**: Percentage of required skills present
- **Nice-to-Have Skills Match**: Bonus for additional relevant skills
- **Skill Taxonomy**: Normalized skill names (e.g., "JS" = "JavaScript")

#### Experience Relevance (25% weight)
- Years of experience vs. requirement
- Experience quality (seniority progression)
- Industry relevance

#### Project Similarity (20% weight)
- Project descriptions analyzed for relevance
- Technology stack overlap
- Domain alignment

#### Domain Familiarity (15% weight)
- Semantic similarity of experience to job description
- Industry/domain match
- Role similarity

### 3. AI Explanation Generation

**Prompt Engineering:**
The system uses carefully crafted prompts to generate explanations:

```
Analyze this candidate-job match and provide a comprehensive explanation.

JOB: [Title] at [Company]
Required Skills: [List]
Nice-to-Have Skills: [List]
Experience Required: [Years]

CANDIDATE:
Skills: [List]
Experience: [Years]
Education: [Details]

SCORES:
Overall: [Score]/100
Skill Match: [Score]/100
Experience: [Score]/100

Provide:
1. Summary (2-3 sentences)
2. Strengths (3-5 specific points)
3. Weaknesses/Gaps (3-5 specific points)
4. Recommendations (2-3 actionable items)
```

**Output Structure:**
```json
{
  "summary": "Overall assessment...",
  "strengths": [
    "Has 8 out of 10 required skills",
    "5+ years of relevant experience",
    "Strong project portfolio"
  ],
  "weaknesses": [
    "Missing React experience",
    "No cloud deployment experience"
  ],
  "recommendations": [
    "Consider skills transferability from Vue.js",
    "Assess willingness to learn React"
  ],
  "confidence_score": 0.85,
  "reasoning_quality": "high"
}
```

### 4. Confidence Levels

**High (80-100 score):**
- Strong skill match
- Experience aligns well
- Clear fit indicators

**Medium (60-79 score):**
- Partial skill match
- Some experience gaps
- Potential fit with training

**Low (<60 score):**
- Significant skill gaps
- Experience mismatch
- Not a good fit

## Explainability Features

### 1. Transparent Scoring
- Breakdown by dimension
- Weight explanation
- Percentile ranking

### 2. Actionable Insights
- Specific skill gaps identified
- Training recommendations
- Transferable skills highlighted

### 3. Business-Friendly Language
- No technical jargon
- Recruiter-focused explanations
- Clear, concise summaries

### 4. Confidence Indicators
- Confidence score (0-1)
- Reasoning quality (high/medium/low)
- Uncertainty acknowledgment

## AI Model Selection

### Primary: OpenAI GPT-4
- **Use Case**: Explanation generation
- **Why**: High-quality reasoning, natural language
- **Cost**: Per-token pricing
- **Caching**: Aggressive caching to reduce costs

### Fallback: Sentence Transformers
- **Use Case**: Embeddings when OpenAI unavailable
- **Why**: Free, local, good quality
- **Model**: `all-MiniLM-L6-v2`

### Future: Fine-tuned Models
- Custom models trained on hiring data
- Reduced API costs
- Domain-specific improvements

## Cost Optimization

1. **Caching**: All AI responses cached (hash-based keys)
2. **Batch Processing**: Group similar requests
3. **Fallback Models**: Use cheaper models when appropriate
4. **Token Limits**: Truncate inputs to essential content
5. **Rate Limiting**: Prevent excessive API calls

## Bias & Fairness

### Current Approach
- Skill-based matching (not demographic)
- Transparent scoring
- Audit logs for all decisions

### Future Enhancements
- Demographic parity analysis
- Bias detection in explanations
- Fairness metrics
- A/B testing framework

## Example Explanation

**Candidate**: Senior Python Developer
**Job**: Backend Engineer (Python, FastAPI, AWS)

**Score**: 87/100 (High Confidence)

**Summary:**
This candidate is an excellent fit for the Backend Engineer role. They have 6 years of Python experience with strong FastAPI expertise and AWS deployment experience. The candidate's project portfolio demonstrates production-grade system design.

**Strengths:**
- ✅ 9 out of 10 required skills match
- ✅ 6 years Python experience (exceeds 4-year requirement)
- ✅ Strong FastAPI and async programming experience
- ✅ Production AWS deployment experience
- ✅ Experience with microservices architecture

**Gaps:**
- ⚠️ Limited Kubernetes experience (nice-to-have)
- ⚠️ No GraphQL experience (optional requirement)

**Recommendations:**
1. Proceed to technical interview - strong technical fit
2. Assess Kubernetes knowledge in interview (can be learned)
3. Consider candidate's system design experience as major plus

**Confidence**: High (0.87)

## Technical Implementation

### Embedding Generation
```python
def generate_embedding(text: str) -> List[float]:
    # Check cache first
    cached = get_cache(f"embedding:{hash(text)}")
    if cached:
        return cached
    
    # Generate embedding
    embedding = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=text[:2000]  # Limit length
    )
    
    # Cache for 24 hours
    set_cache(f"embedding:{hash(text)}", embedding, ttl=86400)
    return embedding
```

### Explanation Generation
```python
def generate_explanation(candidate_data, job_data, scores):
    prompt = build_explanation_prompt(candidate_data, job_data, scores)
    
    response = openai_client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower = more deterministic
        max_tokens=2000
    )
    
    return parse_explanation(response.choices[0].message.content)
```

## Future Improvements

1. **Fine-tuned Models**: Train on hiring success data
2. **Multi-modal**: Analyze GitHub profiles, portfolios
3. **Real-time Updates**: Live explanation updates as data changes
4. **Comparative Analysis**: Compare candidates side-by-side
5. **Learning Loop**: Improve based on recruiter feedback

