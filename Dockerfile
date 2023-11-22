FROM python:3.8

WORKDIR /usr/src/app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y \
    mongodb-clients

ENV MONGODB_ATLAS_URI=mongodb+srv://Itzzteletech:Devaismadman@cluster0.ehgdefs.mongodb.net/?retryWrites=true&w=majority

ENV TELEGRAM_BOT_TOKEN=6401687982:AAFb01-nccjXKa0dAmySwZ3YsDaZG3C6xEA

CMD ["python", "your_bot_script.py"
