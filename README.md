[![Tests](https://github.com/xaer981/hw05_final/actions/workflows/python-app.yml/badge.svg)](https://github.com/xaer981/hw05_final/actions/workflows/python-app.yml)

# Социальная сеть YaTube 📱

С помощью YaTube можно:
- 🙂 создавать свой профиль
- 🖼️ писать посты и прикреплять к ним картинки
- 🧑‍🤝‍🧑 комментировать посты других авторов
- ⭐ подписываться на других авторов
- 🌟 подписываться на группы по интересам
- 🎞️ прикреплять посты к группам по интересам

Кроме того, с помощью админ-панели можно:
- 📊 управлять объектами пользователей, постов, комментариев
- 🆕 создавать новые группы

> [!TIP]
> **Попробовать проект в работе можно [тут](http://yatube4k.pythonanywhere.com/)**


## Установка

1. Для начала склонируйте репозиторий к себе на машину:

   ```bash
   git clone https://github.com/xaer981/hw05_final.git
   ```

   ```bash
   cd hw05_final/
   ```

2. Затем создайте виртуальное окружение и установите зависимости:
   <details>
     <summary>Windows</summary>

     ```bash
     python -m venv venv
     ```

     ```bash
     source venv/Scripts/activate
     ```

     ```bash
     pip install -r requirements.txt
     ```
   </details>

   <details>
     <summary>Mac</summary>

      ```bash
      python3 -m venv venv
      ```

      ```bash
      source venv/bin/activate
      ```

      ```bash
      pip install -r requirements.txt
      ```
   </details>
3. После этого необходимо выполнить миграции:

   ```bash
   cd yatube/
   ```

   ```bash
   python manage.py migrate
   ```

4. Запускаем!

   ```bash
   python manage.py runserver
   ```

> [!TIP]
> Проект стал доступен по адресу `http://localhost:8000/`

<p align=center>
  <a href="url"><img src="https://github.com/xaer981/xaer981/blob/main/main_cat.gif" align="center" height="40" width="128"></a>
</p>
