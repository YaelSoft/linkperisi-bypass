# Resmi Python imajı
FROM python:3.10-slim

# Gerekli sistem paketlerinin kurulumu
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Google Chrome deposu için anahtarı yeni yöntemle ekliyoruz (apt-key yerine)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg

# Depoyu listeye ekliyoruz
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Chrome'u kuruyoruz
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Kütüphaneleri yüklüyoruz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyalıyoruz
COPY . .

# Sunucuyu başlatıyoruz
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
