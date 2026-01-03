param(
    [Parameter(Mandatory=$false)]
    [int]$ResumeId = 42
)

Write-Host "=== Testing Candidate Kundali Parser ===" -ForegroundColor Green
Write-Host ""

Write-Host "1. Checking Ollama models..." -ForegroundColor Yellow
.\scripts\check_ollama.ps1

Write-Host ""
Write-Host "2. Testing Kundali Parser with Resume ID $ResumeId..." -ForegroundColor Yellow
Write-Host ""

# Build Python code with proper escaping
$resumeIdValue = $ResumeId.ToString()
$pythonCode = @"
from app.resumes.kundali_parser import kundali_parser
from app.core.database import SessionLocal
from app.models.resume import Resume

resume_id = $resumeIdValue
db = SessionLocal()
try:
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if resume:
        print(f'Testing with: {resume.file_name}')
        print(f'File path: {resume.file_path}')
        print('')
        print('Parsing resume...')
        kundali = kundali_parser.parse_resume(resume.file_path, text_from_pdf=resume.raw_text)
        candidate_kundali = kundali.get('candidate_kundali', {})
        print('')
        print('='*80)
        print('KUNDALI PARSING RESULTS')
        print('='*80)
        confidence = candidate_kundali.get('overall_confidence_score', 0.0)
        print(f'Overall Confidence: {confidence:.2f}')
        identity = candidate_kundali.get('identity', {})
        name = identity.get('name', 'unknown')
        print(f'Name: {name}')
        experience = candidate_kundali.get('experience', [])
        print(f'Experience Entries: {len(experience)}')
        projects = candidate_kundali.get('projects', [])
        print(f'Projects: {len(projects)}')
        skills = candidate_kundali.get('skills', {})
        skill_categories = len([k for k, v in skills.items() if v])
        print(f'Skills Categories: {skill_categories}')
        has_personality = bool(candidate_kundali.get('personality_inference'))
        personality_status = 'Yes' if has_personality else 'No'
        print(f'Personality Inference: {personality_status}')
        if has_personality:
            personality = candidate_kundali.get('personality_inference', {})
            work_style = personality.get('work_style', 'unknown')
            ownership = personality.get('ownership_level', 'unknown')
            personality_conf = personality.get('confidence', 0.0)
            print(f'  - Work Style: {work_style}')
            print(f'  - Ownership Level: {ownership}')
            print(f'  - Confidence: {personality_conf:.2f}')
    else:
        print(f'Resume ID {resume_id} not found')
finally:
    db.close()
"@

docker-compose exec backend python -c $pythonCode

Write-Host ""
Write-Host "✅ Test complete!" -ForegroundColor Green
