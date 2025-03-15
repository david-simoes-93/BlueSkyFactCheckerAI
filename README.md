# BlueSky FactCheckerAI

## A bot that fact checks text posts when tagged. [Profile Link](https://bsky.app/profile/factcheckerai.bsky.social)

# Deployment

Create a BlueSky account (like [FactCheckerAI](https://bsky.app/profile/factcheckerai.bsky.social)), and generate an ATP password in the Settings. Export those before running the bot.

    export ATP_AUTH_HANDLE="FactCheckerAI.bsky.social"
    export ATP_AUTH_PASSWORD="some-thing-some-thing"

Install python deps (for example, with virtualenv):

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate

Install [LM Studio](https://lmstudio.ai/download), and download desired LLM ([Mistral Nemo](https://lmstudio.ai/model/mistral-nemo-instruct-2407) in this case). Run LM Studio once, then start the LM Studio CLI server

    lms server start
    lms server status

Run bot with 

    source venv/bin/activate
    python3 bot.py
    deactivate
