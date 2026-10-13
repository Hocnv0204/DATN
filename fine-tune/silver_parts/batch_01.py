# -*- coding: utf-8 -*-
"""Batch 1: silver labels cho file 1.txt - 6.txt (trích xuất thủ công bởi AI)."""

BATCH = [
    {
        "file": "1.txt",
        "profile": {
            "personal_info": {
                "full_name": "Nguyễn Trung Hiếu",
                "email": "nguyentrunghieu200603@gmail.com",
                "phone": "0865200603",
                "github_url": None,
            },
            "objective": "Với hơn 2 năm kinh nghiệm trong lĩnh vực Front-end Development, tôi đã xây dựng nền tảng vững chắc về phát triển giao diện người dùng thông qua việc sử dụng HTML5, CSS3 và JavaScript (ES6+). Tôi thành thạo Angular framework, bao gồm triển khai component, service, routing và quản lý state hiệu quả. Bên cạnh đó, tôi đang mở rộng kỹ năng sang Back-end với Node.js, Express.js và cơ sở dữ liệu như MongoDB, PostgreSQL nhằm hướng đến vị trí Fullstack Developer. Tôi có kinh nghiệm làm việc với RESTful APIs và GraphQL để tích hợp dữ liệu từ back-end, kết hợp với các công cụ như RxJS để xử lý luồng dữ liệu bất đồng bộ. Tôi cũng có khả năng thiết kế, xây dựng API với Node.js và tối ưu hiệu suất hệ thống. Thông qua quy trình Agile, tôi phối hợp chặt chẽ với team UX/UI để triển khai thiết kế, tối ưu trải nghiệm người dùng và đảm bảo tính nhất quán của giao diện. Ngoài ra, tôi chủ động học hỏi và áp dụng các best practices trong cả Angular và Node.js để nâng cao chất lượng sản phẩm và phát triển bền vững.",
            "education": [
                {
                    "school": "Cao đẳng FPT Polytechnic",
                    "major": "Ứng dụng phần mềm chuyên JAVA",
                    "start_year": 2021,
                    "end_year": 2023,
                    "gpa": None,
                }
            ],
            "experience": [
                {
                    "company": "Datacenter",
                    "job_title": "Nhân viên Front End Developer",
                    "start_date": "2022",
                    "end_date": "2024",
                    "description": [
                        "Xây dựng hệ thống CRM quản lý gói cước sử dụng Angular kết hợp Node.js (Back-end).",
                        "Triển khai Auth JWT, phân trang, thiết kế giao diện admin, user, staff, merchant.",
                        "Áp dụng CI/CD, sử dụng thư viện Bootstrap, Carousel, hỗ trợ đa ngôn ngữ & theme sáng/tối.",
                        "Triển khai thành công hệ thống trên domain: crm.productx.vn.",
                        "Phát triển hệ thống sử dụng Web3D, tích hợp phân quyền JWT (admin, user).",
                        "Kết nối với các API để tối ưu hóa trải nghiệm người dùng.",
                        "Ứng dụng AI Auto Post Blog Page, hỗ trợ tối ưu SEO và viết bài blog.",
                        "Tham khảo sản phẩm tại: hiubeba.id.vn.",
                    ],
                },
                {
                    "company": "Freelance Home",
                    "job_title": "Fullstack",
                    "start_date": "2022",
                    "end_date": "2024",
                    "description": [
                        "Phát triển nhiều sản phẩm cá nhân bao gồm công cụ auto deploy, game nông trại 2D trên Telegram, ứng dụng đặt xe, ứng dụng xem phim, website đặt vé xem phim, AI Agent tự động post nội dung chuẩn SEO và ứng dụng Flutter kết hợp AI Agent local.",
                        "Công nghệ sử dụng: Front-end Angular, Flutter; Back-end Node.js, Express.js, Socket.io; Cơ sở dữ liệu MongoDB; DevOps Docker, CI/CD, Nginx.",
                    ],
                },
            ],
            "personal_projects": [
                {
                    "name": "Công Cụ Auto Deploy Lên Server",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Phát triển một tool tự động triển khai ứng dụng lên server nhằm tối ưu hóa quy trình deploy, giảm thiểu thời gian thực hiện và hạn chế sai sót thủ công. Công nghệ: Backend Node.js, RESTful APIs; DevOps Docker, CI/CD. Rút ngắn đáng kể thời gian deploy.",
                    "tech_stack": ["Node.js", "RESTful APIs", "Docker", "CI/CD"],
                },
                {
                    "name": "Game Nông Trại 2D Trên Telegram",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Phát triển game nông trại 2D với giao diện sinh động, tích hợp cơ chế quản lý thời gian thu hoạch và dữ liệu tài nguyên thông qua Node.js. Game đã được deploy và có thể trải nghiệm qua Telegram tại @FramHBB_bot.",
                    "tech_stack": ["Godot", "Node.js", "MongoDB"],
                },
                {
                    "name": "Ứng Dụng Đặt Xe (Tương Tự Grab)",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Xây dựng ứng dụng đặt xe với giao diện người dùng thân thiện, kết nối API để cập nhật vị trí tài xế và người dùng theo thời gian thực. Tích hợp hệ thống admin để duyệt hồ sơ tài xế khi đăng ký. Ứng dụng hiện đang trong giai đoạn demo.",
                    "tech_stack": ["Flutter", "Firebase", "Google Maps API"],
                },
                {
                    "name": "Ứng Dụng Xem Phim (Tương Tự Netflix)",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Phát triển ứng dụng xem phim với giao diện hiện đại, kết nối với API KKPhim để cung cấp nội dung đa dạng và chất lượng. Có thể trình diễn trực tiếp trong buổi phỏng vấn.",
                    "tech_stack": ["Flutter", "API KKPhim"],
                },
                {
                    "name": "Website Đặt Vé Xem Phim",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Xây dựng hệ thống đặt vé xem phim trực tuyến với chức năng quản lý ghế, phòng chiếu và lịch chiếu. Tích hợp hệ thống phân quyền với Auth JWT, cho phép admin quản lý dữ liệu và người dùng thực hiện các giao dịch (nạp rút tiền, đặt vé). Sử dụng Socket để xử lý đặt chỗ thời gian thực, ngăn chặn trường hợp đặt trùng ghế.",
                    "tech_stack": ["Angular", "Node.js", "Socket.io", "JWT Authentication"],
                },
                {
                    "name": "AI Agent Tự Động Post Nội Dung Chuẩn SEO",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Phát triển AI Agent tự động thu thập, phân tích và tái cấu trúc nội dung từ các nguồn tin chính, từ đó đăng bài lên website với chuẩn SEO tối ưu. Mục tiêu là tăng tần suất đăng bài hàng ngày. Công nghệ: Backend Node.js, tích hợp các thư viện NLP.",
                    "tech_stack": ["Node.js", "NLP"],
                },
                {
                    "name": "Ứng Dụng Flutter Kết Hợp AI Agent Local",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "Phát triển ứng dụng Flutter tích hợp với AI Agent chạy ngầm trên thiết bị Android, cho phép hoạt động nội bộ mà không cần kết nối mạng. Công nghệ: Frontend Flutter; Backend AI Agent phát triển bằng Node.js.",
                    "tech_stack": ["Flutter", "Node.js"],
                },
            ],
            "skills": [
                "Angular", "Typescript", "Bootstrap", "RxJS", "Node.js", "Express.js",
                "RESTful API", "JWT Authentication", "MongoDB", "CI/CD", "Docker",
                "Nginx", "Web3D", "SEO Optimization", "AI Auto Content",
                "HTML5", "CSS3", "JavaScript (ES6+)",
            ],
            "certificates": [],
            "honours": [],
            "languages": [],
        },
    },
    {
        "file": "2.txt",
        "profile": {
            "personal_info": {
                "full_name": "NGUYỄN QUANG HƯNG",
                "email": "nqh1703k2@gmail.com",
                "phone": "0344917301",
                "github_url": "https://github.com/HiImLawtSimp1e",
            },
            "objective": "Short-Term Objective: To contribute my skills and expertise in a software engineer to achieve both personal financial growth and deliver value to the company's objectives. Long-term Objectives: Experience in Real-World software project implementation; Acquire knowledge in computer science & software system; Completed certifications from AWS, Microsoft, Coursera, etc",
            "education": [
                {
                    "school": "FPT Polytechnic College of Hanoi",
                    "major": "Information Technology",
                    "start_year": 2021,
                    "end_year": 2024,
                    "gpa": None,
                }
            ],
            "experience": [
                {
                    "company": "Thien Hoang Solution JSC",
                    "job_title": "Web Developer Intern",
                    "start_date": "04/2024",
                    "end_date": "09/2024",
                    "description": [
                        "I gained hands-on experience working with ASP.NET Core for back-end development and Next.js for front-end development",
                    ],
                }
            ],
            "personal_projects": [
                {
                    "name": "EshopMicroservices",
                    "role": None,
                    "team_size": None,
                    "start_date": "10/2024",
                    "end_date": "03/2025",
                    "github_url": "https://github.com/HiImLawtSimp1e/EShopMicroservices",
                    "description": "Udemy Tutorial Exercise. Experience Gained: Implementing Microservices, Database per Service, Asynchronous Communication with Message Broker, Logical CQRS, Clean Architecture with Domain-Driven Design approach. Using Docker to package and isolate the application environment.",
                    "tech_stack": [
                        "ASP.NET 8.0", "EF Core ORM", "Marten ORM", "PostgreSQL", "RabbitMQ",
                        "Minial API", "gRPC", "MediatR", "Redis", "Docker",
                    ],
                },
                {
                    "name": "DATN-LKDT",
                    "role": None,
                    "team_size": None,
                    "start_date": "04/2024",
                    "end_date": "09/2024",
                    "github_url": "https://github.com/HiImLawtSimp1e/DATN-LKDT",
                    "description": "School Graduation Project. Experience Gained: Using ASP.NET API with EF Core ORM, building UI with Next.js & Tailwind CSS, authentication & authorization with JWT, create dynamic attributes (EAV data model).",
                    "tech_stack": [
                        "ASP.NET API", "EF Core ORM", "JWT", "TypeScript", "Next.js 14",
                        "Tailwind CSS",
                    ],
                },
            ],
            "skills": [
                "OOP", "SOLID", "ASP.NET Core", "EF Core ORM", "CQRS", "Vertical-Slice", "Clean Architecture",
                "Clean Architecture", "N-Layer", "MVC", "RESTful API", "gRPC", "RabbitMQ",
                "MSSQL", "MySQL", "PostgreSQL", "MongoDB", "Redis", "JWT",
                "TypeScript", "Next.js", "Tailwind CSS", "Git", "Docker",
            ],
            "certificates": [
                ".NET 8 Microservices: DDD, CQRS, Vertical/Clean Architecture (Udemy & Mehmet Ozkaya)",
            ],
            "honours": [],
            "languages": [],
        },
    },
    {
        "file": "3.txt",
        "profile": {
            "personal_info": {
                "full_name": "Phan Bảo",
                "email": "phangcbao250302@gmail.com",
                "phone": "0789944092",
                "github_url": None,
            },
            "objective": "Kỹ sư AI định hướng ứng dụng với nền tảng vững chắc về Machine Learning, NLP và hệ thống AI Agent. Mục tiêu của tôi là tham gia và đóng góp vào các dự án thực tế, mang lại giá trị từ AI thông qua tư duy sáng tạo, khả năng học hỏi nhanh và kinh nghiệm thực tập thực chiến. Trở thành một kỹ sư AI chuyên nghiệp, tham gia phát triển các hệ thống thông minh ứng dụng NLP, AI Agent và các mô hình RAG, với định hướng lâu dài là chuyên gia giải pháp AI trong doanh nghiệp.",
            "education": [
                {
                    "school": "Đại học Nguyễn Tất Thành",
                    "major": "Kỹ sư Công nghệ Thông tin",
                    "start_year": None,
                    "end_year": 2025,
                    "gpa": "3.74 / 4.0 – Xếp loại: Xuất sắc",
                }
            ],
            "experience": [
                {
                    "company": "Công ty Cổ phần Hệ sinh thái 365",
                    "job_title": "Thực tập sinh AI",
                    "start_date": "09/2024",
                    "end_date": "10/2024",
                    "description": [
                        "Dự án đã thực hiện: Xây dựng hệ thống đề xuất sản phẩm cho khách hàng.",
                        "Công nghệ sử dụng: Python, Scikit-learn, TensorFlow.",
                    ],
                },
                {
                    "company": "HPT Vietnam Corporation",
                    "job_title": "Thực tập sinh AI",
                    "start_date": "03/2025",
                    "end_date": "06/2025",
                    "description": [
                        "Xây dựng hệ thống AI Agent hỗ trợ tuyển dụng.",
                        "Thiết kế hệ thống RagDB phân loại cảnh báo.",
                        "Công nghệ sử dụng: Python, LangChain, LangGraph, Google-Gemini, Gradio.",
                    ],
                },
            ],
            "personal_projects": [],
            "skills": [
                "Scikit-learn", "TensorFlow", "PyTorch", "Machine Learning", "Deep Learning",
                "NLP", "AI Agent", "RAG", "LangChain", "LangGraph", "Prompt Engineering",
                "RAG Architecture", "RagDB", "Python", "SQL Server", "Mạng máy tính",
                "Google Colab", "Anaconda", "VSCode", "JupyterLab",
                "ChatGPT", "Copilot", "Midjourney", "Veo3",
                "Giao tiếp", "Thuyết trình", "Quản lý thời gian và công việc",
                "Làm việc nhóm", "Chịu áp lực tốt",
            ],
            "certificates": ["Kỹ năng làm chủ công việc"],
            "honours": ["GPA 3.74/4.0 – Xếp loại: Xuất sắc"],
            "languages": [
                {"language": "Tiếng Anh", "note": "Nghe 4/10 – Nói 6/10 - Đọc 8/10 – Viết 6/10"}
            ],
        },
    },
    {
        "file": "4.txt",
        "profile": {
            "personal_info": {
                "full_name": "Trần Hoàng Khải",
                "email": "thkhai0912@gmail.com",
                "phone": "0853367367",
                "github_url": "https://github.com/THKhai",
            },
            "objective": "I recently graduated with a degree in Information Systems from VNUHCM - University of Science and am seeking full-time opportunities as a Back-end Developer. I have hands-on experience building back-end systems using C#, ASP.NET Core, FastAPI, and Entity Framework Core for .NET and SQLAlchemy/SQLModel for FastAPI, with practical experience in HRM systems and e-commerce platforms. My current goal is to build a long-term commitment with the company in order to understand the work environment and gain valuable experience. I also aim to expand my knowledge about career development paths and future opportunities for personal growth in the IT field",
            "education": [
                {
                    "school": "VNUHCM - University of Science (HCMUS)",
                    "major": "Information Systems",
                    "start_year": 2021,
                    "end_year": None,
                    "gpa": None,
                }
            ],
            "experience": [],
            "personal_projects": [
                {
                    "name": "EC-AirBnB Auction",
                    "role": "Back-end Developer",
                    "team_size": 4,
                    "start_date": "06/2025",
                    "end_date": "09/2025",
                    "github_url": "https://github.com/vongagh094/ecommerce_be",
                    "description": "Full-stack Airbnb Clone Platform with clean architecture built using Next.js 15 frontend, FastAPI Python backend, and an advanced data crawling system. Features include real-time messaging via Pusher, PostgreSQL database with SQLAlchemy ORM, Redis caching, and RabbitMQ streaming for scalable property management, user authentication, and booking systems across Traveller, Host, and Admin interfaces. Responsibilities: developed the real-time bidding feature using RabbitMQ to publish and subscribe to bids, combined with Redis cache to boost performance in storing and querying bid data; established the clean architecture pattern, configured Docker for database containerization, and implemented dependency injection.",
                    "tech_stack": [
                        "Next.js 15", "FastAPI", "Python", "Pusher", "PostgreSQL",
                        "SQLAlchemy ORM", "Redis", "RabbitMQ", "Docker",
                    ],
                },
                {
                    "name": "Hospital management system",
                    "role": "Back-end Developer",
                    "team_size": 4,
                    "start_date": "08/2025",
                    "end_date": "09/2025",
                    "github_url": "https://github.com/THKhai/UDPT-Hospital-Management-System-BE",
                    "description": "Developed a microservices-based hospital management system with FastAPI and PostgreSQL handling 100+ requests/second during peak hours. Achieved sub-1-second API response times through optimized database queries, Redis caching, and Docker containerization with RabbitMQ message queuing. Developed a comprehensive JWT authentication system - implemented user login, registration, and session management with automatic token expiration, fully integrated with the user interface. Built user management APIs - created RESTful endpoints for patient profile management, including displaying user information, updating profile data, and serving the dashboard/home page content.",
                    "tech_stack": [
                        "FastAPI", "Python", "SQLAlchemy ORM", "PostgreSQL", "Redis",
                        "RabbitMQ", "Docker", "Next.js", "TypeScript", "MongoDB", "JWT",
                        "HTML/CSS", "JavaScript", "Bootstrap 5",
                    ],
                },
            ],
            "skills": [
                "C#", "C++", "Python", "ASP.NET Core", ".NET Framework", "RESTful APIs",
                "Entity Framework Core", "FastAPI", "SQLAlchemy", "SQLModel",
                "Microsoft SQL Server", "MongoDB", "Redis", "Cassandra", "Neo4j", "Oracle",
                "Postgres", "Docker", "Dependency Injection", "JWT", "ASP.NET Identity",
                "Swagger", "CORS", "WinForms", "React.js",
                "ETL", "Data preprocessing", "Tableau", "Git", "GitHub", "GitLab",
                "Teamwork", "Problem-solving", "Adaptability", "Time management",
                "Presentation skills", "Work under pressure", "Responsibility & accountability",
            ],
            "certificates": [],
            "honours": [
                "Redis Caching: Reduced bid query time from 1000ms to <1ms, achieving 99.9% cache hit rate and supporting 1000+ concurrent users",
                "RabbitMQ Streaming: Implemented asynchronous processing, handling 10,000+ bids/second with <50ms latency and zero message loss",
            ],
            "languages": [
                {"language": "English", "note": "Intermediate – capable of reading technical materials, following conversations, and using domain-specific vocabulary in simple discussions."}
            ],
        },
    },
    {
        "file": "5.txt",
        "profile": {
            "personal_info": {
                "full_name": "BÙI MẠNH KHƯƠNG",
                "email": "dochinhlatoi113@gmail.com",
                "phone": "0931492527",
                "github_url": None,
            },
            "objective": "Find a job in a professional, long-term environment. Being a calm person, quickly adapting to new environments, not afraid of difficulties, interested in finding solutions to problems.",
            "education": [
                {
                    "school": "ISPACE COLLEGE",
                    "major": "Network Administration",
                    "start_year": 2015,
                    "end_year": 2018,
                    "gpa": "6",
                }
            ],
            "experience": [
                {
                    "company": "LENGUYENDECOR - GOOWEB",
                    "job_title": "Dev",
                    "start_date": "03/2021",
                    "end_date": "04/2021",
                    "description": [
                        "Describe: Website design according to customer requirements.",
                        "Language: php, lavarel, html, css, js.",
                        "Fullstack.",
                    ],
                },
                {
                    "company": "NOITHATOHAHA-GOOWEB",
                    "job_title": "Dev",
                    "start_date": "04/2021",
                    "end_date": "05/2021",
                    "description": [
                        "Perform bug fixing, develop functionality based on existing functionality as requested by leader.",
                        "Language: reactjs, nodejs, mangeto.",
                    ],
                },
                {
                    "company": "CANON",
                    "job_title": "Dev",
                    "start_date": "11/2021",
                    "end_date": "09/2022",
                    "description": [
                        "Fix interface with reactjs.",
                        "Building on existing features (nodejs).",
                    ],
                },
                {
                    "company": "LIMITED LIABILITY COMPANY GOOWEB",
                    "job_title": "Dev",
                    "start_date": "03/2021",
                    "end_date": "11/2021",
                    "description": [
                        "Website selling furniture.",
                        "Functions: buy and sell, receive quotes, show products, contact.",
                        "Require: implement the entire website from FE to BE.",
                    ],
                },
                {
                    "company": "FPT SOFTWARE",
                    "job_title": "Dev",
                    "start_date": "11/2021",
                    "end_date": "09/2022",
                    "description": [
                        "Webapp to sell and manage call center admin.",
                        "The process of customers ordering products to the time of delivery.",
                    ],
                },
            ],
            "personal_projects": [],
            "skills": [
                "Word", "Excel", "Powerpoint", "Photoshop",
                "HTML", "CSS", "JS", "PHP", "Node.js",
                "MVC", "Windows", "Ubuntu",
                "Laravel", "ReactJS", "WordPress", "ExpressJS", "Bootstrap",
            ],
            "certificates": [],
            "honours": [],
            "languages": [],
        },
    },
    {
        "file": "6.txt",
        "profile": {
            "personal_info": {
                "full_name": "PHAM CHAU VO",
                "email": "phamchauvo219112001@gmail.com",
                "phone": "0834962086",
                "github_url": "https://github.com/vopham",
            },
            "objective": "To work hard and use my skills in the best possible way for achieving the company's goals. Mainly learn from the company's experience.",
            "education": [
                {
                    "school": "Can Tho University",
                    "major": "Information Technology",
                    "start_year": 2019,
                    "end_year": None,
                    "gpa": "3.13/4",
                }
            ],
            "experience": [],
            "personal_projects": [
                {
                    "name": "E-commerce website",
                    "role": None,
                    "team_size": None,
                    "start_date": None,
                    "end_date": None,
                    "github_url": None,
                    "description": "The website is currently running on localhost, allowing management and purchase of products. For users: Login, register, find products, add to cart, order. For administrator: Login, CRUD products, customer information management.",
                    "tech_stack": [
                        "HTML", "CSS", "Bootstrap", "VueJS", "Node.js (ExpressJS)",
                        "MySQL", "MongoDB", "Github", "Figma",
                    ],
                }
            ],
            "skills": [
                "HTML", "CSS", "Javascript", "Bootstrap", "VueJS", "Node.js (ExpressJS)",
                "MySQL", "MongoDB", "GitHub", "Figma", "Teamwork",
            ],
            "certificates": [],
            "honours": [],
            "languages": [
                {"language": "English", "note": "VSTEP-B1 - I can basic communicate and read, comprehend documents in English."}
            ],
        },
    },
]
