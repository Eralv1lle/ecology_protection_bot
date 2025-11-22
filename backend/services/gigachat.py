import os
import json
from gigachat import GigaChat
from dotenv import load_dotenv

load_dotenv()


class GigaChatService:
    def __init__(self):
        self.credentials = os.getenv("GIGACHAT_API_TOKEN")
        self.model = "GigaChat-Pro"

        if not self.credentials:
            raise ValueError("Укажите GIGACHAT_API_TOKEN в .env")

    def analyze_image(self, image_path: str):
        prompt = """
Проанализируй изображение и определи:
1) Есть ли на фото экологическое загрязнение.
2) Тип отходов (пластик, стекло, металл, органика, строительный мусор, химические отходы, смешанные).
3) Уровень опасности (Низкий, Средний, Высокий, Критический).
4) Краткое описание.

Верни строго JSON:
{
    "is_pollution": true/false,
    "waste_type": "...",
    "danger_level": "...",
    "description": "..."
}

Если загрязнений нет, верни:
{
    "is_pollution": false,
    "message": "На фото нет экологических загрязнений"
}
"""

        with GigaChat(
            credentials=self.credentials,
            verify_ssl_certs=False,
            model=self.model
        ) as giga:
            with open(image_path, "rb") as file:
                file_obj = giga.upload_file(file)

            response = giga.chat(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                            "attachments": [file_obj.id_],
                        }
                    ],
                    "temperature": 0.7
                }
            )

        text = response.choices[0].message.content

        try:
            text_clean = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_clean)
        except json.JSONDecodeError:
            return {
                "is_pollution": False,
                "message": "Не удалось распарсить JSON",
                "raw": text
            }

gigachat_service = GigaChatService()
