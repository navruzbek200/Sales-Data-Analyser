# 📊 Sales Data Analyzer

AI-powered satish ma'lumotlari tahlil qiluvchi Streamlit app.

## 🚀 Streamlit Cloud'da Deploy qilish

### 1. GitHub repository yarating
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/sales-analyzer.git
git push -u origin main
```

### 2. Streamlit Cloud'da deploy qiling
1. [share.streamlit.io](https://share.streamlit.io) ga kiring
2. GitHub account bilan login qiling
3. **"New app"** tugmasini bosing
4. Repository, branch va `app.py` ni tanlang
5. **"Advanced settings"** → **"Secrets"** bo'limiga qo'shing:

```toml
ANTHROPIC_API_KEY = "sk-ant-sizning-api-kalitingiz"
```

6. **"Deploy!"** tugmasini bosing

### 3. URL olasiz
Deploy tugagandan so'ng siz quyidagi formatda URL olasiz:
```
https://username-sales-analyzer-app-xxxxx.streamlit.app
```

---

## 🧪 Lokal ishga tushirish

```bash
pip install -r requirements.txt

# .streamlit/secrets.toml fayliga API key qo'shing
echo 'ANTHROPIC_API_KEY = "sk-ant-..."' > .streamlit/secrets.toml

streamlit run app.py
```

---

## 📁 Fayl tuzilishi

```
sales-analyzer/
├── app.py                  # Asosiy Streamlit ilovasi
├── requirements.txt        # Python dependencies
├── sample_data.csv         # Test uchun namuna ma'lumotlar
├── .streamlit/
│   └── secrets.toml        # API kalitlar (gitignore qiling!)
└── README.md
```

---

## ✨ Xususiyatlar

- 📂 **CSV / Excel yuklash** — drag & drop fayl uploader
- 📈 **Metric cards** — avtomatik daromad, miqdor, foyda ko'rsatkichlari
- 📋 **Data table** — qidiruv va filtrlash bilan
- 📊 **Interaktiv grafiklar** — bar chart, pie chart, time series
- 🤖 **AI chat** — Claude bilan natural language orqali tahlil
- 🇺🇿 **O'zbekcha** qo'llab-quvvatlash

---

## 🔑 Anthropic API Key olish

1. [console.anthropic.com](https://console.anthropic.com) ga kiring
2. **API Keys** bo'limiga o'ting
3. **"Create Key"** tugmasini bosing
4. Kalit nusxasini oling va secrets.toml ga qo'shing
