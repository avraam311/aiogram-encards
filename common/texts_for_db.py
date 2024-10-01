from aiogram.utils.formatting import Bold, as_marked_section


categories = ["Фильмы/Сериалы", "Смотреть тут", "Вопросы для говорения", "Топики для чтения",
              "Книги для чтения", "Вопросы для письма", "Мемы", "Мотивация", "Грамматика",
              "Субтитры к фильмам"]

description_for_info_pages = {
    "main": "Добро пожаловать!",
    "words": as_marked_section(
        Bold("Изучение слов:"),
        "Добавить",
        "Удалить",
        "Заучить",
        marker="✅ ",
    ).as_html(),
    "listening": as_marked_section(
        Bold("Аудирование:"),
        "Что посмотреть?",
        "Аудировать",
        marker="✅ ",
    ).as_html(),
    "speaking": as_marked_section(
        Bold("Говорение:"),
        "Вопросы",
        marker="✅ ",
    ).as_html(),
    'reading': as_marked_section(
        Bold("Чтение:"),
        "Топики",
        "Книги",
        marker="✅ ",
    ).as_html(),
    'writing': as_marked_section(
        Bold("Письмо:"),
        "Вопросы",
        marker="✅ ",
    ).as_html(),
    'spec_pack': as_marked_section(
        Bold("Спец. пакет:"),
        "Мемы",
        "Мотивация",
        "Грамматика",
        "Сленг",
        "Тесты",
        marker="✅ ",
    ).as_html(),
}
