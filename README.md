# Crop Recommendation System 🌾

A **web application** that recommends crops to farmers based on soil and environmental data. This system uses **AI/ML models** to suggest the most suitable crops along with their **current market price, cultivation tips, season, description, and image**.

---

## **Features**

- **Landing Page**  
  - Modern, responsive UI with navigation: Home, Features, About, Contact, and Sign In.
  - Brief info about the system and its mission.
  - “Get Started” button redirects to dashboard after login/signup.

- **Dashboard**  
  - User-friendly interface for farmers to input data (soil, region, etc.).
  - AI-powered crop recommendations with confidence levels.
  - Detailed crop information:
    - Description
    - Current price (real-time)
    - Season
    - Cultivation tips
    - Crop image

- **AI Model**  
  - Uses a **Random Forest classifier** trained on crop and soil data.
  - Provides multiple crop recommendations for better flexibility.
  - Confidence score included for each recommendation.

- **Automated JSON Data**  
  - Crop info is stored in a JSON file with image URLs, descriptions, tips, season, and price.
  - Supports automatic updates using Gemini AI API for real-time information.
  - Images fetched from copyright-free sources (Pixabay).

---

## **Installation**

1. Clone the repository:

```bash
git clone https://github.com/username/crop-recommendation-system.git
```

2. Navigate into the project folder:
   ```bash
   cd crop-recommendation-system
    ```

3. python app.py
```bash
python app.py
```

4. Open the frontend in a browser http://127.0.0.1:5000

- **Usage**
1. Open the landing page.
2. Click Get Started.
3. Enter your soil details, Temperature, and other required data in the dashboard.
4. View recommended crops with:
  - Description
  - Current price
  - Season
  - Cultivation tips
  - Crop image
