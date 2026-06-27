"""
generate_dataset.py
Generates a synthetic dataset of 1000 internship postings (500 fake, 500 genuine)
and saves to dataset/internship_dataset.csv
"""

import pandas as pd
import random
import os

random.seed(42)

# ─────────────────────────────────────────────
# FAKE internship building blocks
# ─────────────────────────────────────────────

fake_titles = [
    "Online Data Entry Operator", "Work From Home – Typing Job",
    "Social Media Promoter", "Easy Copy-Paste Job",
    "Survey Filling Executive", "WhatsApp Marketing Intern",
    "Telegram Channel Manager", "Simple Form Filling Job",
    "Online Ad Posting Intern", "Part-Time SMS Sending Job",
    "Guaranteed Placement Intern", "Instant Hiring – No Interview",
    "Home Based Packaging Intern", "Mobile App Testing Intern (No Skills Needed)",
    "Affiliate Marketing Trainee", "Network Marketing Associate",
    "Digital Marketing Intern – Earn ₹1 Lakh/Month",
    "Online Reselling Business Intern", "Virtual Assistant – Immediate Start",
    "Crypto Trading Intern", "Paid Review Writer",
    "YouTube Channel Growth Intern", "Instagram Influencer Intern",
    "Quick Money Online Intern", "Referral Program Coordinator",
]

fake_companies = [
    "GlobalTech Solutions Pvt Ltd", "EarnMore India",
    "QuickHire Consultancy", "DreamJob Services",
    "FastTrack Careers", "MoneyPlus Digital",
    "SkillBridge Academy", "TopNotch Placements",
    "EliteHire Solutions", "ProStart Global",
    "RapidGrowth Inc", "NextGen Opportunities",
    "SmartEarn Technologies", "InfoGain Services",
    "TrustHire India", "PrimePath Consulting",
    "ClickEarn Solutions", "BrightFuture Placements",
    "AlphaHire Digital", "MegaSuccess Corp",
    "GoldenGate Careers", "Universal Staffing Hub",
    "ZenithPlacement Services", "DigiWork India",
    "CareerBoost Academy",
]

fake_contact_methods = [
    "WhatsApp only", "Telegram group", "Personal Gmail",
    "WhatsApp/Telegram", "Send DM on Instagram",
    "Call on personal mobile", "WhatsApp group link",
    "Telegram channel", "SMS only", "Facebook Messenger",
]

fake_description_templates = [
    # Fee-based scams
    "Exciting opportunity to earn ₹{stipend} per month from home! Just pay a one-time registration fee of ₹{fee} to get started. No experience or interview required. Start earning immediately after payment confirmation.",
    "We are hiring freshers for data entry work. Earn up to ₹{stipend}/month with just 2 hours of daily work. A refundable security deposit of ₹{fee} is required. Guaranteed income with no risk involved.",
    "Join our team and earn ₹{stipend} monthly! Pay ₹{fee} registration fee and start working today. No skills needed, training provided free. This offer is valid for limited seats only – apply now!",
    "Work from home opportunity! Earn ₹{stipend}/month doing simple copy-paste tasks. One-time processing fee of ₹{fee} applicable. 100% genuine opportunity with money-back guarantee.",
    "Urgent hiring for online typing jobs! Salary ₹{stipend}/month. Small registration fee of ₹{fee} to cover admin costs. Thousands of students already earning. Don't miss this chance!",
    "Guaranteed placement after internship! Earn ₹{stipend} per month during training. Pay ₹{fee} as course material fee. Certificate provided. Companies like Google and Amazon hire from our program.",
    "Hiring interns for social media work. Stipend ₹{stipend}/month. To reserve your seat, pay ₹{fee} enrollment fee via UPI. Limited spots available – hurry up!",

    # Data harvesting scams
    "Apply now for an exclusive internship program! Fill the Google Form with your Aadhaar number, PAN card, and bank details for verification. Stipend of ₹{stipend}/month credited directly to your account.",
    "We need your full personal details including bank account number, IFSC code, and ID proof for onboarding. Stipend ₹{stipend}/month for simple tasks. No interview needed, just submit documents.",
    "Congratulations! You've been selected for our premium internship. Share your personal documents including Aadhaar, PAN, and passport photo via WhatsApp for immediate joining. Earn ₹{stipend}/month.",

    # MLM disguised as internships
    "Join our network marketing internship! Earn ₹{stipend}/month by recruiting 5 people. Each referral earns you ₹500 bonus. Build your own team and earn unlimited passive income!",
    "Become a digital marketing intern! Your job is to promote our products on social media and recruit more interns. Commission-based earning up to ₹{stipend}/month. No fixed salary but unlimited potential!",
    "Exciting MLM business internship! Invest ₹{fee} and start earning through our multi-level referral program. Top earners make ₹{stipend}/month. Be your own boss!",

    # Urgency and pressure tactics
    "URGENT: Last 3 seats remaining for our internship program! Stipend ₹{stipend}/month. Registration closes in 24 hours. Pay ₹{fee} now to confirm your spot. Don't think – just apply!",
    "LIMITED TIME OFFER: Paid internship with ₹{stipend}/month stipend. This opportunity won't come again! Apply before midnight today. Fee ₹{fee} for processing. Act fast!",
    "FLASH HIRING: No interview, no resume needed. Just register with ₹{fee} and start earning ₹{stipend}/month from tomorrow. Verified by thousands of students. 100% safe!",

    # Unrealistic promises
    "Earn ₹{stipend} per month working just 1 hour daily! Our AI-powered platform assigns tasks automatically. No skills required. Pay ₹{fee} for platform access and start earning today.",
    "Work from anywhere in the world and earn ₹{stipend}/month. We provide all equipment and training. Just pay ₹{fee} for shipping of your work kit. Start within 48 hours of payment.",
    "Make ₹{stipend}/month with our automated earning system! Simply install our app, complete daily tasks, and withdraw earnings instantly. Registration fee ₹{fee} applicable.",

    # Vague descriptions
    "We are a leading company looking for interns. Good pay of ₹{stipend}/month. Easy work. Apply now by sending ₹{fee} to our UPI. We will contact you with details after payment.",
    "Internship available. Work from home. Earn well. Contact us on WhatsApp for more details. Stipend ₹{stipend}/month. Small fee of ₹{fee} for registration. Hurry, spots filling fast!",
    "Great opportunity for students! Earn ₹{stipend}/month. Work is simple and can be done on mobile phone. Pay ₹{fee} to join. We have placed 10000+ students in top companies.",
]

fake_requirements_list = [
    "No experience needed", "Anyone can apply",
    "No skills required – training provided", "Just need a smartphone",
    "Must have UPI or bank account", "Class 10 pass or above",
    "No qualification required", "Basic English knowledge",
    "Ability to use WhatsApp", "Must be willing to pay registration fee",
    "Smartphone with internet connection", "Freshers only",
    "No resume or interview needed", "Age 16 and above",
    "Must share ID proof for verification",
]

# ─────────────────────────────────────────────
# GENUINE internship building blocks
# ─────────────────────────────────────────────

genuine_titles = [
    "Software Engineering Intern", "Data Science Intern",
    "Backend Developer Intern", "Frontend Developer Intern",
    "Full Stack Developer Intern", "Machine Learning Intern",
    "Product Management Intern", "Business Analyst Intern",
    "UI/UX Design Intern", "DevOps Intern",
    "Cloud Engineering Intern", "Cybersecurity Intern",
    "Quality Assurance Intern", "Mobile App Developer Intern",
    "Research Intern – NLP", "Embedded Systems Intern",
    "Content Writing Intern", "Marketing Analytics Intern",
    "Financial Analyst Intern", "Human Resources Intern",
    "Operations Intern", "Supply Chain Intern",
    "Graphic Design Intern", "Video Editing Intern",
    "Technical Writer Intern", "Database Administrator Intern",
    "Blockchain Developer Intern", "IoT Intern",
    "Robotics Intern", "Quantitative Research Intern",
]

genuine_companies = [
    "Tata Consultancy Services", "Infosys", "Wipro", "HCL Technologies",
    "Tech Mahindra", "Google India", "Microsoft India",
    "Amazon India", "Flipkart", "Zomato", "Swiggy",
    "Paytm", "PhonePe", "Razorpay", "Zerodha",
    "CRED", "Meesho", "Ola", "Uber India",
    "Reliance Jio", "Byju's", "Unacademy",
    "Freshworks", "Zoho", "MakeMyTrip",
    "Nykaa", "Dunzo", "Groww", "upGrad",
    "Accenture India", "Deloitte India", "EY India",
    "KPMG India", "PwC India", "Goldman Sachs India",
    "JP Morgan India", "Morgan Stanley India",
    "Adobe India", "Cisco India", "Intel India",
    "Samsung R&D India", "Qualcomm India",
    "ISRO", "DRDO", "IIT Bombay Research Lab",
    "IISc Bangalore", "Tata Steel", "Mahindra & Mahindra",
    "Bosch India", "Siemens India",
]

genuine_contact_methods = [
    "careers@company.com", "Apply via company careers portal",
    "LinkedIn application", "Apply on Internshala",
    "Apply on LinkedIn Jobs", "hr@company.com",
    "Apply via Naukri.com", "recruitment@company.com",
    "Company official website", "Apply through campus placement cell",
    "talent@company.com", "hiring@company.com",
    "Apply on AngelList", "University placement portal",
]

genuine_description_templates = [
    # Software/Tech roles
    "We are looking for a motivated {title} to join our engineering team for a {duration}-month internship. You will work on {tech_area} projects, collaborate with senior engineers, and contribute to production codebases. Strong fundamentals in {skill1} and {skill2} are expected.",
    "Join our {department} team as a {title}. During this {duration}-month internship, you will design, develop, and test features for our {product}. You will participate in code reviews, sprint planning, and gain exposure to agile development practices.",
    "As a {title} at {company}, you will work on building scalable solutions using {skill1} and {skill2}. This is a {duration}-month program with mentorship from industry experts. Top performers may receive a pre-placement offer.",
    "We are hiring a {title} for our {location} office. The role involves working on {tech_area} using {skill1}, {skill2}, and {skill3}. You'll collaborate with cross-functional teams and present your work to stakeholders at the end of the internship.",
    "Seeking a {title} for a {duration}-month internship. Responsibilities include developing features, writing unit tests, and documenting technical specifications. You will gain hands-on experience with {skill1} and {skill2} in a fast-paced environment.",

    # Data/ML roles
    "We are looking for a {title} to work on data analysis and visualization projects. You will use {skill1} and {skill2} to extract insights from large datasets. Experience with SQL and statistical methods is preferred. Duration: {duration} months.",
    "Join us as a {title} and help build machine learning models for {tech_area}. You will preprocess data, train models, evaluate performance, and deploy solutions. Familiarity with {skill1}, {skill2}, and deep learning frameworks is a plus.",
    "As a {title}, you will analyze business data using {skill1} and {skill2}, create dashboards, and present findings to the management team. This is a {duration}-month internship with exposure to real-world business problems.",

    # Business/Non-tech roles
    "We are seeking a {title} for a {duration}-month internship in our {location} office. You will assist in {tech_area}, prepare reports, and support the team with day-to-day operations. Strong communication and analytical skills required.",
    "Join our team as a {title}. You will work closely with the {department} team on projects involving {tech_area}. Responsibilities include market research, data analysis, and creating presentations for senior leadership.",
    "Looking for a {title} to support our {department} team. The intern will help with {tech_area}, coordinate with internal teams, and contribute to process improvements. Duration: {duration} months with a monthly stipend.",

    # Research/Specialized roles
    "We have an opening for a {title} in our R&D division. You will work on cutting-edge {tech_area} projects, conduct literature reviews, run experiments, and contribute to research publications. Strong background in {skill1} and {skill2} required.",
    "Exciting internship opportunity as a {title}! Work on {tech_area} with our research team. You will develop prototypes, analyze results, and present findings. This {duration}-month program is ideal for students passionate about innovation.",

    # Design/Creative roles
    "We are hiring a {title} for our design team. You will create user interfaces, conduct user research, and build interactive prototypes using {skill1} and {skill2}. A strong portfolio demonstrating your design thinking process is required.",
    "Join us as a {title} and contribute to creating compelling visual content for our brand. You will work with the marketing and product teams on {tech_area}. Proficiency in {skill1} and {skill2} is essential. Duration: {duration} months.",
]

genuine_skills = [
    "Python", "Java", "JavaScript", "C++", "Go", "Rust",
    "React", "Angular", "Vue.js", "Node.js", "Django", "Flask",
    "Spring Boot", "TypeScript", "SQL", "MongoDB", "PostgreSQL",
    "AWS", "Azure", "GCP", "Docker", "Kubernetes",
    "TensorFlow", "PyTorch", "scikit-learn", "Pandas",
    "Figma", "Adobe XD", "Sketch", "Photoshop", "Illustrator",
    "Git", "Linux", "REST APIs", "GraphQL", "Redis",
    "Tableau", "Power BI", "Excel", "R", "MATLAB",
    "Hadoop", "Spark", "Kafka", "Airflow",
    "HTML/CSS", "Swift", "Kotlin", "Flutter", "React Native",
]

genuine_tech_areas = [
    "recommendation systems", "natural language processing",
    "computer vision", "cloud infrastructure",
    "payment processing", "e-commerce platforms",
    "search optimization", "ad-tech",
    "logistics and supply chain", "fintech solutions",
    "healthcare analytics", "fraud detection",
    "autonomous systems", "IoT platforms",
    "content management", "social media analytics",
    "customer experience", "inventory management",
    "enterprise SaaS", "developer tools",
    "brand strategy", "digital marketing campaigns",
    "financial modeling", "risk assessment",
    "HR operations", "talent acquisition",
    "microservices architecture", "real-time data pipelines",
]

genuine_departments = [
    "Engineering", "Product", "Data Science", "Marketing",
    "Finance", "Operations", "Human Resources", "Design",
    "Research", "Business Development", "Strategy", "Analytics",
]

genuine_locations = [
    "Bangalore", "Hyderabad", "Mumbai", "Pune", "Delhi NCR",
    "Chennai", "Gurgaon", "Noida", "Kolkata", "Ahmedabad",
    "Remote", "Hybrid (Bangalore)", "Hybrid (Mumbai)",
]

genuine_requirements_templates = [
    "Currently pursuing B.Tech/B.E. in {branch}. Proficiency in {skill1} and {skill2}. Good problem-solving skills.",
    "B.Tech/M.Tech student in {branch} with knowledge of {skill1}, {skill2}, and {skill3}. CGPA 7.0 or above preferred.",
    "Pursuing B.Tech/BCA/MCA in {branch}. Hands-on experience with {skill1} and {skill2}. Strong analytical thinking.",
    "Final year or pre-final year student in {branch}. Must know {skill1} and {skill2}. Excellent communication skills required.",
    "Graduate or postgraduate in {branch}. Experience with {skill1} preferred. Ability to work in a team and meet deadlines.",
    "Any degree with strong aptitude for {skill1} and {skill2}. Portfolio or GitHub profile with relevant projects is a plus.",
    "Engineering student with knowledge of {skill1}, {skill2}. Available for full-time internship of 3-6 months.",
    "B.Sc/M.Sc in {branch}. Research experience in {skill1} is preferred. Strong written and verbal communication.",
]

genuine_branches = [
    "Computer Science", "Information Technology", "Electronics",
    "Electrical Engineering", "Mechanical Engineering",
    "Data Science", "Artificial Intelligence",
    "Commerce", "MBA", "Statistics", "Mathematics",
    "Design", "Mass Communication",
]


def generate_fake_postings(n=500):
    """Generate n fake internship postings."""
    rows = []
    for i in range(n):
        title = random.choice(fake_titles)
        company = random.choice(fake_companies)
        contact = random.choice(fake_contact_methods)

        # Unrealistic stipends for fake postings
        stipend_val = random.choice([50000, 60000, 75000, 80000, 100000, 30000, 40000, 45000])
        fee_val = random.choice([500, 999, 1500, 1999, 2500, 3000, 5000, 299, 199])

        template = random.choice(fake_description_templates)
        description = template.format(
            stipend=f"{stipend_val:,}",
            fee=f"{fee_val:,}",
        )

        stipend_str = f"₹{stipend_val:,}/month"
        requirements = random.choice(fake_requirements_list)

        rows.append({
            "title": title,
            "company": company,
            "description": description,
            "stipend": stipend_str,
            "requirements": requirements,
            "contact_method": contact,
            "label": 1,
        })
    return rows


def generate_genuine_postings(n=500):
    """Generate n genuine internship postings."""
    rows = []
    for i in range(n):
        title = random.choice(genuine_titles)
        company = random.choice(genuine_companies)
        contact = random.choice(genuine_contact_methods)

        # Realistic stipends for genuine postings
        stipend_val = random.choice([
            5000, 8000, 10000, 12000, 15000, 18000, 20000, 25000,
            7000, 9000, 11000, 14000, 16000, 22000,
        ])
        stipend_str = f"₹{stipend_val:,}/month"

        duration = random.choice([2, 3, 4, 6])
        location = random.choice(genuine_locations)
        department = random.choice(genuine_departments)
        tech_area = random.choice(genuine_tech_areas)

        skills = random.sample(genuine_skills, k=min(4, len(genuine_skills)))
        skill1, skill2, skill3 = skills[0], skills[1], skills[2]

        product_names = [
            "mobile app", "web platform", "internal tools",
            "customer-facing dashboard", "API gateway",
            "analytics platform", "recommendation engine",
            "marketplace", "payment system", "core platform",
        ]
        product = random.choice(product_names)

        template = random.choice(genuine_description_templates)
        description = template.format(
            title=title,
            company=company,
            duration=duration,
            location=location,
            department=department,
            tech_area=tech_area,
            skill1=skill1,
            skill2=skill2,
            skill3=skill3,
            product=product,
        )

        # Generate requirements
        req_template = random.choice(genuine_requirements_templates)
        branch = random.choice(genuine_branches)
        requirements = req_template.format(
            branch=branch,
            skill1=skill1,
            skill2=skill2,
            skill3=skill3,
        )

        rows.append({
            "title": title,
            "company": company,
            "description": description,
            "stipend": stipend_str,
            "requirements": requirements,
            "contact_method": contact,
            "label": 0,
        })
    return rows


def main():
    print("Generating synthetic internship dataset...")

    fake_rows = generate_fake_postings(500)
    genuine_rows = generate_genuine_postings(500)

    all_rows = fake_rows + genuine_rows
    random.shuffle(all_rows)

    df = pd.DataFrame(all_rows, columns=[
        "title", "company", "description", "stipend",
        "requirements", "contact_method", "label"
    ])

    # Create directory if it doesn't exist
    os.makedirs("dataset", exist_ok=True)

    # Save to CSV with proper quoting
    output_path = os.path.join("dataset", "internship_dataset.csv")
    df.to_csv(output_path, index=False, quoting=1)  # quoting=1 => QUOTE_ALL

    print(f"Dataset saved to {output_path}")
    print(f"Total rows: {len(df)}")
    print(f"Fake (label=1): {(df['label'] == 1).sum()}")
    print(f"Genuine (label=0): {(df['label'] == 0).sum()}")
    print(f"\nSample rows:")
    print(df.head(5).to_string(max_colwidth=80))


if __name__ == "__main__":
    main()
