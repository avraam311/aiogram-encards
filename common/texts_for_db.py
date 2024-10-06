from aiogram.utils.formatting import Bold, as_marked_section


categories = ["Аудирование", "Говорение", "Чтение", "Письмо", "Спец. пакет"]

sub_categories = {"Фильмы/Сериалы": 1,
                  "Смотреть тут": 1,
                  "Вопросы для говорения": 2,
                  "Топики для чтения": 3,
                  "Книги для чтения": 3,
                  "Вопросы для письма": 4,
                  "Мемы": 5,
                  "Мотивация": 5,
                  "Грамматика": 5,
                  "Субтитры к фильмам": 5,
                  }

description_for_info_pages = {
    "main": "Добро пожаловать!",
    "read!": "Обязательно для прочтения для всех",
    "spec_pack": as_marked_section(
        Bold("Спец. пакет включает в себя:\n"),
        "Мемы",
        "Мотивация",
        "Грамматика",
        "Сленг",
        "Тесты",
        marker="✅ ",
    ).as_html(),
    "catalog": "Категории:\n",
    "sub_catalog": "Подкатегории:\n",
    "media": "Список медиа пуст\n",
    "words_catalog": "Каталоги слов\n",
    "words_sub_catalog": "У вас 0 пакетов слов\n",
    "words": "Вот ваши слова\n"
}
