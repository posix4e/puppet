---
title: puppet 
colorTo: indigo
app_file: backend/backend.py
sdk: gradio
sdk_version: 3.36.1
python_version: 3.11.2
pinned: false
license: mit
---
Drive android with GPT


I was inspired by https://github.com/nat/natbot/blob/main/natbot.py, but this is for android instead of the web. It uses acceesibility to see, and additionally Android Intents to steer. Sometimes it needs the users' help because of android's security model. 


This is a 3 part system
- [puppet](puppet/README.md) The android app
- [backend](backend/README.md) A simple python backend
- [client](earth/README.md) A browser extension
# Deployment
- Here's my puppet backend https://posix4e-puppet.hf.space, you can push the repo to your own huggingspace to deploy it easily
- Check out the most recently released apk to try out the puppet without compiling code
# Planning 
We are using the github projects and issues features.
