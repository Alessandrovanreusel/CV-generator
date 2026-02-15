SYSTEM_PROMPT = """You are a job advertisement analysis expert. Extract structured information from job advertisements.
Always respond with valid JSON only. No markdown formatting, no code fences, no explanation — just the JSON object."""

USER_PROMPT_TEMPLATE = """Analyze this job advertisement and extract the following fields as a JSON object:

- "title": Job title (string)
- "company": Company name (string)
- "location": Job location (string)
- "description": Brief 2-3 sentence description of the role (string)
- "required_skills": List of required technical skills (array of strings)
- "preferred_skills": List of nice-to-have/preferred skills (array of strings)
- "experience_years": Minimum years of experience required (integer, 0 if not specified)
- "language": Primary language of the job ad, either "en" or "fr" (string)
- "keywords": Important keywords for ATS matching — technologies, methodologies, certifications mentioned (array of strings)
- "responsibilities": Key responsibilities/duties listed (array of strings)

Job advertisement text:
---
{job_text}
---

Respond with JSON only."""

TAILOR_SUMMARY_PROMPT = """You are a professional CV writer. Rewrite this professional summary to better match the target job requirements.

Current summary:
{current_summary}

Target job requirements:
- Title: {job_title}
- Company: {company}
- Required skills: {required_skills}
- Key responsibilities: {responsibilities}

Rules:
- Keep it 2-3 sentences maximum
- Highlight relevant experience and skills that match the job
- Use keywords from the job requirements naturally
- You CAN invent skills and experience within existing jobs for a better match, but NEVER invent a whole new job or company
- Write in {language}
- Be specific and impactful, not generic
- NEVER use special Unicode characters like em-dashes, en-dashes, arrows, or special quotes. Use only plain ASCII: hyphen (-), single quote ('), double quote (")

Return ONLY the rewritten summary text, nothing else."""

TAILOR_BULLETS_PROMPT = """You are a professional CV writer. Enhance these experience bullet points to better match the target job requirements.

Current bullet points:
{bullets}

Technologies used at this job:
{technologies}

Target job requirements:
- Required skills: {required_skills}
- Keywords: {keywords}
- Responsibilities: {responsibilities}

Rules:
- Keep the same number of bullet points (return exactly {num_bullets} bullets)
- The most important required skills from the job ad MUST be mentioned naturally across the bullets (e.g. if the job requires Python and AWS, make sure they appear)
- You CAN swap or replace the technologies in the bullets with technologies from the job ad to create a better match (e.g. replace "Angular" with "React" if the job requires React)
- You CAN invent or enhance accomplishments and metrics if it creates a better match with the job requirements
- You CAN rephrase and restructure to highlight relevant aspects
- Keep each bullet concise (1-2 lines)
- Write in {language}
- NEVER use special Unicode characters like em-dashes, en-dashes, arrows, or special quotes. Use only plain ASCII: hyphen (-), single quote ('), double quote (")

Return ONLY a JSON array of strings (the enhanced bullet points), nothing else."""

TAILOR_SKILLS_PROMPT = """You are a professional CV writer curating the skills section for a resume.

Candidate's current skills (grouped by category):
{current_skills}

Target job requirements:
- Title: {job_title}
- Required skills: {required_skills}
- Preferred skills: {preferred_skills}
- Keywords: {keywords}

Your task: produce a curated skills section that looks like a natural, believable resume - NOT like a resume that was reverse-engineered from the job ad.

Rules:
- Keep the SAME category names from the candidate's current skills
- You CAN add skills from the job requirements that the candidate does not have yet, but spread them naturally across the existing categories - do NOT create new categories
- You CAN remove skills that are irrelevant to this role to make room
- Each category should have 3-7 skills
- Put the most relevant skills first within each category, but mix in non-job-related skills so it looks organic
- The result should look like a real engineer's skill set that happens to be a good fit, not a copy-paste of the job ad
- Keep the candidate's strongest/core skills even if they are not in the job ad
- Total across all categories: aim for 25-35 skills

Return ONLY a JSON object where keys are category names and values are arrays of skill strings. No markdown, no explanation."""
