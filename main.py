"""
!pip install -q groq gradio
"""

from groq import Groq
import gradio as gr
import json
import random
from datetime import datetime
from typing import List, Dict
import os


STUDENTS_DB = {
    "test@lpnu.ua": {"name": "Тестовий Студент", "active": True},
}

NLP_TOPICS = [
    "Tokenization та Word Embeddings",
    "Transformer Architecture та Self-Attention",
    "BERT та Masked Language Modeling",
    "GPT моделі та Autoregressive Generation",
    "Fine-tuning та Transfer Learning",
    "Named Entity Recognition (NER)",
    "Machine Translation та Seq2Seq",
    "Text Classification та Sentiment Analysis",
    "Question Answering Systems",
    "Prompt Engineering та Few-Shot Learning",
]

EXAM_RESULTS = []
CURRENT_EXAMS = {}


def start_exam(email: str, name: str) -> dict:
    if email in CURRENT_EXAMS:
        return {
            "success": False,
            "message": f"Іспит уже розпочато для {name}. Завершіть попередній іспит перед стартом нового."
        }

    if email not in STUDENTS_DB:
        return {
            "success": False,
            "message": f"Студента {email} не знайдено в базі.\n\nДоступні студенти:\n" +
                       "\n".join([f"• {e}" for e in list(STUDENTS_DB.keys())[:3]])
        }

    student_info = STUDENTS_DB[email]
    if not student_info["active"]:
        return {"success": False, "message": "Ваш акаунт неактивний"}

    num_topics = random.randint(2, 3)
    selected_topics = random.sample(NLP_TOPICS, num_topics)

    CURRENT_EXAMS[email] = {
        "name": name,
        "email": email,
        "start_time": datetime.now().isoformat(),
        "topics": selected_topics,
        "current_topic_index": 0,
        "questions_on_topic": 0,
        "answers": []
    }

    print(f"Іспит розпочато для {name}")
    print(f"Теми: {', '.join(selected_topics)}")

    return {
        "success": True,
        "topics": selected_topics,
        "student_name": name,
        "message": f"Іспит успішно розпочато для {name}!\n\nВаші теми:\n" +
                   "\n".join([f"{i + 1}. {t}" for i, t in enumerate(selected_topics)])
    }


def next_topic(email: str) -> dict:
    print(f"next_topic викликано для {email}")

    if email not in CURRENT_EXAMS:
        return {
            "success": False,
            "message": "Не знайдено активного іспиту"
        }

    exam = CURRENT_EXAMS[email]
    exam["current_topic_index"] += 1
    exam["questions_on_topic"] = 0

    new_index = exam["current_topic_index"]
    topics = exam["topics"]

    print(f"Перейшли на тему {new_index + 1}/{len(topics)}")

    if new_index >= len(topics):
        return {
            "success": True,
            "finished": True,
            "message": "Всі теми пройдено! Час завершувати іспит."
        }

    return {
        "success": True,
        "finished": False,
        "current_topic": topics[new_index],
        "topic_number": new_index + 1,
        "total_topics": len(topics),
        "message": f"Переходимо до теми {new_index + 1}/{len(topics)}: {topics[new_index]}"
    }


def end_exam(email: str, score: float, feedback: str) -> dict:
    print(f"end_exam викликано: {email}, оцінка={score}")

    if email not in CURRENT_EXAMS:
        return {
            "success": False,
            "message": "Не знайдено активного іспиту для цього email"
        }

    exam_info = CURRENT_EXAMS[email]
    end_time = datetime.now()
    start_time = datetime.fromisoformat(exam_info["start_time"])
    duration = (end_time - start_time).total_seconds() / 60

    result = {
        "email": email,
        "name": exam_info["name"],
        "score": round(score, 1),
        "start_time": exam_info["start_time"],
        "end_time": end_time.isoformat(),
        "duration_minutes": round(duration, 2),
        "topics": exam_info["topics"],
        "feedback": feedback,
        "answers_count": len(exam_info.get("answers", []))
    }

    EXAM_RESULTS.append(result)
    del CURRENT_EXAMS[email]

    if score >= 9:
        grade = "Відмінно!"
    elif score >= 7:
        grade = "Добре!"
    elif score >= 5:
        grade = "Задовільно"
    else:
        grade = "Потрібно вчити"

    print(f"Іспит завершено! Оцінка: {score}/10, Grade: {grade}")

    return {
        "success": True,
        "score": score,
        "grade": grade,
        "duration": duration,
        "message": f"{grade}\n\nВаша оцінка: {score}/10\nТривалість: {duration:.1f} хв"
    }


def get_statistics() -> str:
    try:
        if not EXAM_RESULTS:
            return "Ще немає завершених іспитів"

        scores = [r["score"] for r in EXAM_RESULTS]

        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        total_exams = len(EXAM_RESULTS)
        total_time = sum(r["duration_minutes"] for r in EXAM_RESULTS)

        stats = f"СТАТИСТИКА ІСПИТІВ\n"
        stats += "=" * 50 + "\n\n"
        stats += f"ЗАГАЛЬНІ ПОКАЗНИКИ:\n"
        stats += f"Всього проведено іспитів: {total_exams}\n"
        stats += f"Середня оцінка: {avg_score:.2f}/10\n"
        stats += f"Найвища оцінка: {max_score}/10\n"
        stats += f"Найнижча оцінка: {min_score}/10\n"
        stats += f"Загальний час: {total_time:.1f} хвилин\n\n"
        stats += "=" * 50 + "\n\n"
        stats += "ОСТАННІ 5 СТУДЕНТІВ:\n\n"

        for i, r in enumerate(EXAM_RESULTS[-5:], 1):
            stats += f"{i}. {r['name']}\n"
            stats += f"   Оцінка: {r['score']}/10\n"
            stats += f"   Час: {r['duration_minutes']:.1f} хв\n"
            topic_list = ", ".join(r['topics'][:2])
            if len(r['topics']) > 2:
                topic_list += ", ..."
            stats += f"   Теми: {topic_list}\n\n"

        return stats

    except Exception as e:
        return f"Помилка при обчисленні статистики: {str(e)}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "start_exam",
            "description": "Розпочати іспит ТІЛЬКИ коли студент чітко надав ІМ'Я та EMAIL. Викликай ОДИН РАЗ!",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email студента: name@lpnu.ua (наприклад test@lpnu.ua)"
                    },
                    "name": {
                        "type": "string",
                        "description": "Повне ім'я студента (наприклад 'Іван Петренко')"
                    }
                },
                "required": ["email", "name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "next_topic",
            "description": "Перейти на НАСТУПНУ тему іспиту. Викликай коли задав 3-4 запитання на поточній темі АБО студент не знає тему.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email студента"
                    }
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "end_exam",
            "description": "Завершити іспит ТІЛЬКИ ПІСЛЯ того як next_topic повернув finished=True. Дай справедливу оцінку.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email студента"
                    },
                    "score": {
                        "type": "number",
                        "description": "Оцінка 0-10 (може бути 7.5). Оцінюй справедливо!"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "Мінімум 3-4 речення: що знає добре, над чим попрацювати"
                    }
                },
                "required": ["email", "score", "feedback"]
            }
        }
    }
]


def execute_function(function_name: str, arguments: dict) -> dict:
    print(f"Виконую функцію: {function_name}")
    print(f"Аргументи: {arguments}")

    try:
        if function_name == "start_exam":
            result = start_exam(arguments["email"], arguments["name"])
        elif function_name == "next_topic":
            result = next_topic(arguments["email"])
        elif function_name == "end_exam":
            result = end_exam(
                arguments["email"],
                float(arguments["score"]),
                arguments["feedback"]
            )
        else:
            result = {"success": False, "message": f"Невідома функція: {function_name}"}

        print(f"Результат: {result}")
        return result

    except Exception as e:
        print(f"Помилка: {e}")
        return {"success": False, "message": f"Помилка: {str(e)}"}


SYSTEM_PROMPT = """Ти - професійний AI екзаменатор курсу Natural Language Processing (NLP).

МОВА: ТІЛЬКИ УКРАЇНСЬКА!

ЕТАП 1: ПОЧАТОК
1. Привітай студента
2. Запитай ім'я та email
3. ЧЕКАЙ повну інформацію (наприклад: "Іван Петренко, test@lpnu.ua")
4. ТІЛЬКИ ТОДІ викликай start_exam

ЕТАП 2: ІСПИТ ПО ТЕМАХ
1. Отримавши теми - почни з першої
2. Задавай 3-4 запитання на КОЖНУ тему:
   - Перше запитання - базове
   - Наступні - глибші
   - Адаптуй складність під студента

3. ПІСЛЯ 3-4 запитань на темі:
   - Викликай next_topic (передай email)
   - Якщо next_topic повернув finished=False:
     * Продовжуй з наступною темою
     * Знову задай 3-4 запитання
   - Якщо next_topic повернув finished=True:
     * ВСІ ТЕМИ ПРОЙДЕНО!
     * ВІДРАЗУ викликай end_exam

ЕТАП 3: ЗАВЕРШЕННЯ
- Викликай end_exam ТІЛЬКИ коли next_topic повернув finished=True
- Дай чесну оцінку 0-10
- Напиши детальний відгук (3-4 речення мінімум)

ОЦІНЮВАННЯ:
9-10: Глибоке розуміння, деталі, приклади
7-8: Хороше розуміння основ
5-6: Базове розуміння
3-4: Слабке розуміння
0-2: Не знає

ВАЖЛИВІ ПРАВИЛА:
-ГОВОРИ ТІЛЬКИ УКРАЇНСЬКОЮ
- ВИКЛИКАЙ next_topic після 3-4 запитань на темі
- ВИКЛИКАЙ end_exam тільки коли finished=True
- НЕ переходь на наступну тему без виклику next_topic
- Будь чесним екзаменатором

ПРИКЛАД ПРАВИЛЬНОЇ ПОСЛІДОВНОСТІ:
1. start_exam -> отримав 3 теми
2. Задаєш 3-4 запитання на тему 1
3. next_topic->отримав тему 2
4. Задаєш 3-4 запитання на тему 2
5. next_topic->отримав тему 3
6. Задаєш 3-4 запитання на тему 3
7. next_topic->finished=True
8. end_exam->іспит завершено!
"""


def get_current_topic(email: str):
    exam = CURRENT_EXAMS.get(email)
    if not exam:
        return None
    idx = exam.get("current_topic_index", 0)
    if idx >= len(exam.get("topics", [])):
        return None
    return exam["topics"][idx]


def get_exam_progress(email: str) -> dict:
    exam = CURRENT_EXAMS.get(email)
    if not exam:
        return {"active": False}

    idx = exam.get("current_topic_index", 0)
    topics = exam.get("topics", [])
    questions = exam.get("questions_on_topic", 0)

    return {
        "active": True,
        "current_topic": topics[idx] if idx < len(topics) else None,
        "topic_index": idx,
        "total_topics": len(topics),
        "questions_on_topic": questions,
        "all_topics_done": idx >= len(topics)
    }


def chat_with_groq(message: str, history: List[List[str]], api_key: str) -> tuple:

    if not api_key:
        error = """Будь ласка, введіть API ключ Groq!

Як отримати (1 хвилина):
1. Перейдіть на https://console.groq.com/
2. Зареєструйтесь (безкоштовно, БЕЗ картки!)
3. Перейдіть у розділ "API Keys"
4. Натисніть "Create API Key"
5. Скопіюйте ключ (починається з gsk_)
6. Вставте вище"""
        return history + [[message, error]], history

    if not api_key.startswith("gsk_"):
        error = "Невірний формат ключа Groq. Ключ має починатися з 'gsk_'"
        return history + [[message, error]], history

    try:
        client = Groq(api_key=api_key)

        active_email = next(iter(CURRENT_EXAMS.keys()), None)
        progress = get_exam_progress(active_email) if active_email else {"active": False}

        print(f" Прогрес: email={active_email}")
        if progress["active"]:
            print(f"   Тема {progress['topic_index']+1}/{progress['total_topics']}: {progress['current_topic']}")
            print(f"   Запитань на темі: {progress['questions_on_topic']}")
            print(f"   Всі теми пройдено: {progress['all_topics_done']}")

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if progress["active"] and progress["current_topic"]:
            context = f"""
ПОТОЧНИЙ СТАН ІСПИТУ:
- Тема {progress['topic_index']+1}/{progress['total_topics']}: {progress['current_topic']}
- Запитань на цій темі: {progress['questions_on_topic']}

{"УВАГА: Задав вже " + str(progress['questions_on_topic']) + " запитань на цій темі!" if progress['questions_on_topic'] >= 3 else ""}
{" ЧАС ВИКЛИКАТИ next_topic!" if progress['questions_on_topic'] >= 3 else "Продовжуй задавати запитання по цій темі"}
            """
            messages.append({"role": "system", "content": context})

        for user_msg, assistant_msg in history:
            messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})

        messages.append({"role": "user", "content": message})

        available_tools = []

        if not progress["active"]:
            available_tools = [t for t in TOOLS if t["function"]["name"] == "start_exam"]
            print("🔧 Режим: очікування start_exam")

        elif progress["all_topics_done"]:
            available_tools = [t for t in TOOLS if t["function"]["name"] == "end_exam"]
            print(" Режим: ДОЗВОЛЕНО end_exam (всі теми пройдено)")

        else:
            available_tools = [t for t in TOOLS if t["function"]["name"] == "next_topic"]
            print(f" Режим: дозволено next_topic (питань на темі: {progress['questions_on_topic']})")

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=available_tools if available_tools else None,
            tool_choice="auto" if available_tools else "none",
            max_tokens=500,
            temperature=0.7
        )

        max_iterations = 3
        iteration = 0

        while (response.choices[0].finish_reason == "tool_calls" and iteration < max_iterations):
            iteration += 1
            print(f"\n Ітерація {iteration}: обробка tool calls")

            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                break

            print(f"   Знайдено {len(tool_calls)} tool call(s)")
            messages.append(response.choices[0].message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                try:
                    arguments = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                result = execute_function(function_name, arguments)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })

            progress = get_exam_progress(active_email) if active_email else {"active": False}

            if not progress["active"]:
                available_tools = [t for t in TOOLS if t["function"]["name"] == "start_exam"]
            elif progress["all_topics_done"]:
                available_tools = [t for t in TOOLS if t["function"]["name"] == "end_exam"]
            else:
                available_tools = [t for t in TOOLS if t["function"]["name"] == "next_topic"]

            print(f"   Follow-up запит...")
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=available_tools if available_tools else None,
                tool_choice="auto" if available_tools else "none",
                max_tokens=500,
                temperature=0.7
            )

        assistant_message = ""
        if response.choices and response.choices[0].message.content:
            assistant_message = response.choices[0].message.content
        else:
            assistant_message = "Вибачте, я не можу відповісти. Спробуйте переформулювати питання."

        print(f"💬 Відповідь: {assistant_message[:100]}...")

        if active_email and active_email in CURRENT_EXAMS and not progress["all_topics_done"]:
            CURRENT_EXAMS[active_email]["questions_on_topic"] += 1

        history.append([message, assistant_message])
        return history, history

    except Exception as e:
        error_msg = f"Помилка: {str(e)}\n\n"

        if "authentication" in str(e).lower() or "api key" in str(e).lower():
            error_msg += "Перевірте API ключ:\n"
            error_msg += "- Ключ має починатися з 'gsk_'\n"
            error_msg += "- Створіть новий на https://console.groq.com/\n"
        elif "rate" in str(e).lower() or "limit" in str(e).lower():
            error_msg += "Перевищено ліміт запитів.\n"
        else:
            error_msg += f"Деталі: {str(e)}"

        print(f" ПОМИЛКА: {e}")
        history.append([message, error_msg])
        return history, history


def create_interface():
    with gr.Blocks(
            title="AI Examiner - Groq",
            theme=gr.themes.Soft(primary_hue="purple", secondary_hue="blue")
    ) as demo:
        gr.Markdown("""
#  AI Examiner Agent - NLP Course

### Швидкий старт:

1. **Отримайте API ключ :**
   - https://console.groq.com/
   - Зареєструйтесь (безкоштовно!)
   - API Keys->Create API Key
   - Скопіюйте ключ (gsk_...)

2. **Вставте ключ** у поле нижче

3. **Почніть іспит:**
   - Напишіть: "Привіт! Я [Ім'я], email: [email@lpnu.ua]"

### Тестові студенти:
- test@lpnu.ua - Тестовий Студент
        """)

        with gr.Row():
            api_key_input = gr.Textbox(
                label=" Groq API Key",
                placeholder="gsk_...",
                type="password",
                info="Отримайте на https://console.groq.com/",
                scale=3
            )
            stats_btn = gr.Button("Статистика", scale=1, variant="secondary")

        chatbot = gr.Chatbot(
            label="Чат з екзаменатором (Llama 3.3 70B)",
            height=500,
            show_copy_button=True,
            avatar_images=(None, None)
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Ваше повідомлення",
                placeholder="Напишіть тут...",
                lines=2,
                scale=4
            )
            with gr.Column(scale=1):
                send_btn = gr.Button(" Відправити", variant="primary")
                clear_btn = gr.Button(" Новий іспит")

        stats_output = gr.Textbox(
            label="Результати",
            lines=15,
            interactive=False,
            visible=True
        )

        chat_state = gr.State([])

        def show_stats():
            return get_statistics()

        msg.submit(
            chat_with_groq,
            inputs=[msg, chat_state, api_key_input],
            outputs=[chatbot, chat_state]
        ).then(
            lambda: "",
            outputs=[msg]
        )

        send_btn.click(
            chat_with_groq,
            inputs=[msg, chat_state, api_key_input],
            outputs=[chatbot, chat_state]
        ).then(
            lambda: "",
            outputs=[msg]
        )

        clear_btn.click(
            lambda: ([], []),
            outputs=[chatbot, chat_state]
        )

        stats_btn.click(
            show_stats,
            outputs=[stats_output]
        )

    return demo


if __name__ == "__main__":
    demo = create_interface()
    demo.launch(
        share=True,
        debug=True,
        show_error=True
    )