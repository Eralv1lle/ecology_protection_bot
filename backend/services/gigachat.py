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
        prompt = """Проанализируй это изображение на наличие экологических загрязнений.

    Если на фото есть мусор, свалка или другие загрязнения, опиши:
    1. Тип отходов - обязательно пиши с заглавной буквы, не все большие, а только первая (Пластик, Стекло, Металл, Органика, Строительный мусор, Химические отходы, Смешанные)
    2. Уровень опасности - также с заглавной, не все большие, а только первая (Низкий, Средний, Высокий, Критический)
    3. Краткое описание ситуации
    4. Рейтинг - сколько баллов дать пользователю за этот отчёт (от 5 до 30):
       - 5-10: незначительное загрязнение (немного мусора)
       - 11-15: среднее загрязнение (мусор, но не критично)
       - 16-20: серьёзное загрязнение (много мусора или опасные отходы)
       - 21-30: критическое загрязнение (свалка, химикаты, большая опасность)

    Ответ дай строго в формате JSON:
    {
        "is_pollution": true/false,
        "waste_type": "Тип отходов",
        "danger_level": "Уровень опасности",
        "description": "описание ситуации",
        "rating_points": число от 5 до 30
    }

    Если на фото нет загрязнений, верни:
    {
        "is_pollution": false,
        "message": "На фото нет экологических загрязнений"
    }"""

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
