# -*- coding: utf-8 -*-
"""Batch 11: silver labels cho file 64, 65, 68, 70, 81, 82.txt (ảnh OCR có tên).

Lưu ý: các file ảnh còn lại (56-63, 66-67, 69, 71-80, 83-85) bị ẩn danh - không
có họ tên trong văn bản -> không thể điền full_name mà không bịa. Xem EXCLUSIONS
trong assemble_silver_dataset.py.
"""

BATCH = [
    {
        "file": "64.txt",
        "profile": {
            "personal_info": {
                "full_name": "NGUYEN KHAC LE NHAN",
                "email": None,
                "phone": None,
                "github_url": "https://github.com/nhannki5",
            },
            "objective": "Third-year Software Engineering student passionate about Backend development, backed by hands-on projects in JavaEE, Spring Boot, MySQL — seeking an internship to learn from experienced engineers and turn what I've built into production-grade impact.",
            "education": [
                {
                    "school": "FPT University",
                    "major": "Software Engineering Major",
                    "start_year": 2024,
                    "end_year": 2028,
                    "gpa": "3.5",
                }
            ],
            "experience": [],
            "personal_projects": [
                {
                    "name": "Autowash Pro",
                    "role": "Team Leader - Backend",
                    "team_size": 4,
                    "start_date": "05/2026",
                    "end_date": None,
                    "github_url": "github.com/nhannk15/autowash-pro",
                    "description": "A car wash booking platform with slot-based scheduling, online payment, and a tier-based loyalty program.",
                    "tech_stack": [
                        "Java", "Spring Boot", "Spring Security", "JWT", "Spring Data JPA",
                        "MySQL", "REST API", "VNPAY", "Agile/Scrum",
                    ],
                },
                {
                    "name": "Online Shopping Website",
                    "role": "Backend",
                    "team_size": None,
                    "start_date": "02/2026",
                    "end_date": "04/2026",
                    "github_url": "github.com/nhannk15/Workshop2",
                    "description": "A Java EE e-commerce web app with role-based access control for admin, manager, and customer account using Java Servlet MVC2 Architecture.",
                    "tech_stack": [
                        "Java EE 7", "Servlets", "JSP/JSTL", "JPA 2.1 (EclipseLink)",
                        "Microsoft SQL Server", "Apache Ant", "HTML/CSS/JavaScript",
                        "Bootstrap",
                    ],
                },
            ],
            "skills": [
                "Programming language: Java", "JavaScript",
                "Database: MS SQL", "MySQL", "PostgreSQL",
                "Frontend: HTML5", "CSS3", "Bootstrap", "React", "MUI", "SASS/SCSS",
                "Backend: RESTful API", "Spring Boot", "Spring Security", "JWT",
                "Spring Data JPA",
                "Others: Git/Github",
                "Intermediate level in English",
                "Having a solid grasp of Agile/Scrum methodology",
            ],
            "certificates": [],
            "honours": ["TOP 5 EXCELLENT STUDENT OF TRIMESTER FALL 2025"],
            "languages": [{"language": "English", "note": "Intermediate level"}],
        },
    },
    {
        "file": "65.txt",
        "profile": {
            "personal_info": {
                "full_name": "Nguyễn Thành Duy",
                "email": "nguyenthanhduyofficial@gmail.com",
                "phone": None,
                "github_url": None,
            },
            "objective": "Self-taught full-stack developer with hands-on experience building, deploying, and maintaining real-world projects using Next.js and NestJS. I focus on writing clean, maintainable code and have independently delivered two live projects. Actively seeking an internship or junior role to contribute and grow.",
            "education": [
                {
                    "school": "Self-Taught Developer",
                    "major": "Full-stack web development through structured online resources (documentation, tutorials, hands-on projects)",
                    "start_year": 2023,
                    "end_year": None,
                    "gpa": None,
                }
            ],
            "experience": [],
            "personal_projects": [
                {
                    "name": "Car Rental Website",
                    "role": "Solo Full-stack Developer",
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Full-stack web application that allows users to browse available cars, select rental dates, and complete orders seamlessly.",
                    "tech_stack": [
                        "Next.js", "TailwindCSS", "NestJS", "Prisma", "Swagger",
                        "PostgreSQL", "JWT", "Render", "Vercel", "Supabase", "Stripe",
                    ],
                },
                {
                    "name": "Odyssey Website",
                    "role": "Solo Full-stack Developer",
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "A multi-page static website built for a 100+ member Discord study community to attract new members and share resources.",
                    "tech_stack": [
                        "Next.js", "TailwindCSS", "ShadcenUI", "MDXContent", "Velite", "Vercel",
                    ],
                },
            ],
            "skills": [
                "Languages & Frameworks: TypeScript", "React", "Next.js", "Node.js",
                "Nest.JS", "TailwindCSS", "ShadcnUI",
                "Databases & ORM: PostgreSQL", "SQLite", "Prisma",
                "API & Architecture: REST APIs", "JWT", "Stripe Checkout & Webhooks",
                "DevOps & Tools: Docker", "Git", "Vercel", "Supabase", "Render",
                "Testing: Jest",
            ],
            "certificates": [],
            "honours": [],
            "languages": [
                {"language": "Vietnamese", "note": "Native"},
                {"language": "English", "note": "Reading technical documents"},
            ],
        },
    },
    {
        "file": "68.txt",
        "profile": {
            "personal_info": {
                "full_name": "NGUYEN PHAM NHAT ANH",
                "email": "gmail.com",
                "phone": None,
                "github_url": "https://github.com/nhatanh-dev",
            },
            "objective": "Software Engineering student at FPT University with hands-on experience in ASP.NET Core, RESTful APIs, relational databases, and AWS-based deployment through team projects. Seeking a Backend Developer Internship to contribute to backend development, testing, and system integration.",
            "education": [
                {
                    "school": "FPT University HCM",
                    "major": "Bachelor of Software Engineering, Specialization: .NET",
                    "start_year": 2023,
                    "end_year": 2027,
                    "gpa": "8.6",
                }
            ],
            "experience": [],
            "personal_projects": [
                {
                    "name": "EV Station Management System",
                    "role": "Backend Developer",
                    "team_size": None,
                    "start_date": "09/2025",
                    "end_date": "11/2025",
                    "github_url": "github.com/nhatanh-dev/EVoltStation_BE",
                    "description": "Web platform managing EV infrastructure: real-time station monitoring, slot reservation, and automated billing via VNPay.",
                    "tech_stack": [
                        "ASP.NET Core", "EF Core", "SQL Server", "JWT", "SignalR",
                        "VNPay Sandbox",
                    ],
                },
                {
                    "name": "SmartInvoice Shield",
                    "role": "Cloud & Backend Developer",
                    "team_size": None,
                    "start_date": "01/2026",
                    "end_date": "04/2026",
                    "github_url": "github.com/nhatanh-dev/Smartlnvoice",
                    "description": "Developed a multi-tenant SaaS platform for automated invoice processing and supplier risk assessment using AI-powered OCR.",
                    "tech_stack": [
                        ".NET 9", "ASP.NET Core", "PostgreSQL", "AWS", "JWT", "Docker",
                        "VNPay", "VietQR API", "xUnit", "VPC", "ECS", "RDS PostgreSQL",
                        "ALB", "S3", "Cognito", "CloudWatch",
                    ],
                },
            ],
            "skills": [
                "Languages: C#", "Java",
                "Backend: ASP.NET Core", "EF Core", "RESTful APIs", "JWT", "SignalR",
                "Databases: SQL Server", "PostgreSQL",
                "Cloud & DevOps: AWS", "Docker", "GitHub Actions", "Git",
                "Testing & Tools: xUnit", "Postman", "Swagger", "SSMS", "Jira",
                "Frontend Exposure: Angular", "Tailwind CSS", "Bootstrap",
            ],
            "certificates": [
                "AWS First Cloud AI Journey Participant",
            ],
            "honours": [
                "Excellent Student Recognition: Earned for four consecutive semesters at FPT University.",
                "High Distinction in Core Courses: Data Structures & Algorithms (9.3/10), Probability & Statistics (9.1/10).",
            ],
            "languages": [
                {"language": "English", "note": "Upper Intermediate (B2)"},
                {"language": "Japanese", "note": "Basic"},
            ],
        },
    },
    {
        "file": "70.txt",
        "profile": {
            "personal_info": {
                "full_name": "TRAN THANH HOÀI",
                "email": "tthoai654@gmail.com",
                "phone": "(+84) 379 830 494",
                "github_url": "https://github.com/TranThanh-Hoai",
            },
            "objective": "Software Engineering graduate with hands-on experience building web applications and RESTful APIs using Java, Spring Boot, PostgreSQL, Docker, and React. Seeking a Fresher position to gain practical experience and grow into a Junior Developer within 1—2 years.",
            "education": [
                {
                    "school": "HCMC University of Technology (HUTECH)",
                    "major": "Bachelor of Software Engineering",
                    "start_year": 2022,
                    "end_year": 2026,
                    "gpa": "3.22 / 4.0",
                }
            ],
            "experience": [],
            "personal_projects": [
                {
                    "name": "HComic — Comic Reading Platform",
                    "role": "Fullstack Developer",
                    "team_size": None,
                    "start_date": "07/2026",
                    "end_date": None,
                    "github_url": "github.com/TranThanh-Hoai/Hcomic",
                    "description": "A comic reading platform featuring automated image optimization, user libraries, and admin management.",
                    "tech_stack": [
                        "Java 21", "Spring Boot", "Spring Security", "PostgreSQL", "Docker",
                        "React 19", "TypeScript",
                    ],
                },
                {
                    "name": "URL Shortener Service",
                    "role": "Backend Developer",
                    "team_size": None,
                    "start_date": "04/2026",
                    "end_date": "07/2026",
                    "github_url": "github.com/TranThanh-Hoai/shortlink",
                    "description": "A URL shortening service optimized for low-latency HTTP 302 redirection and distributed unique ID generation.",
                    "tech_stack": [
                        "Java 21", "Spring Boot", "PostgreSQL", "Redis", "Docker", "JWT",
                        "Bucket4j",
                    ],
                },
            ],
            "skills": [
                "Languages: Java", "JavaScript", "TypeScript", "Python",
                "Technologies: Spring Boot", "Spring Security", "Spring Data JPA",
                "RESTful API", "Hibernate", "React", "Tailwind-CSS",
                "Database: PostgreSQL", "Redis",
                "Tools: Docker", "Docker Compose", "Git", "GitHub", "Swagger/OpenAPI", "Postman",
                "Testing: JUnit 5", "Mockito",
            ],
            "certificates": [],
            "honours": [],
            "languages": [{"language": "English", "note": "CEFR B1"}],
        },
    },
    {
        "file": "81.txt",
        "profile": {
            "personal_info": {
                "full_name": "TRAN CONG SANG",
                "email": "congsang9738@gmail.com",
                "phone": "0703697726",
                "github_url": "github.com/hades-han",
            },
            "objective": "Recent Information Technology graduate with hands-on experience in computer vision and AI applications, including industrial defect inspection and real-time face recognition. Built end-to-end workflows from data collection and annotation to model training.",
            "education": [],
            "experience": [
                {
                    "company": "SANCOPACK",
                    "job_title": "Quality Control Staff",
                    "start_date": "2025",
                    "end_date": "2026",
                    "description": [
                        "Inspected wooden pallets against dimensional and quality standards, documented defects, and coordinated resolution.",
                        "Applied production-quality knowledge to the Computer Vision inspection project.",
                    ],
                },
                {
                    "company": "HINOVA Technology JSC",
                    "job_title": "Implementation Engineer",
                    "start_date": "2024",
                    "end_date": "2025",
                    "description": [
                        "Gathered requirements, deployed/configured systems and databases, verified functionality, resolved technical issues, and supported acceptance/handover.",
                    ],
                },
                {
                    "company": "T.L.S Import Export Co., Ltd.",
                    "job_title": "Software Developer",
                    "start_date": "2023",
                    "end_date": "2024",
                    "description": [
                        "Tested and developed web features and collaborated with the team to improve application stability, performance, and operations.",
                    ],
                },
            ],
            "personal_projects": [
                {
                    "name": "Computer Vision inspection project",
                    "role": "AI / Computer Vision Engineer",
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Applied production-quality knowledge to the Computer Vision inspection project.",
                    "tech_stack": [
                        "Al & Computer Vision", "OpenCV", "OpenCVDNN", "YOLO(Ultralytics)",
                        "object detection", "face recognition", "image/video processing",
                    ],
                },
            ],
            "skills": [
                "Al & Computer Vision", "OpenCV", "OpenCVDNN", "YOLO(Ultralytics)",
                "object detection", "face recognition", "image/video processing",
                "Machine Learning", "scikit-learn", "ensemble classifiers",
                "embedding extraction", "prediction-confidence estimation",
                "bounding-box annotation", "YOLO labels", "YAML/CSV metadata",
                "data filtering", "model training", "real-time inference",
            ],
            "certificates": [],
            "honours": [],
            "languages": [],
        },
    },
    {
        "file": "82.txt",
        "profile": {
            "personal_info": {
                "full_name": "Lê Huỳnh Phước",
                "email": "phxxxxxxxxx@gmail.com",
                "phone": "09xxxxxxxxx",
                "github_url": None,
            },
            "objective": "Machine learning student with Python and C++ projects spanning computer vision, nonlinear forecasting, and search-algorithm optimization. Applies mathematical modeling, numerical methods, and performance engineering to build predictive models and high-performance inference pipelines.",
            "education": [
                {
                    "school": "Saigon University (SGU)",
                    "major": "Machine Learning / Computer Science",
                    "start_year": None,
                    "end_year": 2029,
                    "gpa": None,
                }
            ],
            "experience": [],
            "personal_projects": [
                {
                    "name": "Animal Species Classification System",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Combined MobileNetV2 (CNN) feature extraction with XGBoost to classify images of 10 animal species. Packaged an inference pipeline for OpenCV image preprocessing, feature scaling, and model loading, achieving prediction latency under 100 ms. Created a Tkinter interface displaying supported species and real-time prediction confidence.",
                    "tech_stack": [
                        "Python", "TensorFlow", "CNN", "Tkinter", "OpenCV", "MobileNetV2",
                        "XGBoost",
                    ],
                },
                {
                    "name": "Custom Chess Engine & Search Optimization",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Engineered a UCI-compliant chess engine in C++ with alpha-beta search (principal variation search, iterative deepening) and Zobrist-hashed transposition tables; deployed as a live bot on Lichess via the lichess-bot framework. Implemented 15+ pruning and move-ordering heuristics across a 56-parameter tunable search configuration. Built an automated SPSA self-play tuning pipeline to calibrate search parameters over thousands of engine-vs-engine games, and verified move-generation correctness via perft testing against known reference node counts through depth 6.",
                    "tech_stack": [
                        "C++", "UCI Protocol", "Alpha-Beta / PVS Search", "Zobrist Hashing",
                        "SPSA",
                    ],
                },
            ],
            "skills": [
                "Programming & numerical computing: Python", "C++", "NumPy", "SciPy",
                "Machine learning & computer vision: TensorFlow", "CNN", "XGBoost", "OpenCV",
                "Methods & tools: Regularization", "hyperparameter tuning",
                "heuristic/adversarial search", "SPSA tuning", "Tkinter",
            ],
            "certificates": [],
            "honours": [],
            "languages": [],
        },
    },
]
