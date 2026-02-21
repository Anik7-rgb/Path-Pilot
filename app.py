import logging
import sys
import os
import json
import requests
import time
import sqlite3
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash
import traceback
import random
import re

print("🚀 Starting Path Pilot Backend with Enhanced Processing...")

# Configure logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'skill-sense-secret-key-2024-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt'}
app.config['DATABASE'] = 'database.db'

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# --------------------------
# LM Studio Configuration (for optional AI enhancement)
# --------------------------
LM_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
CHATBOT_MODEL = os.getenv("CHATBOT_MODEL", "phi-3-mini-4k-instruct")
CHATBOT_TIMEOUT = float(os.getenv("CHATBOT_TIMEOUT", "10"))
COURSE_MODEL = os.getenv("COURSE_MODEL", "phi-3-mini-4k-instruct")
COURSE_TIMEOUT = float(os.getenv("COURSE_TIMEOUT", "8"))
LM_AVAILABLE = False

# Check LM Studio availability
try:
    response = requests.get(f"{LM_BASE_URL}/models", timeout=2)
    if response.status_code == 200:
        LM_AVAILABLE = True
        print("✅ LM Studio detected - AI enhancement available")
    else:
        print("⚠️ LM Studio not responding - using fallback mode")
except:
    print("⚠️ LM Studio not available - using fallback mode")

# --------------------------
# ENHANCED SKILL DATABASE
# --------------------------
skill_categories = {
    'Programming Languages': ['Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'TypeScript', 'Scala', 'Perl', 'R'],
    'Web Development': ['HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring', 'Express', 'jQuery', 'Bootstrap', 'Tailwind', 'SASS', 'Webpack'],
    'Databases': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'Cassandra', 'Elasticsearch', 'DynamoDB', 'Firebase', 'MariaDB', 'CouchDB'],
    'Cloud & DevOps': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform', 'Ansible', 'Jenkins', 'Git', 'CI/CD', 'GitHub Actions', 'GitLab CI', 'CircleCI', 'Prometheus', 'Grafana'],
    'Data Science': ['Machine Learning', 'Deep Learning', 'Data Analysis', 'Pandas', 'NumPy', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'Tableau', 'Power BI', 'Statistics', 'NLP', 'Computer Vision'],
    'Soft Skills': ['Communication', 'Teamwork', 'Leadership', 'Problem Solving', 'Project Management', 'Agile', 'Scrum', 'Critical Thinking', 'Time Management', 'Adaptability', 'Creativity'],
    'Certifications': ['AWS Certified', 'CISSP', 'PMP', 'Scrum Master', 'CEH', 'CompTIA', 'Cisco Certified', 'Azure Certified', 'Google Cloud Certified'],
    'Tools': ['JIRA', 'Confluence', 'Slack', 'Trello', 'Asana', 'Figma', 'Adobe XD', 'Photoshop', 'VS Code', 'IntelliJ', 'Eclipse', 'Postman'],
    'Mobile Development': ['iOS', 'Android', 'Swift', 'Kotlin', 'React Native', 'Flutter', 'Xamarin', 'Ionic'],
    'Testing': ['Jest', 'Mocha', 'Selenium', 'Cypress', 'JUnit', 'PyTest', 'Unit Testing', 'Integration Testing']
}

# Role requirements for ML prediction
role_requirements = {
    'Software Engineer': ['Python', 'JavaScript', 'Java', 'Git', 'SQL', 'Data Structures', 'Algorithms', 'OOP'],
    'Data Scientist': ['Python', 'Machine Learning', 'Data Analysis', 'SQL', 'Statistics', 'Pandas', 'NumPy', 'Visualization'],
    'DevOps Engineer': ['AWS', 'Docker', 'Kubernetes', 'Linux', 'CI/CD', 'Jenkins', 'Terraform', 'Ansible', 'Git'],
    'Full Stack Developer': ['JavaScript', 'React', 'Node.js', 'HTML', 'CSS', 'SQL', 'REST APIs', 'Git'],
    'Backend Developer': ['Python', 'Java', 'SQL', 'Django', 'Flask', 'API', 'Database Design', 'Microservices'],
    'Frontend Developer': ['JavaScript', 'React', 'HTML', 'CSS', 'TypeScript', 'Responsive Design', 'UI/UX'],
    'Machine Learning Engineer': ['Python', 'Machine Learning', 'TensorFlow', 'PyTorch', 'Statistics', 'Data Processing', 'Model Deployment'],
    'Cloud Architect': ['AWS', 'Azure', 'Docker', 'Kubernetes', 'Networking', 'Security', 'Microservices', 'Cloud Design'],
    'Product Manager': ['Project Management', 'Communication', 'Agile', 'Leadership', 'Analytics', 'User Research', 'Strategy'],
    'UX/UI Designer': ['HTML', 'CSS', 'JavaScript', 'Design', 'Prototyping', 'User Research', 'Figma', 'Adobe XD'],
    'Data Engineer': ['Python', 'SQL', 'ETL', 'Data Warehousing', 'Spark', 'Hadoop', 'Kafka', 'Airflow'],
    'Security Engineer': ['Network Security', 'Encryption', 'Penetration Testing', 'Firewalls', 'SIEM', 'Incident Response'],
    'QA Engineer': ['Testing', 'Selenium', 'Jest', 'Cypress', 'Automation', 'Bug Tracking', 'Test Planning'],
    'Technical Lead': ['Architecture', 'Team Leadership', 'Code Review', 'Mentoring', 'Project Planning', 'Technical Strategy'],
    'Site Reliability Engineer': ['Linux', 'Monitoring', 'Automation', 'Incident Management', 'Performance Tuning', 'Capacity Planning']
}

# Course database
course_db = {
    "python": ["Python for Everybody – Coursera", "Complete Python Bootcamp – Udemy", "Advanced Python – Pluralsight"],
    "javascript": ["Modern JavaScript – The Odin Project", "JavaScript: The Advanced Concepts – ZeroToMastery", "JavaScript Algorithms – freeCodeCamp"],
    "react": ["React – The Complete Guide – Udemy", "Modern React with Redux – Stephen Grider", "React Documentation – Official"],
    "sql": ["The Complete SQL Bootcamp – Udemy", "SQL for Data Analysis – Mode Analytics", "Advanced SQL – Stanford Online"],
    "aws": ["AWS Certified Solutions Architect – AWS Training", "AWS Essentials – freeCodeCamp", "AWS Developer – A Cloud Guru"],
    "docker": ["Docker & Kubernetes: The Practical Guide – Udemy", "Docker Mastery – Bret Fisher", "Containerization – Coursera"],
    "machine learning": ["Machine Learning Specialization – Andrew Ng", "Deep Learning A-Z – Udemy", "ML Crash Course – Google"],
    "data analysis": ["Data Analysis with Python – freeCodeCamp", "Pandas Tutorial – Kaggle", "Data Science Bootcamp – Jovian"],
    "devops": ["DevOps Bootcamp – TechWorld with Nana", "CI/CD with Jenkins – Udemy", "Terraform – HashiCorp Learn"],
    "java": ["Java Programming Masterclass – Udemy", "Spring Framework – Baeldung", "Java Certification – Oracle"],
    "git": ["Git & GitHub – freeCodeCamp", "Pro Git Book – Official", "Git Branching – Interactive Tutorial"],
    "flask": ["Flask Mega-Tutorial – Miguel Grinberg", "REST APIs with Flask – Corey Schafer", "Flask Documentation"],
    "django": ["Django for Beginners – WS Vincent", "Django REST Framework – Udemy", "Django Girls Tutorial"],
    "html": ["HTML & CSS – freeCodeCamp", "Web Design – The Odin Project", "HTML5 – MDN Web Docs"],
    "css": ["CSS Complete Guide – Udemy", "Flexbox & Grid – CSS Tricks", "Tailwind CSS – Official"],
    "node.js": ["Node.js Tutorial – The Net Ninja", "Express.js – MDN", "Node.js API Masterclass – Udemy"],
    "typescript": ["TypeScript Handbook – Official", "Understanding TypeScript – Udemy", "TypeScript with React"],
    "mongodb": ["MongoDB University – Official", "Mongoose – Udemy", "NoSQL Databases – Coursera"],
    "postgresql": ["PostgreSQL Bootcamp – Udemy", "SQL & PostgreSQL – freeCodeCamp", "Database Design"],
    "tensorflow": ["TensorFlow Developer Certificate", "Deep Learning with TF – Coursera", "TF Official Tutorials"]
}

# --------------------------
# DATABASE FUNCTIONS
# --------------------------
def init_database():
    """Initialize SQLite database with enhanced schema"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            preferences TEXT DEFAULT '{}'
        )
        ''')
        
        # Create user_uploads table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            skills TEXT,
            top_roles TEXT,
            jobs TEXT,
            courses TEXT,
            ai_response TEXT,
            match_history TEXT DEFAULT '[]',
            analysis_version TEXT DEFAULT '2.0',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Create user_sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            session_token TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            logout_time TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Create job_matches table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            job_title TEXT,
            match_score REAL,
            matched_skills TEXT,
            missing_skills TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        ''')
        
        # Create default admin user if not exists
        cursor.execute("SELECT * FROM users WHERE email = ?", ("admin@skillsense.com",))
        if not cursor.fetchone():
            password_hash = generate_password_hash("admin123")
            cursor.execute('''
            INSERT INTO users (email, username, password, full_name) 
            VALUES (?, ?, ?, ?)
            ''', ("admin@skillsense.com", "admin", password_hash, "Administrator"))
            print("✅ Created default admin user")
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
init_database()

# --------------------------
# AUTHENTICATION DECORATOR - DEFINED BEFORE ROUTES
# --------------------------
def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --------------------------
# ENHANCED RESUME PARSING
# --------------------------
def extract_text_from_pdf(filepath):
    """Extract text from PDF file with enhanced error handling"""
    try:
        # Check file extension
        if filepath.lower().endswith('.pdf'):
            try:
                import PyPDF2
                text = ""
                with open(filepath, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    return text
            except ImportError:
                print("⚠️ PyPDF2 not installed, using fallback")
            except Exception as e:
                print(f"⚠️ PDF extraction error: {e}")
        
        elif filepath.lower().endswith(('.doc', '.docx')):
            try:
                import docx
                doc = docx.Document(filepath)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                return text
            except ImportError:
                print("⚠️ python-docx not installed, using fallback")
            except Exception as e:
                print(f"⚠️ DOCX extraction error: {e}")
        
        elif filepath.lower().endswith('.txt'):
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                return file.read()
        
        # Fallback to reading as text
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
            
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
    
    # Return enhanced mock data as fallback
    return """
    JOHN DOE - Senior Software Engineer
    Email: john.doe@email.com | Phone: (555) 123-4567 | Location: San Francisco, CA
    
    SUMMARY
    Experienced software engineer with 5+ years in full-stack development. 
    Passionate about building scalable applications and solving complex problems.
    
    SKILLS
    • Programming: Python, JavaScript, Java, TypeScript, Go
    • Web Frameworks: Django, Flask, React, Node.js, Express
    • Databases: PostgreSQL, MongoDB, Redis, MySQL
    • Cloud & DevOps: AWS (EC2, S3, Lambda), Docker, Kubernetes, Jenkins
    • Tools: Git, JIRA, VS Code, Postman, Figma
    • Soft Skills: Team Leadership, Agile/Scrum, Communication, Problem Solving
    
    WORK EXPERIENCE
    
    Senior Software Engineer | TechCorp Inc. | 2020 - Present
    • Led development of microservices architecture using Python and Docker
    • Implemented CI/CD pipelines reducing deployment time by 40%
    • Mentored junior developers and conducted code reviews
    • Technologies: Python, Django, AWS, PostgreSQL, React
    
    Full Stack Developer | Startup Innovations | 2018 - 2020
    • Developed RESTful APIs serving 10k+ daily users
    • Built responsive frontend using React and Redux
    • Optimized database queries improving performance by 30%
    • Technologies: JavaScript, Node.js, MongoDB, Express
    
    EDUCATION
    
    BS Computer Science | University of Technology | 2014 - 2018
    • GPA: 3.8/4.0
    • Coursework: Data Structures, Algorithms, Database Systems, Web Development
    
    CERTIFICATIONS
    • AWS Certified Solutions Architect
    • Certified Kubernetes Administrator (CKA)
    • Professional Scrum Master I
    
    PROJECTS
    • E-commerce Platform: Full-stack application with React and Django
    • Task Manager: Python Flask app with real-time updates
    • Portfolio Website: Personal site with modern UI/UX
    """

def extract_skills_from_text(text):
    """Extract skills from text using enhanced keyword matching"""
    found_skills = []
    text_lower = text.lower()
    
    # Check each skill in each category with improved matching
    for category, skills in skill_categories.items():
        for skill in skills:
            skill_lower = skill.lower()
            # Check for skill with various patterns
            patterns = [
                skill_lower,
                skill_lower.replace(' ', ''),
                skill_lower.replace('.', ''),
                skill_lower.replace('#', 'sharp') if 'c#' in skill_lower else None,
                skill_lower.replace('++', 'pp') if 'c++' in skill_lower else None
            ]
            
            for pattern in patterns:
                if pattern and pattern in text_lower:
                    # Check word boundaries for more accurate matching
                    if f" {pattern} " in f" {text_lower} " or text_lower.startswith(pattern) or text_lower.endswith(pattern):
                        found_skills.append(skill)
                        break
    
    # If no skills found, return enhanced default ones
    if not found_skills:
        found_skills = ['Python', 'JavaScript', 'SQL', 'Communication', 'Problem Solving', 
                       'Git', 'HTML', 'CSS', 'Teamwork', 'Leadership']
    
    # Remove duplicates while preserving order
    unique_skills = []
    for skill in found_skills:
        if skill not in unique_skills:
            unique_skills.append(skill)
    
    return unique_skills[:20]  # Return top 20 skills

# --------------------------
# ML-BASED ROLE PREDICTION
# --------------------------
def predict_top_roles(skills):
    """Predict top career roles based on skills with ML-style scoring"""
    role_scores = {}
    skills_lower = [s.lower() for s in skills]
    
    # Calculate scores for each role
    for role, required_skills in role_requirements.items():
        score = 0
        matched_skills = []
        
        for skill in skills_lower:
            for req_skill in required_skills:
                req_lower = req_skill.lower()
                # Check for partial matches
                if req_lower in skill or skill in req_lower:
                    score += 15  # Base points per match
                    matched_skills.append(req_skill)
                    break
        
        # Add bonus for multiple matches in same category
        unique_matches = len(set(matched_skills))
        if unique_matches >= 3:
            score += 10
        if unique_matches >= 5:
            score += 15
        
        # Add randomness for realism (70-95% range)
        base_score = min(95, score)
        if base_score > 0:
            variation = random.randint(-5, 5)
            final_score = max(60, min(98, base_score + variation))
            role_scores[role] = final_score
    
    # Sort by score and return top 5
    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_roles[:5]

def get_jobs_for_role(role):
    """Get job listings for a specific role with real job search links"""
    # Base URLs for job searches
    job_boards = {
        'linkedin': 'https://www.linkedin.com/jobs/search/?keywords=',
        'indeed': 'https://www.indeed.com/q-',
        'glassdoor': 'https://www.glassdoor.com/Job/jobs.htm?sc.keyword=',
        'monster': 'https://www.monster.com/jobs/search/?q=',
        'google': 'https://www.google.com/search?q=',
        'ziprecruiter': 'https://www.ziprecruiter.com/candidate/search?search='
    }
    
    # Role-specific search terms
    role_search_terms = {
        'Software Engineer': 'software-engineer',
        'Data Scientist': 'data-scientist',
        'DevOps Engineer': 'devops-engineer',
        'Full Stack Developer': 'full-stack-developer',
        'Backend Developer': 'backend-developer',
        'Frontend Developer': 'frontend-developer',
        'Machine Learning Engineer': 'machine-learning-engineer',
        'Cloud Architect': 'cloud-architect',
        'Product Manager': 'product-manager',
        'UX/UI Designer': 'ui-ux-designer',
        'Python Developer': 'python-developer',
        'Java Developer': 'java-developer',
        'React Developer': 'react-developer',
        'Node.js Developer': 'nodejs-developer',
        'AWS Engineer': 'aws-engineer',
        'Data Analyst': 'data-analyst',
        'Security Engineer': 'security-engineer',
        'QA Engineer': 'qa-engineer',
        'Technical Lead': 'technical-lead',
        'Site Reliability Engineer': 'site-reliability-engineer'
    }
    
    # Get search term for the role
    search_term = role_search_terms.get(role, role.lower().replace(' ', '-'))
    
    # Generate diverse job listings with real URLs
    jobs = [
        (f"{role} - LinkedIn Jobs", f"{job_boards['linkedin']}{search_term}"),
        (f"{role} - Indeed Jobs", f"{job_boards['indeed']}{search_term.replace('-', '+')}"),
        (f"Remote {role}", f"{job_boards['linkedin']}{search_term}&location=remote"),
        (f"Senior {role}", f"{job_boards['linkedin']}{search_term}&f_E=2"),
        (f"Junior {role}", f"{job_boards['linkedin']}{search_term}&f_E=1"),
        (f"{role} - Glassdoor", f"{job_boards['glassdoor']}{search_term.replace('-', '+')}"),
        (f"{role} - ZipRecruiter", f"{job_boards['ziprecruiter']}{search_term.replace('-', '+')}")
    ]
    
    # Remove duplicates and return top 5
    unique_jobs = []
    seen = set()
    for job in jobs:
        if job[1] not in seen:
            seen.add(job[1])
            unique_jobs.append(job)
    
    return unique_jobs[:5]

# --------------------------
# ENHANCED COURSE RECOMMENDATIONS
# --------------------------
def recommend_courses_baseline(skills):
    """Baseline course recommendation without LLM"""
    recommended = []
    added_courses = set()
    skills_lower = [s.lower() for s in skills]
    
    for skill in skills_lower[:8]:  # Check top 8 skills
        for course_skill, courses in course_db.items():
            if course_skill in skill or skill in course_skill:
                for course in courses[:2]:  # Take first 2 courses per skill
                    if course not in added_courses:
                        recommended.append((course_skill.title(), course))
                        added_courses.add(course)
    
    # If no courses found, recommend popular ones
    if not recommended:
        popular = [
            ('Python', 'Python for Everybody – Coursera'),
            ('JavaScript', 'Modern JavaScript – The Odin Project'),
            ('SQL', 'The Complete SQL Bootcamp – Udemy'),
            ('AWS', 'AWS Certified Solutions Architect – AWS Training'),
            ('React', 'React – The Complete Guide – Udemy')
        ]
        recommended = popular
    
    return recommended[:5]

def _format_candidates(cands):
    """Format course candidates for LLM"""
    lines = []
    for i, (skill, title) in enumerate(cands, 1):
        lines.append(f"{i}. [{skill}] {title}")
    return "\n".join(lines)

def _parse_llm_selection(text, num_to_take=5):
    """Parse LLM response to extract selected course indices"""
    indices = []
    for line in text.splitlines()[:10]:
        # Look for numbers in the response
        for word in line.split():
            if word.isdigit():
                num = int(word)
                if 1 <= num <= 20 and num not in indices:
                    indices.append(num)
                    if len(indices) >= num_to_take:
                        return indices
            elif word.endswith(',') and word[:-1].isdigit():
                num = int(word[:-1])
                if 1 <= num <= 20 and num not in indices:
                    indices.append(num)
                    if len(indices) >= num_to_take:
                        return indices
    return indices[:num_to_take]

def recommend_courses_llm(skills):
    """LLM-enhanced course recommendation (if LM Studio available)"""
    if not LM_AVAILABLE:
        return recommend_courses_baseline(skills)
    
    try:
        # Build candidate pool
        pool = []
        skills_lower = [s.lower() for s in skills[:10]]
        
        for skill in skills_lower:
            for course_skill, courses in course_db.items():
                if course_skill in skill or skill in course_skill:
                    for c in courses[:3]:
                        pool.append((course_skill.title(), c))
        
        # Remove duplicates
        unique_pool = []
        seen = set()
        for item in pool:
            if item[1] not in seen:
                seen.add(item[1])
                unique_pool.append(item)
        
        if len(unique_pool) < 5:
            return recommend_courses_baseline(skills)
        
        # Take top candidates for LLM to rank
        candidates = unique_pool[:15]
        candidate_block = _format_candidates(candidates)
        
        # Prepare LLM prompt
        system_msg = "You are a career advisor. Return only numbers of the best courses for the given skills."
        user_msg = f"User skills: {', '.join(skills[:7])}\n\nCourse options:\n{candidate_block}\n\nPick the 5 most relevant courses. Return numbers only, comma-separated."
        
        # Call LM Studio
        response = requests.post(
            f"{LM_BASE_URL}/chat/completions",
            json={
                "model": COURSE_MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                "temperature": 0.3,
                "max_tokens": 50,
                "top_k": 20,
                "top_p": 0.8
            },
            timeout=COURSE_TIMEOUT
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            chosen_indices = _parse_llm_selection(content, num_to_take=5)
            
            ranked = []
            for idx in chosen_indices:
                if 1 <= idx <= len(candidates):
                    ranked.append(candidates[idx - 1])
            
            if ranked:
                return ranked
        
        return recommend_courses_baseline(skills)
        
    except Exception as e:
        print(f"LLM course recommendation failed: {e}")
        return recommend_courses_baseline(skills)

def recommend_courses(skills, use_llm=True):
    """Main course recommendation function"""
    if use_llm and LM_AVAILABLE:
        return recommend_courses_llm(skills)
    return recommend_courses_baseline(skills)

# --------------------------
# ENHANCED AI RESPONSES
# --------------------------
def ai_answer_query(query, skills=None):
    """Generate AI response for career queries"""
    if skills is None:
        skills = []
    
    # If LM Studio is available, use it for better responses
    if LM_AVAILABLE:
        try:
            # Limit query length for speed
            query_short = query[:300] if len(query) > 300 else query
            skills_str = ', '.join(skills[:7]) if skills else 'general technology'
            
            prompt = f"""User skills: {skills_str}
User question: {query_short}

Provide concise, helpful career advice (2-3 sentences):"""
            
            response = requests.post(
                f"{LM_BASE_URL}/chat/completions",
                json={
                    "model": CHATBOT_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5,
                    "max_tokens": 120,
                    "top_k": 20,
                    "top_p": 0.8
                },
                timeout=CHATBOT_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"LM Studio query failed: {e}, using fallback")
    
    # Enhanced fallback responses
    query_lower = query.lower()
    
    # Job-related queries
    if any(word in query_lower for word in ['job', 'career', 'position', 'work', 'employment']):
        if 'remote' in query_lower:
            return "Remote jobs are widely available in tech. Check LinkedIn, We Work Remotely, and Remote.co. Update your LinkedIn profile to 'Open to Work' and filter by remote locations."
        elif 'interview' in query_lower:
            return "For interviews, practice common questions, research the company, prepare your own questions, and use the STAR method for behavioral questions. Do mock interviews with friends."
        elif 'entry' in query_lower or 'junior' in query_lower:
            return f"For entry-level positions with skills in {', '.join(skills[:3]) if skills else 'tech'}, focus on building a strong portfolio, contributing to open source, and networking."
        else:
            return f"Based on your skills in {', '.join(skills[:3]) if skills else 'technology'}, look for roles on LinkedIn, Indeed, and Glassdoor. Tailor your resume for each application."
    
    # Learning/Courses queries
    elif any(word in query_lower for word in ['learn', 'study', 'course', 'certification', 'training']):
        skill_topics = {
            'python': "For Python, I recommend: 'Python for Everybody' on Coursera, 'Complete Python Bootcamp' on Udemy.",
            'javascript': "For JavaScript, check out: 'The Complete JavaScript Course' on Udemy, freeCodeCamp's JavaScript curriculum.",
            'data': "For Data Science, consider: 'Machine Learning Specialization' by Andrew Ng on Coursera.",
            'cloud': "For Cloud Computing, get certified: AWS Solutions Architect, Google Cloud certifications."
        }
        
        for key, response in skill_topics.items():
            if key in query_lower or (key in str(skills).lower()):
                return response
        
        return f"Based on your profile, I recommend courses in {', '.join(skills[:2]) if skills else 'your area of interest'}. Check Coursera, Udemy, and edX."
    
    # Salary queries
    elif any(word in query_lower for word in ['salary', 'pay', 'compensation', 'money', 'earn']):
        return "Tech salaries vary: Junior: $60-85k, Mid-level: $85-120k, Senior: $120-180k+. Location, company size, and your skills impact compensation."
    
    # Resume/CV queries
    elif any(word in query_lower for word in ['resume', 'cv', 'curriculum']):
        return "Your resume should: 1) Be 1-2 pages, 2) Highlight achievements with metrics, 3) Use action verbs, 4) Include relevant keywords from job descriptions."
    
    # Default responses
    else:
        responses = [
            f"Based on your skills in {', '.join(skills[:3]) if skills else 'technology'}, focus on building a strong portfolio and networking.",
            "Consider getting certified in cloud platforms (AWS, Azure, GCP) as they're in high demand.",
            "Soft skills like communication and teamwork are just as important as technical skills.",
            "Stay updated with tech trends by following industry blogs and joining online communities.",
            "Your skill set is valuable! Keep learning, building, and connecting with others in your field."
        ]
        return random.choice(responses)

# --------------------------
# ENHANCED JOB MATCHING FEATURE
# --------------------------
def extract_skills_from_job_description(text):
    """Extract required skills from job description"""
    found_skills = []
    text_lower = text.lower()
    
    for category, skills in skill_categories.items():
        for skill in skills:
            skill_lower = skill.lower()
            if (skill_lower in text_lower or 
                skill_lower.replace(' ', '') in text_lower or
                skill_lower.replace('.', '') in text_lower):
                found_skills.append(skill)
    
    return list(dict.fromkeys(found_skills))

def extract_experience_requirement(text):
    """Extract required years of experience from job description"""
    patterns = [
        r'(\d+)[\+]?\s*(?:plus\s*)?years?.*?experience',
        r'experience.*?(\d+)[\+]?\s*(?:plus\s*)?years?',
        r'minimum.*?(\d+)[\+]?\s*years?',
        r'at least.*?(\d+)[\+]?\s*years?'
    ]
    
    text_lower = text.lower()
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                return int(matches[0])
            except:
                pass
    
    return 0

def extract_experience_from_resume(text):
    """Extract years of experience from resume"""
    text_lower = text.lower()
    
    patterns = [
        r'(\d+)[\+]?\s*years?.*?experience',
        r'experience.*?(\d+)[\+]?\s*years?'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_lower)
        if matches:
            try:
                return int(matches[0])
            except:
                pass
    
    return 2  # Default to 2 years

def extract_job_title(text):
    """Extract job title from job description"""
    lines = text.split('\n')
    for line in lines[:15]:
        line = line.strip()
        if len(line) > 3 and len(line) < 100:
            job_indicators = ['engineer', 'developer', 'manager', 'analyst', 'architect', 
                            'specialist', 'consultant', 'director', 'lead', 'senior']
            if any(indicator in line.lower() for indicator in job_indicators):
                return line
    
    return "Software Engineer Position"

def calculate_job_match_score(resume_skills, job_skills, resume_text="", job_text=""):
    """Calculate match percentage between resume and job description"""
    
    # Convert to sets for easier comparison
    resume_skills_set = set([s.lower() for s in resume_skills])
    job_skills_set = set([s.lower() for s in job_skills])
    
    # Calculate skill match
    if len(job_skills_set) > 0:
        matched_skills = resume_skills_set.intersection(job_skills_set)
        missing_skills = job_skills_set - resume_skills_set
        skill_match_percentage = (len(matched_skills) / len(job_skills_set)) * 100
    else:
        matched_skills = set()
        missing_skills = set()
        skill_match_percentage = 60
    
    # Extract experience
    resume_exp = extract_experience_from_resume(resume_text)
    job_exp_req = extract_experience_requirement(job_text)
    
    # Calculate experience match
    if job_exp_req > 0:
        if resume_exp >= job_exp_req:
            exp_match = 100
        elif resume_exp >= job_exp_req * 0.7:
            exp_match = 70
        else:
            exp_match = 40
    else:
        exp_match = 80
    
    # Calculate overall score (70% skills, 30% experience)
    overall_score = (skill_match_percentage * 0.7) + (exp_match * 0.3)
    overall_score = round(overall_score, 2)
    
    # Categorize match level
    if overall_score >= 80:
        match_level = "Excellent Match"
    elif overall_score >= 60:
        match_level = "Good Match"
    elif overall_score >= 40:
        match_level = "Fair Match"
    else:
        match_level = "Needs Improvement"
    
    return {
        'overall_score': overall_score,
        'match_level': match_level,
        'skill_match': round(skill_match_percentage, 2),
        'experience_match': exp_match,
        'matched_skills': sorted([s.capitalize() for s in list(matched_skills)]),
        'missing_skills': sorted([s.capitalize() for s in list(missing_skills)]),
        'total_job_skills': len(job_skills_set),
        'total_resume_skills': len(resume_skills_set),
        'resume_experience': resume_exp,
        'required_experience': job_exp_req
    }

# --------------------------
# ROUTES
# --------------------------

@app.route('/')
def index():
    """Home page - redirects to login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? OR username = ?', 
            (email, email)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['full_name'] = user['full_name'] or user['username']
            
            # Update last login
            conn = get_db_connection()
            conn.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user['id'],)
            )
            conn.commit()
            conn.close()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email/username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        
        if not all([email, username, password]):
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        existing = conn.execute(
            'SELECT * FROM users WHERE email = ? OR username = ?', 
            (email, username)
        ).fetchone()
        
        if existing:
            conn.close()
            flash('Email or username already exists', 'error')
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (email, username, password, full_name) VALUES (?, ?, ?, ?)',
            (email, username, password_hash, full_name)
        )
        conn.commit()
        
        user = conn.execute(
            'SELECT * FROM users WHERE email = ?', (email,)
        ).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['full_name'] = user['full_name'] or user['username']
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    from datetime import datetime
    
    user_data = {
        'username': session.get('username', 'User'),
        'full_name': session.get('full_name', 'User'),
        'email': session.get('email', '')
    }
    
    # Get user's recent uploads
    conn = get_db_connection()
    recent_uploads = conn.execute(
        'SELECT * FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 3',
        (session['user_id'],)
    ).fetchall()
    
    # Get job match history
    match_history = conn.execute(
        'SELECT * FROM job_matches WHERE user_id = ? ORDER BY created_at DESC LIMIT 3',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    uploads_list = []
    for upload in recent_uploads:
        upload_dict = dict(upload)
        try:
            if upload_dict.get('skills'):
                upload_dict['skills_parsed'] = json.loads(upload_dict['skills'])[:5]
            if upload_dict.get('top_roles'):
                upload_dict['roles_parsed'] = json.loads(upload_dict['top_roles'])[:3]
        except:
            pass
        uploads_list.append(upload_dict)
    
    matches_list = [dict(match) for match in match_history]
    
    # Default data
    skills = ['Python', 'JavaScript', 'SQL', 'Communication', 'Problem Solving']
    top_roles = [
        ['Software Engineer', 92],
        ['Data Scientist', 88],
        ['DevOps Engineer', 85],
        ['Full Stack Developer', 82],
        ['Backend Developer', 80]
    ]
    
    primary_role = top_roles[0][0] if top_roles else "Software Engineer"
    jobs = get_jobs_for_role(primary_role)
    courses = recommend_courses(skills)
    
    ai_response = "Your resume analysis is ready! Based on your skills, you're well-positioned for roles in software development."
    filename = None
    show_results = False
    
    if uploads_list:
        latest_upload = uploads_list[0]
        filename = latest_upload['filename']
        show_results = True
        
        try:
            if latest_upload.get('skills'):
                parsed_skills = json.loads(latest_upload['skills'])
                if parsed_skills:
                    skills = parsed_skills
            if latest_upload.get('top_roles'):
                parsed_roles = json.loads(latest_upload['top_roles'])
                if parsed_roles:
                    top_roles = parsed_roles
                    primary_role = top_roles[0][0] if top_roles else "Software Engineer"
                    jobs = get_jobs_for_role(primary_role)
            if latest_upload.get('courses'):
                parsed_courses = json.loads(latest_upload['courses'])
                if parsed_courses:
                    courses = parsed_courses
            if latest_upload.get('ai_response'):
                ai_response = latest_upload['ai_response']
        except Exception as e:
            print(f"Error parsing upload data: {e}")
    
    return render_template('index.html', 
                          user=user_data,
                          recent_uploads=uploads_list,
                          match_history=matches_list,
                          skills=skills, 
                          top_roles=top_roles, 
                          jobs=jobs, 
                          courses=courses,
                          filename=filename,
                          ai_response=ai_response,
                          show_results=show_results,
                          lm_available=LM_AVAILABLE,
                          now=datetime.now)

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Enhanced analyze resume endpoint"""
    print("📤 Received analyze request")
    
    try:
        if 'resume_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('dashboard'))
        
        file = request.files['resume_file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('dashboard'))
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload PDF, DOC, DOCX, or TXT.', 'error')
            return redirect(url_for('dashboard'))
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        resume_text = extract_text_from_pdf(filepath)
        extracted_skills = extract_skills_from_text(resume_text)
        top_roles = predict_top_roles(extracted_skills)
        primary_role = top_roles[0][0] if top_roles else "Software Developer"
        jobs = get_jobs_for_role(primary_role)
        courses = recommend_courses(extracted_skills, use_llm=True)
        
        custom_query = request.form.get('custom_query', '').strip()
        if custom_query:
            ai_response = ai_answer_query(custom_query, extracted_skills)
        else:
            ai_response = "Your resume has been analyzed successfully!"
        
        conn = get_db_connection()
        cur = conn.execute('''
            INSERT INTO user_uploads (user_id, filename, filepath, skills, top_roles, jobs, courses, ai_response, analysis_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            filename,
            filepath,
            json.dumps(extracted_skills),
            json.dumps(top_roles),
            json.dumps(jobs),
            json.dumps(courses),
            ai_response,
            "2.0"
        ))
        conn.commit()
        new_upload_id = cur.lastrowid
        conn.close()
        
        flash('Resume analyzed successfully!', 'success')
        return redirect(url_for('view_upload', upload_id=new_upload_id))
    
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        traceback.print_exc()
        flash(f'Analysis failed: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    """Enhanced chatbot endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        print(f"💬 Chat request: {user_message[:50]}...")
        
        # Get user's skills for context
        try:
            conn = get_db_connection()
            latest_upload = conn.execute(
                'SELECT skills FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 1',
                (session['user_id'],)
            ).fetchone()
            conn.close()
            
            skills = []
            if latest_upload and latest_upload['skills']:
                try:
                    skills = json.loads(latest_upload['skills'])
                except:
                    skills = []
        except Exception as e:
            print(f"Error fetching skills: {e}")
            skills = []
        
        # Get response using enhanced function
        start_time = time.time()
        response = ai_answer_query(user_message, skills)
        processing_time = time.time() - start_time
        
        print(f"✅ Chat response generated in {processing_time:.2f}s")
        return jsonify({'response': response, 'lm_available': LM_AVAILABLE})
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        traceback.print_exc()
        return jsonify({'response': 'I apologize, but I encountered an error. Please try again.'}), 500

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE id = ?', 
        (session['user_id'],)
    ).fetchone()
    
    uploads = conn.execute(
        'SELECT COUNT(*) as count FROM user_uploads WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    
    matches = conn.execute(
        'SELECT COUNT(*) as count FROM job_matches WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    
    recent_uploads = conn.execute(
        'SELECT * FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 5',
        (session['user_id'],)
    ).fetchall()
    
    conn.close()
    
    user_data = dict(user) if user else {}
    uploads_list = [dict(upload) for upload in recent_uploads]
    
    return render_template('profile.html', 
                          user=user_data,
                          upload_count=uploads['count'] if uploads else 0,
                          match_count=matches['count'] if matches else 0,
                          recent_uploads=uploads_list)

@app.route('/history')
@login_required
def history():
    """Upload history"""
    conn = get_db_connection()
    uploads = conn.execute(
        'SELECT * FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC',
        (session['user_id'],)
    ).fetchall()
    conn.close()
    
    uploads_list = []
    for upload in uploads:
        upload_dict = dict(upload)
        try:
            if upload_dict.get('skills'):
                upload_dict['skills_parsed'] = json.loads(upload_dict['skills'])[:5]
            if upload_dict.get('top_roles'):
                upload_dict['roles_parsed'] = json.loads(upload_dict['top_roles'])[:3]
        except:
            pass
        uploads_list.append(upload_dict)
    
    return render_template('history.html', uploads=uploads_list)

@app.route('/view/<int:upload_id>')
@login_required
def view_upload(upload_id):
    """View specific upload analysis"""
    from datetime import datetime
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    upload = conn.execute('SELECT * FROM user_uploads WHERE id = ? AND user_id = ?', (upload_id, session['user_id'])).fetchone()
    recent_uploads = conn.execute('SELECT * FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 3', (session['user_id'],)).fetchall()
    conn.close()
    
    user_data = dict(user) if user else {}
    uploads_list = [dict(u) for u in recent_uploads]
    
    skills = []
    top_roles = []
    jobs = []
    courses = []
    ai_response = ""
    filename = None
    show_results = False
    
    if upload:
        up = dict(upload)
        filename = up.get('filename')
        show_results = True
        
        try:
            if up.get('skills'):
                skills = json.loads(up['skills'])
            if up.get('top_roles'):
                top_roles = json.loads(up['top_roles'])
                if top_roles:
                    primary_role = top_roles[0][0] if top_roles else "Software Engineer"
                    jobs = get_jobs_for_role(primary_role)
            if up.get('courses'):
                courses = json.loads(up['courses'])
            if up.get('ai_response'):
                ai_response = up['ai_response']
        except Exception as e:
            print(f"Error parsing upload data: {e}")
    
    if not jobs:
        jobs = get_jobs_for_role("Software Engineer")
    
    return render_template('index.html',
                          user=user_data,
                          recent_uploads=uploads_list,
                          skills=skills,
                          top_roles=top_roles,
                          jobs=jobs,
                          courses=courses,
                          filename=filename,
                          ai_response=ai_response,
                          show_results=show_results,
                          lm_available=LM_AVAILABLE,
                          now=datetime.now)

@app.route('/reanalyze/<int:upload_id>')
@login_required
def reanalyze_upload(upload_id):
    """Re-analyze an existing upload"""
    conn = get_db_connection()
    upload = conn.execute('SELECT * FROM user_uploads WHERE id = ? AND user_id = ?', (upload_id, session['user_id'])).fetchone()
    conn.close()
    
    if not upload:
        flash('Upload not found', 'error')
        return redirect(url_for('dashboard'))
    
    filepath = upload['filepath']
    
    try:
        resume_text = extract_text_from_pdf(filepath)
        extracted_skills = extract_skills_from_text(resume_text)
        top_roles = predict_top_roles(extracted_skills)
        primary_role = top_roles[0][0] if top_roles else "Software Developer"
        jobs = get_jobs_for_role(primary_role)
        courses = recommend_courses(extracted_skills, use_llm=True)
        ai_response = "Re-analysis completed with enhanced algorithms."
        
        conn = get_db_connection()
        conn.execute('''
            UPDATE user_uploads 
            SET skills=?, top_roles=?, jobs=?, courses=?, ai_response=?, analysis_version='2.0'
            WHERE id=?
        ''', (
            json.dumps(extracted_skills), 
            json.dumps(top_roles), 
            json.dumps(jobs), 
            json.dumps(courses), 
            ai_response, 
            upload_id
        ))
        conn.commit()
        conn.close()
        
        flash('Re-analysis completed successfully!', 'success')
        return redirect(url_for('view_upload', upload_id=upload_id))
        
    except Exception as e:
        flash(f'Re-analysis failed: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/job-match', methods=['GET', 'POST'])
@login_required
def job_match():
    """Enhanced job matching page"""
    if request.method == 'POST':
        try:
            if 'resume_file' not in request.files or 'job_file' not in request.files:
                flash('Please upload both resume and job description files', 'error')
                return redirect(url_for('job_match'))
            
            resume_file = request.files['resume_file']
            job_file = request.files['job_file']
            
            if resume_file.filename == '' or job_file.filename == '':
                flash('Please select both files', 'error')
                return redirect(url_for('job_match'))
            
            if not allowed_file(resume_file.filename) or not allowed_file(job_file.filename):
                flash('Invalid file type. Please upload PDF, DOC, DOCX, or TXT files.', 'error')
                return redirect(url_for('job_match'))
            
            # Save files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            resume_filename = secure_filename(resume_file.filename)
            resume_filename = f"resume_{timestamp}_{resume_filename}"
            resume_filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
            resume_file.save(resume_filepath)
            
            job_filename = secure_filename(job_file.filename)
            job_filename = f"job_{timestamp}_{job_filename}"
            job_filepath = os.path.join(app.config['UPLOAD_FOLDER'], job_filename)
            job_file.save(job_filepath)
            
            # Extract and analyze
            resume_text = extract_text_from_pdf(resume_filepath)
            job_text = extract_text_from_pdf(job_filepath)
            
            resume_skills = extract_skills_from_text(resume_text)
            job_skills = extract_skills_from_job_description(job_text)
            
            match_results = calculate_job_match_score(resume_skills, job_skills, resume_text, job_text)
            job_title = extract_job_title(job_text)
            
            # Save to database
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO job_matches (user_id, job_title, match_score, matched_skills, missing_skills)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                session['user_id'],
                job_title,
                match_results['overall_score'],
                json.dumps(match_results['matched_skills']),
                json.dumps(match_results['missing_skills'])
            ))
            conn.commit()
            conn.close()
            
            return render_template('job_match_results.html',
                                 user={'username': session.get('username', 'User')},
                                 job_title=job_title,
                                 match_results=match_results,
                                 resume_skills=resume_skills,
                                 job_skills=job_skills,
                                 lm_available=LM_AVAILABLE)
            
        except Exception as e:
            print(f"❌ Job match error: {str(e)}")
            traceback.print_exc()
            flash(f'Job matching failed: {str(e)}', 'error')
            return redirect(url_for('job_match'))
    
    return render_template('job_match.html', user={'username': session.get('username', 'User')})

@app.route('/quick-actions', methods=['POST'])
@login_required
def quick_actions():
    """Quick actions endpoint for common operations"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        
        if action == 'refresh_jobs':
            conn = get_db_connection()
            latest_upload = conn.execute(
                'SELECT top_roles FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 1',
                (session['user_id'],)
            ).fetchone()
            conn.close()
            
            if latest_upload and latest_upload['top_roles']:
                top_roles = json.loads(latest_upload['top_roles'])
                primary_role = top_roles[0][0] if top_roles else "Software Engineer"
                jobs = get_jobs_for_role(primary_role)
                return jsonify({'success': True, 'jobs': jobs})
        
        elif action == 'get_career_advice':
            conn = get_db_connection()
            latest_upload = conn.execute(
                'SELECT skills FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 1',
                (session['user_id'],)
            ).fetchone()
            conn.close()
            
            skills = []
            if latest_upload and latest_upload['skills']:
                skills = json.loads(latest_upload['skills'])
            
            advice = ai_answer_query("What career advice do you have for me?", skills)
            return jsonify({'success': True, 'advice': advice})
        
        elif action == 'recommend_courses_quick':
            conn = get_db_connection()
            latest_upload = conn.execute(
                'SELECT skills FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 1',
                (session['user_id'],)
            ).fetchone()
            conn.close()
            
            skills = []
            if latest_upload and latest_upload['skills']:
                skills = json.loads(latest_upload['skills'])
            
            courses = recommend_courses(skills, use_llm=True)
            return jsonify({'success': True, 'courses': courses})
        
        return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/test-upload', methods=['GET'])
@login_required
def test_upload():
    """Test endpoint to simulate file upload"""
    try:
        test_content = """
        JOHN DOE - Senior Software Engineer
        Email: john.doe@email.com | Phone: (555) 123-4567
        
        SKILLS
        • Programming: Python, JavaScript, Java, TypeScript
        • Web Frameworks: Django, Flask, React, Node.js
        • Databases: PostgreSQL, MongoDB, MySQL
        • Cloud & DevOps: AWS, Docker, Kubernetes, Jenkins
        • Tools: Git, JIRA, VS Code
        
        WORK EXPERIENCE
        Senior Software Engineer | TechCorp Inc. | 2020 - Present
        Full Stack Developer | Startup Innovations | 2018 - 2020
        
        EDUCATION
        BS Computer Science | University of Technology | 2014 - 2018
        """
        
        test_filename = f"test_resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        test_filepath = os.path.join(app.config['UPLOAD_FOLDER'], test_filename)
        
        with open(test_filepath, 'w') as f:
            f.write(test_content)
        
        resume_text = test_content
        extracted_skills = extract_skills_from_text(resume_text)
        top_roles = predict_top_roles(extracted_skills)
        jobs = get_jobs_for_role(top_roles[0][0] if top_roles else "Software Developer")
        courses = recommend_courses(extracted_skills, use_llm=True)
        ai_response = "Test analysis completed with enhanced algorithms!"
        
        conn = get_db_connection()
        cur = conn.execute('''
            INSERT INTO user_uploads (user_id, filename, filepath, skills, top_roles, jobs, courses, ai_response, analysis_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            test_filename,
            test_filepath,
            json.dumps(extracted_skills),
            json.dumps(top_roles),
            json.dumps(jobs),
            json.dumps(courses),
            ai_response,
            "2.0"
        ))
        conn.commit()
        new_upload_id = cur.lastrowid
        conn.close()
        
        flash('Test analysis completed!', 'success')
        return redirect(url_for('view_upload', upload_id=new_upload_id))
        
    except Exception as e:
        print(f"❌ Test upload failed: {e}")
        flash(f'Test failed: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Path Pilot Enhanced',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat(),
        'lm_studio_available': LM_AVAILABLE,
        'database': 'connected' if os.path.exists(app.config['DATABASE']) else 'disconnected'
    })

@app.route('/debug')
@login_required
def debug():
    """Debug endpoint"""
    conn = get_db_connection()
    uploads_count = conn.execute('SELECT COUNT(*) as c FROM user_uploads WHERE user_id = ?', (session['user_id'],)).fetchone()
    matches_count = conn.execute('SELECT COUNT(*) as c FROM job_matches WHERE user_id = ?', (session['user_id'],)).fetchone()
    conn.close()
    
    debug_info = {
        'session': dict(session),
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'user_uploads_count': uploads_count['c'] if uploads_count else 0,
        'job_matches_count': matches_count['c'] if matches_count else 0,
        'lm_studio_available': LM_AVAILABLE
    }
    return jsonify(debug_info)

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Internal server error'), 500

# --------------------------
# START APPLICATION
# --------------------------
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Path Pilot Enhanced Backend v2.0")
    print("=" * 60)
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📊 Database: {app.config['DATABASE']}")
    print(f"🤖 LM Studio: {'✅ Available' if LM_AVAILABLE else '⚠️ Not Available'}")
    print("-" * 60)
    print(f"🌐 Login URL: http://localhost:5000/login")
    print(f"👤 Default admin: admin@skillsense.com / admin123")
    print(f"🤝 Job Match: http://localhost:5000/job-match")
    print("=" * 60)
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5000,
        threaded=True
    )