import re
import spacy
from pdfminer.high_level import extract_text
from spacy.matcher import PhraseMatcher

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")


def extract_text_from_pdf(file_path):
    """
    Extract raw text from uploaded PDF resume
    """
    text = extract_text(file_path)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text


def load_skills_from_jobs(jobs_collection):
    """
    Dynamically collect all unique skills from jobs collection
    jobs.skills is an array, so we flatten all arrays
    """
    jobs = jobs_collection.find()

    skill_set = set()

    for job in jobs:
        skills_array = job.get("skills", [])

        for skill in skills_array:
            cleaned_skill = skill.strip().lower()

            if cleaned_skill:
                skill_set.add(cleaned_skill)

    return list(skill_set)


def extract_skills(text, jobs_collection):
    """
    Use spaCy PhraseMatcher with dynamic skills from jobs DB
    """
    dynamic_skills = load_skills_from_jobs(jobs_collection)

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

    patterns = [nlp.make_doc(skill) for skill in dynamic_skills]

    if patterns:
        matcher.add("SKILLS", patterns)

    doc = nlp(text)

    matches = matcher(doc)

    found_skills = set()

    for match_id, start, end in matches:
        found_skills.add(doc[start:end].text.lower())

    return list(found_skills)


def match_jobs(resume_text, jobs, jobs_collection):
    """
    Match extracted resume skills against each job
    """
    resume_skills = extract_skills(resume_text, jobs_collection)

    resume_set = set(resume_skills)

    results = []

    for job in jobs:

        job_skills = [skill.strip().lower() for skill in job.get("skills", [])]

        job_set = set(job_skills)

        common_skills = resume_set & job_set

        common = len(common_skills)

        total_job = len(job_set)
        total_resume = len(resume_set)

        # Weighted hybrid score
        match_percent = round(
            ((common / total_job) * 70 + (common / total_resume) * 30), 2
        ) if total_job and total_resume else 0

        # Resume relevance score
        resume_score = round(
            (common / total_resume) * 100, 2
        ) if total_resume else 0

        # Missing skills
        missing = list(job_set - resume_set)

        # Recommendation label
        if match_percent >= 85:
            recommendation = "Highly Recommended"
        elif match_percent >= 65:
            recommendation = "Good Match"
        elif match_percent >= 40:
            recommendation = "Moderate Match"
        else:
            recommendation = "Needs Improvement"

        results.append({
            "title": job.get("title", "Unknown"),
            "match": match_percent,
            "resume_score": resume_score,
            "missing_skills": missing,
            "job_skills": list(job_set),
            "matched_skills": list(common_skills),
            "recommendation": recommendation
        })

    return sorted(results, key=lambda x: x["match"], reverse=True)