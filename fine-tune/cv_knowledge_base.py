#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cv_knowledge_base.py
===================
Từ điển kiến thức (ground-truth) cho bộ sinh CV tổng hợp.

Mọi dữ liệu trong đây là dữ liệu "giả lập nhưng thực tế" mô phỏng thị trường
tuyển dụng IT Việt Nam: trường học, công ty, tech stack, chức danh, cách diễn đạt.

Cấu trúc:
  * Tên, liên hệ, trường học, công ty, bảng thành tựu
  * ROLE_BANKS: theo 8 nhóm ngành, mỗi nhóm có chức danh + tech stack + domain
  * LEVEL_BANKS: theo 5 cấp bậc, mỗi cấp bậc có độ sâu kinh nghiệm, số dự án,
    câu mô tả trách nhiệm, chỉ số KPI
  * TEMPLATES: khuôn văn bản tiếng Việt / tiếng Anh cho từng section
"""

from __future__ import annotations

# ============================================================ HỌ TÊN & LIÊN HỆ
VN_SURNAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Phan", "Vũ", "Võ", "Đặng", "Bùi",
    "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đinh", "Mai", "Trương", "Cao", "Tô",
    "Lưu", "Chu", "Tạ", "Hà", "Kiều", "Thái", "Vũ", "Lao", "Quách", "Từ",
    "Ông", "Bạch", "Doãn", "Giang", "Khương", "Mạc", "Ninh", "Ô", "Phùng",
]
VN_MIDDLE = [
    "Văn", "Hữu", "Thị", "Ngọc", "Minh", "Quang", "Thanh", "Anh", "Tuấn", "Xuân",
    "Hoài", "Thu", "Bảo", "Đức", "Khắc", "Công", "Đình", "Gia", "Khánh", "Phước",
]
VN_GIVEN = [
    "An", "Bình", "Cường", "Dũng", "Giang", "Hà", "Hải", "Hùng", "Khôi", "Long",
    "Mạnh", "Nam", "Phong", "Quân", "Quý", "Sơn", "Tài", "Thắng", "Toàn", "Tuấn",
    "Việt", "Vinh", "Bảo", "Cảnh", "Dũng", "Hiếu", "Khoa", "Lộc", "Nghĩa", "Phúc",
    "Quang", "Tâm", "Thái", "Trung", "Tùng", "Văn", "Yến", "Duy", "Huy", "Kiệt",
]
EN_FIRST = [
    "Alex", "Brian", "Chris", "Daniel", "Emily", "Felix", "Grace", "Henry", "Ivy",
    "Jack", "Kevin", "Laura", "Mason", "Nina", "Oscar", "Priya", "Quinn", "Rachel",
    "Simon", "Tessa", "Victor", "Wendy", "Yara", "Zane", "Anna", "Ben", "Chloe",
]
EN_LAST = [
    "Anderson", "Baker", "Carter", "Davis", "Edwards", "Foster", "Green", "Harris",
    "Irwin", "Jones", "Kim", "Lopez", "Miller", "Nguyen", "Owens", "Park", "Reed",
    "Singh", "Turner", "Usman", "Vega", "Walker", "Xu", "Young", "Zimmerman",
]

CITIES_VN = [
    "Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Biên Hòa",
    "Huế", "Nha Trang", "Đà Lạt", "Vũng Tàu", "Hạ Long", "Nam Định", "Vinh",
    "Buôn Ma Thuột", "Thái Nguyên", "Quy Nhơn",
]
CITIES_EN = [
    "Ho Chi Minh City, Vietnam", "Hanoi, Vietnam", "Da Nang, Vietnam",
    "Singapore", "Bangkok, Thailand", "Remote (GMT+7)", "Ho Chi Minh City, Vietnam",
]

EMAIL_DOMAINS = ["gmail.com", "gmail.com", "outlook.com", "hotmail.com", "mail.com"]


# ============================================================ TRƯỜNG HỌC
SCHOOLS_VN = [
    ("Trường Đại học Bách Khoa TP.HCM", "Khoa học Máy tính"),
    ("Trường Đại học Bách Khoa Hà Nội", "Khoa học Máy tính"),
    ("Trường Đại học FPT", "Kỹ thuật Phần mềm"),
    ("Trường Đại học Công nghệ TP.HCM", "Kỹ thuật Phần mềm"),
    ("Học viện Công nghệ Bưu chính Viễn thông", "Kỹ thuật Phần mềm"),
    ("Trường Đại học Quốc gia TP.HCM", "Khoa học Máy tính"),
    ("Trường Đại học Thủy Lợi", "Kỹ thuật Phần mềm"),
    ("Trường Đại học Công nghiệp TP.HCM", "Kỹ thuật Phần mềm"),
    ("Trường Đại học Điện lực", "Kỹ thuật Phần mềm"),
    ("Trường Đại học Kinh tế - Kỹ thuật TP.HCM", "Khoa học Máy tính"),
    ("Học viện Công nghệ Viettel", "Kỹ thuật Phần mềm"),
]
SCHOOLS_VN_COURSE = [
    ("Trường Cao đẳng Công nghệ FPT", "Lập trình phần mềm"),
    ("Trường Cao đẳng FPoly", "Lập trình phần mềm"),
    ("Trường Cao đẳng Công nghệ Sài Gòn", "Lập trình phần mềm"),
    ("Trường Cao đẳng Công nghệ Hà Nội", "Lập trình phần mềm"),
]

# ============================================================ CÔNG TY
COMPANIES_VN = [
    "FPT Software", "Viettel Software", "VNG Corporation", "MoMo",
    "Shopee Vietnam", "Grab Vietnam", "Techcombank", "VNPT IT", "Viettel PAY",
    "TMA Solutions", "KMS Technology", "Simbicon", "Topica", "Vinsoft",
    "Zalo", "Bitexco Digital", "Ngân hàng Ngoại thương Việt Nam", "Kiosk VN",
    "Sun Medical", "LogiGear Vietnam", "TMA", "Ncompact", "Blueocean Digital",
    "Home Credit Vietnam", "Vietjet Air", "VinFast", "Rất nhiều", "Tổng công ty",
]
COMPANIES_EN = [
    "Ninja Van", "Grab", "Sea Ltd", "Gojek", "Bukalapak", "Traveloka", "Shopee",
    "Standard Chartered", "Wise", "Grabtech", "Binance Vietnam", "Paytm VN",
]

# ============================================================ CHỨNG CHỈ
CERTS_VN = [
    "Google IT Support Professional Certificate",
    "AWS Certified Cloud Practitioner",
    "Microsoft Certified: Azure Fundamentals (AZ-900)",
    "Scrum Fundamentals Certified (SFC)",
    "Certified Kubernetes Administrator (CKA)",
    "Oracle Java SE 8 Programmer",
    "TensorFlow Developer Certificate",
    "AWS Certified Solutions Architect – Associate",
    "PMI Professional in Business Analysis (PMP)",
    "Certified Information Systems Security Professional (CISSP)",
    "CompTIA Security+",
    "ISTQB Certified Tester - Advanced Level",
    "Databricks Certified Data Engineer Associate",
    "HashiCorp Certified: Terraform Associate",
    "Meta Front-End Developer Certificate",
    "DeepLearning.AI - Generative AI for Everyone",
]
CERTS_EN = [
    "AWS Certified Developer - Associate",
    "Google Professional Cloud Architect",
    "Certified Kubernetes Application Developer (CKAD)",
    "Microsoft Certified: Azure Solutions Architect Expert",
    "Databricks Certified Data Scientist",
    "Red Hat Certified System Administrator (RHCSA)",
    "Offensive Security Certified Professional (OSCP)",
    "ISTQB Certified Software Tester",
]

# ============================================================ NGOẠI NGỮ
LANG_VN = [
    ("Tiếng Việt", "Ngôn ngữ bản ngữ"),
    ("Tiếng Anh", "Thông thạo - IELTS 7.5"),
    ("Tiếng Anh", "Tốt - TOEFL 95"),
    ("Tiếng Anh", "Khá - IELTS 6.0"),
    ("Tiếng Anh", "Tốt - giao tiếp công việc"),
    ("Tiếng Nhật", "Cơ bản - N4"),
    ("Tiếng Trung", "Cơ bản"),
    ("Tiếng Hàn", "Sơ cấp"),
]

# ============================================================ GIẢI THƯỞNG / HOẠT ĐỘNG
ACHIEVEMENTS_VN = [
    "Giải Nhì Hackathon JS Star Spring 2024",
    "Giải Ba cuộc thi Ý tưởng khởi nghiệp VCCI Startup Challenge",
    "Top 10% khóa học tuyển sinh đầu vào",
    "Học bổng khuyến khích học giỏi 03 học kỳ liên tiếp",
    "Giải Nhất cuộc thi Lập trình sinh viên ACM ICPC cấp trường",
    "Giải Nhì Hackathon AI Việt Nam 2023",
    "Chứng nhận hoàn thành chương trình đào tạo chuyên sâu FPT",
    "Thành viên đội tuyển Khoa Khoa học Máy tính thi Olympic Tin học",
    "Giải thưởng Nhân viên xuất sắc quý cuối năm",
    "Vượt khoảng cách số 1000 leetcode trong cộng đồng sinh hoạt",
    "Phiếu bình chọn Ảnh CV đẹp nhất TopCV.vn 2024",
    "Hoàn thành chứng chỉ nội bộ về System Design của công ty",
]
ACTIVITIES_VN = [
    "Tình nguyện tại CLB Tin học, hỗ trợ đào tạo lập trình cho sinh viên năm nhất",
    "Bí thư Câu lạc bộ Trí tuệ nhân tạo",
    "Tham gia diễn đàn công nghệ DevOps Vietnam",
    "Mentor cho chương trình Open Source Contribution của trường",
    "Trưởng ban kỹ thuật câu lạc bộ Robotics",
    "Tham gia đội tuyển thể thao điện tử tối giải Solve For IT",
]
ACHIEVEMENTS_EN = [
    "Second place - Hackathon for Social Good 2024",
    "Dean's List for 3 consecutive semesters",
    "Finalist - National Student Programming Contest 2023",
    "Employee of the Month (Q3 2024)",
    "Outstanding Contributor Award - Open Source Program",
    "Completed AWS Skill Builder - Architect Design",
]


# ============================================================ ROLE BANKS
ROLE_BANKS: dict[str, dict] = {
    "backend": {
        "vi": {
            "titles": {
                "intern": ["Thực tập sinh Backend Developer", "Intern Backend Developer",
                           "Lập trình viên Backend (Thực tập)"],
                "junior": ["Backend Developer", "Lập trình viên Backend Junior",
                           "Software Engineer Backend"],
                "middle": ["Backend Developer", "Kỹ sư Phần mềm Backend",
                           "Mid-level Backend Engineer"],
                "senior": ["Senior Backend Developer", "Kỹ sư Phần mềm Cao cấp",
                           "Senior Software Engineer - Backend"],
                "lead": ["Tech Lead Backend", "Trưởng nhóm Backend",
                         "Backend Architect", "Lead Backend Engineer"],
            },
            "core": ["Java", "Spring Boot", "Spring MVC", "Spring Security", "JPA/Hibernate",
                     "RESTful API", "MySQL", "PostgreSQL", "Redis", "RabbitMQ", "Maven/Gradle"],
            "stack": ["Docker", "Git/GitHub", "Jenkins", "Linux", "Microservices", "Redis Cache",
                      "Apache Kafka", "Elasticsearch", "Swagger/OpenAPI", "Grafana"],
            "domains": ["hệ thống ngân hàng", "nền tảng thương mại điện tử", "ứng dụng thanh toán",
                        "hệ thống quản lý kho", "nền tảng đặt lịch y tế", "CRM bán hàng",
                        "hệ thống loyalty", "ứng dụng giao hàng"],
            "modules": ["module xác thực và phân quyền", "module thanh toán", "module đơn hàng",
                        "module báo cáo doanh thu", "module quản lý khách hàng",
                        "API tích hợp với đối tác", "module thông báo", "module quản lý kho"],
        },
        "domains_en": ["digital banking", "e-commerce platform", "payment gateway",
                       "inventory management", "healthcare scheduling", "CRM"],
        "core_en": ["Java", "Spring Boot", "Spring Security", "JPA/Hibernate", "REST API"],
        "stack_en": ["MySQL", "PostgreSQL", "Redis", "Docker", "Kubernetes", "Kafka", "Maven"],
    },
    "frontend": {
        "vi": {
            "titles": {
                "intern": ["Thực tập sinh Front-end Developer", "Intern Frontend Developer",
                           "Lập trình viên Front-end (Thực tập)"],
                "junior": ["Front-end Developer", "Lập trình viên Front-end Junior",
                           "Frontend Engineer"],
                "middle": ["Front-end Developer", "Kỹ sư Front-end",
                           "Mid-level Frontend Engineer"],
                "senior": ["Senior Front-end Developer", "Kỹ sư Front-end Cao cấp",
                           "Senior UI Engineer"],
                "lead": ["Tech Lead Front-end", "Front-end Architect",
                         "Trưởng nhóm Front-end", "Lead UI Engineer"],
            },
            "core": ["HTML5", "CSS3/SCSS", "JavaScript/ES6+", "TypeScript", "ReactJS",
                     "Next.js", "Redux Toolkit", "React Query", "Tailwind CSS", "Vite"],
            "stack": ["Node.js", "REST API", "Figma", "Ant Design", "Responsive Design",
                      "Webpack", "Jest", "Testing Library", "Git/GitHub", "CI/CD"],
            "domains": ["trang thương mại điện tử", "dashboard quản trị", "ứng dụng đặt vé",
                        "trang landing page sản phẩm", "app theo dõi sức khỏe",
                        "hệ thống quản lý học tập", "app giao diện người dùng"],
            "modules": ["trang danh mục sản phẩm", "luồng thanh toán", "trang đăng nhập/đăng ký",
                        "dashboard báo cáo", "component chia sẻ", "trang chi tiết đơn hàng",
                        "tính năng giỏ hàng", "giao diện đa ngôn ngữ"],
        },
        "domains_en": ["e-commerce storefront", "admin dashboard", "booking application",
                       "health tracking app", "learning management system"],
        "core_en": ["React", "TypeScript", "Next.js", "Redux", "Tailwind CSS"],
        "stack_en": ["Vite", "Jest", "Figma", "REST API", "Vercel", "Sentry"],
    },
    "devops": {
        "vi": {
            "titles": {
                "intern": ["Thực tập sinh DevOps", "Intern DevOps Engineer",
                           "Kỹ sư Mạng & DevOps (Thực tập)"],
                "junior": ["DevOps Engineer", "Kỹ sư DevOps Junior",
                           "Cloud Engineer"],
                "middle": ["DevOps Engineer", "Kỹ sư DevOps",
                           "Site Reliability Engineer"],
                "senior": ["Senior DevOps Engineer", "Kỹ sư SRE Cao cấp",
                           "Senior Cloud Engineer"],
                "lead": ["DevOps Lead", "Trưởng nhóm DevOps", "Cloud Architect",
                         "Head of Infrastructure"],
            },
            "core": ["Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
                     "GitLab CI/CD", "GitHub Actions", "AWS", "Linux", "Bash"],
            "stack": ["Prometheus", "Grafana", "Nginx", "Helm", "ArgoCD", "Vault",
                      "ELK Stack", "Azure/GCP", "SonarQube", "Trivy"],
            "domains": ["môi trường production", "hạ tầng microservices",
                        "pipeline CI/CD", "hệ thống monitoring", "cloud AWS",
                        "hệ thống logging tập trung"],
            "modules": ["pipeline build và deploy", "hệ thống monitoring 24/7",
                        "quản lý secret", "cluster Kubernetes", "hệ thống backup",
                        "auto-scaling", "cấu hình reverse proxy"],
        },
        "domains_en": ["production infrastructure", "microservices platform",
                       "CI/CD pipeline", "24/7 monitoring stack", "AWS cloud footprint"],
        "core_en": ["Docker", "Kubernetes", "Terraform", "AWS", "CI/CD"],
        "stack_en": ["Prometheus", "Grafana", "ArgoCD", "Helm", "Linux", "Bash"],
    },
    "data": {
        "vi": {
            "titles": {
                "intern": ["Thực tập sinh Data Scientist", "Intern Data Analyst",
                           "Thực tập sinh AI/ML Engineer"],
                "junior": ["Data Analyst", "Data Engineer", "Machine Learning Engineer"],
                "middle": ["Data Engineer", "Senior Data Analyst", "ML Engineer"],
                "senior": ["Senior Data Scientist", "Senior ML Engineer",
                           "Lead Data Engineer"],
                "lead": ["Head of Data", "Chief Data Officer", "Data Architect",
                         "Trưởng phòng Dữ liệu"],
            },
            "core": ["Python", "SQL", "Pandas", "NumPy", "scikit-learn", "PyTorch",
                     "Power BI", "Tableau", "Pandas", "SQL Server"],
            "stack": ["Airflow", "Spark", "Hadoop", "dbt", "Kafka", "Docker",
                      "MLflow", "FastAPI", "Google BigQuery", "Snowflake"],
            "domains": ["dự báo doanh thu", "phân khúc khách hàng", "phát hiện gian lận",
                        "tối ưu giá trị vòng khách hàng", "phân tích hành vi người dùng",
                        "mô hình dự báo thời điểm rời bỏ"],
            "modules": ["pipeline dữ liệu ETL", "mô hình phân loại rủi ro",
                        "dashboard doanh thu", "feature store", "mô hình gợi ý nội dung",
                        "hệ thống dữ liệu lịch sử"],
        },
        "domains_en": ["revenue forecasting", "customer segmentation", "fraud detection",
                       "customer lifetime value", "user behaviour analysis"],
        "core_en": ["Python", "SQL", "PyTorch", "scikit-learn", "Power BI"],
        "stack_en": ["Airflow", "Spark", "dbt", "MLflow", "Docker", "BigQuery"],
    },
    "ba": {
        "vi": {
            "titles": {
                "intern": ["Thực tập sinh Business Analyst", "Intern Business Analyst"],
                "junior": ["Business Analyst", "Business Analyst - Nghiệp vụ"],
                "middle": ["Business Analyst", "Senior Business Analyst"],
                "senior": ["Senior Business Analyst", "Lead Business Analyst"],
                "lead": ["Product Owner", "Product Manager", "Scrum Master",
                         "BA Lead - Trưởng nhóm phân tích nghiệp vụ"],
            },
            "core": ["Phân tích nghiệp vụ", "BPMN", "BRD/SRS", "User Story",
                     "Acceptance Criteria", "Jira", "Confluence", "UAT"],
            "stack": ["Agile/Scrum", "Kanban", "Figma Prototype", "SQL cơ bản",
                      "Power BI", "Postman", "Draw.io", "Mô hình hóa nghiệp vụ"],
            "domains": ["quy trình đăng ký tài khoản", "quy trình hoàn tiền",
                        "luồng đặt đơn kèm voucher", "nghiệp vụ bảo hiểm nhân thọ",
                        "quy trình tuyển dụng nội bộ", "luồng phê duyệt tài liệu"],
            "modules": ["quy trình phê duyệt tín dụng", "luồng đăng ký khách hàng",
                        "quy trình khiếu nại", "quy trình vận chuyển",
                        "luồng đặt lịch dịch vụ"],
        },
        "domains_en": ["account registration flow", "refund workflow",
                       "credit approval process", "internal recruitment process"],
        "core_en": ["Business Analysis", "BPMN", "User Stories", "UAT", "Jira"],
        "stack_en": ["Agile/Scrum", "Confluence", "Figma", "SQL", "Postman"],
    },
    "qa": {
        "vi": {
            "titles": {
                "intern": ["Thực tập sinh QA/QC", "Intern QA Tester", "Thực tập sinh Kiểm thử"],
                "junior": ["QA Engineer", "Software Tester", "QA/QC Engineer"],
                "middle": ["Automation QA Engineer", "QA Engineer",
                           "Senior Software Tester"],
                "senior": ["Senior QA Automation Engineer", "SDET",
                           "Kỹ sư Kiểm thử Tự động Cao cấp"],
                "lead": ["QA Lead", "Trưởng nhóm QA", "Test Architect",
                         "Head of Quality Assurance"],
            },
            "core": ["Manual Testing", "Test Case Design", "API Testing", "Postman",
                     "Selenium", "Cypress", "Playwright", "JMeter", "SQL"],
            "stack": ["Jira", "TestRail", "Junit", "Pytest", "GitLab CI",
                      "Test Automation", "SQL", "Charles Proxy", "Charles/Fiddler"],
            "domains": ["ứng dụng ngân hàng số", "app thương mại điện tử",
                        "hệ thống bán vé", "app thanh toán di động",
                        "portal khách hàng doanh nghiệp"],
            "modules": ["luồng đăng ký tài khoản", "luồng thanh toán",
                        "module báo cáo", "app iOS/Android", "API nội bộ"],
        },
        "domains_en": ["digital banking app", "e-commerce application",
                       "mobile payment app", "enterprise customer portal"],
        "core_en": ["Test Case Design", "API Testing", "Selenium", "Playwright", "JMeter"],
        "stack_en": ["Postman", "SQL", "Jira", "Pytest", "Charles Proxy"],
    },
    "security": {
        "vi": {
            "titles": {
                "intern": ["Thực tập sinh An ninh mạng", "Intern SOC Analyst",
                           "Thực tập sinh Pentester"],
                "junior": ["Security Analyst", "SOC Analyst", "Pentester",
                           "Quản trị hệ thống"],
                "middle": ["Security Engineer", "Cyber Security Engineer",
                           "SOC Analyst - Level 2"],
                "senior": ["Senior Security Engineer", "Penetration Tester",
                           "Senior SOC Analyst"],
                "lead": ["Security Lead", "Trưởng nhóm An ninh mạng",
                         "Security Architect", "Head of Information Security"],
            },
            "core": ["Network Security", "Linux/Windows", "TCP/IP", "Firewall",
                     "SIEM", "Kali Linux", "OWASP Top 10", "Vulnerability Assessment"],
            "stack": ["Burp Suite", "Nmap", "Metasploit", "Splunk", "Wazuh",
                      "Active Directory", "VPN", "IAM", "SOC 2", "ISO 27001"],
            "domains": ["hệ thống SOC", "giám sát an ninh mạng nội bộ",
                        "kiểm toán lỗ hổng ứng dụng web", "quản lý tài khoản đặc quyền",
                        "giám sát sự cố", "bảo mật hạ tầng cloud"],
            "modules": ["giám sát log tập trung", "quét lỗ hổng định kỳ",
                        "cảnh báo sự cố", "phân tích malware", "kiểm toán cấu hình máy chủ"],
        },
        "domains_en": ["security operations centre", "network monitoring",
                       "web application penetration testing", "cloud infrastructure security"],
        "core_en": ["Linux", "Network Security", "OWASP", "SIEM", "Burp Suite"],
        "stack_en": ["Nmap", "Metasploit", "Splunk", "Active Directory", "IAM"],
    },
    "fullstack": {
        "vi": {
            "titles": {
                "intern": ["Thực tập sinh Full-stack Developer", "Intern Web Developer"],
                "junior": ["Full-stack Developer", "Web Developer",
                           "Lập trình viên Full-stack"],
                "middle": ["Full-stack Developer", "Kỹ sư Phần mềm Full-stack"],
                "senior": ["Senior Full-stack Developer", "Kỹ sư Phần mềm Cao cấp"],
                "lead": ["Solution Architect", "Tech Lead Full-stack",
                         "Kiến trúc sư giải pháp", "Head of Engineering"],
            },
            "core": ["ReactJS", "Node.js/NestJS", "Java/Spring Boot", "TypeScript",
                     "MySQL/PostgreSQL", "REST API", "Docker", "Git"],
            "stack": ["Redis", "RabbitMQ", "AWS", "CI/CD", "Tailwind CSS", "Prisma",
                      "Elasticsearch", "Nginx", "TypeORM", "Redis"],
            "domains": ["nền tảng SaaS", "website bán hàng", "hệ thống quản lý công việc",
                        "app đặt lịch dịch vụ", "CRM cho doanh nghiệp nhỏ",
                        "cổng thông tin khách hàng"],
            "modules": ["luồng đăng ký và xác thực", "module thanh toán",
                        "module báo cáo", "quản lý vai trò và phân quyền",
                        "module tìm kiếm nâng cao", "hệ thống thông báo"],
        },
        "domains_en": ["SaaS platform", "e-commerce website", "work management system",
                       "service booking app", "small business CRM"],
        "core_en": ["React", "Node.js", "TypeScript", "PostgreSQL", "REST API"],
        "stack_en": ["Docker", "Redis", "AWS", "Tailwind CSS", "Prisma", "Nginx"],
    },
}


# ============================================================ LEVEL BANKS
LEVEL_BANKS: dict[str, dict] = {
    "intern": {
        "vi": {
            "exp_years": [0, 1],
            "n_jobs": [1],
            "n_projects": [2, 3],
            "job_suffix": ["Thực tập sinh", "Intern", "Thực tập"],
            "desc_bullets": [
                "Tham gia phát triển {module} trong {domain} theo yêu cầu của team.",
                "Sử dụng {tech} để xử lý nghiệp vụ {module}.",
                "Viết unit test cho các hàm xử lý nghiệp vụ cốt lõi, đạt độ bao phủ {cov}%.",
                "Phối hợp với senior để review code và sửa lỗi phát sinh.",
                "Tham gia viết tài liệu kỹ thuật và hỗ trợ kiểm thử sau triển khai.",
                "Đóng góp cho {n_repo} pull request trên kho mã nguồn của công ty.",
            ],
            "project_bullets": [
                "Xây dựng {project} - {domain} làm đồ án môn {course}.",
                "Mô hình hóa cơ sở dữ liệu gồm {n_table} bảng với quan hệ chuẩn hóa 3NF.",
                "Triển khai REST API gồm {n_api} endpoint cho module {module}.",
                "Áp dụng {tech} để xử lý {n_concurrent} request đồng thời.",
                "Hỗ trợ kiểm thử thủ công và ghi nhận lỗi phát hiện được.",
                "Trình bày dự án đạt điểm {score}/10 trong kỳ bảo vệ đồ án.",
            ],
            "objective": [
                "Sinh viên năm cuối ngành {major} với nền tảng {tech}, mong muốn thực tập tại vị trí {title} để áp dụng kiến thức đã học vào dự án thực tế.",
                "Mục tiêu tìm cơ hội thực tập vị trí {title}, đồng thời củng cố kiến thức về {tech} qua các dự án cá nhân.",
                "Tìm kiếm vị trí {title} tại công ty môi trường làm việc chuyên nghiệp để phát triển bản thân và đóng góp cho sản phẩm thực.",
            ],
        },
        "en": {
            "desc_bullets": [
                "Implemented {module} features in the {domain} product with guidance from senior engineers.",
                "Used {tech} to handle core business logic and data validation.",
                "Wrote unit tests covering {cov}% of the modules I owned.",
                "Fixed {n_bug} bugs reported during integration testing.",
                "Participated in code review sessions and adopted team coding standards.",
            ],
            "project_bullets": [
                "Built {project} - a {domain} application as my final-year capstone project.",
                "Designed a normalized schema with {n_table} tables and foreign-key constraints.",
                "Implemented {n_api} REST API endpoints for {module}.",
                "Handled {n_concurrent} concurrent requests with proper indexing and caching.",
                "Scored {score}/10 in the final project defense.",
            ],
            "objective": [
                "Final-year {major} student with hands-on experience in {tech}, seeking a {title} internship to apply my skills on real-world projects.",
                "Looking for a {title} position where I can strengthen my {tech} knowledge through practical engineering work.",
            ],
        },
        "years": 0,
    },
    "junior": {
        "vi": {
            "exp_years": [1, 3],
            "n_jobs": [1, 2],
            "n_projects": [2, 3],
            "job_suffix": ["Junior", "Developer"],
            "desc_bullets": [
                "Phát triển và bảo trì {module} của {domain} từ giai đoạn thiết kế đến khi đưa vào vận hành.",
                "Tối ưu truy vấn cơ sở dữ liệu giúp giảm {pct}% thời gian phản hồi API.",
                "Xây dựng {n_api} RESTful API và viết tài liệu OpenAPI cho {module}.",
                "Áp dụng {tech} để xử lý lưu lượng cao điểm với {n_concurrent} request đồng thời.",
                "Viết unit test và integration test, nâng độ bao phủ từ {cov0}% lên {cov}%.",
                "Hỗ trợ xử lý sự cố production, giảm thời gian khắc phục trung bình {pct}%.",
                "Tham gia code review cho {n_pull} pull request của đồng nghiệp.",
                "Triển khai tính năng mới theo yêu cầu nghiệp vụ, đạt tiêu chuẩn nghiệm thu.",
            ],
            "project_bullets": [
                "Dự án {project} - {domain}, đóng góp {n_pull} pull request chính.",
                "Thiết kế kiến trúc {n_service} service với giao tiếp qua REST/gRPC.",
                "Tích hợp thanh toán trực tuyến với {n_partner} đối tác.",
                "Tối ưu hiệu năng trang danh sách, thời gian tải giảm từ {t0}s xuống {t1}s.",
                "Được đánh giá hoàn thành xuất sắc trong kỳ đánh giá nội bộ của công ty.",
            ],
            "objective": [
                "Lập trình viên có {years} năm kinh nghiệm với {tech}, tìm cơ hội gia nhập môi trường chuyên nghiệp để phát triển sâu hơn về {domain}.",
                "Kỹ sư phần mềm với {years} năm kinh nghiệm xây dựng hệ thống {domain}, tìm vị trí {title} để đảm nhận trách nhiệm lớn hơn.",
            ],
        },
        "en": {
            "desc_bullets": [
                "Developed and maintained {module} in the {domain} platform from design through production rollout.",
                "Optimized database queries, cutting API response time by {pct}%.",
                "Built {n_api} RESTful endpoints with OpenAPI documentation for {module}.",
                "Used {tech} to sustain {n_concurrent} concurrent requests in production.",
                "Raised automated test coverage from {cov0}% to {cov}% across the service.",
                "Participated in code review for {n_pull} pull requests from teammates.",
            ],
            "project_bullets": [
                "{project} - {domain}; authored {n_pull} merged pull requests.",
                "Designed a {n_service}-service architecture with REST/gRPC communication.",
                "Integrated online payments with {n_partner} external partners.",
                "Cut page load time from {t0}s to {t1}s through rendering optimizations.",
            ],
            "objective": [
                "Software engineer with {years} years of experience building {domain} systems, seeking a {title} role with broader ownership.",
                "Backend-focused engineer with {years} years of experience in {tech}, looking to grow into larger systems and higher impact work.",
            ],
        },
        "years": 2,
    },
    "middle": {
        "vi": {
            "exp_years": [3, 5],
            "n_jobs": [2, 3],
            "n_projects": [3, 4],
            "job_suffix": ["Engineer", "Developer"],
            "desc_bullets": [
                "Thiết kế và triển khai kiến trúc module {module} trong hệ thống {domain}, phục vụ {n_user} người dùng hoạt động.",
                "Dẫn dắt tách lớp service, giảm coupling và rút ngắn thời gian triển khai tính năng mới {pct}%.",
                "Tối ưu hiện năng hệ thống, giảm p95 latency từ {t0}ms xuống {t1}ms.",
                "Thiết kế chiến lược cache và phân tán tải, giảm tải cơ sở dữ liệu {pct}%.",
                "Xây dựng pipeline CI/CD tự động, rút ngắn thời gian deploy từ {t0} phút xuống {t1} phút.",
                "Áp dụng nguyên tắc SOLID và mẫu thiết kế, nâng khả năng kiểm thử lên {cov}%.",
                "Điều tra và khắc phục {n_bug} sự cố production, tỷ lệ tái phát giảm {pct}%.",
                "Tham gia thiết kế schema cho {n_table} bảng, xử lý khóa chính và chỉ mục phù hợp tải.",
            ],
            "project_bullets": [
                "Dự án {project} - {domain}, kiến trúc sư chính cho {n_service} service.",
                "Chuyển đổi kiến trúc monolith sang microservices, triển khai dần không gián đoạn dịch vụ.",
                "Thiết kế hệ thống xử lý đồng bộ dữ liệu theo thời gian thực, độ trễ dưới {t1} giây.",
                "Đưa tỷ lệ lỗi phát hiện trước khi lên production lên {cov}%.",
                "Hệ thống phục vụ {n_user} người dùng đồng thời với {n_concurrent} phiên hoạt động.",
            ],
            "objective": [
                "Kỹ sư phần mềm có {years} năm kinh nghiệm chuyên sâu về {tech}, tìm kiếm vị trí {title} tại môi trường sản phẩm quy mô lớn để phát triển sâu về kiến trúc và hiệu năng.",
                "Kỹ sư có {years} năm kinh nghiệm thiết kế và tối ưu hệ thống {domain}, mong muốn đảm nhận trách nhiệm về kiến trúc hệ thống và chất lượng kỹ thuật.",
            ],
        },
        "en": {
            "desc_bullets": [
                "Designed and delivered the architecture for {module} serving {n_user} active users.",
                "Led service decomposition, reducing coupling and shortening feature delivery by {pct}%.",
                "Optimized system performance, reducing p95 latency from {t0}ms to {t1}ms.",
                "Built an automated CI/CD pipeline, cutting deploy time from {t0} to {t1} minutes.",
                "Applied SOLID principles and design patterns, raising testability to {cov}%.",
                "Investigated and resolved {n_bug} production incidents, cutting recurrence by {pct}%.",
            ],
            "project_bullets": [
                "{project} - {domain}; primary architect for {n_service} services.",
                "Migrated a monolith to microservices incrementally with zero downtime.",
                "Designed real-time data synchronisation with sub-{t1}-second latency.",
                "Raised pre-production defect detection to {cov}%.",
            ],
            "objective": [
                "Software engineer with {years} years of deep {tech} experience, seeking a {title} role on large-scale production systems.",
                "Engineer with {years} years designing and tuning {domain} systems, aiming to own system architecture and engineering quality.",
            ],
        },
        "years": 4,
    },
    "senior": {
        "vi": {
            "exp_years": [5, 8],
            "n_jobs": [2, 3],
            "n_projects": [3, 4],
            "job_suffix": ["Senior Engineer", "Kỹ sư Cao cấp"],
            "desc_bullets": [
                "Phụ trách thiết kế hệ thống cho {module} phục vụ {n_user} người dùng, đảm bảo khả năng mở rộng theo chiều ngang.",
                "Kiến trúc sư chính cho {n_service} service, đưa ra quyết định công nghệ và trade-off về chi phí, độ trễ và độ sẵn sàng.",
                "Dẫn dắt {n_team} kỹ sư trong {n_sprint} sprint liên tiếp, đạt đúng tiến độ cam kết.",
                "Mentor cho {n_mentee} kỹ sư mới, nâng cao chất lượng code review toàn nhóm.",
                "Thiết kế chiến lược multi-region và disaster recovery, thời gian khôi phục dưới {t1} phút.",
                "Giảm chi phí hạ tầng {pct}% bằng cách tối ưu tài nguyên và thiết kế multi-tenant.",
                "Điều hướng quy trình system design, chuẩn hóa đánh giá giải pháp kỹ thuật trước khi triển khai.",
                "Xử lý {n_bug} sự cố nghiêm trọng, không có downtime ảnh hưởng người dùng trong {n_month} tháng.",
            ],
            "project_bullets": [
                "Dự án {project} - {domain}, kiến trúc sư trưởng cho {n_service} service.",
                "Thiết kế kiến trúc event-driven với Kafka, xử lý {n_event} sự kiện mỗi giây.",
                "Áp dụng kiến trúc hexagonal để tách lớp nghiệp vụ khỏi hạ tầng.",
                "Tăng khả năng chịu lỗi: thời gian khôi phục trung bình {t1} phút.",
                "Dẫn dắt quá trình tái cấu trúc, giảm nợ kỹ thuật {pct}%.",
            ],
            "objective": [
                "Kỹ sư cao cấp có {years} năm kinh nghiệm thiết kế hệ thống phân tán và dẫn dắt kỹ sư, tìm kiếm vị trí {title} tại công ty sản phẩm quy mô lớn.",
                "Chuyên gia kiến trúc hệ thống với {years} năm kinh nghiệm {tech}, tập trung vào hiệu năng, an toàn và khả năng mở rộng của sản phẩm.",
            ],
        },
        "en": {
            "desc_bullets": [
                "Owned system design for {module} serving {n_user} users with horizontal scalability.",
                "Served as principal architect for {n_service} services, balancing cost, latency and availability trade-offs.",
                "Led a team of {n_team} engineers across {n_sprint} consecutive sprints with consistent delivery.",
                "Mentored {n_mentee} engineers and raised code review quality across the team.",
                "Designed multi-region strategy and disaster recovery with recovery time under {t1} minutes.",
                "Reduced infrastructure cost by {pct}% through resource optimisation and multi-tenancy.",
                "Facilitated system design reviews and standardised technical evaluation before rollout.",
            ],
            "project_bullets": [
                "{project} - {domain}; lead architect for {n_service} services.",
                "Designed an event-driven architecture on Kafka handling {n_event} events per second.",
                "Applied hexagonal architecture to decouple domain logic from infrastructure.",
                "Led a refactoring effort that reduced technical debt by {pct}%.",
            ],
            "objective": [
                "Senior engineer with {years} years designing distributed systems and leading engineers, seeking a {title} role at a large-scale product company.",
                "Systems architect with {years} years of {tech} experience focused on performance, reliability and product scalability.",
            ],
        },
        "years": 6,
    },
    "lead": {
        "vi": {
            "exp_years": [7, 12],
            "n_jobs": [3, 4],
            "n_projects": [3, 4],
            "job_suffix": ["Lead", "Trưởng nhóm", "Kiến trúc sư"],
            "desc_bullets": [
                "Quản lý nhóm {n_team} kỹ sư, phân bổ nguồn lực và định hướng kỹ thuật cho {n_product} sản phẩm.",
                "Điều hành quy trình phát triển theo Agile/Scrum, cam kết bàn giao đúng thời hạn trên {n_sprint} quý liên tiếp.",
                "Thiết kế kiến trúc tổng thể cho hệ thống {domain} phục vụ {n_user} người dùng và {n_team} team.",
                "Làm việc trực tiếp với stakeholder nghiệp vụ để làm rõ yêu cầu và cân bằng phạm vi với thời hạn.",
                "Xây dựng lộ trình kỹ thuật dài hạn cho {n_year} năm, định hướng công nghệ và loại bỏ nợ kỹ thuật.",
                "Nâng cao hiệu quả nhóm: thời gian giao hàng giảm {pct}% sau khi chuẩn hóa quy trình review.",
                "Quản lý hiệu năng và chất lượng: độ bao phủ kiểm thử đạt {cov}%, tỷ lệ lỗi nghiêm trọng giảm {pct}%.",
                "Thúc đẩy văn hóa kỹ thuật, tổ chức workshop chia sẻ kiến thức hàng tháng cho toàn bộ nhóm.",
                "Đánh giá rủi ro kỹ thuật và đề xuất phương án giảm thiểu trước khi cam kết với khách hàng.",
            ],
            "project_bullets": [
                "Chỉ đạo dự án {project} - {domain} với quy mô {n_user} người dùng.",
                "Thiết kế kiến trúc tổng thể, chọn công nghệ và chuẩn hóa nền tảng dùng chung.",
                "Quản lý chuyển giao từ nhà cung cấp sang vận hành nội bộ, giảm {pct}% chi phí license.",
                "Xây dựng lộ trình chuyển đổi số cho {n_product} sản phẩm của công ty.",
                "Điều hành {n_team} team với quy mô nhân sự ổn định qua {n_year} năm.",
            ],
            "objective": [
                "Lãnh đạo kỹ thuật với {years} năm kinh nghiệm {tech}, từng quản lý nhóm {n_team} kỹ sư và phụ trách kiến trúc hệ thống {domain}.",
                "Tìm kiếm vị trí {title} để định hướng sản phẩm, cân bằng giữa yêu cầu kinh doanh và giới hạn kỹ thuật tại quy mô lớn.",
            ],
        },
        "en": {
            "desc_bullets": [
                "Managed a team of {n_team} engineers across {n_product} products, owning technical direction.",
                "Ran Agile/Scrum delivery with committed releases across {n_sprint} consecutive quarters.",
                "Designed the overall architecture for the {domain} platform serving {n_user} users and {n_team} teams.",
                "Partnered directly with business stakeholders to clarify requirements and scope trade-offs.",
                "Owned a {n_year}-year technology roadmap, driving adoption decisions and technical debt reduction.",
                "Improved team throughput by {pct}% after standardising the design review process.",
                "Raised automated coverage to {cov}% and cut critical incident rate by {pct}%.",
                "Ran monthly engineering workshops and grew the team's technical capability.",
            ],
            "project_bullets": [
                "Directed {project} - {domain} at a scale of {n_user} users.",
                "Designed the target architecture, technology selection and shared platform standards.",
                "Drove migration from vendor platform to in-house operations, cutting licence cost by {pct}%.",
                "Managed a stable team of {n_team} engineers over {n_year} years.",
            ],
            "objective": [
                "Engineering lead with {years} years of {tech} experience, having managed {n_team} engineers and owned {domain} architecture.",
                "Seeking a {title} role where I can shape product direction and balance business requirements against technical constraints at scale.",
            ],
        },
        "years": 9,
    },
}


# ============================================================ THÔNG SỐ NGẪU NHIÊN
METRIC_POOL = {
    "pct": [15, 20, 25, 30, 35, 40, 45, 50, 60, 65, 70],
    "n_api": [12, 15, 18, 20, 24, 30, 35, 40],
    "n_concurrent": [500, 1000, 1500, 2000, 3000, 5000, 8000, 10000],
    "n_user": [50000, 100000, 200000, 300000, 500000, 800000, 1000000],
    "n_team": [5, 6, 7, 8, 9, 10, 12],
    "n_mentee": [2, 3, 4, 5, 6],
    "n_service": [5, 6, 8, 10, 12, 15, 18],
    "n_table": [6, 8, 10, 12, 15],
    "n_bug": [12, 20, 28, 35, 45, 60],
    "n_pull": [15, 20, 30, 40, 55, 70],
    "n_partner": [2, 3, 4, 5, 6],
    "n_repo": [3, 5, 8, 10, 12],
    "n_sprint": [4, 6, 8, 10, 12],
    "n_month": [6, 9, 12, 18],
    "n_year": [2, 3, 5],
    "n_product": [2, 3, 4, 5],
    "n_event": [5000, 10000, 20000, 50000, 100000],
    "cov": [70, 75, 80, 85, 88, 90],
    "cov0": [20, 25, 30, 35, 40],
    "t0": [1200, 1800, 2500, 3500, 4800],
    "t1": [200, 320, 450, 600, 850, 1200],
    "score": [8, 8.5, 9, 9.5, 10],
}

PROJECT_NAMES_VI = [
    "Hệ thống quản lý bán hàng", "Nền tảng đặt lịch dịch vụ", "Ứng dụng ví điện tử",
    "Cổng thông tin khách hàng", "Hệ thống quản lý kho hàng", "Sàn thương mại điện tử",
    "Ứng dụng theo dõi sức khỏe", "Hệ thống quản lý học tập", "Nền tảng tuyển dụng",
    "Ứng dụng giao hàng thông minh", "Hệ thống báo cáo kinh doanh",
    "Nền tảng chatbot hỗ trợ khách hàng", "Ứng dụng quản lý tài chính cá nhân",
    "Hệ thống quản lý nội dung", "Nền tảng chia sẻ tài liệu",
]
PROJECT_NAMES_EN = [
    "Order Management Platform", "Service Booking System", "E-wallet Application",
    "Customer Self-Service Portal", "Inventory Tracking System", "E-commerce Marketplace",
    "Health Monitoring App", "Learning Management System", "Recruitment Platform",
    "Smart Delivery Application", "Business Reporting System",
    "AI Support Chatbot", "Personal Finance App", "Content Management System",
]

COURSE_NAMES = ["Phân tích và thiết kế phần mềm", "Cơ sở dữ liệu", "Lập trình Web",
                "Kiểm thử phần mềm", "An toàn thông tin", "Quản trị mạng",
                "Xử lý dữ liệu lớn", "Mạng xã hội", "Kiến trúc phần mềm",
                "Hệ quản trị cơ sở dữ liệu"]

SOFT_SKILLS_VI = [
    "Làm việc nhóm", "Giao tiếp và trình bày", "Tư duy phản biện", "Chủ động học hỏi",
    "Quản lý thời gian", "Giải quyết vấn đề", "Thích nghi môi trường khởi nghiệp",
    "Tiếng Anh giao tiếp tốt", "Tinh thần trách nhiệm", "Khả năng thích nghi nhanh",
]
SOFT_SKILLS_EN = [
    "Teamwork", "Communication", "Problem solving", "Self-learning",
    "Time management", "Critical thinking", "Ownership", "Adaptability",
]

GIT_HOSTS = ["github.com", "gitlab.com", "bitbucket.org"]
