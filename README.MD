📌 Project Overview
Bhopal is officially designated as a Smart City under the Government of India'sSmart Cities Mission. This project audits whether the Smart City promise is being
delivered — using data across 4 critical dimensions: 
🏛️ Smart City Delivery - Are projects being completed on time and on budget?
🌿 Environment & Lakes - Is Bhopal's air and water quality improving?
🏥 Healthcare Access - Are hospital facilities distributed fairly across zones?
📋 Citizen Grievances - Are civic complaints being resolved effectively?

🔧 Tools & Technologies
Python - Data generation, EDA, 
PostgreSQL - Central data warehouse
KNIME - Visual ETL pipeline — data cleaning & transformation
Power BI - Interactive 5-page intelligence dashboard
Jupyter Notebook- Exploratory data analysis

Note: Data is synthetically generated using real Bhopal ward names,zone demographics, and realistic parameter ranges based on publicly available Smart City Mission reports.

📈 Key Findings

🏛️ Smart City Delivery

Only 20% of projects fully delivered despite 53% budget utilization
New Bhopal received 3× more investment than Periphery zones
22 out of 25 projects are Ongoing, Delayed or Not Started

🌿 Environment

Winter AQI averages 174 — classified as Poor
89 unhealthy air quality days recorded across the study period
Lower Lake records Heavily Polluted months regularly while Upper Lake remains cleaner

🏥 Healthcare

City average of only 1.78 beds per 1000 population
Periphery zone critically underserved with minimal hospital presence
Old Bhopal wards show under 0.4 beds per 1000 people

📋 Citizen Grievances

560K complaints recorded with only 64.43% resolution rate
199K complaints remain unresolved
Water Supply takes longest to resolve — averaging 9+ days

bhopal-smart-city-analysis/
│
├── data/
│   ├── raw/              ← generated datasets
│   └── cleaned/          ← KNIME output
│
├── sql/
│   ├── schema.sql        ← database schema
│
├── knime/
│   └── workflow/         ← KNIME ETL export
│
├── notebooks/
│   └── eda.ipynb         ← Python EDA
│
├── powerbi/
│   └── bhopal_analysis.pbix
│
│
├── generate_data.py      ← synthetic data generator
├── load_data.py          ← PostgreSQL data loader
└── README.MD

👤 Author
Om Jitpure
Aspiring Data Analyst | Bhopal, Madhya Pradesh
Tools: Python | SQL | Power BI | KNIME
