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
import threading
from concurrent.futures import ThreadPoolExecutor

print("🚀 Starting SkillSense Backend with Enhanced Processing...")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'skill-sense-secret-key-2024-change-in-production'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt'}
app.config['DATABASE'] = 'database.db'

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=3)

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# JSearch API Configuration
JSEARCH_API_KEY = "d7c16a9efdmsh3f85b85a7b8ae51p14e8cfjsnfda220ee5c6f"
JSEARCH_API_HOST = "jsearch.p.rapidapi.com"
JSEARCH_API_URL = "https://jsearch.p.rapidapi.com/search"

# --------------------------
# COMPREHENSIVE SKILL DATABASE BY DEPARTMENT
# --------------------------
SKILL_DATABASE = {
    # TECHNOLOGY SKILLS
    'technology': {
        'Programming Languages': [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Ruby', 'PHP', 'Swift', 
            'Kotlin', 'Go', 'Rust', 'Scala', 'Perl', 'R', 'MATLAB', 'Dart', 'Elixir', 'Haskell'
        ],
        'Web Development': [
            'HTML', 'HTML5', 'CSS', 'CSS3', 'SASS', 'LESS', 'React', 'React.js', 'Angular', 
            'Angular.js', 'Vue', 'Vue.js', 'Next.js', 'Nuxt.js', 'Node.js', 'Express.js', 
            'Django', 'Flask', 'FastAPI', 'Spring', 'Spring Boot', 'ASP.NET', 'Laravel', 
            'Ruby on Rails', 'jQuery', 'Bootstrap', 'Tailwind', 'Material UI', 'Redux', 
            'Webpack', 'Babel', 'REST API', 'GraphQL', 'API Development'
        ],
        'Databases': [
            'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Cassandra', 'Oracle', 
            'SQL Server', 'SQLite', 'DynamoDB', 'Firebase', 'MariaDB', 'CouchDB', 'Elasticsearch',
            'Database Design', 'Data Modeling', 'Query Optimization'
        ],
        'Cloud & DevOps': [
            'AWS', 'Amazon Web Services', 'Azure', 'Google Cloud', 'GCP', 'Docker', 
            'Kubernetes', 'Jenkins', 'GitHub Actions', 'GitLab CI', 'CircleCI', 'Terraform', 
            'Ansible', 'Puppet', 'Chef', 'CloudFormation', 'CI/CD', 'DevOps', 'Linux', 
            'Unix', 'Bash', 'Shell Scripting', 'Nginx', 'Apache', 'Infrastructure as Code'
        ],
        'Data Science & ML': [
            'Machine Learning', 'Deep Learning', 'Neural Networks', 'NLP', 'Natural Language Processing',
            'Computer Vision', 'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 
            'NumPy', 'SciPy', 'Matplotlib', 'Seaborn', 'Plotly', 'Jupyter', 'Data Analysis',
            'Data Visualization', 'Statistics', 'Statistical Analysis', 'Feature Engineering',
            'Model Deployment', 'MLOps', 'Big Data', 'Spark', 'Hadoop', 'Data Mining'
        ],
        'Mobile Development': [
            'iOS', 'Android', 'Swift', 'Kotlin', 'React Native', 'Flutter', 'Xamarin', 
            'Ionic', 'Mobile App Development', 'UI/UX for Mobile'
        ],
        'Testing': [
            'Testing', 'Unit Testing', 'Integration Testing', 'Jest', 'Mocha', 'Chai',
            'Selenium', 'Cypress', 'Puppeteer', 'JUnit', 'PyTest', 'QA', 'Quality Assurance',
            'Test Automation', 'Manual Testing'
        ],
        'Tools & Methodologies': [
            'Git', 'GitHub', 'GitLab', 'Bitbucket', 'JIRA', 'Confluence', 'Slack', 'Trello',
            'Agile', 'Scrum', 'Kanban', 'Waterfall', 'Project Management', 'VS Code', 
            'IntelliJ', 'Eclipse', 'Postman', 'Swagger', 'Figma', 'Adobe XD'
        ],
        'Security': [
            'Cybersecurity', 'Network Security', 'Information Security', 'Encryption',
            'Penetration Testing', 'Ethical Hacking', 'Security Auditing', 'CISSP',
            'CompTIA Security+', 'Firewalls', 'SIEM', 'Incident Response'
        ]
    },
    
    # FINANCE SKILLS
    'finance': {
        'Financial Analysis': [
            'Financial Analysis', 'Financial Modeling', 'Valuation', 'DCF', 'LBO', 'M&A',
            'Financial Planning', 'Budgeting', 'Forecasting', 'Financial Reporting',
            'Investment Analysis', 'Portfolio Management', 'Risk Management'
        ],
        'Accounting': [
            'Accounting', 'Bookkeeping', 'GAAP', 'IFRS', 'Tax Preparation', 'Auditing',
            'Accounts Payable', 'Accounts Receivable', 'General Ledger', 'Financial Statements',
            'Balance Sheet', 'Income Statement', 'Cash Flow'
        ],
        'Investment': [
            'Investment Banking', 'Private Equity', 'Venture Capital', 'Asset Management',
            'Equity Research', 'Fixed Income', 'Derivatives', 'Trading', 'Hedge Funds',
            'Wealth Management', 'Financial Advisory'
        ],
        'Financial Software': [
            'Excel', 'Advanced Excel', 'VBA', 'Bloomberg Terminal', 'Reuters Eikon',
            'QuickBooks', 'SAP FI', 'Oracle Financials', 'Peachtree', 'Tableau', 'Power BI'
        ],
        'Banking': [
            'Commercial Banking', 'Retail Banking', 'Corporate Banking', 'Credit Analysis',
            'Loan Processing', 'Mortgage', 'Wealth Management', 'Private Banking'
        ],
        'FinTech': [
            'Blockchain', 'Cryptocurrency', 'Smart Contracts', 'Payments', 'Digital Banking',
            'FinTech Regulations', 'Payment Gateways', 'Mobile Payments'
        ]
    },
    
    # MARKETING SKILLS
    'marketing': {
        'Digital Marketing': [
            'SEO', 'Search Engine Optimization', 'SEM', 'Search Engine Marketing',
            'PPC', 'Pay Per Click', 'Google Ads', 'Facebook Ads', 'Social Media Marketing',
            'Content Marketing', 'Email Marketing', 'Marketing Automation'
        ],
        'Analytics': [
            'Google Analytics', 'Data Analytics', 'Marketing Analytics', 'Conversion Rate Optimization',
            'A/B Testing', 'Customer Analytics', 'Market Research', 'Competitive Analysis'
        ],
        'Brand Management': [
            'Brand Strategy', 'Brand Management', 'Brand Development', 'Brand Identity',
            'Marketing Strategy', 'Campaign Management', 'Product Marketing'
        ],
        'Content Creation': [
            'Copywriting', 'Content Writing', 'Blogging', 'Technical Writing', 'Creative Writing',
            'Video Production', 'Photography', 'Graphic Design', 'Adobe Creative Suite',
            'Photoshop', 'Illustrator', 'InDesign', 'Canva'
        ],
        'Social Media': [
            'Social Media Management', 'Community Management', 'Instagram', 'Facebook',
            'Twitter', 'LinkedIn', 'TikTok', 'YouTube', 'Social Media Strategy'
        ],
        'PR & Communications': [
            'Public Relations', 'Media Relations', 'Corporate Communications',
            'Crisis Communication', 'Press Releases', 'Event Planning'
        ]
    },
    
    # HUMAN RESOURCES SKILLS
    'hr': {
        'Recruitment': [
            'Recruiting', 'Talent Acquisition', 'Sourcing', 'Interviewing', 'Candidate Screening',
            'Headhunting', 'Executive Search', 'Applicant Tracking Systems', 'Workday', 'Greenhouse'
        ],
        'HR Operations': [
            'HR Management', 'HRIS', 'Employee Relations', 'Performance Management',
            'Compensation & Benefits', 'Payroll', 'HR Policies', 'Compliance'
        ],
        'Training & Development': [
            'Training', 'Learning & Development', 'Onboarding', 'Employee Training',
            'Talent Management', 'Succession Planning', 'Coaching', 'Mentoring'
        ],
        'HR Strategy': [
            'HR Strategy', 'Organizational Development', 'Workforce Planning',
            'Change Management', 'Culture Building', 'Employee Engagement'
        ],
        'HR Compliance': [
            'Labor Law', 'Employment Law', 'HR Compliance', 'EEO', 'OSHA',
            'Workplace Safety', 'HR Auditing'
        ]
    },
    
    # SALES SKILLS
    'sales': {
        'Sales Techniques': [
            'Sales', 'Business Development', 'Account Management', 'Lead Generation',
            'Cold Calling', 'Negotiation', 'Closing', 'Upselling', 'Cross-selling'
        ],
        'Sales Management': [
            'Sales Management', 'Sales Strategy', 'Sales Operations', 'Sales Forecasting',
            'Territory Management', 'Team Leadership', 'Sales Training'
        ],
        'CRM': [
            'Salesforce', 'HubSpot', 'Zoho CRM', 'Microsoft Dynamics', 'CRM Software',
            'Customer Relationship Management'
        ],
        'B2B Sales': [
            'B2B Sales', 'Enterprise Sales', 'Solution Selling', 'Consultative Selling',
            'Strategic Partnerships', 'Channel Sales'
        ],
        'B2C Sales': [
            'B2C Sales', 'Retail Sales', 'E-commerce', 'Direct Sales', 'Inside Sales'
        ]
    }
}

# Flatten skills with department info for better matching
ALL_SKILLS_WITH_DEPT = []
for dept, categories in SKILL_DATABASE.items():
    for category, skills in categories.items():
        for skill in skills:
            ALL_SKILLS_WITH_DEPT.append({
                'skill': skill.lower(),
                'display': skill,
                'category': category,
                'department': dept
            })

# Skill variations for better matching
SKILL_VARIATIONS = {
    'js': 'javascript',
    'ts': 'typescript',
    'py': 'python',
    'ml': 'machine learning',
    'dl': 'deep learning',
    'k8s': 'kubernetes',
    'tf': 'tensorflow',
    'sklearn': 'scikit-learn',
    'aws': 'amazon web services',
    'gcp': 'google cloud platform',
    'cpp': 'c++',
    'csharp': 'c#',
    'reactjs': 'react',
    'vuejs': 'vue.js',
    'nodejs': 'node.js',
    'expressjs': 'express.js',
    'd3': 'd3.js',
    'ai': 'artificial intelligence',
    'nlp': 'natural language processing',
    'cv': 'computer vision',
    'fintech': 'financial technology',
    'seo': 'search engine optimization',
    'sem': 'search engine marketing',
    'ppc': 'pay per click',
    'crm': 'customer relationship management',
    'erp': 'enterprise resource planning',
    'hris': 'human resource information system'
}

# --------------------------
# COMPREHENSIVE ROLE REQUIREMENTS BY DEPARTMENT
# --------------------------
ROLE_REQUIREMENTS = {
    # TECHNOLOGY ROLES
    'Software Engineer': {
        'skills': ['python', 'java', 'javascript', 'git', 'sql', 'data structures', 'algorithms', 'oop'],
        'department': 'technology',
        'weight': 1.0
    },
    'Data Scientist': {
        'skills': ['python', 'machine learning', 'data analysis', 'sql', 'statistics', 'pandas', 'numpy', 'visualization'],
        'department': 'technology',
        'weight': 1.0
    },
    'DevOps Engineer': {
        'skills': ['aws', 'docker', 'kubernetes', 'linux', 'ci/cd', 'jenkins', 'terraform', 'ansible', 'git'],
        'department': 'technology',
        'weight': 1.0
    },
    'Full Stack Developer': {
        'skills': ['javascript', 'react', 'node.js', 'html', 'css', 'sql', 'rest api', 'git', 'mongodb'],
        'department': 'technology',
        'weight': 1.0
    },
    'Backend Developer': {
        'skills': ['python', 'java', 'sql', 'django', 'flask', 'api', 'database design', 'microservices'],
        'department': 'technology',
        'weight': 1.0
    },
    'Frontend Developer': {
        'skills': ['javascript', 'react', 'html', 'css', 'typescript', 'responsive design', 'ui/ux', 'redux'],
        'department': 'technology',
        'weight': 1.0
    },
    'Machine Learning Engineer': {
        'skills': ['python', 'machine learning', 'tensorflow', 'pytorch', 'statistics', 'data processing', 'model deployment'],
        'department': 'technology',
        'weight': 1.0
    },
    'Cloud Architect': {
        'skills': ['aws', 'azure', 'docker', 'kubernetes', 'networking', 'security', 'microservices', 'cloud design'],
        'department': 'technology',
        'weight': 1.0
    },
    'Data Engineer': {
        'skills': ['python', 'sql', 'etl', 'data warehousing', 'spark', 'hadoop', 'kafka', 'airflow'],
        'department': 'technology',
        'weight': 1.0
    },
    'Security Engineer': {
        'skills': ['network security', 'encryption', 'penetration testing', 'firewalls', 'siem', 'incident response'],
        'department': 'technology',
        'weight': 1.0
    },
    'QA Engineer': {
        'skills': ['testing', 'selenium', 'automation', 'jest', 'pytest', 'bug tracking', 'test planning'],
        'department': 'technology',
        'weight': 1.0
    },
    'Technical Lead': {
        'skills': ['architecture', 'leadership', 'code review', 'mentoring', 'project planning', 'technical strategy'],
        'department': 'technology',
        'weight': 1.0
    },
    'Site Reliability Engineer': {
        'skills': ['linux', 'monitoring', 'automation', 'incident management', 'performance tuning', 'capacity planning'],
        'department': 'technology',
        'weight': 1.0
    },
    'Database Administrator': {
        'skills': ['sql', 'database design', 'performance tuning', 'backup recovery', 'data modeling'],
        'department': 'technology',
        'weight': 1.0
    },
    'Product Manager': {
        'skills': ['project management', 'communication', 'agile', 'leadership', 'analytics', 'user research', 'strategy'],
        'department': 'technology',
        'weight': 0.8
    },
    'UX/UI Designer': {
        'skills': ['html', 'css', 'javascript', 'design', 'prototyping', 'user research', 'figma', 'adobe xd'],
        'department': 'technology',
        'weight': 0.8
    },
    
    # FINANCE ROLES
    'Financial Analyst': {
        'skills': ['financial analysis', 'financial modeling', 'excel', 'valuation', 'budgeting', 'forecasting'],
        'department': 'finance',
        'weight': 1.0
    },
    'Investment Banker': {
        'skills': ['investment banking', 'financial modeling', 'valuation', 'mergers and acquisitions', 'deals'],
        'department': 'finance',
        'weight': 1.0
    },
    'Accountant': {
        'skills': ['accounting', 'bookkeeping', 'quickbooks', 'tax preparation', 'gaap', 'auditing'],
        'department': 'finance',
        'weight': 1.0
    },
    'Financial Advisor': {
        'skills': ['financial planning', 'wealth management', 'investment advice', 'retirement planning'],
        'department': 'finance',
        'weight': 1.0
    },
    'Risk Manager': {
        'skills': ['risk management', 'credit risk', 'market risk', 'compliance', 'regulations'],
        'department': 'finance',
        'weight': 1.0
    },
    'Portfolio Manager': {
        'skills': ['portfolio management', 'investment analysis', 'asset allocation', 'performance measurement'],
        'department': 'finance',
        'weight': 1.0
    },
    'Auditor': {
        'skills': ['auditing', 'internal audit', 'compliance', 'risk assessment', 'accounting'],
        'department': 'finance',
        'weight': 1.0
    },
    'Tax Specialist': {
        'skills': ['tax preparation', 'tax planning', 'tax law', 'irs regulations', 'accounting'],
        'department': 'finance',
        'weight': 1.0
    },
    
    # MARKETING ROLES
    'Digital Marketing Manager': {
        'skills': ['digital marketing', 'seo', 'sem', 'social media', 'content marketing', 'analytics'],
        'department': 'marketing',
        'weight': 1.0
    },
    'SEO Specialist': {
        'skills': ['seo', 'google analytics', 'keyword research', 'link building', 'content optimization'],
        'department': 'marketing',
        'weight': 1.0
    },
    'Social Media Manager': {
        'skills': ['social media', 'content creation', 'community management', 'instagram', 'facebook'],
        'department': 'marketing',
        'weight': 1.0
    },
    'Content Marketer': {
        'skills': ['content marketing', 'copywriting', 'blogging', 'email marketing', 'storytelling'],
        'department': 'marketing',
        'weight': 1.0
    },
    'Brand Manager': {
        'skills': ['brand strategy', 'brand management', 'marketing strategy', 'campaign management'],
        'department': 'marketing',
        'weight': 1.0
    },
    'Marketing Analyst': {
        'skills': ['marketing analytics', 'google analytics', 'data analysis', 'market research'],
        'department': 'marketing',
        'weight': 1.0
    },
    'PR Specialist': {
        'skills': ['public relations', 'media relations', 'press releases', 'crisis communication'],
        'department': 'marketing',
        'weight': 1.0
    },
    
    # HR ROLES
    'HR Manager': {
        'skills': ['hr management', 'recruiting', 'employee relations', 'performance management'],
        'department': 'hr',
        'weight': 1.0
    },
    'Recruiter': {
        'skills': ['recruiting', 'talent acquisition', 'sourcing', 'interviewing', 'applicant tracking'],
        'department': 'hr',
        'weight': 1.0
    },
    'HR Business Partner': {
        'skills': ['hr strategy', 'employee relations', 'talent management', 'organizational development'],
        'department': 'hr',
        'weight': 1.0
    },
    'Training Specialist': {
        'skills': ['training', 'learning and development', 'onboarding', 'employee training'],
        'department': 'hr',
        'weight': 1.0
    },
    'Compensation Analyst': {
        'skills': ['compensation', 'benefits', 'salary benchmarking', 'payroll'],
        'department': 'hr',
        'weight': 1.0
    },
    
    # SALES ROLES
    'Sales Representative': {
        'skills': ['sales', 'lead generation', 'cold calling', 'negotiation', 'closing'],
        'department': 'sales',
        'weight': 1.0
    },
    'Account Executive': {
        'skills': ['sales', 'account management', 'b2b sales', 'relationship building', 'negotiation'],
        'department': 'sales',
        'weight': 1.0
    },
    'Sales Manager': {
        'skills': ['sales management', 'team leadership', 'sales strategy', 'forecasting'],
        'department': 'sales',
        'weight': 1.0
    },
    'Business Development Manager': {
        'skills': ['business development', 'partnerships', 'strategic alliances', 'sales'],
        'department': 'sales',
        'weight': 1.0
    },
    'Account Manager': {
        'skills': ['account management', 'client relations', 'upselling', 'customer service'],
        'department': 'sales',
        'weight': 1.0
    }
}

# Course database (PRESERVED)
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
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize SQLite database"""
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
            last_login TIMESTAMP
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
            contact_info TEXT,
            education TEXT,
            experience TEXT,
            department TEXT,
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
        
        # Create default admin user
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

init_database()

# --------------------------
# AUTHENTICATION DECORATOR
# --------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

init_database()

# --------------------------
# AUTHENTICATION DECORATOR
# --------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
def migrate_database():
    """Add missing columns to existing tables"""
    try:
        conn = sqlite3.connect(app.config['DATABASE'])
        cursor = conn.cursor()
        
        # Check existing columns in user_uploads
        cursor.execute("PRAGMA table_info(user_uploads)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Columns that should exist
        required_columns = ['skills', 'top_roles', 'jobs', 'courses', 'ai_response', 
                           'contact_info', 'education', 'experience', 'department']
        
        # Add missing columns
        for col in required_columns:
            if col not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE user_uploads ADD COLUMN {col} TEXT")
                    print(f"✅ Added missing column: {col}")
                except Exception as e:
                    print(f"⚠️ Could not add column {col}: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Database migration complete")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")

# Call this after init_database()
migrate_database()
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
# --------------------------
# ADVANCED RESUME PARSING
# --------------------------
def extract_text_from_pdf(filepath):
    """Fast text extraction"""
    try:
        if filepath.lower().endswith('.pdf'):
            try:
                import PyPDF2
                text = ""
                with open(filepath, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages[:5]:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    return text
            except:
                pass
        
        # Try reading as text
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        return ""

def extract_contact_info(text):
    """Extract contact information"""
    contact = {
        'name': None,
        'email': None,
        'phone': None,
        'linkedin': None,
        'github': None
    }
    
    lines = text.split('\n')[:10]
    
    # Extract name (usually first non-empty line)
    for line in lines:
        line = line.strip()
        if line and len(line.split()) <= 4 and not any(x in line.lower() for x in ['@', 'http', 'www', 'phone', 'email']):
            contact['name'] = line
            break
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contact['email'] = emails[0]
    
    # Extract phone
    phone_pattern = r'(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}'
    phones = re.findall(phone_pattern, text)
    if phones:
        contact['phone'] = phones[0]
    
    # Extract LinkedIn
    linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
    linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
    if linkedin:
        contact['linkedin'] = linkedin[0]
    
    # Extract GitHub
    github_pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+'
    github = re.findall(github_pattern, text, re.IGNORECASE)
    if github:
        contact['github'] = github[0]
    
    return contact

def extract_education(text):
    """Extract education information"""
    education = []
    edu_keywords = ['bachelor', 'master', 'phd', 'b.tech', 'm.tech', 'b.e', 'm.e', 'b.sc', 'm.sc', 
                    'bca', 'mca', 'mba', 'degree', 'university', 'college', 'institute']
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in edu_keywords):
            edu_text = line.strip()
            # Get next line if it's part of education
            if i + 1 < len(lines) and len(lines[i + 1].strip()) > 0:
                next_line = lines[i + 1].strip()
                if not any(x in next_line.lower() for x in ['experience', 'skill', 'project']):
                    edu_text += " " + next_line
            education.append(edu_text)
    
    return list(set(education))[:3]

def extract_experience_summary(text):
    """Extract work experience summary"""
    exp_keywords = ['experience', 'work', 'employment', 'job']
    experience = []
    
    lines = text.split('\n')
    exp_section = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Find experience section
        if any(keyword in line_lower for keyword in exp_keywords) and 'summary' not in line_lower:
            exp_section = True
            continue
        
        # Extract experience entries (usually with dates)
        if exp_section and re.search(r'\b(19|20)\d{2}\b', line):
            exp_text = line.strip()
            # Get next few lines for context
            for j in range(1, 4):
                if i + j < len(lines) and lines[i + j].strip():
                    next_line = lines[i + j].strip()
                    if not any(x in next_line.lower() for x in ['education', 'skill', 'project']):
                        exp_text += " " + next_line
                    else:
                        break
            experience.append(exp_text)
        
        # End of experience section
        if exp_section and any(keyword in line_lower for keyword in ['education', 'skill', 'project']):
            exp_section = False
    
    return experience[:5]

def extract_skills_from_text(text):
    """Extract ALL skills from text with department categorization"""
    text_lower = text.lower()
    found_skills = []
    skills_by_department = {}
    
    # Check each skill
    for skill_info in ALL_SKILLS_WITH_DEPT:
        skill = skill_info['skill']
        # Check exact match
        if skill in text_lower:
            found_skills.append(skill_info['display'])
            
            # Track by department
            dept = skill_info['department']
            if dept not in skills_by_department:
                skills_by_department[dept] = []
            skills_by_department[dept].append(skill_info['display'])
        
        # Check word boundary match
        elif re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_skills.append(skill_info['display'])
            dept = skill_info['department']
            if dept not in skills_by_department:
                skills_by_department[dept] = []
            skills_by_department[dept].append(skill_info['display'])
    
    # Check variations
    for abbr, full in SKILL_VARIATIONS.items():
        if abbr in text_lower:
            # Find the full skill info
            for skill_info in ALL_SKILLS_WITH_DEPT:
                if skill_info['skill'] == full:
                    if skill_info['display'] not in found_skills:
                        found_skills.append(skill_info['display'])
                        dept = skill_info['department']
                        if dept not in skills_by_department:
                            skills_by_department[dept] = []
                        skills_by_department[dept].append(skill_info['display'])
                    break
    
    # Remove duplicates while preserving order
    unique_skills = []
    for skill in found_skills:
        if skill not in unique_skills:
            unique_skills.append(skill)
    
    return {
        'all': unique_skills[:30],
        'by_department': skills_by_department
    }

# --------------------------
# SMART ROLE PREDICTION
# --------------------------
def predict_top_roles(skills_result):
    """Predict roles based on extracted skills with department awareness"""
    skills_lower = [s.lower() for s in skills_result['all']]
    skills_by_dept = skills_result['by_department']
    
    # Determine primary department
    dept_scores = {}
    for dept, dept_skills in skills_by_dept.items():
        dept_scores[dept] = len(dept_skills)
    
    primary_dept = max(dept_scores.items(), key=lambda x: x[1])[0] if dept_scores else 'technology'
    
    # Score each role
    role_scores = []
    
    for role, requirements in ROLE_REQUIREMENTS.items():
        # Only consider roles from primary department and related departments
        if requirements['department'] != primary_dept and requirements['weight'] < 0.8:
            continue
        
        score = 0
        matched_skills = []
        
        for skill in skills_lower:
            for req_skill in requirements['skills']:
                if req_skill in skill or skill in req_skill:
                    score += 10
                    matched_skills.append(req_skill)
                    break
        
        # Apply department weight
        score = score * requirements['weight']
        
        # Add bonus for multiple matches
        unique_matches = len(set(matched_skills))
        if unique_matches >= 3:
            score += 15
        if unique_matches >= 5:
            score += 25
        
        if score > 30:  # Minimum threshold
            final_score = min(98, int(score))
            role_scores.append((role, final_score, requirements['department']))
    
    # Sort by score
    role_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return top 5 formatted for display
    return [[role, score] for role, score, _ in role_scores[:5]]

# --------------------------
# JOB SEARCH
# --------------------------
def get_jobs_for_role(role):
    """Get job listings"""
    try:
        headers = {
            "X-RapidAPI-Key": JSEARCH_API_KEY,
            "X-RapidAPI-Host": JSEARCH_API_HOST
        }
        querystring = {"query": role, "num_pages": "1", "page": "1"}
        
        response = requests.get(JSEARCH_API_URL, headers=headers, params=querystring, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            jobs = []
            for job in data.get("data", [])[:5]:
                title = job.get("job_title", "No Title")
                link = job.get("job_apply_link") or "#"
                company = job.get("employer_name", "")
                jobs.append((f"{title} at {company}", link))
            if jobs:
                return jobs
    except:
        pass
    
    # Fallback
    search_term = role.lower().replace(' ', '-')
    return [
        (f"{role} - LinkedIn", f"https://www.linkedin.com/jobs/search/?keywords={search_term}"),
        (f"{role} - Indeed", f"https://www.indeed.com/q-{search_term}.html"),
        (f"Remote {role}", f"https://www.linkedin.com/jobs/search/?keywords={search_term}&location=remote"),
        (f"Senior {role}", f"https://www.linkedin.com/jobs/search/?keywords=senior-{search_term}"),
        (f"{role} - Glassdoor", f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={search_term}")
    ]

# --------------------------
# COURSE RECOMMENDATIONS (PRESERVED)
# --------------------------
def recommend_courses(skills):
    """Fast course recommendations"""
    recommended = []
    added_courses = set()
    skills_lower = [s.lower() for s in skills['all'][:5]]
    
    for skill in skills_lower:
        for course_skill, courses in course_db.items():
            if course_skill in skill or skill in course_skill:
                for course in courses[:2]:
                    if course not in added_courses:
                        recommended.append((course_skill.title(), course))
                        added_courses.add(course)
                break
    
    if len(recommended) < 3:
        popular = [
            ('Python', 'Python for Everybody – Coursera'),
            ('JavaScript', 'Modern JavaScript – The Odin Project'),
            ('SQL', 'The Complete SQL Bootcamp – Udemy')
        ]
        for item in popular:
            if item[1] not in added_courses:
                recommended.append(item)
                added_courses.add(item[1])
            if len(recommended) >= 5:
                break
    
    return recommended[:5]

# --------------------------
# AI RESPONSE
# --------------------------
def ai_answer_query(query, skills=None):
    """Quick AI response"""
    if skills is None:
        skills = {'all': []}
    
    query_lower = query.lower()
    
    if 'job' in query_lower or 'career' in query_lower:
        return f"Based on your skills in {', '.join(skills['all'][:3])}, look for roles on LinkedIn and Indeed."
    elif 'learn' in query_lower:
        return f"Check Coursera and Udemy for courses in {', '.join(skills['all'][:2])}."
    elif 'salary' in query_lower:
        return "Tech salaries: Junior $60-85k, Mid $85-120k, Senior $120-180k+"
    else:
        return f"Your skills in {', '.join(skills['all'][:3])} are valuable! Keep learning and networking."

# --------------------------
# ROUTES
# --------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        db = get_db()
        user = db.execute(
            'SELECT * FROM users WHERE email = ? OR username = ?', 
            (email, email)
        ).fetchone()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name'] or user['username']
            
            db = get_db()
            db.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user['id'],)
            )
            db.commit()
            db.close()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        full_name = request.form.get('full_name', '').strip()
        
        if not all([email, username, password]):
            flash('All fields required', 'error')
            return render_template('register.html')
        
        db = get_db()
        existing = db.execute(
            'SELECT * FROM users WHERE email = ? OR username = ?', 
            (email, username)
        ).fetchone()
        
        if existing:
            db.close()
            flash('Email or username already exists', 'error')
            return render_template('register.html')
        
        password_hash = generate_password_hash(password)
        db.execute(
            'INSERT INTO users (email, username, password, full_name) VALUES (?, ?, ?, ?)',
            (email, username, password_hash, full_name)
        )
        db.commit()
        
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        db.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name'] or user['username']
            flash('Registration successful!', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_data = {
        'username': session.get('username', 'User'),
        'full_name': session.get('full_name', 'User')
    }
    
    db = get_db()
    recent = db.execute(
        'SELECT id, filename, upload_time FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 3',
        (session['user_id'],)
    ).fetchall()
    db.close()
    
    recent_uploads = [dict(r) for r in recent]
    
    skills = ['Python', 'JavaScript', 'SQL', 'Communication']
    top_roles = [['Software Engineer', 92], ['Data Scientist', 88], ['DevOps Engineer', 85]]
    jobs = get_jobs_for_role('Software Engineer')
    courses = recommend_courses({'all': skills})
    
    return render_template('index.html',
                          user=user_data,
                          recent_uploads=recent_uploads,
                          skills=skills,
                          top_roles=top_roles,
                          jobs=jobs,
                          courses=courses,
                          show_results=False,
                          now=datetime.now())

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Fast resume analysis with comprehensive parsing"""
    try:
        if 'resume_file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('dashboard'))
        
        file = request.files['resume_file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('dashboard'))
        
        if not allowed_file(file.filename):
            flash('Invalid file type', 'error')
            return redirect(url_for('dashboard'))
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Extract text
        resume_text = extract_text_from_pdf(filepath)
        
        # Extract all information in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            contact_future = executor.submit(extract_contact_info, resume_text)
            education_future = executor.submit(extract_education, resume_text)
            experience_future = executor.submit(extract_experience_summary, resume_text)
            skills_future = executor.submit(extract_skills_from_text, resume_text)
            
            contact_info = contact_future.result()
            education = education_future.result()
            experience = experience_future.result()
            skills_result = skills_future.result()
        
        # Predict roles based on extracted skills
        top_roles = predict_top_roles(skills_result)
        
        # Get jobs and courses
        primary_role = top_roles[0][0] if top_roles else "Software Engineer"
        jobs = get_jobs_for_role(primary_role)
        courses = recommend_courses(skills_result)
        
        # Save to database
        db = get_db()
        cursor = db.execute('''
            INSERT INTO user_uploads 
            (user_id, filename, filepath, skills, top_roles, jobs, courses, contact_info, education, experience)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            filename,
            filepath,
            json.dumps(skills_result['all']),
            json.dumps(top_roles),
            json.dumps(jobs),
            json.dumps(courses),
            json.dumps(contact_info),
            json.dumps(education),
            json.dumps(experience)
        ))
        db.commit()
        upload_id = cursor.lastrowid
        db.close()
        
        flash('Analysis complete! Found {} skills'.format(len(skills_result['all'])), 'success')
        return redirect(url_for('view_upload', upload_id=upload_id))
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        flash('Analysis failed', 'error')
        return redirect(url_for('dashboard'))

@app.route('/view/<int:upload_id>')
@login_required
def view_upload(upload_id):
    db = get_db()
    upload = db.execute(
        'SELECT * FROM user_uploads WHERE id = ? AND user_id = ?',
        (upload_id, session['user_id'])
    ).fetchone()
    db.close()
    
    if not upload:
        flash('Upload not found', 'error')
        return redirect(url_for('dashboard'))
    
    # Parse data
    skills = json.loads(upload['skills']) if upload['skills'] else []
    top_roles = json.loads(upload['top_roles']) if upload['top_roles'] else []
    jobs = json.loads(upload['jobs']) if upload['jobs'] else []
    courses = json.loads(upload['courses']) if upload['courses'] else []
    contact_info = json.loads(upload['contact_info']) if upload['contact_info'] else {}
    education = json.loads(upload['education']) if upload['education'] else []
    experience = json.loads(upload['experience']) if upload['experience'] else []
    
    user_data = {
        'username': session.get('username', 'User'),
        'full_name': session.get('full_name', 'User')
    }
    
    return render_template('index.html',
                          user=user_data,
                          skills=skills,
                          top_roles=top_roles,
                          jobs=jobs,
                          courses=courses,
                          contact_info=contact_info,
                          education=education,
                          experience=experience,
                          filename=upload['filename'],
                          show_results=True,
                          now=datetime.now())

@app.route('/profile')
@login_required
def profile():
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    uploads = db.execute(
        'SELECT COUNT(*) as count FROM user_uploads WHERE user_id = ?',
        (session['user_id'],)
    ).fetchone()
    
    recent = db.execute(
        'SELECT * FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 5',
        (session['user_id'],)
    ).fetchall()
    db.close()
    
    user_data = dict(user) if user else {}
    uploads_list = [dict(u) for u in recent]
    
    return render_template('profile.html', 
                          user=user_data,
                          upload_count=uploads['count'] if uploads else 0,
                          recent_uploads=uploads_list)

@app.route('/history')
@login_required
def history():
    """Upload history page - Simplified version"""
    try:
        db = get_db()
        
        # Simple query with only essential columns
        uploads = db.execute(
            'SELECT id, filename, upload_time FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC',
            (session['user_id'],)
        ).fetchall()
        db.close()
        
        # Convert to list of dictionaries
        uploads_list = []
        for upload in uploads:
            uploads_list.append({
                'id': upload['id'],
                'filename': upload['filename'],
                'upload_time': upload['upload_time'],
                'skills_parsed': ['Python', 'JavaScript'],  # Placeholder
                'roles_parsed': [['Software Engineer', 85]]  # Placeholder
            })
        
        user_data = {
            'username': session.get('username', 'User'),
            'full_name': session.get('full_name', 'User')
        }
        
        return render_template('history.html', 
                             user=user_data,
                             uploads=uploads_list)
        
    except Exception as e:
        print(f"History error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return empty list instead of redirecting
        user_data = {
            'username': session.get('username', 'User'),
            'full_name': session.get('full_name', 'User')
        }
        return render_template('history.html', 
                             user=user_data,
                             uploads=[])

@app.route('/job-match', methods=['GET', 'POST'])
@login_required
def job_match():
    """Job matching page - compare resume with job description"""
    if request.method == 'POST':
        try:
            if 'resume_file' not in request.files or 'job_file' not in request.files:
                flash('Please upload both files', 'error')
                return redirect(url_for('job_match'))
            
            resume_file = request.files['resume_file']
            job_file = request.files['job_file']
            
            if resume_file.filename == '' or job_file.filename == '':
                flash('Please select both files', 'error')
                return redirect(url_for('job_match'))
            
            # Save files temporarily
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save resume
            resume_filename = secure_filename(resume_file.filename)
            resume_filename = f"match_resume_{timestamp}_{resume_filename}"
            resume_filepath = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
            resume_file.save(resume_filepath)
            
            # Save job description
            job_filename = secure_filename(job_file.filename)
            job_filename = f"match_job_{timestamp}_{job_filename}"
            job_filepath = os.path.join(app.config['UPLOAD_FOLDER'], job_filename)
            job_file.save(job_filepath)
            
            # Extract text from both files
            resume_text = extract_text_from_pdf(resume_filepath)
            job_text = extract_text_from_pdf(job_filepath)
            
            # Clean up temp files
            try:
                os.remove(resume_filepath)
                os.remove(job_filepath)
            except:
                pass
            
            if not resume_text or not job_text:
                flash('Could not extract text from files', 'error')
                return redirect(url_for('job_match'))
            
            # Extract skills
            resume_skills_result = extract_skills_from_text(resume_text)
            job_skills_result = extract_skills_from_text(job_text)
            
            resume_skills = resume_skills_result['all']
            job_skills = job_skills_result['all']
            
            # Calculate match score
            if not job_skills:
                match_score = 70
                matched_skills = resume_skills[:5]
                missing_skills = []
            else:
                resume_set = set([s.lower() for s in resume_skills])
                job_set = set([s.lower() for s in job_skills])
                
                matched = list(resume_set.intersection(job_set))
                missing = list(job_set - resume_set)
                
                match_score = int((len(matched) / len(job_set)) * 100) if job_set else 70
                match_score = min(98, max(30, match_score))
            
            # Create match_results dictionary (what your template expects)
            match_results = {
                'overall_score': match_score,
                'match_level': 'Excellent Match' if match_score >= 80 else 'Good Match' if match_score >= 60 else 'Fair Match' if match_score >= 40 else 'Needs Improvement',
                'skill_match': match_score,
                'experience_match': 80,  # Default value
                'matched_skills': [s.title() for s in matched[:15]],
                'missing_skills': [s.title() for s in missing[:15]],
                'total_job_skills': len(job_set),
                'total_resume_skills': len(resume_set),
                'resume_experience': 3,  # Default value
                'required_experience': 2  # Default value
            }
            
            return render_template('job_match_results.html',
                                 match_results=match_results,
                                 job_title="Job Position",
                                 resume_skills=resume_skills[:15],
                                 job_skills=job_skills[:15])
            
        except Exception as e:
            logger.error(f"Job match error: {e}")
            traceback.print_exc()
            flash(f'Job match failed: {str(e)}', 'error')
            return redirect(url_for('job_match'))
    
    return render_template('job_match.html', user={'username': session.get('username', 'User')})
@app.route('/test-upload')
@login_required
def test_upload():
    """Test endpoint for quick demo"""
    test_skills = ['Python', 'JavaScript', 'React', 'Node.js', 'MongoDB', 'AWS', 'Docker', 'Git']
    test_roles = [['Full Stack Developer', 92], ['Software Engineer', 88], ['DevOps Engineer', 85]]
    test_jobs = get_jobs_for_role('Software Engineer')
    test_courses = recommend_courses({'all': test_skills})
    
    user_data = {
        'username': session.get('username', 'User'),
        'full_name': session.get('full_name', 'User')
    }
    
    return render_template('index.html',
                          user=user_data,
                          skills=test_skills,
                          top_roles=test_roles,
                          jobs=test_jobs,
                          courses=test_courses,
                          filename="test_resume.pdf",
                          contact_info={'name': 'John Doe', 'email': 'john@example.com'},
                          education=['BS Computer Science'],
                          experience=['Software Engineer at Tech Corp'],
                          show_results=True,
                          now=datetime.now())

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        # Get user's skills
        db = get_db()
        latest = db.execute(
            'SELECT skills FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 1',
            (session['user_id'],)
        ).fetchone()
        db.close()
        
        skills = json.loads(latest['skills']) if latest and latest['skills'] else []
        
        response = ai_answer_query(user_message, {'all': skills})
        
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'response': 'Sorry, I encountered an error.'})

@app.route('/quick-actions', methods=['POST'])
@login_required
def quick_actions():
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'refresh_jobs':
            db = get_db()
            latest = db.execute(
                'SELECT top_roles FROM user_uploads WHERE user_id = ? ORDER BY upload_time DESC LIMIT 1',
                (session['user_id'],)
            ).fetchone()
            db.close()
            
            if latest and latest['top_roles']:
                top_roles = json.loads(latest['top_roles'])
                role = top_roles[0][0] if top_roles else "Software Engineer"
                jobs = get_jobs_for_role(role)
                return jsonify({'success': True, 'jobs': jobs})
        
        elif action == 'get_career_advice':
            return jsonify({
                'success': True,
                'advice': "Keep learning and building projects. Network on LinkedIn."
            })
        
        elif action == 'recommend_courses_quick':
            return jsonify({
                'success': True,
                'courses': [('Python', 'Python for Everybody'), ('JavaScript', 'Modern JavaScript')]
            })
        
        return jsonify({'success': False})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'time': datetime.now().isoformat()})

@app.route('/debug')
@login_required
def debug():
    db = get_db()
    uploads_count = db.execute('SELECT COUNT(*) as c FROM user_uploads WHERE user_id = ?', (session['user_id'],)).fetchone()
    db.close()
    
    return jsonify({
        'session': dict(session),
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'uploads_count': uploads_count['c'] if uploads_count else 0
    })

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error='Server error'), 500

# --------------------------
# START APPLICATION
# --------------------------
if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("✅ SkillSense Enhanced - Ready!")
    print("=" * 60)
    print("🌐 URL: http://localhost:5000")
    print("👤 Admin: admin@skillsense.com / admin123")
    print("📁 Upload folder:", app.config['UPLOAD_FOLDER'])
    print("💾 Database:", app.config['DATABASE'])
    print("=" * 60 + "\n")
    
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5000,
        threaded=True
    )