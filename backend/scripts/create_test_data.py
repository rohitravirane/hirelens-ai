"""
Script to create comprehensive test data for development
"""
import sys
from pathlib import Path
import random
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, Role
from app.models.job import JobDescription
from app.models.resume import Resume, ResumeVersion
from app.models.candidate import Candidate
from app.models.matching import MatchResult, AIExplanation
from app.auth.service import get_password_hash
from faker import Faker
import structlog

logger = structlog.get_logger()
fake = Faker()

# Sample data pools
JOB_TITLES = [
    "Senior Backend Engineer", "Full Stack Developer", "Frontend Developer",
    "DevOps Engineer", "Data Scientist", "Machine Learning Engineer",
    "Product Manager", "UX Designer", "QA Engineer", "Security Engineer",
    "Cloud Architect", "Mobile Developer", "Backend Developer", "Software Architect",
    "Technical Lead", "Engineering Manager", "Data Engineer", "AI Researcher"
]

COMPANIES = [
    "Tech Corp", "Innovate Labs", "Digital Solutions", "Cloud Systems",
    "Data Dynamics", "Code Masters", "Future Tech", "Smart Innovations",
    "Global Software", "NextGen Technologies", "Elite Developers", "Prime Solutions",
    "Apex Systems", "Vertex Technologies", "Quantum Computing", "Neural Networks Inc"
]

DEPARTMENTS = ["Engineering", "Product", "Data Science", "Design", "DevOps", "Security", "Research"]

SKILLS_POOL = [
    "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#",
    "react", "vue", "angular", "node.js", "django", "flask", "fastapi", "spring",
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "aws", "azure", "gcp",
    "docker", "kubernetes", "terraform", "jenkins", "git", "graphql", "rest api",
    "machine learning", "deep learning", "tensorflow", "pytorch", "pandas", "numpy",
    "agile", "scrum", "ci/cd", "microservices", "system design", "algorithms", "data structures"
]

SENIORITY_LEVELS = ["junior", "mid", "senior", "lead", "principal"]
EMPLOYMENT_TYPES = ["full-time", "part-time", "contract", "internship"]
LOCATIONS = [
    "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
    "Boston, MA", "Chicago, IL", "Remote", "London, UK", "Toronto, Canada"
]

STATUSES = ["new", "screening", "interview", "offer", "rejected", "hired"]

EDUCATION_DEGREES = ["Bachelor's", "Master's", "PhD", "Associate's", "Diploma"]
EDUCATION_FIELDS = ["Computer Science", "Software Engineering", "Information Technology", "Data Science", "Mathematics", "Electrical Engineering"]


def create_test_users(db: Session):
    """Create test users with different roles"""
    admin = db.query(User).filter(User.email == "admin@hirelens.ai").first()
    if not admin:
        logger.warning("admin_user_not_found")
        return None
    
    # Get roles
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    recruiter_role = db.query(Role).filter(Role.name == "recruiter").first()
    hiring_manager_role = db.query(Role).filter(Role.name == "hiring_manager").first()
    
    # Create additional test users
    test_users = []
    for i in range(5):
        email = f"recruiter{i+1}@test.com"
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            user = User(
                email=email,
                hashed_password=get_password_hash("password123"),
                full_name=fake.name(),
                is_active=True,
                is_verified=True,
            )
            user.roles = [recruiter_role] if recruiter_role else []
            db.add(user)
            test_users.append(user)
            logger.info("test_user_created", email=email)
    
    for i in range(3):
        email = f"manager{i+1}@test.com"
        existing = db.query(User).filter(User.email == email).first()
        if not existing:
            user = User(
                email=email,
                hashed_password=get_password_hash("password123"),
                full_name=fake.name(),
                is_active=True,
                is_verified=True,
            )
            user.roles = [hiring_manager_role] if hiring_manager_role else []
            db.add(user)
            test_users.append(user)
            logger.info("test_user_created", email=email)
    
    db.commit()
    return admin


def create_test_jobs(db: Session, admin: User):
    """Create multiple test job descriptions"""
    jobs = []
    
    for i in range(20):  # Create 20 jobs
        title = random.choice(JOB_TITLES)
        company = random.choice(COMPANIES)
        department = random.choice(DEPARTMENTS)
        
        # Check if job already exists
        existing = db.query(JobDescription).filter(
            JobDescription.title == title,
            JobDescription.company == company
        ).first()
        if existing:
            continue
        
        # Generate skills
        num_required = random.randint(4, 8)
        num_nice_to_have = random.randint(2, 5)
        required_skills = random.sample(SKILLS_POOL, min(num_required, len(SKILLS_POOL)))
        nice_to_have_skills = random.sample(
            [s for s in SKILLS_POOL if s not in required_skills],
            min(num_nice_to_have, len(SKILLS_POOL) - num_required)
        )
        
        # Generate job description text
        raw_text = f"""
        {title} - {company}
        
        We are looking for a {title} to join our {department} team.
        
        Required Skills:
        {chr(10).join(['- ' + skill for skill in required_skills])}
        
        Nice to Have:
        {chr(10).join(['- ' + skill for skill in nice_to_have_skills])}
        
        Experience: {random.randint(2, 10)}+ years of experience required.
        Location: {random.choice(LOCATIONS)}
        Employment Type: {random.choice(EMPLOYMENT_TYPES)}
        
        About the Role:
        {fake.paragraph(nb_sentences=5)}
        
        Responsibilities:
        {chr(10).join(['- ' + fake.sentence() for _ in range(5)])}
        
        Qualifications:
        {chr(10).join(['- ' + fake.sentence() for _ in range(4)])}
        """
        
        job = JobDescription(
            title=title,
            company=company,
            department=department,
            raw_text=raw_text,
            required_skills=required_skills,
            nice_to_have_skills=nice_to_have_skills,
            experience_years_required=random.randint(2, 10),
            seniority_level=random.choice(SENIORITY_LEVELS),
            location=random.choice(LOCATIONS),
            remote_allowed=random.choice([True, False]),
            employment_type=random.choice(EMPLOYMENT_TYPES),
            created_by=admin.id,
            is_active=random.choice([True, True, True, False]),  # Mostly active
            is_archived=random.choice([False, False, False, True]),
        )
        db.add(job)
        jobs.append(job)
        logger.info("test_job_created", job_id=job.id, title=title, company=company)
    
    db.commit()
    return jobs


def create_test_resumes_and_candidates(db: Session, admin: User):
    """Create test resumes and candidates"""
    resumes = []
    candidates = []
    
    for i in range(30):  # Create 30 candidates
        # Create resume
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.email()
        phone = fake.phone_number()
        
        # Generate resume text
        years_exp = random.randint(1, 15)
        skills = random.sample(SKILLS_POOL, random.randint(5, 15))
        
        resume_text = f"""
        {first_name} {last_name}
        {email} | {phone}
        {fake.address()}
        LinkedIn: linkedin.com/in/{fake.user_name()}
        
        PROFESSIONAL SUMMARY
        {fake.paragraph(nb_sentences=3)}
        
        EXPERIENCE ({years_exp} years)
        """
        
        # Add work experience
        for j in range(random.randint(2, 5)):
            company = fake.company()
            role = random.choice(JOB_TITLES)
            start_date = fake.date_between(start_date='-10y', end_date='-1y')
            end_date = fake.date_between(start_date=start_date, end_date='today')
            resume_text += f"""
        
        {role} at {company}
        {start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}
        {chr(10).join(['- ' + fake.sentence() for _ in range(random.randint(3, 6))])}
        """
        
        resume_text += f"""
        
        EDUCATION
        {random.choice(EDUCATION_DEGREES)} in {random.choice(EDUCATION_FIELDS)}
        {fake.company()} University
        {fake.year()}
        
        SKILLS
        {', '.join(skills)}
        
        CERTIFICATIONS
        {chr(10).join(['- ' + fake.sentence() for _ in range(random.randint(1, 3))])}
        
        PROJECTS
        {chr(10).join(['- ' + fake.sentence() for _ in range(random.randint(2, 4))])}
        """
        
        # Create resume record
        resume = Resume(
            file_name=f"resume_{i+1}.pdf",
            file_path=f"/uploads/resume_{i+1}.pdf",
            file_size=random.randint(50000, 500000),
            file_type="pdf",
            raw_text=resume_text,
            processing_status="completed",
        )
        db.add(resume)
        db.flush()  # Get the ID
        
        # Create resume version with parsed data
        resume_version = ResumeVersion(
            resume_id=resume.id,
            version_number=1,
            parsed_data={
                "name": f"{first_name} {last_name}",
                "email": email,
                "phone": phone,
                "summary": fake.paragraph(),
            },
            skills=skills,
            experience_years=years_exp,
            education=[
                {
                    "degree": random.choice(EDUCATION_DEGREES),
                    "field": random.choice(EDUCATION_FIELDS),
                    "institution": fake.company() + " University",
                    "year": fake.year(),
                }
            ],
            experience=[
                {
                    "title": random.choice(JOB_TITLES),
                    "company": fake.company(),
                    "duration": f"{random.randint(1, 5)} years",
                    "description": fake.paragraph(),
                }
                for _ in range(random.randint(2, 5))
            ],
            projects=[
                {
                    "name": fake.catch_phrase(),
                    "description": fake.sentence(),
                    "technologies": random.sample(SKILLS_POOL, random.randint(2, 5)),
                }
                for _ in range(random.randint(2, 4))
            ],
            certifications=[
                {"name": fake.catch_phrase(), "issuer": fake.company()}
                for _ in range(random.randint(1, 3))
            ],
            languages=[{"name": "English", "proficiency": "Native"}],
            is_current=True,
            parser_version="1.0",
        )
        db.add(resume_version)
        
        # Create candidate
        candidate = Candidate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            linkedin_url=f"linkedin.com/in/{fake.user_name()}",
            portfolio_url=f"https://{fake.domain_name()}" if random.choice([True, False]) else None,
            resume_id=resume.id,
            status=random.choice(STATUSES),
            notes=fake.paragraph() if random.choice([True, False]) else None,
            created_by=admin.id,
        )
        db.add(candidate)
        
        resumes.append(resume)
        candidates.append(candidate)
        logger.info("test_candidate_created", candidate_id=candidate.id, email=email)
    
    db.commit()
    return resumes, candidates


def create_match_results(db: Session, jobs: list, candidates: list):
    """Create match results between candidates and jobs"""
    match_results = []
    
    # Match each candidate with 2-5 random jobs
    for candidate in candidates:
        num_matches = random.randint(2, 5)
        selected_jobs = random.sample(jobs, min(num_matches, len(jobs)))
        
        for job in selected_jobs:
            # Check if match already exists
            existing = db.query(MatchResult).filter(
                MatchResult.candidate_id == candidate.id,
                MatchResult.job_description_id == job.id
            ).first()
            if existing:
                continue
            
            # Generate scores
            overall_score = round(random.uniform(45, 95), 2)
            skill_match_score = round(random.uniform(40, 100), 2)
            experience_score = round(random.uniform(40, 100), 2)
            project_similarity_score = round(random.uniform(35, 95), 2)
            domain_familiarity_score = round(random.uniform(30, 90), 2)
            
            confidence_level = "high" if overall_score > 80 else "medium" if overall_score > 60 else "low"
            percentile_rank = round(random.uniform(10, 95), 2)
            
            match_result = MatchResult(
                candidate_id=candidate.id,
                job_description_id=job.id,
                overall_score=overall_score,
                confidence_level=confidence_level,
                skill_match_score=skill_match_score,
                experience_score=experience_score,
                project_similarity_score=project_similarity_score,
                domain_familiarity_score=domain_familiarity_score,
                percentile_rank=percentile_rank,
                is_active=True,
            )
            db.add(match_result)
            db.flush()  # Get the ID
            
            # Create AI explanation
            strengths = [
                f"Strong experience with {random.choice(SKILLS_POOL)}",
                f"Excellent {random.choice(['problem-solving', 'communication', 'leadership'])} skills",
                f"Relevant experience in {random.choice(['agile', 'microservices', 'cloud computing'])}",
            ]
            weaknesses = [
                f"Limited experience with {random.choice(SKILLS_POOL)}",
                f"Could benefit from more {random.choice(['team leadership', 'system design', 'architecture'])} experience",
            ]
            recommendations = [
                f"Consider {random.choice(['technical interview', 'coding challenge', 'system design round'])}",
                f"Evaluate {random.choice(['cultural fit', 'communication skills', 'problem-solving approach'])}",
            ]
            
            ai_explanation = AIExplanation(
                match_result_id=match_result.id,
                summary=fake.paragraph(nb_sentences=3),
                strengths=strengths,
                weaknesses=weaknesses,
                recommendations=recommendations,
                skill_analysis={
                    "matched_skills": random.sample(SKILLS_POOL, random.randint(3, 8)),
                    "missing_skills": random.sample(SKILLS_POOL, random.randint(1, 3)),
                },
                experience_analysis={
                    "relevant_experience": random.randint(2, 8),
                    "years_match": random.choice([True, False]),
                },
                gap_analysis={
                    "primary_gaps": random.sample(SKILLS_POOL, random.randint(1, 3)),
                    "recommendations": recommendations,
                },
                confidence_score=round(random.uniform(0.6, 0.95), 2),
                reasoning_quality=random.choice(["high", "medium", "low"]),
                model_used="huggingface/mistral-7b",
            )
            db.add(ai_explanation)
            
            match_results.append(match_result)
            logger.info(
                "test_match_created",
                match_id=match_result.id,
                candidate_id=candidate.id,
                job_id=job.id,
                score=overall_score
            )
    
    db.commit()
    return match_results


def main():
    """Main function to create all test data"""
    logger.info("starting_test_data_creation")
    db: Session = SessionLocal()
    try:
        # Create users
        admin = create_test_users(db)
        if not admin:
            logger.error("admin_user_not_found_cannot_create_data")
            return
        
        # Create jobs
        jobs = create_test_jobs(db, admin)
        logger.info("jobs_created", count=len(jobs))
        
        # Create resumes and candidates
        resumes, candidates = create_test_resumes_and_candidates(db, admin)
        logger.info("candidates_created", count=len(candidates))
        
        # Create match results
        if jobs and candidates:
            match_results = create_match_results(db, jobs, candidates)
            logger.info("match_results_created", count=len(match_results))
        
        logger.info("test_data_creation_complete")
    except Exception as e:
        logger.error("test_data_creation_failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
