import gdown

file_ids = {
    "model1.pkl": "1UWOMvBdwmBFovuXsAm9VlfXuGlK1O77m",
    "model2.pkl": "15JtCyS6U1wbHIXFJbNryPi1V3qhk5UKa",
    "model3.pkl": "1LRMuGi8JbMVUo6zST5qCK-G_nafui6rL",
    "model4.pkl": "1yCCY_1DIjr-ggUgSGIiXZFPF9r6YyCBk",
    "model5.pkl": "12dfT9AI3uLtZN1Vo4lijVmxz9MXqaR4l",
    "model6.pkl": "1sBUMbejCBeII-WOvrEYVCveV_Sol8TxE",
}

for filename, file_id in file_ids.items():
    url = f"https://drive.google.com/uc?id={file_id}"
    print(f"Downloading {filename}...")
    gdown.download(url, filename, quiet=False)
