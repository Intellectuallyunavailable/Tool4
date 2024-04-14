from flask import Flask
from flask_cors import CORS
from sqlalchemy import create_engine
import pandas as pd  # Importing pandas for data manipulation
import numpy as np  # Importing numpy for numerical operations
import matplotlib.pyplot as plt  # Importing matplotlib for plotting
import seaborn as sns  # Importing seaborn for enhanced visualization

# Flask application setup
app = Flask(__name__)
CORS(app)

# PostgreSQL connection using SQLAlchemy
def get_db_connection():
    engine = create_engine('postgresql://sheshank_sonji_user:Lo2Ze5zVZSRPGxDLCg5WAKUXUfxo7rrZ@dpg-cobrpren7f5s73ftpqrg-a.oregon-postgres.render.com/sheshank_sonji')
    conn = engine.connect()
    return conn

# Load the dataset from PostgreSQL using SQLAlchemy
def load_data():
    conn = get_db_connection()
    query = """
            SELECT district_name AS District_Name, year AS Year, month AS Month, age AS Age, profession AS Profession, sex AS Sex, count(*) as Count
            FROM tool4
            GROUP BY district_name, year, month, age, profession, sex
            ORDER BY district_name, year, month, age, profession, sex;
            """
    data = pd.read_sql_query(query, conn)
    conn.close()
    return data

# Load data from PostgreSQL
data = load_data()

# Adjust age probability values to increase importance
age_probabilities = {
    '0-20': 0.1,
    '21-30': 0.3,
    '31-40': 0.5,
    '41-50': 0.6,
    '51-60': 0.5,
    '61-70': 0.3,
    '71+': 0.1
}

# Calculate profession occurrence counts
profession_counts = data['profession'].value_counts()

# Select the top 15 occurring professions
top_professions = profession_counts.head(15).index.tolist()

# Assign values to professions based on occurrence counts
profession_values = {}
max_value = 20
min_value = 1
max_count = profession_counts.max()
min_count = profession_counts.min()
for profession, count in profession_counts.items():
    if profession in top_professions:
        scaled_value = min_value + (count - min_count) * (max_value - min_value) / (max_count - min_count)
        profession_values[profession] = scaled_value

# Clean up 'AgeGroup' column and ensure all values are strings
data['age'] = pd.to_numeric(data['age'], errors='coerce')

# Considering gender distribution
total_accused = len(data)
male_count = data['sex'].value_counts().get('MALE', 0)
female_count = data['sex'].value_counts().get('FEMALE', 0)
male_probability = male_count / total_accused
female_probability = female_count / total_accused

# Define the additional contribution for gender
male_contribution = 0.1  # Adjust as needed
female_contribution = 0.05  # Adjust as needed

# Group age into predefined age ranges
age_bins = [0, 20, 30, 40, 50, 60, 70, np.inf]
age_labels = ['0-20', '21-30', '31-40', '41-50', '51-60', '61-70', '71+']
data['AgeGroup'] = pd.cut(data['age'], bins=age_bins, labels=age_labels, right=False).astype(str)

# Combine probabilities
data['CriminalityProbability'] = (data['AgeGroup'].map(age_probabilities) +
                                  data['profession'].map(profession_values) +
                                  np.where(data['sex'] == 'MALE', male_contribution, female_contribution))

# Output the CriminalityProbability for each data entry
print(data[['CriminalityProbability']])

# Crimes by profession (Top 15 occurring professions)
plt.figure(figsize=(12, 6))
sns.countplot(x='profession', data=data[data['profession'].isin(top_professions)], order=top_professions)
plt.title('Crimes by profession (Top 15)')
plt.xlabel('profession')
plt.ylabel('Number of Crimes')
plt.xticks(rotation=90)
plt.show()

# Start the Flask application (optional, depending on your deployment setup)
if __name__ == '__main__':
    app.run(debug=True)
